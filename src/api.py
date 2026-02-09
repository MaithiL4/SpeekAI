"""
REST API for interview service
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
import time
from pathlib import Path

from .config import Config
from .interview_service import InterviewService
from .realtime_service import RealtimeTranscriptionService

app = FastAPI(
    title="Clarity Interview AI",
    description="AI-powered interview coaching with transcription and response generation",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services globally
service = None
rt_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global service, rt_service
    service = InterviewService()
    rt_service = RealtimeTranscriptionService(Config.DEEPGRAM_API_KEY)
    print("✓ Interview services initialized")


@app.get("/")
def root():
    return {
        "message": "Clarity Interview AI API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "process_interview": "/process-interview",
            "transcribe_ws": "/ws/transcribe"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "running",
        "config": {
            "deepgram_configured": bool(Config.DEEPGRAM_API_KEY),
            "mistral_configured": bool(Config.MISTRAL_API_KEY)
        }
    }

@app.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await rt_service.transcribe(websocket)
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Error in websocket endpoint: {e}")
    finally:
        await websocket.close()


@app.post("/process-interview")
async def process_interview(
    audio: UploadFile = File(...),
    resume: str = Form(None),
    job_description: str = Form(None)
):
    """
    Process interview audio file
    Returns transcription + suggested response
    """
    start_time = time.time()
    
    # Validate file type
    file_extension = Path(audio.filename).suffix.lower()
    if file_extension not in Config.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {Config.ALLOWED_AUDIO_FORMATS}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        contents = await audio.read()
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        # Build context
        context = {}
        if resume:
            context["resume"] = resume
        if job_description:
            context["job_description"] = job_description
        
        # Step 1: Transcribe
        transcription_result = await service.transcription.transcribe_file(tmp_path)
        
        if not transcription_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {transcription_result['error']}"
            )
        
        # Step 2: Generate suggestion
        suggestion_result = await service.response_gen.generate_interview_response(
            transcription_result["transcript"],
            context
        )
        
        if not suggestion_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Response generation failed: {suggestion_result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "transcription": transcription_result,
            "suggestion": suggestion_result,
            "processing_time_seconds": round(processing_time, 2)
        }
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    print("\n🚀 Starting Clarity Interview AI API...")
    print("📍 Access at: http://localhost:8000")
    print("📖 Docs at: http://localhost:8000/docs\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)