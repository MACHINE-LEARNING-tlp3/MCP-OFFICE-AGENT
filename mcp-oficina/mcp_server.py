from mcp.server.fastmcp import FastMCP
from models import Reunion, Contacto, Email
from typing import List, Optional
import uuid
from datetime import datetime, date
import re
import unicodedata

# Inicializar servidor MCP
mcp = FastMCP("Asistente de Oficina")

# Datos simulados en memoria
reuniones_db = [
    Reunion(
        id="1234",
        titulo="Reunión sobre Mantenimiento",
        dia="15/11/2023",
        hora="10:00",
        invitados=["Juan Pérez", "María García", "Carlos López"],
        descripcion="Reunión para discutir el plan de mantenimiento anual."
    ),
    Reunion(
        id="54321",
        titulo="Reunión sobre Nuevas funcionalidades",
        dia="15/11/2023",
        hora="11:00",
        invitados=["Juan Pérez", "María García", "Carlos López"],
        descripcion="Reunión para discutir las nuevas funcionalidades."
    )
]

contactos_db = [
    Contacto(nombre="Juan Pérez", email="juan@gmail.com", telefono="+123456789", departamento="TI"),
    Contacto(nombre="María García", email="maria@gmail.com", telefono="+987654321", departamento="RRHH"),
    Contacto(nombre="Carlos López", email="carlos@gmail.com", telefono="+112233445", departamento="Ventas")
]

emails_enviados = [
    Email(
        destinatario="tatiana@gmail.com",
        asunto="Charla sobre la importancia de la seguridad en la industria",
        contenido="La seguridad es esencial en la industria, y es importante que todos los empleados se sientan seguros en sus acciones y decisiones.",
        fecha_envio="2023-11-15 10:00:00"
    ),
    Email(
        destinatario="ailin@gmail.com",
        asunto="Reunión sobre ciberseguridad",
        contenido="Hay que hablar sobre las vulnerabilidades recientemente descubiertas.",
        fecha_envio="2023-11-15 10:00:00"
    )
]

# ==========================================================
#                       FUNCIONES AUXILIARES
# ==========================================================

