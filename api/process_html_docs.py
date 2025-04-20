#!/usr/bin/env python3
"""
HTML Document Processing Utility for RAG Chatbot

This script helps process HTML documents for the RAG chatbot by:
1. Analyzing HTML documents for redundancy
2. Creating an optimized processing plan
3. Preprocessing HTML to clean and extract meaningful content
4. Batch processing documents into the vector database

Example usage:
    # Analyze documents
    python process_html_docs.py analyze --folder ./docs --output analysis.json
    
    # Batch process documents
    python process_html_docs.py process --folder ./docs --batch-size 5
    
    # Process a single document with preprocessing
    python process_html_docs.py process-single --file ./docs/example.html
"""

import os
import sys
import argparse
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("html_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the API directory to the Python path
api_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api")
sys.path.append(api_dir)

# Import the required modules
try:
    from api.html_preprocessor import HTMLPreprocessor, preprocess_html_folder
    from api.analyze_docs import analyze_document_similarity, create_processing_plan
    from api.chroma_utils import index_document_to_chroma
    from api.db_utils import insert_document_record
except ImportError as e:
    logger.error(f"Error importing API modules: {str(e)}")
    logger.error("Please make sure you're running this script from the project root directory")
    sys.exit(1)

def analyze_documents(args):
    """Analyze documents in a folder for redundancy and optimization opportunities"""
    folder_path = args.folder
    
    if not os.path.exists(folder_path):
        logger.error(f"Folder not found: {folder_path}")
        return 1
    
    logger.info(f"Analyzing documents in {folder_path}")
    
    try:
        # Analyze documents
        analysis_result = analyze_document_similarity(
            folder_path,
            min_paragraph_length=args.min_length,
            similarity_threshold=args.threshold
        )
        
        # Print basic statistics
        if 'stats' in analysis_result:
            stats = analysis_result['stats']
            logger.info(f"Total documents: {stats['total_documents']}")
            logger.info(f"Total paragraphs: {stats['total_paragraphs']}")
            logger.info(f"Duplicate paragraphs: {stats['duplicate_paragraphs']} ({stats['duplicate_paragraph_percentage']:.2f}%)")
            logger.info(f"Similar document pairs: {stats['similar_document_pairs']}")
        
        # Create processing plan
        if not args.no_plan:
            plan = create_processing_plan(analysis_result, args.plan_output)
            logger.info(f"Processing plan created with {len(plan['document_batches'])} batches")
        
        # Save analysis results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            logger.info(f"Analysis results saved to {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error analyzing documents: {str(e)}")
        return 1

def process_documents(args):
    """Process documents in batches with optimized preprocessing"""
    folder_path = args.folder
    
    if not os.path.exists(folder_path):
        logger.error(f"Folder not found: {folder_path}")
        return 1
    
    # Get plan from file if provided
    if args.plan:
        try:
            with open(args.plan, 'r') as f:
                plan = json.load(f)
            logger.info(f"Loaded processing plan from {args.plan}")
            
            if 'document_batches' in plan:
                batches = plan['document_batches']
                logger.info(f"Found {len(batches)} batches in the plan")
            else:
                logger.error("Invalid plan format - no document_batches found")
                return 1
                
        except Exception as e:
            logger.error(f"Error loading plan: {str(e)}")
            return 1
    else:
        # Create batches from folder
        html_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.html')]
        
        if not html_files:
            logger.error(f"No HTML files found in {folder_path}")
            return 1
            
        logger.info(f"Found {len(html_files)} HTML files in {folder_path}")
        
        # Create batches
        batch_size = args.batch_size
        batches = []
        
        for i in range(0, len(html_files), batch_size):
            batch = html_files[i:i+batch_size]
            batches.append({
                'batch_id': i // batch_size + 1,
                'documents': batch
            })
        
        logger.info(f"Created {len(batches)} batches with batch size {batch_size}")
    
    # Initialize HTML preprocessor
    preprocessor = HTMLPreprocessor(min_text_length=args.min_length)
    
    # Process each batch
    success_count = 0
    failure_count = 0
    
    for i, batch in enumerate(batches):
        batch_id = batch.get('batch_id', i+1)
        documents = batch.get('documents', [])
        
        logger.info(f"Processing batch {batch_id}/{len(batches)} with {len(documents)} documents")
        
        for doc_path in documents:
            try:
                if not os.path.exists(doc_path):
                    logger.warning(f"File not found: {doc_path}")
                    failure_count += 1
                    continue
                
                logger.info(f"Processing document: {doc_path}")
                
                # Process the document
                start_time = time.time()
                original_size = os.path.getsize(doc_path)
                
                # Preprocess HTML content
                processed_content = preprocessor.preprocess_file(doc_path)
                
                if not processed_content:
                    logger.warning(f"No content extracted from {doc_path}")
                    failure_count += 1
                    continue
                    
                processed_size = len(processed_content)
                preprocessing_time = time.time() - start_time
                
                # Generate a unique ID for the document
                file_id = uuid.uuid4().int % (2**31 - 1)  # Convert to integer
                
                # Save preprocessed content to temporary file
                temp_file_path = os.path.join(os.path.dirname(doc_path), f"temp_{os.path.basename(doc_path)}")
                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write(processed_content)
                
                # Index the document
                indexing_start = time.time()
                success = index_document_to_chroma(temp_file_path, file_id)
                indexing_time = time.time() - indexing_start
                
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                if success:
                    # Record the document in the database if needed
                    doc_name = os.path.basename(doc_path)
                    insert_document_record(file_id, doc_name, doc_path)
                    
                    # Log success
                    logger.info(f"Successfully processed {doc_name}:")
                    logger.info(f"  - Original size: {original_size/1024:.2f} KB")
                    logger.info(f"  - Processed size: {processed_size/1024:.2f} KB")
                    logger.info(f"  - Reduction: {(1 - processed_size/original_size) * 100:.2f}%")
                    logger.info(f"  - Preprocessing time: {preprocessing_time:.2f} seconds")
                    logger.info(f"  - Indexing time: {indexing_time:.2f} seconds")
                    
                    success_count += 1
                else:
                    logger.error(f"Failed to index document: {doc_path}")
                    failure_count += 1
            
            except Exception as e:
                logger.error(f"Error processing document {doc_path}: {str(e)}")
                failure_count += 1
        
        # Log batch completion
        logger.info(f"Completed batch {batch_id}/{len(batches)}")
        
        # Pause between batches if requested
        if args.batch_delay > 0 and i < len(batches) - 1:
            logger.info(f"Pausing for {args.batch_delay} seconds before next batch")
            time.sleep(args.batch_delay)
    
    # Log final stats
    logger.info(f"Processing complete: {success_count} documents processed successfully, {failure_count} failed")
    
    return 0

def process_single_document(args):
    """Process a single document with preprocessing"""
    file_path = args.file
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return 1
    
    try:
        logger.info(f"Processing document: {file_path}")
        
        # Process the document
        start_time = time.time()
        
        # Initialize HTML preprocessor
        preprocessor = HTMLPreprocessor(min_text_length=args.min_length)
        
        # Get original file size
        original_size = os.path.getsize(file_path)
        
        # Preprocess HTML content
        processed_content = preprocessor.preprocess_file(file_path)
        
        if not processed_content:
            logger.error(f"No content extracted from {file_path}")
            return 1
            
        processed_size = len(processed_content)
        preprocessing_time = time.time() - start_time
        
        # Generate a unique ID for the document
        file_id = uuid.uuid4().int % (2**31 - 1)  # Convert to integer
        
        # Save preprocessed content to temporary file
        temp_file_path = os.path.join(os.path.dirname(file_path), f"temp_{os.path.basename(file_path)}")
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(processed_content)
        
        # Option to preview the processed content
        if args.preview:
            preview_length = min(500, len(processed_content))
            logger.info(f"Preview of processed content (first {preview_length} chars):")
            logger.info(f"{processed_content[:preview_length]}...")
        
        # Index the document if requested
        if not args.no_index:
            indexing_start = time.time()
            success = index_document_to_chroma(temp_file_path, file_id)
            indexing_time = time.time() - indexing_start
            
            if success:
                # Record the document in the database
                doc_name = os.path.basename(file_path)
                insert_document_record(file_id, doc_name, file_path)
                
                logger.info(f"Successfully indexed document with ID: {file_id}")
                logger.info(f"Indexing time: {indexing_time:.2f} seconds")
            else:
                logger.error("Failed to index document")
        
        # Clean up temp file
        if os.path.exists(temp_file_path) and not args.keep_temp:
            os.remove(temp_file_path)
        elif args.keep_temp:
            logger.info(f"Temporary file saved at: {temp_file_path}")
        
        # Log statistics
        logger.info("Processing statistics:")
        logger.info(f"  - Original size: {original_size/1024:.2f} KB")
        logger.info(f"  - Processed size: {processed_size/1024:.2f} KB")
        logger.info(f"  - Reduction: {(1 - processed_size/original_size) * 100:.2f}%")
        logger.info(f"  - Preprocessing time: {preprocessing_time:.2f} seconds")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Process HTML documents for the RAG chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", 
        help="Analyze documents for redundancy and optimization opportunities"
    )
    analyze_parser.add_argument("--folder", "-f", required=True, help="Path to the folder containing HTML documents")
    analyze_parser.add_argument("--output", "-o", help="Output file to save analysis results (JSON)")
    analyze_parser.add_argument("--min-length", "-m", type=int, default=100, help="Minimum paragraph length to consider")
    analyze_parser.add_argument("--threshold", "-t", type=float, default=0.8, help="Similarity threshold (0.0-1.0)")
    analyze_parser.add_argument("--no-plan", action="store_true", help="Don't create a processing plan")
    analyze_parser.add_argument("--plan-output", "-p", help="Output file to save processing plan (JSON)")
    
    # Batch process command
    process_parser = subparsers.add_parser(
        "process", 
        help="Process documents in batches with optimized preprocessing"
    )
    process_parser.add_argument("--folder", "-f", required=True, help="Path to the folder containing HTML documents")
    process_parser.add_argument("--plan", "-p", help="JSON file with processing plan (optional)")
    process_parser.add_argument("--batch-size", "-b", type=int, default=5, help="Number of documents to process in each batch")
    process_parser.add_argument("--batch-delay", "-d", type=int, default=0, help="Delay in seconds between batches")
    process_parser.add_argument("--min-length", "-m", type=int, default=50, help="Minimum text length to keep")
    
    # Process single document command
    single_parser = subparsers.add_parser(
        "process-single", 
        help="Process a single document with preprocessing"
    )
    single_parser.add_argument("--file", "-f", required=True, help="Path to the HTML file to process")
    single_parser.add_argument("--min-length", "-m", type=int, default=50, help="Minimum text length to keep")
    single_parser.add_argument("--preview", "-p", action="store_true", help="Preview the processed content")
    single_parser.add_argument("--no-index", "-n", action="store_true", help="Don't index the document, just preprocess")
    single_parser.add_argument("--keep-temp", "-k", action="store_true", help="Keep the temporary processed file")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        return analyze_documents(args)
    elif args.command == "process":
        return process_documents(args)
    elif args.command == "process-single":
        return process_single_document(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 