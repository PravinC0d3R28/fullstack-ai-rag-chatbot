import os
import sys
import logging
from collections import defaultdict
from html_preprocessor import HTMLPreprocessor, preprocess_html_folder
from typing import Dict, List, Set, Tuple
import argparse
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_document_similarity(docs_folder: str, min_paragraph_length: int = 100, similarity_threshold: float = 0.8) -> Dict:
    """
    Analyze documents in a folder for similarity and redundancy.
    
    Args:
        docs_folder: Path to the folder containing HTML documents
        min_paragraph_length: Minimum length for a paragraph to be considered
        similarity_threshold: Threshold for considering text similar (0.0-1.0)
        
    Returns:
        Dictionary with analysis results
    """
    results = preprocess_html_folder(docs_folder)
    
    if not results:
        logger.error(f"No documents found or processed in {docs_folder}")
        return {"error": "No documents processed"}
        
    # Store document contents by file path
    documents = {file_path: content for file_path, content in results}
    
    # Extract paragraphs from each document
    all_paragraphs: Dict[str, List[str]] = {}
    for file_path, content in documents.items():
        # Split content into paragraphs
        paragraphs = [p for p in content.split('\n\n') if len(p) >= min_paragraph_length]
        all_paragraphs[file_path] = paragraphs
    
    # Find duplicate paragraphs across documents
    paragraph_to_files: Dict[str, Set[str]] = defaultdict(set)
    for file_path, paragraphs in all_paragraphs.items():
        for para in paragraphs:
            # Use paragraph text as key
            paragraph_to_files[para].add(file_path)
    
    # Filter to only duplicated paragraphs
    duplicate_paragraphs = {
        para: list(files) 
        for para, files in paragraph_to_files.items() 
        if len(files) > 1
    }
    
    # Group similar paragraphs
    similar_paragraph_groups = find_similar_paragraphs(paragraph_to_files, similarity_threshold)
    
    # Calculate document similarity scores
    doc_similarity = calculate_document_similarity(all_paragraphs)
    
    # Sort documents by similarity
    similar_doc_pairs = [
        {'doc1': doc1, 'doc2': doc2, 'similarity': score}
        for (doc1, doc2), score in doc_similarity.items()
        if score > similarity_threshold and doc1 != doc2
    ]
    similar_doc_pairs.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Identify documents with the most duplicated content
    doc_duplicate_count = defaultdict(int)
    for para, files in duplicate_paragraphs.items():
        for file_path in files:
            doc_duplicate_count[file_path] += 1
    
    duplicate_rich_docs = sorted(
        [{'path': doc, 'duplicate_paragraphs': count} 
         for doc, count in doc_duplicate_count.items()],
        key=lambda x: x['duplicate_paragraphs'],
        reverse=True
    )
    
    # Generate statistics
    stats = {
        'total_documents': len(documents),
        'total_paragraphs': sum(len(paragraphs) for paragraphs in all_paragraphs.values()),
        'duplicate_paragraphs': len(duplicate_paragraphs),
        'duplicate_paragraph_percentage': len(duplicate_paragraphs) / sum(len(paragraphs) for paragraphs in all_paragraphs.values()) * 100 if all_paragraphs else 0,
        'similar_paragraph_groups': len(similar_paragraph_groups),
        'similar_document_pairs': len(similar_doc_pairs)
    }
    
    # Prepare recommendations
    recommendations = []
    
    # Recommend processing high-duplication documents separately
    if duplicate_rich_docs:
        top_duplicate_docs = [doc['path'] for doc in duplicate_rich_docs[:min(5, len(duplicate_rich_docs))]]
        recommendations.append({
            'type': 'high_duplication',
            'description': 'These documents contain a high amount of duplicate content:',
            'documents': top_duplicate_docs,
            'suggestion': 'Consider preprocessing these documents to remove duplicate paragraphs before adding to the vector store.'
        })
    
    # Recommend merging similar documents
    if similar_doc_pairs:
        top_similar_pairs = similar_doc_pairs[:min(5, len(similar_doc_pairs))]
        recommendations.append({
            'type': 'similar_documents',
            'description': 'These document pairs are very similar:',
            'document_pairs': [{'doc1': pair['doc1'], 'doc2': pair['doc2'], 'similarity': pair['similarity']} for pair in top_similar_pairs],
            'suggestion': 'Consider merging these document pairs or removing one from each pair to reduce redundancy.'
        })
    
    # Recommend batch processing to avoid overloading
    if len(documents) > 20:
        recommendations.append({
            'type': 'batch_processing',
            'description': 'Large number of documents detected',
            'suggestion': f'Process documents in batches of 5-10 to avoid memory issues. Total documents: {len(documents)}'
        })
    
    # Final analysis result
    analysis = {
        'stats': stats,
        'recommendations': recommendations,
        'duplicate_rich_documents': duplicate_rich_docs[:10] if duplicate_rich_docs else [],
        'similar_document_pairs': similar_doc_pairs[:10] if similar_doc_pairs else []
    }
    
    return analysis

