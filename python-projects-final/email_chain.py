from langchain.chains.base import Chain
from langchain.chains import LLMChain, SequentialChain, TransformChain
from langchain_community.llms import GPT4All
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from typing import Dict, Any, List, Optional
from pydantic import Field
from dataclasses import dataclass
import datetime
import os
import json
import logging
import hashlib
from pathlib import Path
from fetch_emails import fetch_emails_since
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_MAX_TOKENS = 4048
DEFAULT_K_VALUE = 20
BODY_PREVIEW_LENGTH = 200
MAX_CONTEXT_EMAILS = 50

@dataclass
class EmailRAGConfig:
    """Configuration for Email RAG Chain"""
    persist_dir: str = "faiss_index"
    data_dir: str = "data"
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    max_tokens: int = DEFAULT_MAX_TOKENS
    k_value: int = DEFAULT_K_VALUE
    model_name: str = "mistral-7b-instruct-v0.1.Q4_0.gguf"
    embedding_model: str = "all-MiniLM-L6-v2"
    enable_memory: bool = True

class EmailProcessor:
    """Handles email cleaning and normalization"""
    
    @staticmethod
    def clean_html(raw_html: str) -> str:
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            return soup.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return raw_html
    
    @staticmethod
    def normalize_date(raw_date: str) -> str:
        if not raw_date:
            return ""
        try:
            dt = parsedate_to_datetime(raw_date)
            local_dt = dt.astimezone()
            return local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Failed to parse date '{raw_date}': {e}")
            return raw_date
    
    @staticmethod
    def generate_email_hash(email: Dict[str, Any]) -> str:
        msg_id = email.get("message_id", "")
        if msg_id:
            return hashlib.md5(msg_id.encode()).hexdigest()
        unique_str = f"{email.get('from', '')}{email.get('date', '')}{email.get('subject', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()

