import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF
import base64
import os
from dotenv import load_dotenv 

# --- 1. SECURE SETUP ---
# NOTE: The key is loaded from the separate, hidden '.env' file.
load_dotenv() 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

if not GOOGLE_API_KEY:
    st.error("ERROR: API Key not found. Please ensure you have run 'pip install python-dotenv' and created a '.env' file with your key.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- 2. THE AI BRAIN (Backend) ---
@st.cache_data(show_spinner=False)
def get_ai_resume(raw_text, style):
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # Correctly formed multi-line prompt for parsing robustness
    prompt = f"""
    You are an expert Resume Engineer.
    Task: Convert this unstructured text into professional JSON data.
    Input: "{raw_text}"
    
    RULES:
    1. Professional Tone: Change simple words (e.g. "fixed") to professional ones (e.g. "Resolved complex faults").
    2. Style Constraint: Ensure the language and tone reflect a {style} style resume. Drastically change the verb usage and tone between the options.
    3. Format: Output strictly valid JSON.
    4. Schema:
    {{
        "name": "String",
        "title": "String",
        "summary": "String",
        "contact": {{
            "email": "String",
            "phone": "String",
            "linkedin": "String (Optional)"
        }},
        "skills": ["String", "String", "String"],
        "education": [
            {{
                "degree": "String",
                "institution": "String",
                "year": "String"
            }}
        ],
        "experience": [
            {{ "company": "String", "role": "String", "details": ["String", "String"] }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        return {"error": str(e)}

# Function to generate the PDF file (WARNING-FREE VERSION - uses modern fpdf2 syntax)
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Name, Title, and Contact
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 8, str(data.get('name', 'Name Not Found')), new_y="NEXT", new_x="LMARGIN") 
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 6, str(data.get('title', 'Title Not Found')), new_y="NEXT", new_x="LMARGIN") 
    
    # Contact Info
    pdf.set_font("Arial", "", 9)
    contact_data = data.get('contact', {})
    pdf.cell(0, 5, f"Email: {contact_data.get('email', 'N/A')} | Phone: {contact_data.get('phone', 'N/A')}", new_y="NEXT", new_x="LMARGIN") 
    if contact_data.get('linkedin'):
        pdf.cell(0, 5, f"LinkedIn: {contact_data.get('linkedin')}", new_y="NEXT", new_x="LMARGIN") 
    pdf.ln(5)

    # 2. Summary
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 5, 'PROFESSIONAL SUMMARY', new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, str(data.get('summary', ''))) 
    
    # 3. Skills
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 5, 'TECHNICAL SKILLS', new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Arial", "", 10)
    skills = " | ".join(data.get('skills', []))
    pdf.multi_cell(0, 5, skills)

    # 4. Experience
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 5, 'EXPERIENCE', new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Arial", "", 10)
    
    for job in data.get('experience', []):
        job_details = job.get('role', '') + " at " + job.get('company', '')
        pdf.cell(0, 5, job_details, new_y="NEXT", new_x="LMARGIN")
        
        if job['details']:
            pdf.multi_cell(0, 5, "- " + job['details'][0])
            
    # 5. Education
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 5, 'EDUCATION', new_y="NEXT", new_x="LMARGIN")
    pdf.set_font("Arial", "", 10)

    for edu in data.get('education', []):
        pdf.multi_cell(0, 5, f"{edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})")

    # Final conversion to standard bytes object for download
    return bytes(pdf.output(dest='S')) 

# --- 3. THE WEBSITE UI (Frontend) ---
st.set_page_config(page_title="ResumeAI", layout="wide")

st.title("🚀 ResumeAI: Messy Notes to Professional CV")
st.caption("Built by Misbah | Powered by Gemini")

# Create two columns (Left for Input, Right for Output)
col1, col2 = st.columns(2)

with col1:
    st.header("1. Input")
    st.info("👇 **Paste your rough details here**")
    
    # Style Selector UI
    resume_style = st.selectbox(
        "Choose Resume Style:",
        ("Corporate", "Creative/Modern", "Technical/Engineering")
    )
    
    user_input = st.text_area("Your messy notes:", height=300, 
        placeholder="Example: My name is Misbah, I work at PTCL as Electronics Engineer. I deal with fiber optics and server maintenance...")
    
    # Button Logic
    if st.button("✨ Transform My CV"):
        if user_input:
            with st.spinner("AI is engineering your resume..."):
                try:
                    st.session_state['cv_data'] = get_ai_resume(user_input, resume_style)
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please write something first!")

with col2:
    st.header("2. Preview")
    
    # Check if data exists in memory
    if 'cv_data' in st.session_state:
        data = st.session_state['cv_data']
        
        # Check for errors from the AI call
        if "error" in data:
             st.error("AI Error: " + data["error"])
        else:
            
            # --- DOWNLOAD BUTTON LOGIC ---
            pdf_bytes = create_pdf(data)
            st.download_button(
                label="Download as PDF 💾",
                data=pdf_bytes,
                file_name=f"ResumeAI_{data.get('name', 'Output')}.pdf",
                mime="application/pdf"
            )
            
            # --- START DISPLAYING PREVIEW (Comprehensive Sections) ---
            
            # 1. Name and Title
            st.markdown(f"# {data.get('name', 'Name')}")
            st.markdown(f"### {data.get('title', 'Title')}")
            st.write("---")
            
            # 2. Contact Information
            st.subheader("Contact Information")
            contact_data = data.get('contact', {})
            if contact_data:
                st.write(f"📧 **Email:** {contact_data.get('email', 'N/A')} | 📞 **Phone:** {contact_data.get('phone', 'N/A')}")
                if contact_data.get('linkedin'):
                    st.write(f"🔗 **LinkedIn:** {contact_data.get('linkedin')}")
            st.write("---")

            # 3. Summary
            st.subheader("Summary")
            st.write(data.get('summary', ''))
            st.write("---")

            # 4. Technical Skills
            st.subheader("Technical Skills")
            st.write(" • ".join(data.get('skills', [])))
            st.write("---")
            
            # 5. Experience
            st.subheader("Experience")
            for job in data.get('experience', []):
                st.markdown(f"**{job['role']}** | *{job['company']}*")
                for task in job['details']:
                    st.markdown(f"- {task}")
                st.write("")
            
            # 6. Education
            st.subheader("Education")
            for edu in data.get('education', []):
                st.markdown(f"**{edu.get('degree', 'N/A')}** from *{edu.get('institution', 'N/A')}* ({edu.get('year', 'N/A')})")
    
    else:
        st.info("Your generated CV will appear here.")