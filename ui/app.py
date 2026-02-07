import streamlit as st
import requests
import json
import os

# Assuming your FastAPI is running on http://localhost:8000
FASTAPI_URL = "http://localhost:8000/process-interview"

st.set_page_config(
    page_title="Clarity Interview AI",
    page_icon="🎙️",
    layout="centered"
)

st.title("🎙️ Clarity Interview AI")
st.markdown("""
Welcome to your AI-powered interview coach! Upload your audio response,
provide your resume and the job description, and get instant feedback.
""")

# --- Input Section ---
st.header("1. Your Interview Response (Audio)")
uploaded_audio = st.file_uploader(
    "Upload your audio file (MP3, WAV, M4A, OGG, FLAC)",
    type=["mp3", "wav", "m4a", "ogg", "flac"]
)

st.header("2. Provide Context (Optional)")
resume_text = st.text_area("Paste your Resume here (optional)", height=200)
job_description_text = st.text_area("Paste the Job Description here (optional)", height=200)

# --- Process Button ---
if st.button("Get AI Feedback", type="primary", use_container_width=True):
    if uploaded_audio is not None:
        with st.spinner("Processing your interview response..."):
            files = {'audio': (uploaded_audio.name, uploaded_audio.getvalue(), uploaded_audio.type)}
            data = {}
            if resume_text:
                data['resume'] = resume_text
            if job_description_text:
                data['job_description'] = job_description_text

            try:
                response = requests.post(FASTAPI_URL, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("Processing Complete!")
                    
                    st.subheader("Transcription")
                    st.write(result['transcription']['transcript'])
                    
                    st.subheader("AI Suggested Response")
                    st.info(result['suggestion']['response'])
                    
                    st.subheader("Performance Metrics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Time", f"{result['processing_time_seconds']:.2f} s")
                    with col2:
                        st.metric("Tokens Used", result['suggestion']['tokens_used'])
                    with col3:
                        st.metric("Confidence", f"{result['transcription']['confidence']:.2%}")
                else:
                    st.error(f"Error from FastAPI: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the FastAPI backend. Please ensure it is running at " + FASTAPI_URL)
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please upload an audio file to get feedback.")

st.markdown("---")
st.caption("Clarity Interview AI - Powered by Deepgram and Mistral AI")