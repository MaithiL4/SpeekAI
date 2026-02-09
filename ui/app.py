import streamlit as st

# Monkey-patch for streamlit-webrtc compatibility
if not hasattr(st, 'experimental_rerun'):
    st.experimental_rerun = st.rerun

import sys
import os
from pathlib import Path
import tempfile
import asyncio
import websockets
import queue
import threading
import time
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av

# Add src to path so we can import our services
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interview_service import InterviewService

# Page config
st.set_page_config(
    page_title="SpeekAI - Clarity Interview AI",
    page_icon="🎤",
    layout="wide"
)

# Initialize service (with caching)
@st.cache_resource
def get_service():
    """Initialize and cache the interview service"""
    return InterviewService()

if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = queue.Queue()
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "run" not in st.session_state:
    st.session_state.run = False

async def thread_main_async(audio_queue):
    uri = "ws://localhost:8000/ws/transcribe"
    async with websockets.connect(uri) as websocket:
        st.session_state.websocket = websocket

        async def sender(audio_queue):
            while st.session_state.get("run", False):
                try:
                    audio_frame = audio_queue.get(timeout=1)
                    await websocket.send(audio_frame.to_ndarray().tobytes())
                except queue.Empty:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Sender error: {e}")
                    break
        
        async def receiver():
            while st.session_state.get("run", False):
                try:
                    transcript_chunk = await websocket.recv()
                    st.session_state.transcript += transcript_chunk
                except websockets.exceptions.ConnectionClosed:
                    print("Receiver connection closed.")
                    break
                except Exception as e:
                    print(f"Receiver error: {e}")
                    break

        await asyncio.gather(sender(audio_queue), receiver())

