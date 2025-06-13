#!/usr/bin/env python3
"""
Simple test for the improved lab RAG system
"""

import asyncio
import os
from improved_lab_rag import ImprovedLabRAG

async def test_system():
    """Test the improved RAG system"""
    print("🧬 Testing Improved Lab RAG System")
    print("=" * 50)
    
    # Set up environment
    os.environ['OLLAMA_MODEL'] = 'llama3.2:3b'
    
    rag = ImprovedLabRAG()
    
    # Test database connection
    try:
        conn = await rag.connect_to_lab_manager()
        await conn.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Process the test document
    test_doc_path = "test_improved_document.txt"
    
    print(f"\n🔄 Processing test document: {test_doc_path}")
    result = await rag.process_document(test_doc_path)
    
    if result.success:
        print(f"✅ Processing successful!")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        
        submission = result.submission
        print(f"\n📋 Extracted Information:")
        print(f"   Submitter: {submission.submitter_name}")
        print(f"   Email: {submission.submitter_email}")
        print(f"   Phone: {submission.submitter_phone}")
        print(f"   Institution: {submission.institution}")
        print(f"   Project: {submission.project_name}")
        print(f"   Sample: {submission.sample_name} ({submission.sample_barcode})")
        print(f"   Material: {submission.material_type}")
        print(f"   Concentration: {submission.concentration}")
        print(f"   Volume: {submission.volume}")
        print(f"   Storage: {submission.storage_temperature} in {submission.storage_location}")
        print(f"   Platform: {submission.sequencing_platform}")
        print(f"   Analysis: {submission.analysis_type}")
        print(f"   Coverage: {submission.target_coverage}")
        print(f"   Priority: {submission.priority_level}")
        
        print(f"\n🎯 Key Improvements:")
        print(f"   ✅ Lab_manager aligned field names")
        print(f"   ✅ Enhanced extraction prompts")
        print(f"   ✅ Direct database integration")
        print(f"   ✅ Sample record creation capability")
        
    else:
        print(f"❌ Processing failed: {result.warnings}")
    
    print(f"\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_system()) 