def validar_email(email: str) -> bool:
    """Valida formato básico de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))

def validar_fecha(fecha_str: str) -> bool:
    """Valida formato de fecha DD/MM/AAAA"""
    try:
        datetime.strptime(fecha_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def validar_hora(hora_str: str) -> bool:
    """Valida formato de hora HH:MM"""
    try:
        datetime.strptime(hora_str, '%H:%M')
        return True
    except ValueError:
        return False

def es_fecha_pasada(fecha_str: str, hora_str: str) -> bool:
    """Verifica si la fecha y hora están en el pasado"""
    try:
        fecha_reunion = datetime.strptime(f"{fecha_str} {hora_str}", '%d/%m/%Y %H:%M')
        return fecha_reunion < datetime.now()
    except ValueError:
        # Si no puede parsear, asumir que no es pasada para permitir la validación posterior
        return False

def formatear_fecha(dia: str) -> str:
    """Convierte diferentes formatos de fecha a DD/MM/AAAA"""
    hoy = datetime.now()
    
    # Limpiar y normalizar el input
    dia = dia.strip().replace('-', '/').replace('.', '/')
    
    # Caso 1: Solo un número (día del mes actual)
    if dia.isdigit():
        dia_num = int(dia)
        if 1 <= dia_num <= 31:
            return f"{dia_num:02d}/{hoy.month:02d}/{hoy.year}"
        else:
            return dia  # Devolver original para que falle la validación después
    
    # Caso 2: Formato DD/MM
    if "/" in dia:
        partes = dia.split("/")
        
        # DD/MM
        if len(partes) == 2:
            try:
                dia_num = int(partes[0])
                mes_num = int(partes[1])
                if 1 <= dia_num <= 31 and 1 <= mes_num <= 12:
                    return f"{dia_num:02d}/{mes_num:02d}/{hoy.year}"
            except (ValueError, IndexError):
                pass
        
        # DD/MM/AAAA o DD/MM/AA
        elif len(partes) == 3:
            try:
                dia_num = int(partes[0])
                mes_num = int(partes[1])
                año_num = int(partes[2])
                
                # Si el año tiene 2 dígitos, convertirlo a 4
                if año_num < 100:
                    año_num += 2000 if año_num < 50 else 1900
                
                if 1 <= dia_num <= 31 and 1 <= mes_num <= 12 and 1900 <= año_num <= 2100:
                    return f"{dia_num:02d}/{mes_num:02d}/{año_num}"
            except (ValueError, IndexError):
                pass
    
    # Caso 3: Formato con palabras (ej: "15 noviembre", "15 nov")
    palabras_meses = {
        'enero': 1, 'ene': 1, 'jan': 1,
        'febrero': 2, 'feb': 2, 'feb': 2,
        'marzo': 3, 'mar': 3, 'mar': 3,
        'abril': 4, 'abr': 4, 'apr': 4,
        'mayo': 5, 'may': 5, 'may': 5,
        'junio': 6, 'jun': 6, 'jun': 6,
        'julio': 7, 'jul': 7, 'jul': 7,
        'agosto': 8, 'ago': 8, 'aug': 8,
        'septiembre': 9, 'sep': 9, 'sep': 9,
        'octubre': 10, 'oct': 10, 'oct': 10,
        'noviembre': 11, 'nov': 11, 'nov': 11,
        'diciembre': 12, 'dic': 12, 'dec': 12
    }
    
    # Buscar patrones como "15 noviembre" o "15 nov"
    partes = dia.lower().split()
    if len(partes) == 2:
        try:
            dia_num = int(partes[0])
            mes_str = partes[1]
            
            if mes_str in palabras_meses and 1 <= dia_num <= 31:
                mes_num = palabras_meses[mes_str]
                return f"{dia_num:02d}/{mes_num:02d}/{hoy.year}"
        except (ValueError, IndexError):
            pass
    
    # Si no coincide con ningún formato, devolver original para validación
    return dia
# ==========================================================
#                       TOOLS REUNIONES
# ==========================================================

@mcp.tool("agendar_reunion")
def agendar_reunion(
    titulo: str,
    dia: str,
    hora: str,
    invitados: Optional[List[str]] = None,
    descripcion: Optional[str] = None
) -> dict:
    """
    Agenda una nueva reunión con validaciones.
    
    Args:
        titulo: Título de la reunión (obligatorio)
        dia: Fecha en formato DD, DD/MM, DD/MM/AAAA, "15 noviembre", etc.
        hora: Hora en formato HH:MM
        invitados: Lista opcional de nombres de invitados
        descripcion: Descripción opcional de la reunión
    
    Returns:
        Dict con resultado de la operación
    """
    try:
        # Validaciones
        if not titulo or not titulo.strip():
            return {"error": "El título de la reunión es obligatorio"}
        
        if not hora or not validar_hora(hora):
            return {"error": "Formato de hora inválido. Use HH:MM"}
        
        # Formatear fecha
        dia_original = dia
        dia_formateado = formatear_fecha(dia)
        
        if not validar_fecha(dia_formateado):
            return {
                "error": f"Formato de fecha inválido: '{dia_original}'. Use: DD, DD/MM, DD/MM/AAAA, o '15 noviembre'",
                "ejemplos_validos": ["15", "15/11", "15/11/2024", "15 noviembre", "15 nov"]
            }
        
        # Verificar que no sea en el pasado
        if es_fecha_pasada(dia_formateado, hora):
            return {
                "error": f"No se pueden agendar reuniones en el pasado: {dia_formateado} {hora}",
                "fecha_intentada": f"{dia_formateado} {hora}"
            }
        
        # Crear reunión
        nueva_reunion = Reunion(
            id=str(uuid.uuid4())[:8],
            titulo=titulo.strip(),
            dia=dia_formateado,
            hora=hora,
            invitados=invitados or [],
            descripcion=descripcion or f"Reunión '{titulo}' agendada automáticamente"
        )
        
        reuniones_db.append(nueva_reunion)
        
        return {
            "success": True,
            "mensaje": f"Reunión '{titulo}' agendada exitosamente para el {dia_formateado} a las {hora}",
            "reunion": nueva_reunion.dict(),
            "id": nueva_reunion.id,
            "fecha_original": dia_original,
            "fecha_formateada": dia_formateado
        }
        
    except Exception as e:
        return {"error": f"Error al agendar reunión: {str(e)}"}

@mcp.tool("consultar_reuniones")
def consultar_reuniones() -> List[Reunion]:
    """Consulta todas las reuniones agendadas ordenadas por fecha y hora."""
    # Ordenar reuniones por fecha y hora
    reuniones_ordenadas = sorted(
        reuniones_db,
        key=lambda r: datetime.strptime(f"{r.dia} {r.hora}", '%d/%m/%Y %H:%M')
    )
    return reuniones_ordenadas

@mcp.tool("reprogramar_reunion")
def reprogramar_reunion(titulo: str, nuevo_dia: str, nueva_hora: str) -> dict:
    """
    Reprograma una reunión existente por título.
    
    Args:
        titulo: Título de la reunión a reprogramar
        nuevo_dia: Nueva fecha (DD/MM/AAAA)
        nueva_hora: Nueva hora (HH:MM)
    
    Returns:
        Dict con resultado de la operación
    """
    try:
        # Validaciones
        if not validar_hora(nueva_hora):
            return {"error": "Formato de hora inválido. Use HH:MM"}
        
        nuevo_dia_formateado = formatear_fecha(nuevo_dia)
        if not validar_fecha(nuevo_dia_formateado):
            return {"error": "Formato de fecha inválido. Use DD/MM/AAAA"}
        
        if es_fecha_pasada(nuevo_dia_formateado, nueva_hora):
            return {"error": "No se puede reprogramar una reunión al pasado"}
        
        # Buscar reunión
        reunion_encontrada = None
        for reunion in reuniones_db:
            if reunion.titulo.lower() == titulo.lower():
                reunion_encontrada = reunion
                break
        
        if not reunion_encontrada:
            return {"error": f"No se encontró ninguna reunión con título: {titulo}"}
        
        # Actualizar reunión
        reunion_encontrada.dia = nuevo_dia_formateado
        reunion_encontrada.hora = nueva_hora
        reunion_encontrada.descripcion = f"Reprogramada para el {nuevo_dia_formateado} a las {nueva_hora}"
        
        return {
            "success": True,
            "mensaje": f"Reunión '{titulo}' reprogramada exitosamente",
            "reunion": reunion_encontrada.dict()
        }
        
    except Exception as e:
        return {"error": f"Error al reprogramar reunión: {str(e)}"}

@mcp.tool("eliminar_reunion")
def eliminar_reunion(titulo: str) -> dict:
    """
    Elimina una reunión existente por título (busqueda parcial case-insensitive).
    
    Args:
        titulo: Título de la reunión a eliminar
    
    Returns:
        Dict con resultado de la operación
    """
    global reuniones_db
    
    reunion_encontrada = None
    for reunion in reuniones_db:
        if reunion.titulo.lower() == titulo.lower():
            reunion_encontrada = reunion
            break
    
    if not reunion_encontrada:
        return {"error": f"No se encontró ninguna reunión con título: {titulo}"}
    
    reuniones_db = [r for r in reuniones_db if r.titulo.lower() != titulo.lower()]
    
    return {
        "success": True,
        "mensaje": f"Reunión '{titulo}' eliminada exitosamente",
        "reunion_eliminada": reunion_encontrada.dict()
    }

# ==========================================================
#                       TOOLS CONTACTOS
# ==========================================================


@mcp.tool("listar_contactos")
def listar_contactos() -> List[Contacto]:
    """Lista todos los contactos almacenados ordenados alfabéticamente."""
    return sorted(contactos_db, key=lambda c: c.nombre)


def normalizar_texto(texto: str) -> str:
    """Elimina acentos/diacríticos y convierte a minúsculas para búsqueda flexible."""
    # Normaliza Unicode (NFD descompone 'é' → 'e' + '´')
    texto_normalizado = unicodedata.normalize('NFD', texto)
    # Elimina marcas diacríticas (acentos, tildes, etc.)
    texto_sin_acentos = ''.join(c for c in texto_normalizado if not unicodedata.combining(c))
    # Convierte a minúsculas y elimina espacios extra
    return texto_sin_acentos.lower().strip()

@mcp.tool("buscar_contacto")
def buscar_contacto(nombre: str) -> List[Contacto]:
    """
    Busca contactos por nombre (búsqueda parcial, insensible a mayúsculas y acentos).
    Ej: 'Juan Perez' encontrará 'Juan Pérez', 'JUAN PEREZ', etc.
    Args:
        nombre: Texto a buscar en los nombres
    
    Returns:
        Lista de contactos coincidentes
    """
    if not nombre or not nombre.strip():
        return []
    
    busqueda_normalizada = normalizar_texto(nombre)
    resultados = [
        c for c in contactos_db
        if busqueda_normalizada in normalizar_texto(c.nombre)
    ]
    
    return resultados

@mcp.tool("agregar_contacto")
def agregar_contacto(
    nombre: str,
    email: str,
    telefono: Optional[str] = None,
    departamento: Optional[str] = None
) -> dict:
    """Agrega un nuevo contacto con validaciones."""
    try:
        # Validaciones
        if not nombre or not nombre.strip():
            return {"error": "El nombre del contacto es obligatorio"}
        
        if not email or not email.strip():
            return {"error": "El email del contacto es obligatorio"}
        
        if not validar_email(email):
            return {"error": "Formato de email inválido"}
        
        # Verificar si el contacto ya existe
        contacto_existente = next(
            (c for c in contactos_db if c.email.lower() == email.lower()), 
            None
        )
        if contacto_existente:
            return {"error": f"Ya existe un contacto con el email: {email}"}
        
        # Crear contacto
        nuevo_contacto = Contacto(
            nombre=nombre.strip(),
            email=email.strip(),
            telefono=telefono.strip() if telefono else None,
            departamento=departamento.strip() if departamento else None
        )
        
        contactos_db.append(nuevo_contacto)
        
        return {
            "success": True,
            "mensaje": f"Contacto '{nombre}' agregado exitosamente",
            "contacto": nuevo_contacto.dict()
        }
        
    except Exception as e:
        return {"error": f"Error al agregar contacto: {str(e)}"}

@mcp.tool("editar_contacto")
def editar_contacto(
    nombre_actual: str, 
    nuevo_nombre: Optional[str] = None,
    nuevo_email: Optional[str] = None,
    nuevo_telefono: Optional[str] = None,
    nuevo_departamento: Optional[str] = None
) -> dict:
    """
    Edita los datos de un contacto existente.
    
    Args:
        nombre_actual: Nombre actual del contacto a editar
        nuevo_nombre, nuevo_email, nuevo_telefono, nuevo_departamento: campos opcionales a modificar
    """
    try:
        # Buscar contacto
        contacto_encontrado = None
        for contacto in contactos_db:
            if contacto.nombre.lower() == nombre_actual.lower():
                contacto_encontrado = contacto
                break
        
        if not contacto_encontrado:
            return {"error": f"No se encontró el contacto: {nombre_actual}"}
        
        # Validar nuevo email si se proporciona
        if nuevo_email and not validar_email(nuevo_email):
            return {"error": "Formato de email inválido"}
        
        # Verificar duplicado de email
        if nuevo_email:
            email_duplicado = next(
                (c for c in contactos_db 
                 if c.email.lower() == nuevo_email.lower() 
                 and c.nombre.lower() != nombre_actual.lower()), 
                None
            )
            if email_duplicado:
                return {"error": f"Ya existe otro contacto con el email: {nuevo_email}"}
        
        # Aplicar cambios
        cambios = []
        if nuevo_nombre and nuevo_nombre.strip():
            contacto_encontrado.nombre = nuevo_nombre.strip()
            cambios.append("nombre")
        
        if nuevo_email and nuevo_email.strip():
            contacto_encontrado.email = nuevo_email.strip()
            cambios.append("email")
        
        if nuevo_telefono is not None:
            contacto_encontrado.telefono = nuevo_telefono.strip() if nuevo_telefono else None
            cambios.append("teléfono")
        
        if nuevo_departamento is not None:
            contacto_encontrado.departamento = nuevo_departamento.strip() if nuevo_departamento else None
            cambios.append("departamento")
        
        if not cambios:
            return {"error": "No se proporcionaron campos para actualizar"}
        
        return {
            "success": True,
            "mensaje": f"Contacto actualizado exitosamente. Campos modificados: {', '.join(cambios)}",
            "contacto": contacto_encontrado.dict()
        }
        
    except Exception as e:
        return {"error": f"Error al editar contacto: {str(e)}"}

@mcp.tool("eliminar_contacto")
def eliminar_contacto(nombre: str) -> dict:
    """
    Elimina un contacto por nombre exacto.
    
    Args:
        nombre: Nombre del contacto a eliminar
    
    Returns:
        Dict con resultado de la operación
    """
    global contactos_db
    
    contacto_encontrado = None
    for contacto in contactos_db:
        if contacto.nombre.lower() == nombre.lower():
            contacto_encontrado = contacto
            break
    
    if not contacto_encontrado:
        return {"error": f"No se encontró el contacto: {nombre}"}
    
    contactos_db = [c for c in contactos_db if c.nombre.lower() != nombre.lower()]
    
    return {
        "success": True,
        "mensaje": f"Contacto '{nombre}' eliminado exitosamente",
        "contacto_eliminado": contacto_encontrado.dict()
    }

# ==========================================================
#                       TOOLS EMAILS
# ==========================================================

@mcp.tool("enviar_email")
def enviar_email(destinatario: str, asunto: str, contenido: str) -> dict:
    """Envía un email simulado con validaciones."""
    try:
        # Validaciones
        if not destinatario or not destinatario.strip():
            return {"error": "El destinatario es obligatorio"}
        
        if not validar_email(destinatario):
            return {"error": "Formato de email del destinatario inválido"}
        
        if not asunto or not asunto.strip():
            return {"error": "El asunto del email es obligatorio"}
        
        if not contenido or not contenido.strip():
            return {"error": "El contenido del email es obligatorio"}
        
        # Crear email
        nuevo_email = Email(
            destinatario=destinatario.strip(),
            asunto=asunto.strip(),
            contenido=contenido.strip(),
            fecha_envio=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        emails_enviados.append(nuevo_email)
        
        return {
            "success": True,
            "mensaje": f"Email enviado exitosamente a {destinatario}",
            "email": nuevo_email.dict()
        }
        
    except Exception as e:
        return {"error": f"Error al enviar email: {str(e)}"}

@mcp.tool("consultar_emails")
def consultar_emails() -> List[Email]:
    """Consulta el historial de emails enviados ordenados por fecha."""
    return sorted(
        emails_enviados,
        key=lambda e: e.fecha_envio,
        reverse=True
    )

# ========================Servidor mcp ==================================
if __name__ == "__main__":
    print("Iniciando Servidor MCP - Asistente de Oficina")
    print("Herramientas disponibles: agendar_reunion, consultar_reuniones, reprogramar_reunion, eliminar_reunion, agregar_contacto, listar_contactos, buscar_contacto, editar_contacto, eliminar_contacto, enviar_email, consultar_emails")
    print("Servidor ejecutándose en: http://localhost:8000")
    
    mcp.run(transport="sse")