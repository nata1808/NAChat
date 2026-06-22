import streamlit as st
from groq import Groq
from ddgs import DDGS
import PyPDF2
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

load_dotenv()
api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    st.error("⚠️ No se encontró la clave API de Groq.")
    st.stop()
else:
    client = Groq(api_key=api_key)

# Configuración de la página
st.set_page_config(page_title="NAChat AI", page_icon="⚡", layout="wide")

# Tema oscuro/claro (mejora 5)
tema = st.sidebar.radio("🌓 Tema", ["Claro", "Oscuro"], index=0)
if tema == "Oscuro":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("🤖 NAChat AI")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===================== FUNCIONES EXISTENTES =====================
def buscar_internet(pregunta):
    try:
        es_video = any(p in pregunta.lower() for p in ['video', 'youtube', 'vídeo', 'video de youtube', 'video en youtube', 'dame un video', 'video interesante'])
        consulta = f"site:youtube.com {pregunta}" if es_video else pregunta
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=6))
        if not resultados:
            return "No encontré resultados para esa búsqueda."
        respuesta = f"🔍 **Resultados de búsqueda para:** '{pregunta}'\n\n"
        contador = 0
        for r in resultados:
            titulo = r.get('title', 'Sin título')
            enlace = r.get('href', '#')
            descripcion = r.get('body', 'Sin descripción')
            if es_video:
                if 'youtube.com/watch' in enlace or 'youtu.be/' in enlace:
                    contador += 1
                    respuesta += f"{contador}. **[{titulo}]({enlace})**\n   📎 {enlace}\n   📄 {descripcion}\n\n"
                    if contador == 3: break
            else:
                contador += 1
                respuesta += f"{contador}. **[{titulo}]({enlace})**\n   📎 {enlace}\n   📄 {descripcion}\n\n"
                if contador == 3: break
        if es_video and contador == 0:
            return "No encontré videos de YouTube para esa consulta."
        return respuesta
    except Exception as e:
        return f"❌ Error en la búsqueda: {str(e)}"

def necesita_buscar(pregunta):
    palabras_clave = ['busca', 'encuentra', 'link', 'enlace', 'video', 'youtube', 'noticia', 'último', 'última', 'reciente', 'googlea', 'búscame', 'dame el enlace', 'buscar']
    return any(palabra in pregunta.lower() for palabra in palabras_clave)

def leer_pdf(archivo):
    texto = ""
    reader = PyPDF2.PdfReader(archivo)
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

def extraer_texto_url(url):
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:5000]  # Limitar a 5000 caracteres
    except:
        try:
            import requests
            from bs4 import BeautifulSoup
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            texto = soup.get_text()
            return texto[:5000]
        except:
            return None

def obtener_clima(ciudad):
    try:
        url = f"https://wttr.in/{ciudad}?format=%C+%t"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return None
    except:
        return None

# ===================== NUEVAS FUNCIONES DEL NIVEL 1 =====================
def exportar_conversacion():
    return json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)

def importar_conversacion(archivo):
    try:
        contenido = json.loads(archivo.read())
        if isinstance(contenido, list):
            st.session_state.messages = contenido
            return True
        else:
            st.error("El archivo no tiene el formato correcto.")
            return False
    except Exception as e:
        st.error(f"Error al importar: {e}")
        return False

# ===================== BARRA LATERAL =====================
with st.sidebar:
    # Mejora 1: Exportar/Importar
    st.header("💾 Conversación")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Exportar", use_container_width=True):
            json_data = exportar_conversacion()
            st.download_button(
                label="Guardar archivo",
                data=json_data,
                file_name=f"nachat_conversacion_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key="download_btn"
            )
    with col2:
        archivo_cargado = st.file_uploader("📤 Importar", type=["json"], label_visibility="collapsed")
        if archivo_cargado is not None:
            if importar_conversacion(archivo_cargado):
                st.success("✅ Conversación restaurada")
                st.rerun()

    st.divider()

    # Mejora 2: Personalidad ajustable
    st.header("🎛️ Personalidad")
    temperatura = st.slider("Creatividad", 0.0, 1.5, 0.7, 0.1, help="Más alto = más creativo, más bajo = más preciso")
    tono = st.selectbox("Tono", ["Formal", "Casual", "Técnico", "Poético", "Divertido"])
    max_tokens = st.slider("Longitud máxima", 50, 500, 250, 50, help="Número aproximado de palabras en la respuesta")

    st.divider()

    # Sección de archivos original
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

    # Búsqueda web original
    st.header("🌐 Busqueda en internet")
    buscar_manual = st.checkbox("Activar búsqueda web (opcional)", value=False)
    st.caption("La IA también busca automáticamente cuando detecta que lo necesitas.")

# ===================== INPUT DEL USUARIO =====================
pregunta = st.chat_input("Escribe tu mensaje...")

