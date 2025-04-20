from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, CSVLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from typing import List, Callable, Any
from langchain_core.documents import Document
import os
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adjust chunk size to handle more content per chunk
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100, length_function=len)

# Initialize embedding function
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2",model_kwargs={'device': 'cpu'})

# Create a wrapper class for the embedding function to match ChromaDB's interface
class EmbeddingFunctionWrapper:
    def __init__(self, embed_fn: Callable):
        self.embed_fn = embed_fn
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.embed_fn(input)
        return embeddings

# Create the wrapper
embedding_function = EmbeddingFunctionWrapper(embedding_model.embed_documents)

# ChromaDB configuration
PERSIST_DIRECTORY = os.getenv("PERSIST_DIRECTORY", "./chroma_db")

# Initialize ChromaDB client with persistent storage
def get_chroma_client():
    try:
        # Create a persistent client
        client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        logger.info("Successfully connected to ChromaDB")
        return client
    except Exception as e:
        logger.error(f"Error initializing ChromaDB client: {str(e)}")
        raise

# Initialize the vectorstore
def init_vectorstore():
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name="default",
            embedding_function=embedding_function
        )
        
        vectorstore = Chroma(
            client=client,
            collection_name="default",
            embedding_function=embedding_model,
            persist_directory=PERSIST_DIRECTORY
        )
        
        return vectorstore
    except Exception as e:
        logger.error(f"Error initializing vectorstore: {str(e)}")
        raise

# Create and expose the vectorstore instance
vectorstore = init_vectorstore()

def load_and_split_document(file_path: str) -> List[Document]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
        elif file_path.endswith('.html'):
            loader = UnstructuredHTMLLoader(file_path)
            documents = loader.load()
        elif file_path.endswith('.csv'):
            loader = CSVLoader(file_path=file_path)
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
    
        # Split the documents into chunks for more efficient processing
        splits = text_splitter.split_documents(documents)
        logger.info(f"Document split into {len(splits)} chunks")
        return splits
        
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {str(e)}")
        raise

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    """
    Index a document to ChromaDB
    """
    try:
        logger.info(f"Starting indexing of document: {file_path} with file_id: {file_id}")
        
        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Load and split document
        splits = load_and_split_document(file_path)
        if not splits:
            logger.warning("No valid content chunks were created from the document")
            return False
            
        # Get vectorstore
        try:
            documents = []
            ids = []
            metadatas = []
            
            for i, split in enumerate(splits):
                chunk_id = f"{file_id}_{i}"
                documents.append(split.page_content)
                ids.append(chunk_id)
                metadatas.append({
                    "file_id": file_id,
                    "chunk_id": i,
                    "source": file_path
                })
            
            # Use Chroma add method directly
            client = get_chroma_client()
            collection = client.get_or_create_collection(name="default", embedding_function=embedding_function)
            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully indexed document: {file_path} with {len(documents)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error adding document to Chroma: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Unexpected error indexing document: {str(e)}")
        return False

def delete_doc_from_chroma(file_id: int) -> bool:
    """
    Delete a document from ChromaDB
    """
    try:
        logger.info(f"Starting deletion of document with file_id: {file_id}")
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="default", embedding_function=embedding_function)
        
        # Get all chunks for the file_id
        results = collection.get(
            where={"file_id": file_id}
        )
        
        if not results or not results['ids']:
            logger.warning(f"No chunks found for file_id: {file_id}")
            return True
            
        chunk_ids = results['ids']
        logger.info(f"Found {len(chunk_ids)} chunks to delete")
        
        # Delete the chunks
        collection.delete(
            ids=chunk_ids
        )
        
        logger.info(f"Successfully deleted all chunks for file_id: {file_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return False
