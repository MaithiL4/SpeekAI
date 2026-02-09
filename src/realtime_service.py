"""
Real-time transcription service using Deepgram
"""
import asyncio
import logging
from deepgram import AsyncDeepgramClient, LiveTranscriptionEvents
from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeTranscriptionService:
    def __init__(self, deepgram_api_key: str):
        self.client = AsyncDeepgramClient(api_key=deepgram_api_key)
        self.dg_connection = None
        self.client_websocket = None

    async def connect_to_deepgram(self):
        try:
            self.dg_connection = self.client.listen.asynclive.v("1")
            
            async def on_open(self, open, **kwargs):
                logger.info(f"Deepgram connection opened.")

            async def on_message(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if len(transcript) > 0:
                    await self.client_websocket.send_text(transcript)

            async def on_error(self, error, **kwargs):
                logger.error(f"Deepgram error: {error}")

            async def on_close(self, close, **kwargs):
                logger.info(f"Deepgram connection closed.")

            self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Close, on_close)

            # Start the connection
            await self.dg_connection.start(
                {
                    "model": Config.DEEPGRAM_MODEL,
                    "language": "en",
                    "smart_format": True,
                    "punctuate": True,
                    "diarize": True
                }
            )

        except Exception as e:
            logger.error(f"Could not connect to Deepgram: {e}")

    async def _client_to_deepgram(self):
        """ Relay audio from client to Deepgram """
        async for data in self.client_websocket.iter_bytes():
            if self.dg_connection:
                await self.dg_connection.send(data)

    async def transcribe(self, websocket):
        """
        Handle the transcription process for a single client WebSocket connection.
        """
        self.client_websocket = websocket
        await self.connect_to_deepgram()
        
        try:
            # Run the audio relay
            await self._client_to_deepgram()
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
        finally:
            if self.dg_connection:
                await self.dg_connection.finish()

async def main():
    # This is a placeholder for testing the service
    # In a real application, this would be part of the FastAPI WebSocket endpoint
    logger.info("Real-time service module")

if __name__ == "__main__":
    asyncio.run(main())
