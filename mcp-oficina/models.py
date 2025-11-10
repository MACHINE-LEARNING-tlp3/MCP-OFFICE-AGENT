from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Modelos para el servidor MCP
class Reunion(BaseModel):
    id: str = Field(description="ID único de la reunión")
    titulo: str = Field(description="Título de la reunión")
    dia: str = Field(description="Fecha de la reunión (YYYY-MM-DD)")
    hora: str = Field(description="Hora de la reunión (HH:MM)")
    invitados: List[str] = Field(description="Lista de invitados")
    descripcion: Optional[str] = Field(description="Descripción de la reunión")

class Contacto(BaseModel):
    nombre: str = Field(description="Nombre del contacto")
    email: str = Field(description="Email del contacto")
    telefono: Optional[str] = Field(description="Teléfono del contacto")
    departamento: Optional[str] = Field(description="Departamento del contacto")

class Email(BaseModel):
    destinatario: str = Field(description="Email del destinatario")
    asunto: str = Field(description="Asunto del email")
    contenido: str = Field(description="Contenido del email")
    fecha_envio: str = Field(description="Fecha de envío")

# Modelos para el servidor FastAPI
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]