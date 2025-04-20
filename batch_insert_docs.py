import os
import sys
import logging
from tqdm import tqdm

# Add the API directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Import functions from the existing modules
from db_utils import insert_document_record
from chroma_utils import index_document_to_chroma

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def batch_insert_documents(docs_folder):
    """
    Insert all documents from a folder into the vector database
    
    Args:
        docs_folder: Path to the folder containing the documents
    """
    # Check if folder exists
    if not os.path.exists(docs_folder):
        logger.error(f"Folder does not exist: {docs_folder}")
        return False
    
    logger.info(f"Starting batch insertion of documents from: {docs_folder}")
    
    # List all files in the folder
    files = [f for f in os.listdir(docs_folder) if os.path.isfile(os.path.join(docs_folder, f))]
    
    # Filter for supported document types
    supported_extensions = ['.pdf', '.docx', '.html', '.csv']
    supported_files = [f for f in files if os.path.splitext(f)[1].lower() in supported_extensions]
    
    logger.info(f"Found {len(supported_files)} supported documents")
    
    # Setup counters for statistics
    success_count = 0
    failed_count = 0
    
    # Process each file with a progress bar
    for filename in tqdm(supported_files, desc="Indexing documents"):
        file_path = os.path.join(docs_folder, filename)
        
        try:
            # Insert document record to get file_id
            file_id = insert_document_record(filename)
            logger.info(f"Created record for {filename} with ID: {file_id}")
            
            # Index document to ChromaDB
            success = index_document_to_chroma(file_path, file_id)
            
            if success:
                logger.info(f"Successfully indexed: {filename}")
                success_count += 1
            else:
                logger.error(f"Failed to index: {filename}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            failed_count += 1
    
    # Log summary
    logger.info(f"Batch insertion complete.")
    logger.info(f"Successfully indexed: {success_count} documents")
    logger.info(f"Failed to index: {failed_count} documents")
    
    return success_count > 0

if __name__ == "__main__":
    # The '@docs' folder the user mentioned is likely the docs folder in the repository
    docs_folder = os.path.join(os.path.dirname(__file__), 'docs')
    
    # Check if command line argument was provided for docs folder path
    if len(sys.argv) > 1:
        docs_folder = sys.argv[1]
    
    print(f"Using docs folder: {docs_folder}")
    
    # Run the batch insertion
    result = batch_insert_documents(docs_folder)
    
    if result:
        print("Documents successfully inserted into vector database.")
    else:
        print("Failed to insert documents into vector database.") 