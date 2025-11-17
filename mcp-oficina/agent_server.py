import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
import json
from models import ChatRequest, ChatMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
import json

load_dotenv()
# Configuración
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
AGENT_PORT = int(os.getenv("AGENT_PORT", 8001)) 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_HOST = os.getenv("AGENT_HOST", "127.0.0.1")


# System Prompt para el agente de oficina

SYSTEM_PROMPT = """
Eres un asistente de oficina profesional y eficiente. Ayudas a los empleados con gestiones administrativas usando las herramientas disponibles.

# HERRAMIENTAS DISPONIBLES:

## GESTIÓN DE REUNIONES:
- **agendar_reunion**: Agenda nuevas reuniones
  - Parámetros requeridos: título, fecha, hora
  - Parámetros opcionales: invitados (lista), descripción
  - Formatos de fecha aceptados: 
    * Solo día: "15" (asume mes y año actual)
    * Día y mes: "15/11" (asume año actual) 
    * Fecha completa: "15/11/2024"
    * Formato textual: "15 noviembre", "15 nov"
  - Formato de hora: "HH:MM" (ej: "14:30")

- **consultar_reuniones**: Muestra todas las reuniones agendadas (ordenadas por fecha/hora)
- **reprogramar_reunion**: Cambia fecha/hora de reunión existente (por título)
- **eliminar_reunion**: Elimina reunión existente (por título, case-insensitive si no encuentras el título exacto)

## GESTIÓN DE CONTACTOS:
- **agregar_contacto**: Añade nuevo contacto (nombre y email obligatorios)
- **listar_contactos**: Muestra todos los contactos (ordenados alfabéticamente)
- **buscar_contacto**: Busca contactos por nombre (por nombre exacto o case-insensitive si no encuentras el nombre exacto)
- **editar_contacto**: Modifica información de contacto existente
- **eliminar_contacto**: Elimina contacto (por nombre, case-insensitive si es que no encontras el nombre exacto)

## GESTIÓN DE EMAILS:
- **enviar_email**: Envía email (destinatario, asunto y contenido obligatorios)
- **consultar_emails**: Muestra historial de emails enviados (ordenados por fecha)

# PROTOCOLO DE INTERACCIÓN:

## FLUJO DE TRABAJO:
1. **Identificar necesidad**: Analiza qué quiere hacer el usuario
2. **Recopilar información**: Si faltan datos, pregunta amablemente
3. **Usar herramienta apropiada**: Ejecuta la acción solicitada
4. **Confirmar resultado**: Informa al usuario del resultado

## MANEJO DE FECHAS INTELIGENTE:
- Cuando el usuario diga "mañana", "pasado mañana", "el lunes próximo", etc., calcula la fecha correspondiente
- Para fechas parciales, usa el mes y año actual automáticamente
- Siempre verifica que la fecha no sea en el pasado

## VALIDACIONES AUTOMÁTICAS:
- Emails deben tener formato válido (usuario@dominio.ext)
- Horas deben ser en formato 24h (HH:MM)
- Títulos de reuniones no pueden estar vacíos
- Evita duplicados de contactos por email
- Búsqueda de contactos es insensible a mayúsculas y acentos (ej: "Juan Peres" encuentra "Juan Pérez")

## BÚSQUEDA INTELIGENTE DE CONTACTOS
Cuando el usuario pida buscar, editar o eliminar un contacto y el nombre no coincida exactamente:
1. Realiza una búsqueda case-insensitive.
2. Si aun así no hay coincidencia exacta, busca coincidencias similares por aproximación (similitud de texto, coincidencia parcial o nombres que contengan partes del nombre buscado).
3. Si encuentras uno o varios nombres similares, NO ejecutes la acción directamente. Debes preguntar al usuario: "No encontré una coincidencia exacta, pero encontré estos nombres similares: [lista]. ¿Te referías a alguno de ellos?"
4. Espera la confirmación del usuario antes de usar un nombre sugerido.
5. Si el usuario confirma, ejecuta la herramienta correspondiente con ese contacto.
6. Si el usuario no confirma o no reconoce ninguno, pídele que escriba nuevamente el nombre o lo corrija.


## FORMATOS DE RESPUESTA:
- **Éxito**: "[acción completada]. [detalles]"
- **Error**: "[problema]. [solución sugerida]"
- **Información**: "[datos solicitados]"
- **Confirmación**: "¿Está correcto? [resumen]"

## REGLAS DE COMUNICACIÓN:
1. **Tono**: Profesional pero amigable
2. **Idioma**: Español claro y directo
3. **Proactividad**: Sugiere próximos pasos cuando sea apropiado
4. **Claridad**: Explica lo que vas a hacer antes de hacerlo
5. **Flexibilidad**: Adaptate a diferentes formas de expresar la misma solicitud

# FORMATO DE SALIDA (OBLIGATORIO)
- Todas las respuestas deben ser siempre en TEXTO PLANO.
- No uses Markdown, no uses listas con guiones ni símbolos especiales.
- No uses asteriscos, ni negritas, ni encabezados.
- Responde únicamente con texto corrido y saltos de línea simples cuando haga falta.

## EJEMPLOS DE INTERACCIÓN:
Usuario: "Quiero agendar una reunión para el 15 a las 10:00"
Tú: "Perfecto. ¿Qué título le ponemos a la reunión y quiénes serán los invitados?"

Usuario: "Necesito encontrar el contacto de María"
Tú: "Voy a buscar contactos con 'María' en el nombre..."

Usuario: "Busca a Juan Perez"
Tú: "Voy a buscar contactos con 'Juan Perez' (incluso si los nombres tienen tildes)..."

Usuario: "Enviar un email a Juan"
Tú: "Claro. ¿Cuál es el asunto del email y qué contenido quieres que lleve?"

Recuerda: Eres proactivo, helpful y eficiente. Usa las herramientas disponibles para concretar acciones, no solo para dar información.
"""
# Variables globales
model = None
tools = None
client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    global model, tools, client
    
    print("=" * 50)
    print("Iniciando Agente de Asistencia de Oficina")
    print("=" * 50)
    
    try:
        # Inicializar modelo
        print("Cargando modelo Google Gemini...")
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,  
        )
        
        # Probar conexión
        test_response = await model.ainvoke("Hola")
        print("Modelo cargado correctamente")
        
        # Conectar al servidor MCP
        print(f"Conectando al servidor MCP: {MCP_SERVER_URL}")
        client = MultiServerMCPClient({
            "asistente-oficina": {
                "transport": "sse",
                "url": MCP_SERVER_URL
            }
        })
        
        # Obtener herramientas
        print("Obteniendo herramientas del servidor MCP...")
        tools = await client.get_tools()
        
        
        if not tools:
            raise Exception("No se pudieron cargar las herramientas del servidor MCP")
        
        tool_names = [t.name for t in tools]
        print(f"Herramientas cargadas: {', '.join(tool_names)}")
        print("=" * 50)
        print("gente listo para recibir consultas!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error al inicializar el agente: {e}")
        import traceback
        traceback.print_exc()
        model = None
        tools = None
    
    yield
    
    print("Cerrando agente...")

