"""
Real-time transcription service using Deepgram, with FastAPI APIRouter.
"""
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import AsyncDeepgramClient, LiveTranscriptionEvents
from .config import Config

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter()

class RealtimeTranscriptionService:
    def __init__(self, deepgram_api_key: str):
        self.client = AsyncDeepgramClient(api_key=deepgram_api_key)
        self.dg_connection = None
        self.client_websocket = None
        logger.info("✓ RealtimeTranscriptionService initialized")

    async def connect_to_deepgram(self):
        try:
            self.dg_connection = self.client.listen.asynclive.v("1")
            
            async def on_message(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if len(transcript) > 0 and self.client_websocket:
                    await self.client_websocket.send_text(transcript)

            async def on_error(self, error, **kwargs):
                logger.error(f"Deepgram error: {error}")

            self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)

            await self.dg_connection.start({
                "model": Config.DEEPGRAM_MODEL,
                "language": "en",
                "smart_format": True,
                "punctuate": True,
                "diarize": True
            })
            logger.info("✓ Deepgram connection established")

        except Exception as e:
            logger.error(f"Could not connect to Deepgram: {e}")

    async def transcription_loop(self):
        try:
            while True:
                data = await self.client_websocket.receive_bytes()
                if self.dg_connection:
                    await self.dg_connection.send(data)
        except WebSocketDisconnect:
            logger.info("Client disconnected from WebSocket.")
        except Exception as e:
            logger.error(f"Error in transcription loop: {e}")
        finally:
            if self.dg_connection:
                await self.dg_connection.finish()
                self.dg_connection = None
            logger.info("Transcription loop finished.")

# Instantiate the service
rt_service = RealtimeTranscriptionService(Config.DEEPGRAM_API_KEY)

@router.websocket("/ws/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    rt_service.client_websocket = websocket
    await rt_service.connect_to_deepgram()
    await rt_service.transcription_loop()