if pregunta:
    # Detectar si es una URL para resumir (mejora 3)
    if pregunta.startswith(('http://', 'https://')):
        with st.spinner("🔍 Leyendo la página web..."):
            texto_url = extraer_texto_url(pregunta)
            if texto_url:
                # Añadir al contexto
                st.session_state.messages.append({"role": "user", "content": pregunta})
                with st.chat_message("user"):
                    st.markdown(pregunta)
                # Responder con el resumen
                prompt_resumen = f"Resume este contenido de forma clara y concisa:\n\n{texto_url[:4000]}"
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    try:
                        stream = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": prompt_resumen}],
                            stream=True,
                            temperature=0.5,
                        )
                        for chunk in stream:
                            if chunk.choices[0].delta.content is not None:
                                full_response += chunk.choices[0].delta.content
                                response_placeholder.markdown(full_response + "▌")
                        response_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        st.error(f"Error al resumir: {e}")
            else:
                st.error("No pude leer el contenido de esa página.")
        st.stop()  # Salir para no procesar como mensaje normal

    # Detectar si es una consulta de clima (mejora 4)
    if "clima" in pregunta.lower() or "temperatura" in pregunta.lower():
        ciudad = pregunta.lower().replace("clima en", "").replace("temperatura en", "").strip()
        if ciudad:
            with st.spinner("🌤️ Consultando el clima..."):
                clima = obtener_clima(ciudad)
                if clima:
                    respuesta_clima = f"🌡️ **Clima en {ciudad.capitalize()}:** {clima}"
                    st.session_state.messages.append({"role": "user", "content": pregunta})
                    with st.chat_message("user"):
                        st.markdown(pregunta)
                    with st.chat_message("assistant"):
                        st.markdown(respuesta_clima)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta_clima})
                else:
                    st.error(f"No pude obtener el clima de '{ciudad}'. Intenta con otra ciudad.")
            st.stop()

    # MODO CHAT NORMAL
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    contexto = ""
    if st.session_state.conocimiento_personal:
        contexto += f"INFORMACIÓN PERSONAL DEL USUARIO:\n{st.session_state.conocimiento_personal}\n\n"

    if buscar_manual or necesita_buscar(pregunta):
        with st.spinner("🔎 Buscando en internet..."):
            resultados_web = buscar_internet(pregunta)
            contexto += f"INFORMACIÓN DE INTERNET (resultados actuales con enlaces):\n{resultados_web}\n\n"

    prompt_completo = f"{contexto}\nPregunta del usuario: {pregunta}"

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        # Construir el sistema prompt con el tono seleccionado (mejora 2)
        tonos = {
            "Formal": "Responde de manera profesional y estructurada, usando un lenguaje formal.",
            "Casual": "Responde como si hablaras con un amigo, usando expresiones coloquiales y cercanas.",
            "Técnico": "Responde con precisión técnica, usando terminología especializada cuando sea necesario.",
            "Poético": "Responde con un lenguaje poético, usando metáforas y un tono inspirador.",
            "Divertido": "Responde con humor, usando juegos de palabras y un tono alegre."
        }

        system_prompt = f"""Eres un asistente de IA personalizado llamado "NAChat AI". 
Fue creada por **Natanael Ferrer** el día **10 de Junio de 2026** en la ciudad de **Bogotá, Colombia**. 
Tu desarrollador y propietario es Natanael Ferrer, y perteneces a la empresa **Pevaar Software Factory S.A.S**.

Tu misión es ayudar al usuario con respuestas útiles, precisas y amigables. 
{tonos.get(tono, "Responde de manera equilibrada y útil.")}

Si te preguntan quién te creó, cuándo, dónde o de qué empresa eres, debes responder con esta información exacta.

IMPORTANTE: 
- Cuando en el contexto recibas "INFORMACIÓN DE INTERNET" que contenga enlaces en formato [texto](url), MUESTRA los enlaces tal cual, como enlaces clickeables.
- Si el usuario pide un enlace a un video de YouTube, proporciónalo directamente sin explicaciones paso a paso.
- Usa la información personal del usuario si se proporciona (documentos subidos).
- No inventes datos. Si no sabes algo, dilo claramente.
- Mantén las respuestas concisas (aproximadamente {max_tokens} palabras)."""

        mensajes_para_api = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages[:-1]:
            mensajes_para_api.append({"role": msg["role"], "content": msg["content"]})
        mensajes_para_api.append({"role": "user", "content": prompt_completo})

        try:
            modelo = "llama-3.1-8b-instant"
            stream = client.chat.completions.create(
                model=modelo,
                messages=mensajes_para_api,
                stream=True,
                temperature=temperatura,
                max_tokens=max_tokens * 2,  # Aproximación a tokens
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"❌ Error con Groq: {e}")
