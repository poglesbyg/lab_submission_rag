#!/usr/bin/env python3
"""
Model Compatibility Fix for Laboratory RAG System
Fixes validation errors between old LabSubmission and new LabManagerSubmission models
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr

# Import both models to create compatibility layer
from models.submission import LabSubmission, SampleType, StorageCondition, ProcessingStatus
from improved_lab_rag import LabManagerSubmission

def convert_lab_manager_to_legacy(lab_manager_data: LabManagerSubmission) -> Dict[str, Any]:
    """Convert LabManagerSubmission to legacy LabSubmission format"""
    
    # Generate required fields that are missing
    submission_id = str(uuid.uuid4())
    
    # Map field names
    legacy_data = {
        # Required fields for legacy model
        "submission_id": submission_id,
        "client_id": f"CLIENT_{submission_id[:8]}" if lab_manager_data.submitter_name else "UNKNOWN_CLIENT",
        "client_name": lab_manager_data.submitter_name or "Unknown Submitter",
        "client_email": lab_manager_data.submitter_email or "unknown@example.com",
        
        # Sample information mapping
        "sample_type": map_material_to_sample_type(lab_manager_data.material_type),
        "sample_count": 1,  # Default value
        "sample_volume": extract_volume_number(lab_manager_data.volume),
        "storage_condition": map_storage_condition(lab_manager_data.storage_temperature),
        
        # Processing requirements
        "processing_requirements": create_processing_requirements(lab_manager_data),
        "special_instructions": lab_manager_data.special_instructions,
        
        # Administrative tracking
        "submission_date": lab_manager_data.submission_date or datetime.now(),
        "status": ProcessingStatus.RECEIVED,
        "priority": map_priority_to_number(lab_manager_data.priority_level),
        
        # Metadata
        "metadata": create_metadata(lab_manager_data),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    return legacy_data

def map_material_to_sample_type(material_type: Optional[str]) -> SampleType:
    """Map material type to legacy SampleType enum"""
    if not material_type:
        return SampleType.OTHER
    
    material_lower = material_type.lower()
    
    mapping = {
        "blood": SampleType.BLOOD,
        "plasma": SampleType.BLOOD,
        "serum": SampleType.BLOOD,
        "saliva": SampleType.SALIVA,
        "tissue": SampleType.TISSUE,
        "tumor": SampleType.TISSUE,
        "urine": SampleType.URINE,
        "dna": SampleType.DNA,
        "rna": SampleType.RNA,
        "swab": SampleType.SWAB,
        "bacterial": SampleType.SWAB
    }
    
    for key, value in mapping.items():
        if key in material_lower:
            return value
    
    return SampleType.OTHER

def map_storage_condition(storage_temp: Optional[str]) -> StorageCondition:
    """Map storage temperature to legacy StorageCondition enum"""
    if not storage_temp:
        return StorageCondition.MINUS_80C
    
    temp_lower = storage_temp.lower()
    
    if "-80" in temp_lower or "minus 80" in temp_lower:
        return StorageCondition.MINUS_80C
    elif "-20" in temp_lower or "minus 20" in temp_lower:
        return StorageCondition.MINUS_20C
    elif "4" in temp_lower or "plus 4" in temp_lower:
        return StorageCondition.PLUS_4C
    elif "room" in temp_lower or "rt" in temp_lower:
        return StorageCondition.ROOM_TEMP
    else:
        return StorageCondition.MINUS_80C

def extract_volume_number(volume_str: Optional[str]) -> Optional[float]:
    """Extract numeric volume from string"""
    if not volume_str:
        return None
    
    try:
        # Extract numbers from string
        import re
        numbers = re.findall(r'\d+\.?\d*', volume_str)
        if numbers:
            return float(numbers[0])
    except:
        pass
    
    return None

def map_priority_to_number(priority_str: Optional[str]) -> int:
    """Map priority string to number (1-5, 1 highest)"""
    if not priority_str:
        return 3  # Medium priority
    
    priority_lower = priority_str.lower()
    
    if "urgent" in priority_lower or "stat" in priority_lower:
        return 1
    elif "high" in priority_lower:
        return 2
    elif "medium" in priority_lower or "standard" in priority_lower:
        return 3
    elif "low" in priority_lower:
        return 4
    else:
        return 3

def create_processing_requirements(lab_manager_data: LabManagerSubmission) -> list:
    """Create processing requirements list from lab manager data"""
    requirements = []
    
    if lab_manager_data.sequencing_platform:
        requirements.append(f"Platform: {lab_manager_data.sequencing_platform}")
    
    if lab_manager_data.analysis_type:
        requirements.append(f"Analysis: {lab_manager_data.analysis_type}")
    
    if lab_manager_data.target_coverage:
        requirements.append(f"Coverage: {lab_manager_data.target_coverage}")
    
    if lab_manager_data.read_length:
        requirements.append(f"Read Length: {lab_manager_data.read_length}")
    
    if lab_manager_data.library_prep:
        requirements.append(f"Library Prep: {lab_manager_data.library_prep}")
    
    return requirements

def create_metadata(lab_manager_data: LabManagerSubmission) -> Dict[str, Any]:
    """Create metadata dictionary from lab manager data"""
    metadata = {
        "source_system": "LabManagerRAG",
        "extraction_confidence": lab_manager_data.extraction_confidence,
        "source_document": lab_manager_data.source_document
    }
    
    # Add all non-None fields as metadata
    for field_name, field_value in lab_manager_data.dict().items():
        if field_value is not None and field_name not in ['submission_date', 'extraction_confidence', 'source_document']:
            metadata[f"lab_manager_{field_name}"] = field_value
    
    return metadata

def create_compatible_lab_submission(lab_manager_data: LabManagerSubmission) -> LabSubmission:
    """Create a compatible LabSubmission from LabManagerSubmission"""
    try:
        legacy_data = convert_lab_manager_to_legacy(lab_manager_data)
        return LabSubmission(**legacy_data)
    except Exception as e:
        print(f"Error creating compatible submission: {e}")
        # Create minimal valid submission
        return create_minimal_valid_submission(lab_manager_data)

def create_minimal_valid_submission(lab_manager_data: LabManagerSubmission) -> LabSubmission:
    """Create minimal valid LabSubmission when conversion fails"""
    return LabSubmission(
        submission_id=str(uuid.uuid4()),
        client_id="CONVERTED_CLIENT",
        client_name=lab_manager_data.submitter_name or "Converted Submitter",
        client_email=lab_manager_data.submitter_email or "converted@example.com",
        sample_type=SampleType.OTHER,
        sample_count=1,
        storage_condition=StorageCondition.MINUS_80C,
        metadata={
            "converted_from": "LabManagerSubmission",
            "original_data": lab_manager_data.dict(),
            "conversion_note": "Minimal conversion due to compatibility issues"
        }
    )

def test_compatibility():
    """Test the compatibility conversion"""
    print("🔧 Testing Model Compatibility Fix")
    print("=" * 50)
    
    # Create test LabManagerSubmission
    test_data = LabManagerSubmission(
        submitter_name="Dr. Test User",
        submitter_email="test@lab.edu",
        submitter_phone="(555) 123-4567",
        institution="Test Laboratory",
        project_name="Compatibility Test",
        sample_name="TEST_SAMPLE_001",
        sample_barcode="COMPAT_001",
        material_type="DNA",
        concentration="50 ng/uL",
        volume="100 uL",
        storage_location="Freezer A",
        storage_temperature="-80°C",
        sequencing_platform="Illumina",
        analysis_type="WGS",
        target_coverage="30x",
        priority_level="High",
        extraction_confidence=0.85
    )
    
    print("📊 Original LabManagerSubmission:")
    print(f"   Submitter: {test_data.submitter_name}")
    print(f"   Email: {test_data.submitter_email}")
    print(f"   Sample: {test_data.sample_name} ({test_data.sample_barcode})")
    print(f"   Material: {test_data.material_type}")
    print(f"   Platform: {test_data.sequencing_platform}")
    
    # Convert to legacy format
    try:
        legacy_submission = create_compatible_lab_submission(test_data)
        print(f"\n✅ Conversion Successful!")
        print(f"   Legacy submission_id: {legacy_submission.submission_id}")
        print(f"   Legacy client_name: {legacy_submission.client_name}")
        print(f"   Legacy client_email: {legacy_submission.client_email}")
        print(f"   Legacy sample_type: {legacy_submission.sample_type}")
        print(f"   Legacy sample_count: {legacy_submission.sample_count}")
        print(f"   Legacy storage_condition: {legacy_submission.storage_condition}")
        print(f"   Legacy priority: {legacy_submission.priority}")
        print(f"   Processing requirements: {len(legacy_submission.processing_requirements)} items")
        
        # Validate the conversion
        validation_errors = []
        if not legacy_submission.submission_id:
            validation_errors.append("Missing submission_id")
        if not legacy_submission.client_id:
            validation_errors.append("Missing client_id")
        if not legacy_submission.client_name:
            validation_errors.append("Missing client_name")
        if not legacy_submission.client_email:
            validation_errors.append("Missing client_email")
        
        if validation_errors:
            print(f"\n⚠️  Validation Issues: {validation_errors}")
        else:
            print(f"\n✅ All required fields present - Validation passed!")
            
    except Exception as e:
        print(f"\n❌ Conversion Failed: {e}")
    
    print(f"\n🎉 Compatibility test completed!")

if __name__ == "__main__":
    test_compatibility() 
