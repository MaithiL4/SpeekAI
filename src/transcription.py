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
    
    async def transcribe_file(self, audio_path: str, diarize: bool = False) -> Dict:
        """Transcribe audio file using Deepgram"""
        try:
            logger.info(f"Transcribing file: {audio_path} with diarization: {diarize}")
            
            # Read audio file
            with open(audio_path, "rb") as audio:
                buffer_data = audio.read()

            # Make API call
            response = await self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model=Config.DEEPGRAM_MODEL,
                smart_format=True,
                punctuate=True,
                language="en",
                diarize=diarize # <-- Add this line
            )
            
            # Extract results
            transcript_text = ""
            confidence = 0.0
            wer_estimate = 0.0
            word_count = 0
            diarization_results = []

            if diarize and response.results.channels and response.results.channels[0].alternatives[0].words:
                alternative = response.results.channels[0].alternatives[0]
                transcript_text = alternative.transcript
                confidence = alternative.confidence
                word_count = len(transcript_text.split())
                wer_estimate = (1 - confidence) * 100

                # Process diarization from words
                current_speaker = None
                speaker_text = ""
                
                # Group words by speaker
                for word in alternative.words:
                    if word.speaker != current_speaker:
                        if current_speaker is not None:
                            diarization_results.append({
                                "speaker": current_speaker,
                                "transcript": speaker_text.strip()
                            })
                        current_speaker = word.speaker
                        speaker_text = ""
                    speaker_text += word.word + " "

                # Add the last speaker's utterance
                if speaker_text:
                    diarization_results.append({
                        "speaker": current_speaker,
                        "transcript": speaker_text.strip()
                    })

                logger.info(f"✓ Diarized transcription complete. Confidence: {confidence:.2%}")

            elif response.results.channels:
                alternative = response.results.channels[0].alternatives[0]
                transcript_text = alternative.transcript
                confidence = alternative.confidence
                word_count = len(transcript_text.split())
                wer_estimate = (1 - confidence) * 100
                logger.info(f"✓ Non-diarized transcription complete. Confidence: {confidence:.2%}")
            
            return {
                "success": True,
                "transcript": transcript_text,
                "confidence": confidence,
                "wer_estimate": wer_estimate,
                "word_count": word_count,
                "metadata": {
                    "model": Config.DEEPGRAM_MODEL,
                    "language": "en",
                },
                "diarization_results": diarization_results if diarize else None
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
