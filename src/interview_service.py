"""
Main interview service that combines transcription + response generation
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.transcription import TranscriptionService
from src.response_generator import ResponseGenerator
from src.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterviewService:
    def __init__(self):
        """Initialize with API keys from config"""
        load_dotenv()
        
        # Validate config
        Config.validate()
        
        self.transcription = TranscriptionService(Config.DEEPGRAM_API_KEY)
        self.response_gen = ResponseGenerator(Config.MISTRAL_API_KEY, model=Config.MISTRAL_MODEL)
        
        logger.info("✓ Interview service initialized")
    
    async def process_audio_file(self, audio_path: str, context: dict = None):
        """
        Process audio file: transcribe + generate response
        """
        import time
        start = time.time()
        
        print("\n" + "="*80)
        print("🎤 PROCESSING INTERVIEW AUDIO")
        print("="*80 + "\n")
        
        # Step 1: Transcribe
        print("Step 1: Transcribing audio...")
        transcript_result = await self.transcription.transcribe_file(audio_path, diarize=True)
        
        if not transcript_result["success"]:
            print(f"❌ Transcription failed: {transcript_result['error']}")
            return transcript_result
        
        if transcript_result.get("diarization_results"):
            formatted_transcript = "\n".join([f"Speaker {d['speaker']}: {d['transcript']}" for d in transcript_result["diarization_results"]])
            raw_transcript = transcript_result["transcript"] # Keep raw for metrics if needed
            print(f"✓ Diarized Transcript: {formatted_transcript[:150]}...")
            print(f"✓ Raw Transcript: {raw_transcript[:150]}...")
        else:
            formatted_transcript = transcript_result["transcript"]
            print(f"✓ Transcript: {formatted_transcript[:150]}...")
        
        print(f"✓ Confidence: {transcript_result['confidence']:.2%}")
        print(f"✓ WER Estimate: {transcript_result['wer_estimate']:.2f}%\n")
        
        # Step 2: Generate Response
        print("Step 2: Generating AI response...")
        response_result = await self.response_gen.generate_interview_response(
            transcript_result["transcript"], context
        )
        
        if not response_result["success"]:
            print(f"❌ Response generation failed: {response_result['error']}")
            return response_result
        
        elapsed = time.time() - start
        
        print("\n" + "="*80)
        print("✅ SUCCESS! INTERVIEW PROCESSED")
        print("="*80)
        print(f"\n📝 CONVERSATION TRANSCRIBED:")
        if transcript_result.get("diarization_results"):
            for entry in transcript_result["diarization_results"]:
                print(f"  Speaker {entry['speaker']}: {entry['transcript']}")
            print(f"\n💡 AI ANALYZED RESPONSE (based on raw transcript):")
            print(f"{transcript_result['transcript']}\n")
        else:
            print(f"{formatted_transcript}\n")
        print(f"💡 SUGGESTED ANSWER:")
        print(f"{response_result['response']}\n")
        print(f"📊 PERFORMANCE:")
        print(f"   • Total Time: {elapsed:.2f} seconds")
        print(f"   • Tokens Used: {response_result['tokens_used']}")
        print(f"   • Transcription Confidence: {transcript_result['confidence']:.2%}")
        print("="*80 + "\n")
        
        return {
            "success": True,
            "transcription": transcript_result, # Keep full result here
            "response": response_result,
            "processing_time": elapsed
        }


async def main():
    """Test the service"""
    try:
        service = InterviewService()
        
        # Test with sample audio
        audio_file = "audio_samples/test_interview.mp3"
        
        if not os.path.exists(audio_file):
            print(f"❌ Audio file not found: {audio_file}")
            print("\nPlease add a test audio file to audio_samples/")
            print("You can record yourself asking an interview question.")
            return
        
        # Process
        result = await service.process_audio_file(audio_file)
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nMake sure your .env file has:")
        print("  DEEPGRAM_API_KEY=your_key")
        print("  OPENAI_API_KEY=your_key")


if __name__ == "__main__":
    asyncio.run(main())