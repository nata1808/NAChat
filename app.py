import streamlit as st
from groq import Groq
from ddgs import DDGS
import PyPDF2
import os
from dotenv import load_dotenv

# ==================================================
# 1. CONFIGURACIÓN DE CLAVE API (GROQ)
# ==================================================
load_dotenv()
api_key = st.secrets["GROQ_API_KEY"]

# Si no usas .env, descomenta la siguiente línea y pon tu clave real:
# api_key = "gsk_tu_clave_aqui"

if not api_key:
    st.error("⚠️ No se encontró la clave API de Groq. Configura tu archivo .env o pon la clave manualmente en el código.")
    st.stop()
else:
    client = Groq(api_key=api_key)

# ==================================================
# 2. CONFIGURACIÓN DE LA PÁGINA
# ==================================================
st.set_page_config(page_title="Mi IA Personal con Groq", page_icon="⚡")
st.title("🤖 NAChat (Versión Demo)")

# ==================================================
# 3. HISTORIAL DEL CHAT
# ==================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==================================================
# 4. FUNCIONES DE BÚSQUEDA WEB (CON ENLACES QUE SIRVEN)
# ==================================================
def buscar_internet(pregunta):
    """Busca en DuckDuckGo y devuelve resultados con enlaces reales.
       Si el usuario pide videos, busca solo en YouTube y filtra enlaces de video."""
    try:
        # Detectar si es una búsqueda de video/YouTube
        es_video = any(p in pregunta.lower() for p in ['video', 'youtube', 'vídeo', 'video de youtube', 'video en youtube', 'dame un video', 'video interesante'])

        # Construir consulta optimizada
        if es_video:
            consulta = f"site:youtube.com {pregunta}"
        else:
            consulta = pregunta

        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=6))  # Pedimos más para filtrar

        if not resultados:
            return "No encontré resultados para esa búsqueda."

        respuesta = f"🔍 **Resultados de búsqueda para:** '{pregunta}'\n\n"
        contador = 0

        for r in resultados:
            titulo = r.get('title', 'Sin título')
            enlace = r.get('href', '#')
            descripcion = r.get('body', 'Sin descripción')

            # Si es búsqueda de video, filtrar solo enlaces de YouTube que parezcan un video
            if es_video:
                if 'youtube.com/watch' in enlace or 'youtu.be/' in enlace:
                    contador += 1
                    respuesta += f"{contador}. **[{titulo}]({enlace})**\n   📎 {enlace}\n   📄 {descripcion}\n\n"
                    if contador == 3:
                        break
            else:
                # Búsqueda normal: mostrar los primeros 3 resultados sin filtrar
                contador += 1
                respuesta += f"{contador}. **[{titulo}]({enlace})**\n   📎 {enlace}\n   📄 {descripcion}\n\n"
                if contador == 3:
                    break

        if es_video and contador == 0:
            return "No encontré videos de YouTube para esa consulta. Intenta con otras palabras."

        return respuesta

    except Exception as e:
        return f"❌ Error en la búsqueda: {str(e)}"

def necesita_buscar(pregunta):
    """Detecta si la pregunta requiere búsqueda en internet (automático)."""
    palabras_clave = ['busca', 'encuentra', 'link', 'enlace', 'video', 'youtube', 'noticia', 'último', 'última', 'reciente', 'googlea', 'búscame', 'dame el enlace', 'buscar']
    return any(palabra in pregunta.lower() for palabra in palabras_clave)

# ==================================================
# 5. FUNCIÓN PARA LEER PDF
# ==================================================
def leer_pdf(archivo):
    texto = ""
    reader = PyPDF2.PdfReader(archivo)
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

# ==================================================
# 6. BARRA LATERAL (documentos, búsqueda manual)
# ==================================================
with st.sidebar:
    st.header("📁 Archivos")
    archivo_subido = st.file_uploader("Sube un archivo .txt o .pdf", type=["txt", "pdf"])
    if "conocimiento_personal" not in st.session_state:
        st.session_state.conocimiento_personal = ""

    if archivo_subido is not None:
        if archivo_subido.type == "application/pdf":
            texto = leer_pdf(archivo_subido)
        else:
            texto = archivo_subido.read().decode("utf-8")
        st.session_state.conocimiento_personal = texto
        st.success(f"✅ Documento cargado: {len(texto)} caracteres")
        st.text_area("Vista previa", texto[:500], height=150)

    st.divider()
    st.header("🌐 Busqueda en internet")
    buscar_manual = st.checkbox("Activar búsqueda web (opcional)", value=False)
    st.caption("La IA también busca automáticamente cuando detecta que lo necesitas.")

# ==================================================
# 7. ENTRADA DEL USUARIO Y PROCESAMIENTO DEL CHAT
# ==================================================
pregunta = st.chat_input("Escribe tu mensaje...")

if pregunta:
    # 7.1 Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # 7.2 Construir contexto (documentos personales + búsqueda web)
    contexto = ""
    if st.session_state.conocimiento_personal:
        contexto += f"INFORMACIÓN PERSONAL DEL USUARIO:\n{st.session_state.conocimiento_personal}\n\n"

    # Activar búsqueda si está marcado manual o automático por palabras clave
    if buscar_manual or necesita_buscar(pregunta):
        with st.spinner("🔎 Buscando en internet..."):
            resultados_web = buscar_internet(pregunta)
            contexto += f"INFORMACIÓN DE INTERNET (resultados actuales con enlaces):\n{resultados_web}\n\n"

    # 7.3 Preparar el mensaje completo para la IA
    prompt_completo = f"{contexto}\nPregunta del usuario: {pregunta}"

    # 7.4 Llamada a Groq (con memoria e identidad del creador)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # System prompt con la identidad del creador (sin olvidar fecha, ciudad, empresa)
        system_prompt = f"""Eres un asistente de IA personalizado llamado "Mi IA Personal". 
Fue creada por **Natanael Ferrer** el día **10 de Junio de 2026** en la ciudad de **Bogotá, Colombia**. 
Tu desarrollador y propietario es Natanael Ferrer, y perteneces a la empresa **Pevaar Software Factory S.A.S**.

Tu misión es ayudar al usuario con respuestas útiles, precisas y amigables. 
Si te preguntan quién te creó, cuándo, dónde o de qué empresa eres, debes responder con esta información exacta.

IMPORTANTE: 
- Cuando en el contexto recibas "INFORMACIÓN DE INTERNET" que contenga enlaces en formato [texto](url), MUESTRA los enlaces tal cual, como enlaces clickeables.
- Si el usuario pide un enlace a un video de YouTube, proporciónalo directamente sin explicaciones paso a paso.
- Usa la información personal del usuario si se proporciona (documentos subidos).
- No inventes datos. Si no sabes algo, dilo claramente."""

        # Construir mensajes con historial completo
        mensajes_para_api = [{"role": "system", "content": system_prompt}]
        # Agregar todos los mensajes anteriores (excepto el último que acabamos de añadir)
        for msg in st.session_state.messages[:-1]:
            mensajes_para_api.append({"role": msg["role"], "content": msg["content"]})
        # Agregar el mensaje actual con el contexto
        mensajes_para_api.append({"role": "user", "content": prompt_completo})

        try:
            modelo = "llama-3.1-8b-instant"   # Puedes cambiarlo a "llama-3.3-70b-versatile"
            stream = client.chat.completions.create(
                model=modelo,
                messages=mensajes_para_api,
                stream=True,
                temperature=0.7,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

            # Guardar respuesta en el historial
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"❌ Error con Groq: {e}")