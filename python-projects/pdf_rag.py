# pdf_rag.py
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader  # Fixed import
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import glob

# 1️⃣ Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# 2️⃣ Initialize LLM (OpenRouter key)
llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",
    openai_api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    max_tokens=500
)

# 3️⃣ Find and load PDFs
print("Looking for PDF files...")

# Check different possible locations
possible_paths = [
    "LangChain_Basics_Guide.pdf",  # current directory
    "*.pdf",  # any PDF in current directory
    "../*.pdf",  # parent directory
]

pdf_files = []
for path_pattern in possible_paths:
    found_files = glob.glob(path_pattern)
    pdf_files.extend(found_files)
    if found_files:
        break

if not pdf_files:
    print("❌ No PDF files found!")
    print("Current directory contents:")
    print([f for f in os.listdir('.') if f.endswith('.pdf')])
    
    # Create a sample PDF for testing
    print("\n📄 Creating sample document for testing...")
    docs = []
    
    # Sample text documents instead of PDF
    sample_texts = [
        "LangChain is a framework for developing applications powered by language models. It enables applications that are context-aware and can reason about their environment.",
        "RAG (Retrieval-Augmented Generation) combines retrieval of relevant documents with generation from language models to provide accurate, contextual responses.",
        "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, AI, and automation.",
        "Vector databases store high-dimensional vectors and enable similarity search. They are essential for RAG systems to find relevant documents.",
        "FAISS (Facebook AI Similarity Search) is a library for efficient similarity search and clustering of dense vectors."
    ]
    
    from langchain.schema import Document
    docs = [Document(page_content=text, metadata={"source": f"sample_doc_{i}"}) for i, text in enumerate(sample_texts)]
    
else:
    print(f"✅ Found PDF files: {pdf_files}")
    docs = []
    
    for file in pdf_files:
        try:
            print(f"Loading: {file}")
            loader = PyPDFLoader(file)
            file_docs = loader.load()
            docs.extend(file_docs)
            print(f"  → Loaded {len(file_docs)} pages")
        except Exception as e:
            print(f"  ❌ Error loading {file}: {e}")

print(f"\n📚 Total documents loaded: {len(docs)}")

if not docs:
    print("❌ No documents to process!")
    exit(1)

# 4️⃣ Split documents into chunks
print("📝 Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

split_docs = text_splitter.split_documents(docs)
print(f"✅ Created {len(split_docs)} text chunks")

# 5️⃣ Initialize local embeddings
print("🔄 Initializing embeddings...")
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# 6️⃣ Create FAISS vectorstore from PDF chunks
print("🗂️ Creating vectorstore...")
try:
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    print("✅ Vectorstore created successfully")
except Exception as e:
    print(f"❌ Error creating vectorstore: {e}")
    exit(1)

# Optional: save vectorstore to disk for reuse
# vectorstore.save_local("faiss_index")

# 7️⃣ Setup RetrievalQA chain
print("🔗 Setting up QA chain...")
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # retrieve top 3 chunks
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    return_source_documents=True  # returns source documents
)

# 8️⃣ Ask questions
queries = [
    "What is LangChain used for?",
    "What is RAG?",
    "Sample Workflow for RAG",
    "Name a vector store supported by LangChain"
]

print("\n" + "="*50)
print("🤖 Q&A SESSION")
print("="*50)

for query in queries:
    print(f"\n❓ Question: {query}")
    try:
        result = qa_chain({"query": query})
        print(f"💡 Answer: {result['result']}")
        
        # Show source documents
        if 'source_documents' in result:
            print(f"📖 Sources: {len(result['source_documents'])} documents used")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✅ Done! To use your own PDFs, place them in this directory.")