class VectorStoreManager:
    """Manages FAISS vectorstore operations"""
    
    def __init__(self, config: EmailRAGConfig, embeddings: Any):
        self.config = config
        self.embeddings = embeddings
        self.vectorstore: Optional[FAISS] = None
        
    def load_or_create(self, emails: List[Dict]) -> Optional[FAISS]:
        try:
            if self._vectorstore_exists():
                logger.info("Loading existing vectorstore...")
                self.vectorstore = FAISS.load_local(
                    self.config.persist_dir,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✓ Vectorstore loaded successfully")
                return self.vectorstore
        except Exception as e:
            logger.warning(f"Failed to load vectorstore: {e}. Creating new one...")
        
        if emails:
            return self.build_vectorstore(emails)
        return None
    
    def build_vectorstore(self, emails: List[Dict]) -> Optional[FAISS]:
        try:
            logger.info(f"Building vectorstore from {len(emails)} emails...")
            docs = self._prepare_documents(emails)
            
            if not docs:
                logger.warning("No documents to build vectorstore")
                return None
            
            self.vectorstore = FAISS.from_documents(docs, self.embeddings)
            self._save_vectorstore()
            logger.info("✓ Vectorstore built successfully")
            return self.vectorstore
        except Exception as e:
            logger.error(f"Error building vectorstore: {e}")
            return None
    
    def _prepare_documents(self, emails: List[Dict]):
        texts = []
        metadatas = []
        
        for email in emails:
            try:
                clean_body = EmailProcessor.clean_html(email.get("body", ""))
                text = (
                    f"From: {email.get('from', '')}\n"
                    f"Sender Email: {email.get('sender_email', '')}\n"
                    f"Date: {email.get('date', '')}\n"
                    f"Subject: {email.get('subject', '')}\n\n"
                    f"{clean_body}"
                )
                texts.append(text)
                
                metadatas.append({
                    "email_hash": EmailProcessor.generate_email_hash(email),
                    "from": email.get("from", ""),
                    "sender_email": email.get("sender_email", ""),
                    "date": email.get("date", ""),
                    "subject": email.get("subject", ""),
                    "body_preview": clean_body[:BODY_PREVIEW_LENGTH]
                })
            except Exception as e:
                logger.error(f"Error preparing document: {e}")
                continue
        
        if not texts:
            return []
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        return splitter.create_documents(texts, metadatas=metadatas)
    
    def _vectorstore_exists(self) -> bool:
        persist_path = Path(self.config.persist_dir)
        return persist_path.exists() and any(persist_path.iterdir())
    
    def _save_vectorstore(self):
        try:
            os.makedirs(self.config.persist_dir, exist_ok=True)
            self.vectorstore.save_local(self.config.persist_dir)
            logger.info("✓ Vectorstore saved")
        except Exception as e:
            logger.error(f"Error saving vectorstore: {e}")

class EmailRAGSequentialChain(Chain):
    """
    Sequential Chain Architecture:
    1. Context Resolution Chain - resolves pronouns and references
    2. Query Analysis Chain - analyzes intent and requirements
    3. Email Retrieval Transform - fetches relevant emails
    4. Answer Generation Chain - generates final answer
    """
    
    llm: Any
    embeddings: Any
    config: EmailRAGConfig = Field(default_factory=EmailRAGConfig)
    vectorstore_manager: Optional[VectorStoreManager] = None
    internal_memory: Optional[ConversationBufferMemory] = Field(default=None, exclude=True) 
    
    # Email data
    all_emails: List[Dict] = Field(default_factory=list)
    email_hashes: set = Field(default_factory=set)
    last_fetch_date: Optional[str] = None
    
    # Sequential chain components
    sequential_chain: Optional[SequentialChain] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    # The problematic @property for 'memory' has been removed.
    
    def __init__(self, **data):
        internal_memory_instance = data.pop("memory", None)
        super().__init__(**data)
        self.internal_memory = internal_memory_instance
        
        if self.vectorstore_manager is None:
            self.vectorstore_manager = VectorStoreManager(self.config, self.embeddings)
        
        if self.config.enable_memory and self.internal_memory is None:
            self.internal_memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="original_question",
                output_key="final_answer"
            )
        
        self._build_sequential_chain()

    
    @property
    def input_keys(self):
        return ["question"]
    
    @property
    def output_keys(self):
        return ["answer"]
    
    def _build_sequential_chain(self):
        """Build the sequential chain with multiple stages"""
        
        logger.info("🔗 Building Sequential Chain...")
        
        # ============ CHAIN 1: Context Resolution ============
        context_resolution_prompt = PromptTemplate(
            input_variables=["original_question", "chat_history"],
            template="""You are resolving context references in a conversation about emails.

Conversation History:
{chat_history}

Current Question: {original_question}

Task: If the question contains words like "that", "this", "it", "same", "the link", rewrite it to be self-contained using information from the conversation history. Otherwise, return it as-is.

Examples:
- "give that link" -> "give the link from the license renewal email"
- "what was in it?" -> "what was in the email about job opportunities"
- "show me all emails" -> "show me all emails" (already clear)

Resolved Question (be specific and clear):"""
        )
        
        context_chain = LLMChain(
            llm=self.llm,
            prompt=context_resolution_prompt,
            output_key="resolved_question",
            verbose=True
        )
        
        # ============ CHAIN 2: Query Analysis ============
        query_analysis_prompt = PromptTemplate(
            input_variables=["resolved_question"],
            template="""Analyze this email query and determine the search strategy.

Question: {resolved_question}

Determine:
1. SCOPE: Does user want ALL emails or just RELEVANT ones? **If the user asks "how many" or wants to count emails without specifying a topic, the scope is ALL.**
2. SEARCH_TERMS: What keywords should we search for?
3. NEEDS_COUNT: Does the user want to count something?
4. INFO_TYPE: What information do they want? (senders/subjects/links/content/count)

Respond in this format:
SCOPE: [ALL or RELEVANT]
SEARCH_TERMS: [comma-separated keywords]
NEEDS_COUNT: [YES or NO]
INFO_TYPE: [what they want]

Analysis:"""
        )
        
        analysis_chain = LLMChain(
            llm=self.llm,
            prompt=query_analysis_prompt,
            output_key="query_analysis",
            verbose=True
        )
        
        # ============ TRANSFORM: Email Retrieval ============
        def retrieve_emails_transform(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Custom transform to retrieve emails based on analysis"""
            logger.info("📧 Email Retrieval Transform")
            
            resolved_question = inputs["resolved_question"]
            query_analysis = inputs["query_analysis"]
            
            # Parse analysis
            analysis = self._parse_analysis(query_analysis)
            
            # Get emails
            emails = self._fetch_and_process_emails()
            if not emails:
                return {"email_context": "No emails found.", "emails_retrieved": 0}
            
            # Ensure vectorstore
            self._ensure_vectorstore(emails)
            
            # Retrieve based on scope
            if analysis["scope"] == "ALL":
                logger.info("Retrieving ALL emails")
                docs = self._get_all_unique_documents(emails)
            else:
                logger.info("Retrieving RELEVANT emails")
                k = min(len(emails), self.config.k_value if analysis["needs_count"] == "NO" else MAX_CONTEXT_EMAILS)
                docs = self._get_semantic_documents(resolved_question, k)
            
            # Build email context
            email_context = self._build_email_context(docs)
            
            return {
                "email_context": email_context,
                "emails_retrieved": len(docs),
                "scope_used": analysis["scope"]
            }
        
        retrieval_transform = TransformChain(
            input_variables=["resolved_question", "query_analysis"],
            output_variables=["email_context", "emails_retrieved", "scope_used"],
            transform=retrieve_emails_transform
        )
        
        # ============ CHAIN 3: Answer Generation ============
        answer_generation_prompt = PromptTemplate(
            input_variables=["original_question", "resolved_question", "email_context", "emails_retrieved", "scope_used"],
            template="""You are an intelligent email assistant. Answer the user's question based on the emails provided.

Original Question: {original_question}
Clarified Question: {resolved_question}
Number of Emails Retrieved: {emails_retrieved}
Search Scope: {scope_used}

EMAIL DATA:
{email_context}

INSTRUCTIONS:
1. Answer the user's ORIGINAL question directly and naturally
2. Use the email data above to provide accurate, specific information
3. If they ask for links, extract actual URLs from the emails
4. If they ask for contact details, extract actual emails/phone numbers
5. If counting, count all relevant emails shown above
6. Be conversational and helpful
7. Don't say "I don't have access" - the emails are right above

YOUR ANSWER:"""
        )
        
        answer_chain = LLMChain(
            llm=self.llm,
            prompt=answer_generation_prompt,
            output_key="final_answer",
            verbose=True
        )
        
        # ============ BUILD SEQUENTIAL CHAIN ============
        self.sequential_chain = SequentialChain(
            chains=[
                context_chain,
                analysis_chain,
                retrieval_transform,
                answer_chain
            ],
            input_variables=["original_question", "chat_history"],
            output_variables=["final_answer", "resolved_question", "query_analysis", "emails_retrieved"],
            verbose=True,
            memory=None
        )
        
        logger.info("✓ Sequential Chain built successfully")
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the sequential chain"""
        try:
            question = inputs["question"]
            logger.info(f"\n{'='*80}")
            logger.info(f"🚀 Starting Sequential Chain for: {question}")
            logger.info(f"{'='*80}\n")
            
            # Get chat history
            chat_history = ""
            if self.config.enable_memory and self.internal_memory:
                try:
                    history_vars = self.internal_memory.load_memory_variables({})
                    chat_history = history_vars.get("chat_history", "")
                except:
                    chat_history = ""
            
            # Run sequential chain
            result = self.sequential_chain({
                "original_question": question,
                "chat_history": chat_history
            })
            
            answer = result.get("final_answer", "No answer generated.")
            
            # Save to memory
            if self.config.enable_memory and self.internal_memory:
                self.internal_memory.save_context(
                    {"original_question": question},
                    {"final_answer": answer}
                )
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Sequential Chain completed")
            logger.info(f"   Resolved: {result.get('resolved_question', 'N/A')}")
            logger.info(f"   Emails Retrieved: {result.get('emails_retrieved', 0)}")
            logger.info(f"{'='*80}\n")
            
            return {"answer": answer}
            
        except Exception as e:
            logger.error(f"Error in sequential chain execution: {e}", exc_info=True)
            return {"answer": f"An error occurred: {str(e)}"}
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, str]:
        """Parse LLM analysis output"""
        result = {
            "scope": "RELEVANT",
            "search_terms": "",
            "needs_count": "NO",
            "info_type": "general"
        }
        
        for line in analysis_text.split('\n'):
            line = line.strip()
            if line.startswith("SCOPE:"):
                scope = line.split(":", 1)[1].strip().upper()
                if "ALL" in scope:
                    result["scope"] = "ALL"
            elif line.startswith("SEARCH_TERMS:"):
                result["search_terms"] = line.split(":", 1)[1].strip()
            elif line.startswith("NEEDS_COUNT:"):
                count = line.split(":", 1)[1].strip().upper()
                if "YES" in count:
                    result["needs_count"] = "YES"
            elif line.startswith("INFO_TYPE:"):
                result["info_type"] = line.split(":", 1)[1].strip()
        
        return result
    
    def _fetch_and_process_emails(self) -> List[Dict]:
        """Fetch emails and normalize data"""
        os.makedirs(self.config.data_dir, exist_ok=True)
        today = datetime.date.today()
        today_str = today.isoformat()
        data_fname = os.path.join(self.config.data_dir, f"emails_{today_str}.json")
        
        if self.last_fetch_date == today_str and self.all_emails:
            logger.info(f"Using cached emails ({len(self.all_emails)} emails)")
            return self.all_emails
        
        if os.path.exists(data_fname):
            try:
                with open(data_fname, "r", encoding="utf-8") as f:
                    emails = json.load(f)
                    logger.info(f"✓ Loaded {len(emails)} emails from file")
                    self.all_emails = emails
                    self.last_fetch_date = today_str
                    return emails
            except Exception as e:
                logger.error(f"Error loading emails: {e}")
        
        logger.info(f"📧 Fetching emails for {today_str}...")
        try:
            emails = fetch_emails_since(today)
            if not emails:
                return []
            
            for email in emails:
                email["date"] = EmailProcessor.normalize_date(email.get("date", ""))
            
            with open(data_fname, "w", encoding="utf-8") as f:
                json.dump(emails, f, ensure_ascii=False, indent=2)
            
            self.all_emails = emails
            self.last_fetch_date = today_str
            return emails
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _ensure_vectorstore(self, emails: List[Dict]) -> bool:
        """Ensure vectorstore is ready"""
        try:
            if self.vectorstore_manager.vectorstore is None:
                self.vectorstore_manager.load_or_create(emails)
            return self.vectorstore_manager.vectorstore is not None
        except Exception as e:
            logger.error(f"Error ensuring vectorstore: {e}")
            return False
    
    def _get_all_unique_documents(self, emails: List[Dict]):
        """Get all unique email documents"""
        try:
            all_docs = self.vectorstore_manager._prepare_documents(emails)
            return self._deduplicate_documents(all_docs)[:MAX_CONTEXT_EMAILS]
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []
    
    def _get_semantic_documents(self, question: str, k: int):
        """Get semantically relevant documents"""
        try:
            retriever = self.vectorstore_manager.vectorstore.as_retriever(
                search_kwargs={"k": k}
            )
            relevant_docs = retriever.get_relevant_documents(question)
            return self._deduplicate_documents(relevant_docs)
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _deduplicate_documents(self, documents):
        """Remove duplicate documents"""
        seen_hashes = set()
        unique_docs = []
        
        for doc in documents:
            email_hash = doc.metadata.get("email_hash")
            if email_hash and email_hash not in seen_hashes:
                seen_hashes.add(email_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _build_email_context(self, documents) -> str:
        """Build formatted email context for LLM"""
        today_str = datetime.date.today().isoformat()
        
        context = f"Today's date: {today_str}\n"
        context += f"Total emails: {len(documents)}\n\n"
        context += "=" * 80 + "\n\n"
        
        for i, doc in enumerate(documents, 1):
            context += f"EMAIL #{i}:\n"
            context += f"{doc.page_content}\n"
            context += "=" * 80 + "\n\n"
        
        return context
    
    def clear_memory(self):
        """Clear conversation memory"""
        if self.internal_memory:
            self.internal_memory.clear()
            logger.info("✓ Memory cleared")

def make_email_chain(config: Optional[EmailRAGConfig] = None) -> EmailRAGSequentialChain:
    """Factory function to create Email RAG Sequential Chain"""
    if config is None:
        config = EmailRAGConfig()
    
    try:
        logger.info(f"Initializing Sequential Email RAG Chain...")
        logger.info(f"LLM: {config.model_name}")
        logger.info(f"Embeddings: {config.embedding_model}")
        logger.info(f"Memory: {config.enable_memory}")
        
        llm = GPT4All(
            model=config.model_name,
            allow_download=True,
            max_tokens=config.max_tokens
        )
        
        embeddings = SentenceTransformerEmbeddings(model_name=config.embedding_model)
        
        chain = EmailRAGSequentialChain(
            llm=llm,
            embeddings=embeddings,
            config=config
        )
        
        logger.info("✓ Sequential Email RAG Chain ready!\n")
        return chain
        
    except Exception as e:
        logger.error(f"Error creating chain: {e}")
        raise