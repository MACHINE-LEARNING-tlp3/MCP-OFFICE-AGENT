from mcp.server.fastmcp import FastMCP
from models import Reunion, Contacto, Email
from typing import List, Optional
import uuid
from datetime import datetime

# Inicializar servidor MCP
mcp = FastMCP("Asistente de Oficina")

# Datos simulados en memoria
reuniones_db = []
contactos_db = [
    Contacto(nombre="Juan Pérez", email="juan@empresa.com", telefono="+123456789", departamento="TI"),
    Contacto(nombre="María García", email="maria@empresa.com", telefono="+987654321", departamento="RRHH"),
    Contacto(nombre="Carlos López", email="carlos@empresa.com", telefono="+112233445", departamento="Ventas")
]
emails_enviados = []

# ==========================================================
#                       TOOLS REUNIONES
# ==========================================================

@mcp.tool("agendar_reunion")
def agendar_reunion(
    titulo: str,
    dia: str,
    hora: str,
    invitados: List[str],
    descripcion: Optional[str] = None
) -> Reunion:
    """Agenda una nueva reunión en el calendario."""
    nueva_reunion = Reunion(
        id=str(uuid.uuid4())[:8],
        titulo=titulo,
        dia=dia,
        hora=hora,
        invitados=invitados,
        descripcion=descripcion or "Reunión agendada"
    )
    reuniones_db.append(nueva_reunion)
    return nueva_reunion


@mcp.tool("consultar_reuniones")
def consultar_reuniones() -> List[Reunion]:
    """Consulta todas las reuniones agendadas."""
    return reuniones_db


@mcp.tool("reprogramar_reunion")
def reprogramar_reunion(id_reunion: str, nuevo_dia: str, nueva_hora: str) -> Optional[Reunion]:
    """
    Reprograma la fecha y hora de una reunión existente.
    
    Args:
        id_reunion: ID de la reunión a modificar
        nuevo_dia: Nueva fecha (YYYY-MM-DD)
        nueva_hora: Nueva hora (HH:MM)
    """
    for reunion in reuniones_db:
        if reunion.id == id_reunion:
            reunion.dia = nuevo_dia
            reunion.hora = nueva_hora
            reunion.descripcion = f"Reprogramada para el {nuevo_dia} a las {nueva_hora}"
            return reunion
    return None


@mcp.tool("eliminar_reunion")
def eliminar_reunion(id_reunion: str) -> bool:
    """
    Elimina una reunión existente por ID.
    
    Args:
        id_reunion: ID de la reunión a eliminar
    
    Returns:
        True si se eliminó, False si no se encontró
    """
    global reuniones_db
    original_len = len(reuniones_db)
    reuniones_db = [r for r in reuniones_db if r.id != id_reunion]
    return len(reuniones_db) < original_len


# ==========================================================
#                       TOOLS CONTACTOS
# ==========================================================

@mcp.tool("buscar_contacto")
def buscar_contacto(nombre: str) -> List[Contacto]:
    """
    Busca contactos por nombre parcial o completo.
    
    Args:
        nombre: Texto a buscar (no sensible a mayúsculas)
    
    Returns:
        Lista de contactos coincidentes
    """
    resultados = [
        c for c in contactos_db
        if nombre.lower() in c.nombre.lower()
    ]
    return resultados


@mcp.tool("agregar_contacto")
def agregar_contacto(
    nombre: str,
    email: str,
    telefono: Optional[str] = None,
    departamento: Optional[str] = None
) -> Contacto:
    """Agrega un nuevo contacto."""
    nuevo_contacto = Contacto(
        nombre=nombre,
        email=email,
        telefono=telefono,
        departamento=departamento
    )
    contactos_db.append(nuevo_contacto)
    return nuevo_contacto


@mcp.tool("editar_contacto")
def editar_contacto(nombre_actual: str, nuevo_nombre: Optional[str] = None,
                    nuevo_email: Optional[str] = None,
                    nuevo_telefono: Optional[str] = None,
                    nuevo_departamento: Optional[str] = None) -> Optional[Contacto]:
    """
    Edita los datos de un contacto existente.
    
    Args:
        nombre_actual: Nombre actual del contacto a editar
        nuevo_nombre, nuevo_email, nuevo_telefono, nuevo_departamento: campos opcionales a modificar
    """
    for contacto in contactos_db:
        if contacto.nombre.lower() == nombre_actual.lower():
            if nuevo_nombre:
                contacto.nombre = nuevo_nombre
            if nuevo_email:
                contacto.email = nuevo_email
            if nuevo_telefono:
                contacto.telefono = nuevo_telefono
            if nuevo_departamento:
                contacto.departamento = nuevo_departamento
            return contacto
    return None


@mcp.tool("eliminar_contacto")
def eliminar_contacto(nombre: str) -> bool:
    """
    Elimina un contacto por nombre exacto.
    
    Args:
        nombre: Nombre del contacto a eliminar
    
    Returns:
        True si se eliminó, False si no se encontró
    """
    global contactos_db
    original_len = len(contactos_db)
    contactos_db = [c for c in contactos_db if c.nombre.lower() != nombre.lower()]
    return len(contactos_db) < original_len


# ==========================================================
#                       TOOLS EMAILS
# ==========================================================

@mcp.tool("enviar_email")
def enviar_email(destinatario: str, asunto: str, contenido: str) -> Email:
    """Envía un email simulado."""
    nuevo_email = Email(
        destinatario=destinatario,
        asunto=asunto,
        contenido=contenido,
        fecha_envio=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    emails_enviados.append(nuevo_email)
    return nuevo_email


@mcp.tool("consultar_emails")
def consultar_emails() -> List[Email]:
    """Consulta el historial de emails enviados."""
    return emails_enviados


# ========================Servidor mcp ==================================
if __name__ == "__main__":
    print("Iniciando Servidor MCP - Asistente de Oficina")
    print("Herramientas disponibles:agendar_reunion, consultar_reuniones, reprogramar_reunion, eliminar_reunion, agregar_contacto, buscar_contacto, editar_contacto, eliminar_contacto, enviar_email, consultar_emails")
    print("Servidor ejecutándose en: http://localhost:8000")
    
    mcp.run(transport="sse")
