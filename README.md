# AI RAG Chatbot

This is a full-stack AI RAG (Retrieval Augmented Generation) chatbot that can answer questions based on your own documents. The application uses a vector database (ChromaDB) to store document embeddings and retrieves relevant context to provide accurate answers.

## Features

- **Document Management**: Upload, view, and delete documents
- **RAG-powered Q&A**: Get answers based on your uploaded documents
- **Voice-to-Text**: Speak your questions instead of typing
- **Multiple LLM Support**: Choose between different language models
- **Responsive UI**: Works on desktop and mobile devices
- **Authentication**: Secure admin access for document management

## Architecture

- **Frontend**: React with TypeScript, TailwindCSS
- **Backend**: FastAPI (Python)
- **Vector Database**: ChromaDB
- **Embedding Model**: all-MiniLM-L6-v2
- **Authentication**: JWT-based

## Usage

1. **General Users**:
   - Ask questions in the chat interface
   - Enable voice input by clicking the microphone icon
   - View chat history in the conversation window

2. **Admin Users**:
   - Log in to access the admin dashboard
   - Upload new documents (PDF, DOCX, HTML, CSV)
   - View and delete existing documents
   - Monitor system performance

## Development

This project was built with a focus on:
- Modern web technologies and frameworks
- Scalable architecture
- User-friendly interface
- Security best practices

For more information, check out the repository at [GitHub](https://github.com/PravinC0d3R28/fullstack-ai-rag-chatbot). 