# Inicializar FastAPI
app = FastAPI(
    title="Agente de Asistencia de Oficina",
    description="Servidor para el agente de asistencia de oficina con MCP",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Endpoint de salud"""
    status = "ready" if model and tools else "not_ready"
    return {
        "status": status,
        "message": "Agente de asistencia de oficina",
        "tools_loaded": len(tools) if tools else 0
    }


@app.get("/contactos")
async def get_contactos():
    tool = next((t for t in tools if t.name == "listar_contactos"), None)
    if not tool:
        raise HTTPException(status_code=500, detail="Tool listar_contactos no encontrada")

    result = await tool.ainvoke({})

    # Si el resultado es una lista: parsear cada elemento
    if isinstance(result, list):
        parsed = []
        for item in result:
            if isinstance(item, str):
                try:
                    parsed.append(json.loads(item))
                except:
                    parsed.append({"raw": item})  # si algún elemento no es JSON
            else:
                parsed.append(item)
        return parsed

    # Si no es lista, lo devuelve como dict si se puede
    if hasattr(result, "dict"):
        return result.dict()
    return result

@app.get("/reuniones")
async def get_reuniones():
    tool = next((t for t in tools if t.name == "consultar_reuniones"), None)
    if not tool:
        raise HTTPException(status_code=500, detail="Tool consultar_reuniones no encontrada")

    result = await tool.ainvoke({})

    if isinstance(result, list):
        parsed = []
        for item in result:
            if isinstance(item, str):
                try:
                    parsed.append(json.loads(item))
                except:
                    parsed.append({"raw": item}) 
            else:
                parsed.append(item)
        return parsed

    if hasattr(result, "dict"):
        return result.dict()
    return result


@app.get("/emails")
async def get_emails():
    tool = next((t for t in tools if t.name == "consultar_emails"), None)
    if not tool:
        raise HTTPException(status_code=500, detail="Tool consultar_emails no encontrada")

    result = await tool.ainvoke({})

    if isinstance(result, list):
        parsed = []
        for item in result:
            if isinstance(item, str):
                try:
                    parsed.append(json.loads(item))
                except:
                    parsed.append({"raw": item})
            else:
                parsed.append(item)
        return parsed

    if hasattr(result, "dict"):
        return result.dict()
    return result



@app.post("/chat")
async def handle_chat(request: ChatRequest):
    """Endpoint principal para chat con el agente"""
    if not model or not tools:
        raise HTTPException(
            status_code=503,
            detail="El agente no está listo. Revisa los logs del servidor."
        )
    
    print(f"\nMensaje recibido: {request.message}")
    
    # Construir historial de mensajes
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    for msg in request.history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "ai":
            messages.append(AIMessage(content=msg.content))
    
    messages.append(HumanMessage(content=request.message))
    
    try:
        # Configurar modelo con herramientas
        model_with_tools = model.bind_tools(tools)

        # Ejecutar agente con máximo de iteraciones
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"Iteración {iteration}")

            # Invocar modelo
            response = await model_with_tools.ainvoke(messages)

            # Verificar si el modelo quiere usar herramientas
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"Ejecutando {len(response.tool_calls)} herramienta(s)")

                # Agregar respuesta del modelo al historial
                messages.append(response)

                # Procesar cada herramienta
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    tool_id = tool_call['id']

                    print(f"  → Ejecutando: {tool_name}")
                    print(f"    Argumentos: {tool_args}")

                    # Buscar la herramienta
                    tool_to_use = next((t for t in tools if t.name == tool_name), None)

                    if tool_to_use:
                        try:
                            # Ejecutar herramienta
                            tool_result = await tool_to_use.ainvoke(tool_args)

                            # Formatear resultado
                            if hasattr(tool_result, 'dict'):
                                result_str = json.dumps(tool_result.dict(), ensure_ascii=False, indent=2)
                            elif isinstance(tool_result, list):
                                result_str = json.dumps([
                                    item.dict() if hasattr(item, 'dict') else item
                                    for item in tool_result
                                ], ensure_ascii=False, indent=2)
                            else:
                                result_str = str(tool_result)

                            print(f"Resultado: {result_str[:200]}...")

                            # Agregar resultado al historial
                            messages.append(
                                ToolMessage(
                                    content=result_str,
                                    tool_call_id=tool_id
                                )
                            )

                        except Exception as e:
                            error_msg = f"Error ejecutando {tool_name}: {str(e)}"
                            print(f"{error_msg}")
                            messages.append(
                                ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_id
                                )
                            )
                    else:
                        error_msg = f"Herramienta {tool_name} no encontrada"
                        print(f"{error_msg}")
                        messages.append(
                            ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_id
                            )
                        )

                # Continuar para procesar resultados
                continue
            else:
                # Respuesta final sin herramientas
                ai_response = response.content

                # Si la respuesta es una lista, conviértela a string
                if isinstance(ai_response, list):
                    ai_response_str = "\n".join(str(item) for item in ai_response)
                else:
                    ai_response_str = str(ai_response)

                if not ai_response_str or ai_response_str.strip() == "":
                    print("Respuesta vacía, reintentando...")
                    continue

                print(f"Respuesta final: {ai_response_str[:150]}...")
                return {"response": ai_response_str}

        # Límite de iteraciones alcanzado
        print("Límite de iteraciones alcanzado")
        return {"response": "No pude completar tu solicitud. ¿Podrías intentarlo de nuevo?"}

    except Exception as e:
        print(f"Error en el agente: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"\nIniciando servidor del agente en: http://localhost:{AGENT_PORT}")
    print(f"Documentación disponible en: http://localhost:{AGENT_PORT}/docs")
    
    uvicorn.run(
        app,
        host=AGENT_HOST,
        port=AGENT_PORT,
        log_level="info"
    )