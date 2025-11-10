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

load_dotenv()
# Configuración
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
AGENT_PORT = os.getenv("AGENT_PORT")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# System Prompt para el agente de oficina
SYSTEM_PROMPT = """
Eres un asistente de oficina profesional y eficiente. Ayudas a los empleados con:

GESTIÓN DE REUNIONES:
- Agendar nuevas reuniones con título, fecha, hora e invitados
- Consultar reuniones existentes
- Organizar el calendario

GESTIÓN DE CONTACTOS:
- Buscar contactos por nombre
- Agregar nuevos contactos
- Mantener la lista de contactos actualizada

GESTIÓN DE EMAILS:
- Enviar emails a contactos
- Consultar historial de emails enviados

REGLAS IMPORTANTES:
1. Siempre pregunta los detalles necesarios antes de agendar una reunión
2. Verifica que los emails tengan formato válido
3. Mantén un tono profesional y útil
4. Si no tienes información suficiente, pide clarificación
5. Usa las herramientas disponibles para realizar acciones concretas

Responde en español de manera clara y profesional.
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
                
                if not ai_response or ai_response.strip() == "":
                    print("Respuesta vacía, reintentando...")
                    continue
                
                print(f"Respuesta final: {ai_response[:150]}...")
                return {"response": ai_response}
        
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
        host="127.0.0.1",
        port=AGENT_PORT,
        log_level="info"
    )