def find_similar_paragraphs(paragraph_to_files: Dict[str, Set[str]], threshold: float = 0.8) -> List[List[str]]:
    """
    Group similar paragraphs based on character-level similarity.
    
    Args:
        paragraph_to_files: Mapping of paragraphs to files
        threshold: Similarity threshold (0.0-1.0)
        
    Returns:
        List of groups of similar paragraphs
    """
    # Extract unique paragraphs
    unique_paragraphs = list(paragraph_to_files.keys())
    
    # Initialize groups
    similar_groups = []
    processed = set()
    
    # Simple similarity function (character ratio)
    def simple_similarity(text1, text2):
        # Use a simple character overlap measure for speed
        shorter = min(len(text1), len(text2))
        longer = max(len(text1), len(text2))
        
        # If length difference is too great, not similar
        if shorter < longer * 0.7:
            return 0.0
            
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(text1.lower(), text2.lower()))
        return matches / longer if longer > 0 else 0.0
    
    # Group similar paragraphs
    for i, para1 in enumerate(unique_paragraphs):
        if para1 in processed:
            continue
            
        group = [para1]
        processed.add(para1)
        
        # Only check a limited number of paragraphs for efficiency
        check_limit = min(1000, len(unique_paragraphs))
        for j in range(i+1, min(i+check_limit, len(unique_paragraphs))):
            para2 = unique_paragraphs[j]
            if para2 not in processed and simple_similarity(para1, para2) >= threshold:
                group.append(para2)
                processed.add(para2)
                
        if len(group) > 1:
            similar_groups.append(group)
    
    return similar_groups

def calculate_document_similarity(all_paragraphs: Dict[str, List[str]]) -> Dict[Tuple[str, str], float]:
    """
    Calculate similarity scores between document pairs.
    
    Args:
        all_paragraphs: Dictionary mapping file paths to lists of paragraphs
        
    Returns:
        Dictionary mapping document pairs to similarity scores
    """
    # Initialize similarity scores
    similarity_scores = {}
    
    # Get document pairs
    documents = list(all_paragraphs.keys())
    
    # Calculate Jaccard similarity between document paragraphs
    for i in range(len(documents)):
        doc1 = documents[i]
        para_set1 = set(all_paragraphs[doc1])
        
        for j in range(i+1, len(documents)):
            doc2 = documents[j]
            para_set2 = set(all_paragraphs[doc2])
            
            # Jaccard similarity: intersection / union
            intersection = len(para_set1.intersection(para_set2))
            union = len(para_set1.union(para_set2))
            
            if union > 0:
                similarity = intersection / union
                similarity_scores[(doc1, doc2)] = similarity
    
    return similarity_scores

