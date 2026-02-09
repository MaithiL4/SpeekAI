"""
Real-time transcription service using Deepgram SDK v5.
"""
import logging
from fastapi import APIRouter, WebSocket
from deepgram import DeepgramClient
from .config import Config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter()

# Initialize Deepgram client
deepgram = DeepgramClient(api_key=Config.DEEPGRAM_API_KEY)

@router.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Create a Deepgram live transcription connection
        dg_socket = await deepgram.listen.asynclive.v("1").start({
            "punctuate": True,
            "interim_results": False,
            "language": "en-US",
            "diarize": True
        })

        async def on_message(self, data, **kwargs):
            transcript = data.get('channel', {}).get('alternatives', [{}])[0].get('transcript', '')
            if len(transcript) > 0:
                await websocket.send_text(transcript)

        dg_socket.registerHandler(dg_socket.event.TRANSCRIPT_RECEIVED, on_message)

        while True:
            data = await websocket.receive_bytes()
            dg_socket.send(data)

    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        await websocket.close()

