"""
Enhanced LLM interface for intelligent laboratory assistance
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
import json
import openai
import anthropic
import ollama
from datetime import datetime
from pydantic import ValidationError

from models.submission import ExtractionResult
from config import settings

logger = logging.getLogger(__name__)

class ConversationContext:
    """Manages conversation history and context"""
    
    def __init__(self, max_history: int = 10):
        self.messages = []
        self.max_history = max_history
        self.user_context = {}
        
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context_summary(self) -> str:
        """Get a summary of recent conversation for context"""
        if not self.messages:
            return ""
        
        context_parts = []
        for msg in self.messages[-5:]:  # Last 5 messages
            context_parts.append(f"{msg['role']}: {msg['content'][:200]}...")
        
        return "\n".join(context_parts)

class EnhancedLLMInterface:
    """Enhanced LLM interface with lab-specific intelligence"""
    
    def __init__(self):
        self.client = None
        self.client_type = None
        self.conversation_contexts = {}  # Store per-session contexts
        self._initialize_client()
        
        # Lab Manager system knowledge
        self.lab_system_knowledge = self._load_lab_system_knowledge()
    
    def _initialize_client(self):
        """Initialize the LLM client with enhanced configuration"""
        try:
            # Prefer more powerful models
            if hasattr(settings, 'use_ollama') and settings.use_ollama:
                try:
                    ollama.list()
                    self.client = ollama
                    self.client_type = "ollama"
                    # Use more powerful Ollama model if available
                    available_models = ollama.list()
                    model_preferences = ["llama3.1:8b", "llama3:8b", "mistral:7b", settings.ollama_model]
                    
                    for preferred_model in model_preferences:
                        if any(preferred_model in model['name'] for model in available_models.get('models', [])):
                            settings.ollama_model = preferred_model
                            break
                            
                    logger.info(f"Using enhanced Ollama with model: {settings.ollama_model}")
                    return
                except Exception as e:
                    logger.warning(f"Ollama not available: {str(e)}")
            
            # Use more powerful cloud models
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                openai.api_key = settings.openai_api_key
                self.client_type = "openai"
                self.model_name = "gpt-4"  # Use GPT-4 for better intelligence
                logger.info("Using OpenAI GPT-4 for enhanced intelligence")
            elif hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.client_type = "anthropic"
                self.model_name = "claude-3-sonnet-20240229"
                logger.info("Using Anthropic Claude-3 Sonnet for enhanced intelligence")
            else:
                logger.warning("No LLM providers available. Using mock responses.")
                self.client_type = "mock"
        except Exception as e:
            logger.error(f"Failed to initialize enhanced LLM client: {str(e)}")
            self.client_type = "mock"
    
    def _load_lab_system_knowledge(self) -> str:
        """Load lab manager system-specific knowledge"""
        return """
Lab Manager System Knowledge Base:

CORE FEATURES:
- Sample Management: Create, track, validate samples with barcode generation
- Template Processing: Upload and process Excel/CSV templates for batch operations
- RAG Document Processing: AI-powered extraction from PDF/DOCX laboratory forms
- Sequencing Management: Job creation, sample sheet generation, status tracking
- Storage Management: Location tracking, capacity monitoring, barcode scanning
- Reports & Analytics: Custom reports, data export, system analytics

KEY WORKFLOWS:
1. Sample Submission:
   - Navigate to Samples → Create New Sample
   - Fill required fields: name, barcode, location, material type
   - Validate sample data before submission
   - Generate unique barcode automatically

2. RAG-Enhanced Submission:
   - Navigate to AI Submissions → Upload Document
   - System extracts sample information automatically
   - Review extracted data for accuracy
   - Create samples from validated extractions

3. Template Processing:
   - Navigate to Templates → Upload Template
   - System processes Excel/CSV files
   - Batch create samples from template data
   - Validate all entries before final submission

4. Sequencing Jobs:
   - Navigate to Sequencing → Create Job
   - Select samples for sequencing
   - Configure sequencing parameters
   - Generate sample sheets for instruments

5. Storage Management:
   - Navigate to Storage → Manage Locations
   - Scan barcodes to locate samples
   - Track storage capacity and conditions
   - Move samples between locations

SAMPLE REQUIREMENTS:
- Unique barcode (6+ characters)
- Valid storage location
- Material type (DNA, RNA, Protein, etc.)
- Quality metrics when available
- Proper container specifications

SUPPORTED FILE FORMATS:
- Documents: PDF, DOCX, TXT
- Templates: XLSX, CSV
- Exports: JSON, CSV, Excel

