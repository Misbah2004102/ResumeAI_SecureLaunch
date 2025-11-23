import streamlit as st
import google.generativeai as genai

# --- PASTE YOUR KEY HERE ---
GOOGLE_API_KEY = "AIzaSyCXUcMhvqReXsQU1FupO8882isHNA4DaCU"
genai.configure(api_key=GOOGLE_API_KEY)

st.title("🕵️ API Model Scanner")

if st.button("Scan for Available Models"):
    try:
        st.write("Ping Google Servers...")
        found = False
        # Ask Google: "What models can I use?"
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.success(f"✅ Found: {m.name}")
                found = True
        
        if not found:
            st.error("Connection successful, but no models listed. Check permissions.")
            
    except Exception as e:
        st.error(f"Error: {e}")