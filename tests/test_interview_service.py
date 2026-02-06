import pytest
from src.interview_service import InterviewService

@pytest.fixture
def interview_service():
    return InterviewService()

def test_interview_service_init(interview_service):
    assert interview_service.transcription is not None
    assert interview_service.response_gen is not None
