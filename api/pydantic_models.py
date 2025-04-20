from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ModelName(str, Enum):
    GROQ = "llama-3.1-8b-instant"
    OLLAMA = "mistral"
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: ModelName = Field(default=ModelName.GROQ)

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    is_admin: bool
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str
    is_admin: bool = False