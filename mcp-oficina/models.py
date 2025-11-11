from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Modelos para el servidor MCP
from pydantic import BaseModel
from typing import List, Optional

class Reunion(BaseModel):
    id: str 
    titulo: str
    dia: str
    hora: str
    invitados: Optional[List[str]] = []
    descripcion: Optional[str] = None
    

class Contacto(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    departamento: Optional[str] = None

class Email(BaseModel):
    destinatario: str
    asunto: str
    contenido: str
    fecha_envio: str
    
# Modelos para el servidor FastAPI
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]