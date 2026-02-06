import asyncio
import logging
from typing import Dict, Optional

from mistralai import Mistral
from mistralai.models import UserMessage, SystemMessage

from .config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self, api_key: str, model: str = "mistral-small-latest"):
        """Initialize Mistral client"""
        self.client = Mistral(api_key=api_key)
        self.model = model
        logger.info(f"✓ Mistral client initialized with model: {model}")

    async def generate_interview_response(
        self,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Generate intelligent interview response"""
        try:
            logger.info(f"Generating response for: {question[:50]}...")

            # System prompt
            system_prompt = """You are an expert interview coach helping a candidate
respond to interview questions. Your responses should be:

1. Concise (2-3 sentences max for quick reading)
2. Actionable (give specific talking points)
3. Structured (use STAR method when appropriate)
4. Natural (sound conversational, not robotic)
5. Confident (project competence and enthusiasm)

Provide the candidate with a suggested response they can use."""

            # Add context if provided
            if context:
                system_prompt += f"\n\nContext:\n"
                if context.get("resume"):
                    system_prompt += f"Candidate's background: {context['resume']}\n"
                if context.get("job_description"):
                    system_prompt += f"Job description: {context['job_description']}\n"

            # Call Mistral
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=f"Interview question: {question}")
            ]
            
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.9 # Mistral might not support all parameters, will check if error occurs
            )

            # Extract response
            suggested_answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens # Mistral might have different usage API

            logger.info(f"✓ Response generated. Tokens: {tokens_used}")

            return {
                "success": True,
                "response": suggested_answer,
                "tokens_used": tokens_used,
                "model": self.model,
                "metadata": {
                    "finish_reason": response.choices[0].finish_reason,
                    "response_length": len(suggested_answer)
                }
            }

        except Exception as e:
            logger.error(f"❌ Response generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def test_response_generation():
    """Test the response generator"""
    generator = ResponseGenerator(
        api_key=Config.MISTRAL_API_KEY,
        model="mistral-small-latest" # Using a default Mistral model for testing
    )

    # Test question
    test_question = "Tell me about a time you faced a difficult challenge at work."

    result = await generator.generate_interview_response(test_question)

    if result["success"]:
        print(f"\n✅ SUCCESS!")
        print(f"\nQuestion: {test_question}")
        print(f"\nSuggested Response:\n{result['response']}")
        print(f"\nTokens: {result['tokens_used']}")
    else:
        print(f"\n❌ FAILED: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_response_generation())
