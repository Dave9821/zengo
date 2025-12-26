import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
import os

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Zengo Vision", page_icon="👁️", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #e8f5e9; color: #202124; }
    section[data-testid="stSidebar"] { background-color: #c8e6c9; color: #000000; }
    h1 { color: #1b5e20; font-weight: bold; }
    .stChatInput { border-color: #2e7d32 !important; }
    .stMarkdown p { color: #202124 !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. API KEY SETUP (Hybrid: Works Locally AND on Cloud) ---
api_key = None

# First, check if we are on Streamlit Cloud
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # If not on Cloud, try local file
    try:
        import my_settings
        api_key = my_settings.GOOGLE_API_KEY
    except ImportError:
        st.error("⚠️ API Key not found! Please set it in my_settings.py or Streamlit Secrets.")
        st.stop()

# Initialize Client
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. SIDEBAR SETTINGS ---
with st.sidebar:
    st.title("👁️ Vision Controls")
    
    st.write("### 🖼️ Add an Image")
    uploaded_file = st.file_uploader("Upload a screenshot or photo:", type=["jpg", "jpeg", "png"])
    image_data = None
    if uploaded_file is not None:
        image_data = Image.open(uploaded_file)
        st.image(image_data, caption="Ready to send", use_container_width=True)
        st.info("👆 Type your question below.")

    st.markdown("---")
    creativity = st.slider("Creativity Level:", 0.0, 2.0, 0.5)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 5. DISPLAY CHAT HISTORY ---
st.title("Zengo Vision 👁️")
st.caption("Powered by Gemini 2.5 Flash-Lite (Cloud Ready)")

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# --- 6. HANDLE INPUT ---
if prompt := st.chat_input("Ask something about the image, or just chat..."):
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if image_data:
             st.image(image_data, use_container_width=True)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            if image_data:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=[image_data, prompt],
                    config=types.GenerateContentConfig(temperature=creativity)
                )
            else:
                chat_context = ""
                for msg in st.session_state.messages:
                    chat_context += f"{msg['role'].upper()}: {msg['content']}\n"
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=chat_context,
                    config=types.GenerateContentConfig(temperature=creativity)
                )
            
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            message_placeholder.error(f"Error: {e}")
