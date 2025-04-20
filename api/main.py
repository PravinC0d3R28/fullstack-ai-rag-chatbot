from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest, LoginRequest, LoginResponse, TokenData
from langchain_utils import get_rag_chain
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record, verify_user
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, List
import shutil
from pydantic import BaseModel

# JWT Configuration
SECRET_KEY = "YOUR_SECRET_KEY_HERE"  # In production, use a secure random key and store it securely
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Update CORS to allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now - more permissive for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, is_admin=is_admin)
    except JWTError:
        raise credentials_exception
    return token_data

async def get_current_admin_user(current_user: TokenData = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Test endpoint to verify API is working
@app.get("/api/test")
async def test_api():
    return {"message": "API is working correctly"}

# Authentication Endpoints
@app.post("/token", response_model=LoginResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "is_admin": user["is_admin"]}, 
        expires_delta=access_token_expires
    )
    
    return {
        "username": user["username"],
        "is_admin": user["is_admin"],
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = verify_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "is_admin": user["is_admin"]}, 
        expires_delta=access_token_expires
    )
    
    return {
        "username": user["username"],
        "is_admin": user["is_admin"],
        "access_token": access_token,
        "token_type": "bearer"
    }

# Protected API endpoints
@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model.value}")
    if not session_id:
        session_id = str(uuid.uuid4())

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(query_input.model.value)
    answer = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })['answer']
    
    insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post("/upload-doc")
async def upload_and_index_document(
    file: UploadFile = File(...)
    # Temporarily removed admin authentication: current_user: TokenData = Depends(get_current_admin_user)
):
    allowed_extensions = ['.pdf', '.docx', '.html', '.csv']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}"

    try:
        logger.info(f"Starting upload and indexing of document: {file.filename}")
        
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Reset file stream for potential future reads
        await file.seek(0)
        
        logger.info(f"File saved to temporary location: {temp_file_path}")
        
        # Generate a file ID and record in the database
        file_id = insert_document_record(file.filename)
        logger.info(f"Document record created with file_id: {file_id}")
        
        # Index the document
        success = index_document_to_chroma(temp_file_path, file_id)
        
        if success:
            logger.info(f"Successfully indexed document: {file.filename} with file_id: {file_id}")
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            logger.error(f"Failed to index document: {file.filename}")
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
            
    except Exception as e:
        logger.error(f"Error processing upload for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
        
    finally:
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Temporary file removed: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error removing temporary file {temp_file_path}: {str(e)}")

@app.get("/list-docs", response_model=list[DocumentInfo])
async def list_documents():  
    # Temporarily removed admin authentication: current_user: TokenData = Depends(get_current_admin_user)
    return get_all_documents()

@app.post("/delete-doc")
async def delete_document(
    request: DeleteFileRequest
    # Temporarily removed admin authentication: current_user: TokenData = Depends(get_current_admin_user)
):
    # Delete from Chroma
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        # If successfully deleted from Chroma, delete from our database
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}

@app.get("/api/models")
async def get_available_models():
    # Temporarily removed admin authentication: current_user: TokenData = Depends(get_current_admin_user)
    from pydantic_models import ModelName
    return [{"value": model.value, "name": model.name} for model in ModelName]