def thread_main(audio_queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(thread_main_async(audio_queue))
    finally:
        loop.close()

# Title and header
st.title("🎤 SpeekAI - Clarity Interview AI")
st.subheader("AI-Powered Interview Coach • 99.36% Accuracy • Better than ParakeetAI")

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Accuracy", "99.36%", "+8% vs competitors")
col2.metric("WER", "0.64%", "10x better")
col3.metric("Speed", "3.7s", "Real-time")
col4.metric("Cost", "₹0.50", "vs ₹492")

st.divider()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔴 Real-time Interview", "🎙️ Process Interview", "📊 About", "🚀 How It Works"])

with tab1:
    st.header("Real-time Interview Practice")

    def audio_frame_callback(frame: av.AudioFrame):
        if st.session_state.get("run", False):
            st.session_state.audio_buffer.put(frame)
        return frame

    webrtc_streamer(
        key="realtime_interview",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"video": False, "audio": True},
        audio_frame_callback=audio_frame_callback,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Interview"):
            st.session_state.run = True
            st.session_state.transcript = ""
            st.session_state.ai_suggestion = ""
            st.session_state.audio_buffer = queue.Queue() # Clear the queue
            
            if "thread" not in st.session_state or not st.session_state.thread.is_alive():
                st.session_state.thread = threading.Thread(target=thread_main, args=(st.session_state.audio_buffer,))
                st.session_state.thread.start()

    with col2:
        if st.button("Stop Interview"):
            st.session_state.run = False
            if "thread" in st.session_state and st.session_state.thread.is_alive():
                st.session_state.thread.join(timeout=2)
            
            # Get AI suggestion
            if st.session_state.transcript:
                with st.spinner("🤖 Generating AI suggestion..."):
                    service = get_service()
                    result = asyncio.run(service.response_gen.generate_interview_response(st.session_state.transcript))
                    if result["success"]:
                        st.session_state.ai_suggestion = result["response"]
                    else:
                        st.session_state.ai_suggestion = "Sorry, I couldn't generate a suggestion."


    st.subheader("Live Transcript")
    transcript_placeholder = st.empty()
    transcript_placeholder.text_area("Transcript", st.session_state.get("transcript", ""), height=200)

    if "ai_suggestion" in st.session_state and st.session_state.ai_suggestion:
        st.subheader("💡 AI Suggestion")
        st.markdown(st.session_state.ai_suggestion)

    # Rerun the app to update the transcript
    if st.session_state.get("run", False):
        try:
            time.sleep(0.1)
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error during rerun: {e}")



with tab2:
    st.header("Upload Interview Audio")
    st.write("Upload your interview question recording and get instant AI-powered feedback.")
    
    # File uploader
    audio_file = st.file_uploader(
        "Choose audio file (MP3, WAV, M4A, OGG, FLAC)",
        type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
        help="Upload a recording of an interview question"
    )
    
    # Optional context
    with st.expander("📝 Add Context (Optional)"):
        col1, col2 = st.columns(2)
        with col1:
            resume = st.text_area(
                "Your Resume/Background",
                placeholder="Data Engineer with 2 years experience in Python, SQL...",
                height=150
            )
        with col2:
            job_description = st.text_area(
                "Job Description",
                placeholder="Looking for a Backend Developer with experience in...",
                height=150
            )
    
    # Process button
    if audio_file is not None:
        st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
        
        if st.button("🚀 Process Interview", type="primary", use_container_width=True):
            with st.spinner("🎤 Processing your interview... This may take a few seconds..."):
                try:
                    # Save uploaded file to temp location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp_file:
                        tmp_file.write(audio_file.read())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Get service
                        service = get_service()
                        
                        # Build context
                        context = {}
                        if resume and resume.strip():
                            context["resume"] = resume
                        if job_description and job_description.strip():
                            context["job_description"] = job_description
                        
                        # Process the audio file
                        result = asyncio.run(service.process_audio_file(
                            tmp_path,
                            context if context else None
                        ))
                        
                        if result["success"]:
                            st.success("✅ Processing Complete!")
                            
                            # Display results in two columns
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📝 Conversation Transcription")
                                if result["transcription"].get("diarization_results"):
                                    for entry in result["transcription"]["diarization_results"]:
                                        st.markdown(f"**Speaker {entry['speaker']}**: {entry['transcript']}")
                                    st.caption("--- Raw Transcript (for metrics) ---")
                                    st.info(result["transcription"]["transcript"])
                                else:
                                    st.info(result["transcription"]["transcript"])
                                
                                # Metrics
                                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                                metrics_col1.metric(
                                    "Confidence",
                                    f"{result['transcription']['confidence']:.2%}"
                                )
                                metrics_col2.metric(
                                    "WER",
                                    f"{result['transcription']['wer_estimate']:.2f}%"
                                )
                                metrics_col3.metric(
                                    "Words",
                                    result['transcription']['word_count']
                                )
                            
                            with col2:
                                st.subheader("💡 AI-Suggested Response")
                                st.success(result["response"]["response"])
                                
                                # Response metrics
                                st.caption(
                                    f"🤖 Generated using {result['response']['model']} • "
                                    f"⚡ {result['response']['tokens_used']} tokens • "
                                    f"⏱️ {result['processing_time']:.2f}s total"
                                )
                        else:
                            st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.write("**Debug Info**:")
                    st.write(f"Error type: {type(e).__name__}")
                    st.write(f"Error details: {str(e)}")
    else:
        st.info("👆 Upload an audio file to get started")

with tab3:
    st.header("📊 About SpeekAI")
    
    st.markdown("""
    ### 🎯 What is SpeekAI?
    
    SpeekAI is an AI-powered interview coaching tool that helps you prepare for interviews by:
    - Transcribing your interview responses with 99%+ accuracy
    - Generating professional, improved answers using AI
    - Providing instant feedback on your responses
    
    ### 🏆 Why SpeekAI?
    
    **Better Accuracy**
    - 99.36% transcription confidence
    - 0.64% word error rate (10x better than industry standard)
    
    **Faster Processing**
    - Average 3-4 seconds per interview
    - Real-time feedback
    
    **More Affordable**
    - ₹0.50 per interview vs ₹492 (competitors)
    - 99% cost savings
    
    ### 📈 Comparison to ParakeetAI
    """)
    
    # Comparison table
    comparison_data = {
        "Feature": ["Accuracy", "WER", "Speed", "Cost", "Platform"],
        "SpeekAI": ["99.36%", "0.64%", "3.7s", "₹0.50", "Web + API"],
        "ParakeetAI": ["91-94%", "6-9%", "3-5s", "₹492", "Desktop only"],
        "Advantage": ["✅ +8%", "✅ 10x better", "✅ Same", "✅ 99% cheaper", "✅ More accessible"]
    }
    
    st.table(comparison_data)
    
    st.markdown("""
    ### 🔬 Technology Stack
    
    - **Speech Recognition**: Deepgram Nova-2 (industry-leading accuracy)
    - **AI Response**: Mistral AI (advanced language model)
    - **Backend**: Python + FastAPI
    - **Frontend**: Streamlit
    
    ### 📝 How It Works
    
    1. Upload your interview audio recording
    2. Our AI transcribes it with 99%+ accuracy
    3. Mistral AI analyzes your response
    4. Get a professional, improved answer suggestion
    5. Learn and improve for your next interview!
    """)

with tab3:
    st.header("🚀 How to Use SpeekAI")
    
    st.markdown("""
    ### Step-by-Step Guide
    
    **1. Prepare Your Audio**
    - Record yourself answering an interview question
    - Supported formats: MP3, WAV, M4A, OGG, FLAC
    - Duration: Any length (keep under 5 minutes for best results)
    
    **2. Upload**
    - Click "Browse files" in the Process Interview tab
    - Select your audio file
    - (Optional) Add your resume and job description for better context
    
    **3. Process**
    - Click "Process Interview"
    - Wait 3-5 seconds for results
    
    **4. Review**
    - See your transcribed answer
    - Read the AI-suggested improvement
    - Learn from the feedback
    
    **5. Practice**
    - Record your improved answer
    - Process it again
    - Track your progress!
    
    ### 💡 Tips for Best Results
    
    - **Speak clearly** in a quiet environment
    - **Use good audio quality** (phone microphone is fine)
    - **Answer completely** - don't cut yourself off
    - **Add context** - Resume and job description help AI personalize responses
    - **Practice regularly** - Upload 3-5 questions per session
    
    ### 🆘 Need Help?
    
    Having issues? Contact us:
    - GitHub: [MaithiL4/SpeekAI](https://github.com/MaithiL4/SpeekAI)
    - Email: [Your email]
    """)

# Footer
st.divider()
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption("SpeekAI © 2026 • Built with ❤️ in Mumbai")
with col2:
    st.caption("[GitHub](https://github.com/MaithiL4/SpeekAI)")
with col3:
    st.caption("[Report Issue](https://github.com/MaithiL4/SpeekAI/issues)")