API ENDPOINTS:
- /api/samples/* - Sample management
- /api/templates/* - Template operations
- /api/sequencing/* - Sequencing workflows
- /api/storage/* - Storage management
- /api/samples/rag/* - AI-powered processing

STORAGE CONDITIONS:
- -80°C for long-term DNA/RNA storage
- -20°C for short-term storage
- 4°C for active samples
- Room temperature for processed samples

QUALITY REQUIREMENTS:
- DNA: A260/A280 ratio 1.8-2.0
- RNA: RIN score >7 for sequencing
- Concentration >10 ng/μL minimum
- Volume >50 μL recommended
"""
    
    def get_conversation_context(self, session_id: str = "default") -> ConversationContext:
        """Get or create conversation context for a session"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext()
        return self.conversation_contexts[session_id]
    
    async def answer_query(
        self, 
        query: str, 
        relevant_chunks: List[Tuple[str, float]],
        session_id: str = "default",
        submission_data: Optional[dict] = None
    ) -> str:
        """Answer questions with enhanced intelligence and context"""
        try:
            # Get conversation context
            context = self.get_conversation_context(session_id)
            
            # Prepare enhanced context
            context_parts = [
                "=== LAB MANAGER SYSTEM KNOWLEDGE ===",
                self.lab_system_knowledge,
                "",
                "=== RECENT CONVERSATION ===",
                context.get_context_summary(),
                ""
            ]
            
            # Add document chunks if available
            if relevant_chunks:
                context_parts.append("=== RELEVANT DOCUMENTS ===")
                for chunk_content, similarity_score in relevant_chunks:
                    context_parts.append(f"[Relevance: {similarity_score:.2f}]\n{chunk_content}")
                context_parts.append("")
            
            # Add structured submission data if available
            if submission_data:
                context_parts.append("=== CURRENT SUBMISSION DATA ===")
                context_parts.append(json.dumps(submission_data, indent=2))
                context_parts.append("")
            
            full_context = "\n".join(context_parts)
            
            # Create enhanced prompt
            prompt = self._create_smart_assistant_prompt(query, full_context)
            
            # Get LLM response
            response = await self._get_enhanced_llm_response(prompt)
            
            # Add to conversation history
            context.add_message("user", query)
            context.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced query processing: {str(e)}")
            return f"I apologize, but I encountered an error while processing your query. Please try rephrasing your question or contact support if the issue persists."
    
    def _create_smart_assistant_prompt(self, query: str, context: str) -> str:
        """Create an enhanced prompt for intelligent lab assistance"""
        return f"""You are an expert laboratory management assistant specializing in the Lab Manager system. You have deep knowledge of:

• Laboratory workflows and protocols
• Sample management and tracking
• Sequencing operations and requirements  
• Storage conditions and best practices
• Quality control and validation
• Scientific instrumentation and analysis
• RAG-powered document processing
• Data management and reporting

INSTRUCTIONS:
1. Provide accurate, detailed, and actionable responses
2. Reference specific Lab Manager features and workflows when relevant
3. Include step-by-step instructions for complex procedures
4. Suggest best practices and quality considerations
5. Warn about potential issues or requirements
6. Offer alternative approaches when applicable
7. Use the conversation history to maintain context
8. Be helpful, professional, and scientifically accurate

RESPONSE STYLE:
- Start with a direct answer to the question
- Provide specific steps or procedures when relevant
- Include helpful tips or best practices
- Reference Lab Manager system features specifically
- End with related suggestions or next steps when appropriate

Available Context:
{context}

User Question: {query}

Please provide a comprehensive, intelligent response that helps the user accomplish their laboratory management goals effectively.
"""
    
    async def _get_enhanced_llm_response(self, prompt: str) -> str:
        """Get response from LLM with enhanced parameters"""
        try:
            if self.client_type == "ollama":
                response = await asyncio.to_thread(
                    ollama.generate,
                    model=settings.ollama_model,
                    prompt=prompt,
                    options={
                        "temperature": 0.3,  # Lower temperature for more focused responses
                        "num_predict": 2048,  # Allow longer responses
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                    }
                )
                return response['response']
                
            elif self.client_type == "openai":
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert laboratory management assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    top_p=0.9,
                    frequency_penalty=0.1,
                    presence_penalty=0.1
                )
                return response.choices[0].message.content
                
            elif self.client_type == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
                
            else:
                return self._generate_smart_mock_response(prompt)
                
        except Exception as e:
            logger.error(f"Error getting enhanced LLM response: {str(e)}")
            return self._generate_smart_mock_response(prompt)
    
    def _generate_smart_mock_response(self, prompt: str) -> str:
        """Generate intelligent mock responses for testing"""
        query_lower = prompt.lower()
        
        if "submit" in query_lower and "sample" in query_lower:
            return """To submit a new sample in the Lab Manager system:

**Quick Steps:**
1. Navigate to **Samples** → **Create New Sample**
2. Fill in the required fields:
   - Sample Name (descriptive, unique)
   - Barcode (auto-generated or manual)
   - Storage Location (select from dropdown)
   - Material Type (DNA, RNA, Protein, etc.)
3. Add optional details like concentration, volume, quality metrics
4. Click **Submit** to create the sample

**Best Practices:**
• Use descriptive naming conventions (e.g., "PROJ_001_DNA_001")
• Verify storage location availability
• Include quality metrics when available
• Double-check barcode uniqueness

**Alternative Methods:**
- **Batch Upload**: Use Templates → Upload CSV/Excel for multiple samples
- **AI Submission**: Use AI Submissions → Upload PDF forms for automatic extraction

Would you like me to explain any of these methods in more detail?"""

        elif "storage" in query_lower and ("temperature" in query_lower or "condition" in query_lower):
            return """**Storage Requirements for Laboratory Samples:**

**Temperature Guidelines:**
• **-80°C**: Long-term DNA/RNA storage, cell lines, critical samples
• **-20°C**: Short-term nucleic acid storage, enzymes, antibodies  
• **4°C**: Active samples, buffers, short-term protein storage
• **Room Temperature**: Processed samples, dried materials

**Sample-Specific Requirements:**
- **DNA**: -20°C or -80°C, avoid freeze-thaw cycles
- **RNA**: -80°C preferred, RNase-free environment
- **Proteins**: 4°C for active use, -80°C for long-term
- **Blood/Serum**: -80°C for biomarker studies

**Quality Considerations:**
• Use appropriate containers (cryovials for -80°C)
• Label with date, sample ID, storage conditions
• Monitor freezer temperatures and alarms
• Maintain chain of custody documentation

**Lab Manager Integration:**
Navigate to **Storage** → **Manage Locations** to:
- View available storage spaces
- Check temperature monitoring
- Assign samples to specific locations
- Track capacity utilization

Need help setting up storage locations or moving samples?"""

        elif "sequencing" in query_lower:
            return """**Sequencing Workflow in Lab Manager:**

**1. Job Creation:**
- Navigate to **Sequencing** → **Create Job**
- Select samples for sequencing
- Choose sequencing platform (Illumina, PacBio, etc.)
- Set read parameters (paired-end, read length)

**2. Sample Requirements:**
- **DNA**: Concentration >10 ng/μL, A260/A280 ratio 1.8-2.0
- **RNA**: RIN score >7, concentration >25 ng/μL
- **Volume**: Minimum 50 μL recommended

**3. Library Preparation:**
- Specify library prep kit and protocol
- Set target insert size and coverage
- Include adapter/barcode information

**4. Sample Sheet Generation:**
- System generates instrument-specific sample sheets
- Includes sample IDs, barcodes, and parameters
- Export for direct instrument upload

**5. Status Tracking:**
- Monitor job progress through dashboard
- Receive notifications on completion
- Access results and quality metrics

**Supported Platforms:**
• Illumina (NovaSeq, NextSeq, MiSeq)
• PacBio (Sequel, Revio)
• Oxford Nanopore (MinION, PromethION)

Would you like help with sample preparation requirements or job setup?"""

        elif "rag" in query_lower or "ai" in query_lower or "document" in query_lower:
            return """**AI-Powered Document Processing (RAG):**

**How It Works:**
The RAG (Retrieval-Augmented Generation) system automatically extracts laboratory information from documents using AI.

**Supported Documents:**
• PDF laboratory forms and submissions
• Word documents with sample information
• Research papers with experimental details
• Protocol documents and SOPs

**Processing Workflow:**
1. **Navigate** to **AI Submissions** → **Upload Document**
2. **Upload** your PDF/DOCX file
3. **AI Extracts** information across 7 categories:
   - Administrative info (submitter, project)
   - Source material details
   - Pooling/multiplexing data  
   - Sequencing parameters
   - Container specifications
   - Analysis requirements
   - Sample quality metrics

**Review & Validation:**
- System provides confidence scores
- Review extracted data for accuracy
- Edit any incorrect information
- Approve creation of samples

**Advantages:**
• Reduces manual data entry errors
• Processes complex documents quickly
• Maintains data consistency
• Tracks document source and confidence

**Best Results:**
- Use clear, well-formatted documents
- Ensure text is readable (not scanned images)
- Include complete sample information

Ready to try document processing, or need help with a specific document type?"""

        else:
            return """I'm here to help you with the Lab Manager system! I can assist with:

**Sample Management:**
• Creating and tracking samples
• Barcode generation and validation
• Quality control procedures

**Storage & Organization:**
• Temperature requirements
• Location management
• Capacity planning

**Sequencing Operations:**
• Job setup and configuration
• Sample requirements
• Platform-specific workflows

**AI Document Processing:**
• Automated data extraction
• PDF/DOCX form processing
• Batch sample creation

**Templates & Batch Operations:**
• Excel/CSV upload procedures
• Data validation and formatting
• Bulk sample creation

**System Navigation:**
• Feature explanations
• Workflow guidance
• Best practices

What specific aspect would you like help with? Just describe what you're trying to accomplish!"""

# Create enhanced instance
enhanced_llm = EnhancedLLMInterface() 