def create_processing_plan(analysis_result: Dict, output_file: str = None) -> Dict:
    """
    Create a processing plan based on analysis results.
    
    Args:
        analysis_result: Analysis results from analyze_document_similarity
        output_file: Optional file to write the plan to
        
    Returns:
        Dictionary with processing plan
    """
    # Initialize the processing plan
    plan = {
        'batch_processing': True,
        'batch_size': 5,
        'preprocessing': {
            'remove_duplicate_content': True,
            'remove_boilerplate': True,
            'min_content_length': 50
        },
        'document_batches': []
    }
    
    # Extract documents from analysis
    duplicate_rich_docs = [doc['path'] for doc in analysis_result.get('duplicate_rich_documents', [])]
    similar_pairs = analysis_result.get('similar_document_pairs', [])
    
    # Create a list of all documents
    all_docs = set()
    
    # Add duplicate-rich documents
    for doc in duplicate_rich_docs:
        all_docs.add(doc)
    
    # Add similar document pairs
    for pair in similar_pairs:
        all_docs.add(pair['doc1'])
        all_docs.add(pair['doc2'])
    
    # Create efficient batches (potentially excluding one from each similar pair)
    documents_to_process = list(all_docs)
    documents_to_exclude = set()
    
    # For similar pairs, consider excluding the second document
    for pair in similar_pairs:
        # If similarity is very high (>0.9), we might exclude one
        if pair['similarity'] > 0.9:
            if pair['doc2'] not in documents_to_exclude:
                documents_to_exclude.add(pair['doc2'])
    
    # Create batches of documents
    batch_size = plan['batch_size']
    filtered_docs = [doc for doc in documents_to_process if doc not in documents_to_exclude]
    
    # Create batches
    for i in range(0, len(filtered_docs), batch_size):
        batch = filtered_docs[i:i+batch_size]
        plan['document_batches'].append({
            'batch_id': i // batch_size + 1,
            'documents': batch
        })
    
    # Add excluded documents as a separate section
    if documents_to_exclude:
        plan['excluded_documents'] = list(documents_to_exclude)
        plan['exclusion_reason'] = "These documents have high similarity with others and may be redundant."
    
    # Write the plan to a file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(plan, f, indent=2)
        logger.info(f"Processing plan written to {output_file}")
    
    return plan

def main():
    parser = argparse.ArgumentParser(description="Analyze HTML documents for redundancy and optimization")
    parser.add_argument("docs_folder", help="Path to the folder containing HTML documents")
    parser.add_argument("--output", "-o", help="Output file to save analysis results (JSON)")
    parser.add_argument("--plan", "-p", help="Output file to save processing plan (JSON)")
    parser.add_argument("--min-length", "-m", type=int, default=100, help="Minimum paragraph length to consider")
    parser.add_argument("--threshold", "-t", type=float, default=0.8, help="Similarity threshold (0.0-1.0)")
    
    args = parser.parse_args()
    
    # Check if the docs folder exists
    if not os.path.exists(args.docs_folder):
        logger.error(f"Documents folder not found: {args.docs_folder}")
        sys.exit(1)
    
    logger.info(f"Analyzing documents in {args.docs_folder}")
    
    # Run the analysis
    analysis_result = analyze_document_similarity(
        args.docs_folder, 
        min_paragraph_length=args.min_length,
        similarity_threshold=args.threshold
    )
    
    # Print basic stats
    if 'stats' in analysis_result:
        stats = analysis_result['stats']
        logger.info(f"Total documents: {stats['total_documents']}")
        logger.info(f"Total paragraphs: {stats['total_paragraphs']}")
        logger.info(f"Duplicate paragraphs: {stats['duplicate_paragraphs']} ({stats['duplicate_paragraph_percentage']:.2f}%)")
        logger.info(f"Similar document pairs: {stats['similar_document_pairs']}")
    
    # Save analysis results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis_result, f, indent=2)
        logger.info(f"Analysis results saved to {args.output}")
    
    # Create and save processing plan if requested
    if args.plan:
        plan = create_processing_plan(analysis_result, args.plan)
        logger.info(f"Processing plan created with {len(plan['document_batches'])} batches")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 