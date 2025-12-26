import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS
import io
import feedparser
import os # To check if banner exists

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Zengo Vision", page_icon="👁️", layout="wide")

st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f4f4f9; color: #000000; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #e8f5e9; border-right: 1px solid #c8e6c9; }
    
    /* Text Color Enforcement */
    h1, h2, h3, p, span, div { color: #000000 !important; }
    
    /* Sidebar Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; border-radius: 10px; padding: 5px; }
    
    /* --- NEW BUTTON STYLING (Light Colored Tech Cards) --- */
    .stButton button {
        width: 100%;
        height: auto;
        padding: 15px;
        border: 1px solid #b3e5fc; /* Light Blue Border */
        border-radius: 12px;
        background-color: #e1f5fe; /* Light Blue Background */
        color: #01579b; /* Dark Blue Text */
        text-align: left;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    /* Hover Effect */
    .stButton button:hover {
        border-color: #0288d1;
        background-color: #b3e5fc; /* Darker Blue on Hover */
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. API SETUP ---
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    try:
        import my_settings
        api_key = my_settings.GOOGLE_API_KEY
    except ImportError:
        st.error("⚠️ API Key missing.")
        st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. TECH NEWS FUNCTION ---
@st.cache_data(ttl=3600)
def get_tech_news():
    # Fallback if internet fails
    backup_topics = [
        "Latest AI Models Released", 
        "NVIDIA Stock Updates", 
        "Cybersecurity Threats 2025", 
        "New Smartphone Launches"
    ]
    try:
        # Google News - Technology Section RSS
        url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        
        if feed.entries:
            # Return top 4 headlines
            return [entry.title for entry in feed.entries[:4]]
        else:
            return backup_topics
    except:
        return backup_topics

# --- 4. SIDEBAR CONTROLS ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("Zengo Tools 🛠️")
    tab1, tab2, tab3 = st.tabs(["🎤 Voice", "📷 Image", "⚙️ Settings"])
    
    voice_text = None
    image_data = None
    
    with tab1:
        st.write("### Speak")
        voice_text = speech_to_text(language='en', start_prompt="🔴 Record", stop_prompt="Hz Stop", just_once=True, use_container_width=True)
    with tab2:
        st.write("### Vision")
        uploaded_file = st.file_uploader("Image", type=["jpg", "png"], label_visibility="collapsed")
        if uploaded_file:
            image_data = Image.open(uploaded_file)
            st.image(image_data, caption="Ready", use_container_width=True)
    with tab3:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# --- 5. MAIN INTERFACE (WITH NEW BANNER IMAGE) ---

# Check if the banner image exists before trying to display it
banner_path = "zengo_banner.png"
if os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)
else:
    # Fallback text if you haven't saved the image yet
    st.header("Zengo Vision AI") 

# --- TECH TRENDING SECTION (Only when chat is empty) ---
prompt = None

if len(st.session_state.messages) == 0:
    st.subheader("🚀 Tech Trending Now")
    st.caption("Click a topic to analyze it:")
    
    news_items = get_tech_news()
    
    col1, col2 = st.columns(2)
    for i, news in enumerate(news_items):
        with col1 if i % 2 == 0 else col2:
            # We add an emoji to make it look cool
            if st.button(f"⚡ {news}"):
                prompt = f"Give me a detailed technical summary of this news: {news}"

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio" in message:
             st.audio(message["audio"], format='audio/mp3')

# --- 6. LOGIC ENGINE ---
chat_input_text = st.chat_input("Ask about code, tech, or images...")

if prompt:
    pass 
elif voice_text:
    prompt = voice_text
elif chat_input_text:
    prompt = chat_input_text

if prompt:
    # User Message
    with st.chat_message("user"):
        st.markdown(prompt)
        if image_data: st.image(image_data, width=200)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        try:
            if image_data:
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=[image_data, prompt])
            else:
                chat_context = ""
                for msg in st.session_state.messages:
                    if "audio" not in msg:
                        chat_context += f"{msg['role'].upper()}: {msg['content']}\n"
                chat_context += f"USER: {prompt}\n"
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=chat_context)

            full_response = response.text
            message_placeholder.markdown(full_response)
            
            # Audio (Only if voice was used)
            audio_bytes = None
            if voice_text: 
                try:
                    tts = gTTS(text=full_response, lang='en')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_bytes = audio_fp.getvalue()
                    st.audio(audio_bytes, format='audio/mp3', autoplay=True)
                except: pass

            msg_data = {"role": "assistant", "content": full_response}
            if audio_bytes: msg_data["audio"] = audio_bytes
            st.session_state.messages.append(msg_data)
            
            st.rerun()

        except Exception as e:
            message_placeholder.error(f"Error: {e}")
