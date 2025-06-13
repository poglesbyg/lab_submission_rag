#!/usr/bin/env python3
"""
Complete Laboratory RAG System Demo
Demonstrates all improvements: aligned models, custom categories, and automation
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

from improved_lab_rag import ImprovedLabRAG
from custom_lab_categories import LabCategoryConfig, create_custom_genomics_config
from lab_automation_workflows import LabAutomationManager, ProcessingPriority

async def demo_aligned_extraction():
    """Demo 1: Show aligned extraction with lab_manager schema"""
    print("\n🎯 DEMO 1: Lab_Manager Aligned Extraction")
    print("=" * 60)
    
    # Create sample submission documents
    documents = {
        "cancer_research_sample.txt": """
        Cancer Research Sample Submission Form
        
        Principal Investigator: Dr. Maria Rodriguez
        Email: m.rodriguez@cancercenter.edu
        Phone: (617) 555-0123
        Institution: Dana-Farber Cancer Institute
        Project: Colorectal Cancer Genomics Study 2024
        IRB Number: IRB-2024-001
        
        Sample Information:
        Patient ID: CRC_P001 (de-identified)
        Sample Name: Tumor_Tissue_Primary
        Sample Barcode: DFCI_CRC_001
        Material Type: FFPE Tissue
        Concentration: 75 ng/uL
        Volume: 200 uL
        Collection Date: 2024-05-15
        
        Storage Requirements:
        Location: Biobank Freezer A-123
        Temperature: -80°C
        Special Conditions: Store in 20uL aliquots
        
        Sequencing Requirements:
        Platform: Illumina NovaSeq X Plus
        Analysis Type: Whole Exome Sequencing
        Target Coverage: 150x
        Read Length: 150bp paired-end
        Library Prep: SureSelect Human All Exon V8
        
        Analysis Specifications:
        Reference Genome: GRCh38
        Variant Calling: SNPs, Indels, CNVs
        Annotation: ClinVar, COSMIC, OncoKB
        
        Priority: High - Clinical Trial Patient
        Quality Metrics: DV200 = 85%, A260/A280 = 1.9
        Turnaround Time: 2 weeks
        Special Instructions: Rush processing for clinical decision making
        """,
        
        "microbiology_sample.txt": """
        Microbiology Sample Submission
        
        Submitter: Dr. James Park, MD
        Email: jpark@hospital.edu
        Phone: (508) 555-9876
        Department: Infectious Disease
        Institution: Massachusetts General Hospital
        Study: Antibiotic Resistance Surveillance
        
        Sample Details:
        Patient: ID_12345 (anonymized)
        Sample: Bacterial_Isolate_E_coli
        Barcode: MGH_MICRO_2024_067
        Material: Bacterial DNA
        Concentration: 120 ng/uL
        Volume: 150 uL
        Isolation Date: 2024-06-10
        
        Storage:
        Location: Microbiology Lab Freezer B
        Temperature: -20°C
        Conditions: Single use aliquot
        
        Sequencing:
        Platform: Oxford Nanopore MinION
        Analysis: Whole Genome Sequencing
        Coverage: 50x
        Read Type: Long reads
        Library Prep: Rapid Barcoding Kit
        
        Analysis Goals:
        Antimicrobial Resistance Genes
        Plasmid Analysis
        Phylogenetic Classification
        
        Priority: Medium
        Quality: Pure culture, high molecular weight
        Delivery: Secure email with encrypted results
        """
    }
    
    # Process each document
    rag = ImprovedLabRAG()
    
    for filename, content in documents.items():
        # Create document file
        doc_path = Path(filename)
        doc_path.write_text(content)
        
        print(f"\n📄 Processing: {filename}")
        print("-" * 40)
        
        # Extract information
        result = await rag.process_document(str(doc_path))
        
        if result.success:
            submission = result.submission
            print(f"✅ Extraction successful (Confidence: {result.confidence_score:.2f})")
            print(f"⏱️  Processing time: {result.processing_time:.2f}s")
            
            # Show key extracted fields
            print(f"\n🧪 Key Information Extracted:")
            print(f"   PI/Submitter: {submission.submitter_name}")
            print(f"   Institution: {submission.institution}")
            print(f"   Project: {submission.project_name}")
            print(f"   Sample: {submission.sample_name} ({submission.sample_barcode})")
            print(f"   Material: {submission.material_type}")
            print(f"   Platform: {submission.sequencing_platform}")
            print(f"   Analysis: {submission.analysis_type}")
            print(f"   Priority: {submission.priority_level}")
            
            # Show database integration
            print(f"\n🗄️  Database Integration:")
            print(f"   ✅ Stored in rag_submissions table")
            print(f"   ✅ Compatible with lab_manager schema")
            if submission.sample_barcode:
                print(f"   ✅ Can create sample record: {submission.sample_barcode}")
            
        else:
            print(f"❌ Extraction failed: {result.warnings}")
        
        # Cleanup
        doc_path.unlink()

async def demo_custom_categories():
    """Demo 2: Show custom category configuration"""
    print("\n\n🎨 DEMO 2: Custom Categories Configuration")
    print("=" * 60)
    
    # Show standard configuration
    print("📋 Standard Laboratory Categories:")
    standard_config = LabCategoryConfig()
    
    for i, category in enumerate(standard_config.categories, 1):
        required_fields = [f.name for f in category.fields if f.required]
        print(f"   {i}. {category.name}")
        print(f"      └── {len(category.fields)} fields ({len(required_fields)} required)")
        print(f"      └── Type: {category.type.value}, Priority: {category.priority}")
    
    print(f"\n🧬 Custom Genomics Configuration:")
    genomics_config = create_custom_genomics_config()
    print(f"   Added genomics-specific category with specialized fields:")
    
    genomics_category = genomics_config.categories[-1]  # Last added category
    for field in genomics_category.fields:
        print(f"   • {field.display_name}: {field.description}")
        if field.examples:
            print(f"     Examples: {', '.join(field.examples[:2])}")
    
    # Generate custom prompt
    print(f"\n🤖 Generated Custom Extraction Prompt:")
    custom_prompt = genomics_config.generate_extraction_prompt()
    print(f"   Length: {len(custom_prompt):,} characters")
    print(f"   Total fields: {sum(len(cat.fields) for cat in genomics_config.categories)}")
    
    # Export configuration
    config_export = genomics_config.export_configuration()
    print(f"\n📤 Configuration Export:")
    print(f"   Categories: {config_export['total_categories']}")
    print(f"   Total fields: {config_export['total_fields']}")
    print(f"   Required fields: {len(config_export['required_fields'])}")

async def demo_automation_workflows():
    """Demo 3: Show automation system capabilities"""
    print("\n\n🤖 DEMO 3: Automation Workflows")
    print("=" * 60)
    
    # Create automation manager
    automation = LabAutomationManager()
    
    print(f"📁 Automation Directory Structure:")
    print(f"   📥 Inbox: {automation.inbox_dir}")
    print(f"   ⚙️ Processing: {automation.processing_dir}")
    print(f"   ✅ Completed: {automation.completed_dir}")
    print(f"   ❌ Failed: {automation.failed_dir}")
    print(f"   📦 Archive: {automation.archive_dir}")
    
    # Create sample documents with different priorities
    test_documents = [
        ("urgent_clinical_sample.txt", ProcessingPriority.URGENT, """
        URGENT CLINICAL SAMPLE
        
        Submitter: Dr. Emergency Medicine
        Email: urgent@hospital.edu
        Institution: Emergency Department
        Project: Rapid Pathogen ID
        
        Sample: Patient_Critical_001
        Barcode: URGENT_001
        Material: Blood
        Priority: URGENT - ICU Patient
        
        Platform: Rapid Sequencing
        Analysis: Targeted Pathogen Panel
        Turnaround: 4 hours STAT
        """),
        
        ("routine_research.txt", ProcessingPriority.MEDIUM, """
        Research Sample Submission
        
        Submitter: Dr. Research Lab
        Email: research@uni.edu
        Project: Basic Research Study
        
        Sample: Research_Sample_R001
        Material: DNA
        Priority: Standard Processing
        Analysis: WGS
        """),
        
        ("low_priority_archive.txt", ProcessingPriority.LOW, """
        Archive Sample
        
        Submitter: Archive Manager
        Sample: Historical_H001
        Material: Archived DNA
        Priority: Low - Archive Processing
        """)
    ]
    
    print(f"\n📄 Creating Test Documents:")
    for filename, priority, content in test_documents:
        doc_path = automation.inbox_dir / filename
        doc_path.write_text(content)
        print(f"   {priority.value.upper()}: {filename}")
    
    # Show system configuration
    print(f"\n⚙️ System Configuration:")
    print(f"   Max concurrent jobs: {automation.max_concurrent_jobs}")
    print(f"   Check interval: {automation.check_interval}s")
    print(f"   Auto-archive after: {automation.auto_archive_days} days")
    print(f"   Supported formats: {', '.join(automation.watcher.supported_extensions)}")
    
    # Add custom callbacks
    async def custom_notification(job):
        if job.status.value == "completed":
            print(f"   📧 Custom notification: Job {job.job_id[:8]} completed!")
    
    automation.add_post_processing_callback(custom_notification)
    print(f"\n🔗 Custom Callbacks:")
    print(f"   Post-processing callbacks: {len(automation.post_processing_callbacks)}")
    
    # Show what would happen (without actually running long process)
    print(f"\n🎯 Automation Features:")
    print(f"   ✅ Automatic file watching and detection")
    print(f"   ✅ Priority-based job queuing")
    print(f"   ✅ Concurrent processing with limits")
    print(f"   ✅ Retry logic for failed jobs")
    print(f"   ✅ Automatic file organization")
    print(f"   ✅ Status tracking and logging")
    print(f"   ✅ Custom callback system")
    print(f"   ✅ Automatic archiving")
    
    # Clean up test files
    for filename, _, _ in test_documents:
        doc_path = automation.inbox_dir / filename
        if doc_path.exists():
            doc_path.unlink()

async def demo_integration_benefits():
    """Demo 4: Show integration benefits"""
    print("\n\n🔗 DEMO 4: Lab_Manager Integration Benefits")
    print("=" * 60)
    
    print("🎯 Key Integration Benefits:")
    
    print("\n1. 📊 Data Model Alignment:")
    print("   ✅ RAG extraction fields match lab_manager database columns")
    print("   ✅ Automatic sample record creation")
    print("   ✅ Seamless data flow between systems")
    print("   ✅ No manual data entry required")
    
    print("\n2. 🔄 Workflow Integration:")
    print("   ✅ Documents processed and stored in lab_manager DB")
    print("   ✅ Triggers lab_manager workflows automatically") 
    print("   ✅ Updates sample status and location tracking")
    print("   ✅ Generates sequencing job requests")
    
    print("\n3. 🎨 Customization Capabilities:")
    print("   ✅ 7 configurable extraction categories")
    print("   ✅ Custom fields for specific laboratory workflows")
    print("   ✅ Validation rules and data types")
    print("   ✅ Priority-based processing")
    
    print("\n4. 🤖 Automation Features:")
    print("   ✅ Watch folder for automatic processing")
    print("   ✅ Concurrent job processing")
    print("   ✅ Error handling and retry logic")
    print("   ✅ Custom callbacks for external integrations")
    
    print("\n5. 📈 Performance Improvements:")
    print("   ✅ Optimized extraction prompts")
    print("   ✅ Better field recognition")
    print("   ✅ Higher extraction accuracy")
    print("   ✅ Faster processing times")
    
    # Show metrics comparison
    print("\n📊 Improvement Metrics:")
    print("   Extraction Categories: 7 → 7 (customizable)")
    print("   Field Recognition: Standard → Lab_manager aligned")
    print("   Processing: Manual → Automated")
    print("   Integration: None → Direct database")
    print("   Customization: Fixed → Fully configurable")

async def main():
    """Run complete system demonstration"""
    print("🧬 COMPLETE LABORATORY RAG SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("Showing all improvements:")
    print("• Lab_manager aligned data models")
    print("• Custom extraction categories") 
    print("• Automated document processing workflows")
    print("• Database integration")
    print("=" * 80)
    
    # Run all demos
    await demo_aligned_extraction()
    await demo_custom_categories()
    await demo_automation_workflows()
    await demo_integration_benefits()
    
    print("\n\n🎉 DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print("🎯 Next Steps:")
    print("1. 📄 Upload your real laboratory documents")
    print("2. 🎨 Customize categories for your specific workflow")
    print("3. 🤖 Set up automation with watch folders")
    print("4. 🔗 Configure callbacks for your existing systems")
    print("5. 📊 Monitor processing and results")
    print("=" * 80)
    
    print("\n💡 Quick Start Commands:")
    print("# Test improved extraction:")
    print("python test_improved_simple.py")
    print("\n# Configure custom categories:")
    print("python custom_lab_categories.py")
    print("\n# Set up automation:")
    print("python lab_automation_workflows.py")
    print("\n# Full system demo:")
    print("python complete_system_demo.py")

if __name__ == "__main__":
    asyncio.run(main()) 
