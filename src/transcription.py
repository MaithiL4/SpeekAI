import asyncio
import os
from deepgram import AsyncDeepgramClient
from typing import Dict, Optional
import logging

from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, api_key: str):
        """Initialize Deepgram client"""
        self.client = AsyncDeepgramClient(api_key=api_key)
        logger.info("✓ Deepgram client initialized")
    
    async def transcribe_file(self, audio_path: str) -> Dict:
        """Transcribe audio file using Deepgram"""
        try:
            logger.info(f"Transcribing file: {audio_path}")
            
            # Read audio file
            with open(audio_path, "rb") as audio:
                buffer_data = audio.read()

            # Make API call
            response = await self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model=Config.DEEPGRAM_MODEL,
                smart_format=True,
                punctuate=True,
                language="en"
            )
            
            # Extract results
            transcript_text = response.results.channels[0].alternatives[0].transcript
            confidence = response.results.channels[0].alternatives[0].confidence
            
            # Calculate WER
            wer_estimate = (1 - confidence) * 100
            
            logger.info(f"✓ Transcription complete. Confidence: {confidence:.2%}")
            logger.info(f"✓ Estimated WER: {wer_estimate:.2f}%")
            
            return {
                "success": True,
                "transcript": transcript_text,
                "confidence": confidence,
                "wer_estimate": wer_estimate,
                "word_count": len(transcript_text.split()),
                "metadata": {
                    "model": Config.DEEPGRAM_MODEL,
                    "language": "en",
                }
            }
            
        except FileNotFoundError:
            logger.error(f"❌ Audio file not found: {audio_path}")
            return {
                "success": False,
                "error": f"Audio file not found: {audio_path}"
            }
        except Exception as e:
            logger.error(f"❌ Transcription failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def test_transcription():
    """Test the transcription service"""
    service = TranscriptionService(api_key=Config.DEEPGRAM_API_KEY)
    print("✓ Transcription service ready (waiting for audio file)")


if __name__ == "__main__":
    asyncio.run(test_transcription())
