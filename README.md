# Clarity Interview AI

This project is a FastAPI-based API that provides AI-powered interview coaching. It can transcribe a user's spoken response to an interview question and then provide a suggested, improved answer.

## Features

-   **Audio Transcription:** Transcribes interview responses from an audio file using Deepgram's Nova-2 model.
-   **AI-Powered Suggestions:** Generates improved interview responses using Mistral AI.
-   **REST API:** Provides a simple and easy-to-use REST API to access the service.

## Project Structure

\`\`\`
mai-interview-ai/
├── requirements.txt
├── audio_samples/
│   └── test_interview.mp3
├── src/
│   ├── api.py                  # FastAPI application
│   ├── interview_service.py    # Core service logic
│   ├── transcription.py        # Deepgram transcription service
│   ├── response_generator.py   # Mistral response generation service
│   └── config.py               # Application configuration
└── ui/
    └── app.py                  # Streamlit frontend application
└── .env.example                # Example environment file
\`\`\`

## Getting Started

### Prerequisites

-   Python 3.10+
-   An active virtual environment is recommended.

### Installation

1.  **Clone the repository:**
    \`\`\`bash
    git clone https://github.com/your-username/mai-interview-ai.git
    cd mai-interview-ai
    \`\`\`

2.  **Install the dependencies:**
    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`

3.  **Set up your environment variables:**

    Create a `.env` file in the root of the project by copying the `.env.example` file:
    \`\`\`bash
    cp .env.example .env
    \`\`\`

    Open the `.env` file and add your API keys for Deepgram and Mistral:
    \`\`\`
    DEEPGRAM_API_KEY="your_deepgram_api_key"
    OPENAI_API_KEY="your_openai_api_key" # Kept for potential future use or if project switches back
    MISTRAL_API_KEY="your_mistral_api_key" 
    \`\`\`

### Running the Application

To run the application, use the following command:
\`\`\`bash
python -m uvicorn src.api:app --reload
\`\`\`

The API will be available at \`http://localhost:8000\`.

### Running the Streamlit UI

To run the Streamlit frontend application, first ensure your FastAPI backend is running (as described in "Running the Application" above).

Then, open a new terminal in the project root (`mai-interview-ai/`) and run:
\`\`\`bash
streamlit run ui/app.py
\`\`\`

The Streamlit application will open in your web browser, typically at `http://localhost:8501`.

## API Usage

### Process Interview Audio

-   **Endpoint:** \`/process-interview\`
-   **Method:** \`POST\`
-   **Content-Type:** \`multipart/form-data\`

**Parameters:**

-   \`audio\`: The audio file to be processed (e.g., \`.mp3\`, \`.wav\`).
-   \`resume\` (optional): The candidate's resume text.
-   \`job_description\` (optional): The job description text.

**Example \`curl\` request:**
\`\`\`bash
curl -X POST "http://localhost:8000/process-interview" \
-H "Content-Type: multipart/form-data" \
-F "audio=@/path/to/your/audio.mp3" \
-F "resume=Experienced software engineer..." \
-F "job_description=We are looking for a senior software engineer..."
\`\`\`

**Example Response:**
\`\`\`json
{
  "success": true,
  "transcription": {
    "success": true,
    "transcript": "your transcribed text here",
    "confidence": 0.99,
    "wer_estimate": 1.00,
    "word_count": 50,
    "metadata": {
      "model": "nova-2",
      "language": "en"
    }
  },
  "suggestion": {
    "success": true,
    "response": "your suggested response here",
    "tokens_used": 150,
    "model": "mistral-small-latest",
    "metadata": {
      "finish_reason": "stop",
      "response_length": 250
    }
  },
  "processing_time_seconds": 5.25
}
\`\`\`

## Development Log

This section summarizes the key steps, issues encountered, and their resolutions during the development process.

### 1. Initial Setup and Configuration

*   Created `.env` file for API keys (Deepgram, OpenAI, Mistral).
*   Created `src/config.py` for centralized configuration management.
*   Updated `src/api.py` and `src/interview_service.py` to utilize the new `Config` class.
*   Setup initial `audio_samples` directory and placed `test_interview.mp3` for testing.
*   Initialized Python virtual environment and installed dependencies from `requirements.txt`.

### 2. Deepgram SDK Integration (Initial Issues & Resolutions)

**Issue 1: `ImportError: cannot import name 'PrerecordedOptions' from 'deepgram'`**
*   **Problem:** The `deepgram-sdk` (v5.3.0) had changed its API. `PrerecordedOptions` and `FileSource` were no longer directly importable from the top-level `deepgram` package.
*   **Resolution:** After extensive investigation and web searching, it was found that `PrerecordedOptions` should be imported directly from `deepgram` and that `FileSource` is not a separate class but an expected dictionary structure.

**Issue 2: `'coroutine' object is not subscriptable` and `was never awaited`**
*   **Problem:** Asynchronous Deepgram API calls were not properly `await`ed.
*   **Resolution:**
    *   Made `InterviewService.process_audio_file` an `async` method.
    *   Added `await` to calls of `self.transcription.transcribe_file` and `self.response_gen.generate_interview_response`.
    *   Made the `main` function `async` and used `asyncio.run(main())` to execute it.
    *   Added `import asyncio` to `src/interview_service.py`.

**Issue 3: `MediaClient.transcribe_file() takes 1 positional argument but 2 positional arguments were given`**
*   **Problem:** The `transcribe_file` method expected the audio buffer as a keyword argument `request=`, not a positional argument.
*   **Resolution:** Modified the call to `transcribe_file` to pass the audio data as `request=buffer_data`.

**Issue 4: `'ListenV1Response' object has no attribute 'to_dict'`**
*   **Problem:** The `ListenV1Response` object returned by Deepgram SDK (v5.3.0) no longer had a `.to_dict()` method for data access.
*   **Resolution:** Updated data extraction to use direct attribute access (e.g., `response.results.channels[0].alternatives[0].transcript` and `response.results.channels[0].alternatives[0].confidence`).

### 3. OpenAI Quota Issue (Non-code related)

*   **Problem:** After resolving all Deepgram and async issues, the application successfully called the OpenAI API but received a `429 Too Many Requests` error, indicating an exceeded quota.
*   **Resolution:** This was identified as an external issue requiring the user to check their OpenAI account for usage and billing details. The code itself was functioning correctly.

### 4. Mistral API Integration

*   **User Request:** Switch from OpenAI to Mistral API for response generation using a free version, with the API key already in `.env`.
*   **Issue 1: `mistralai` installation error (`Invalid requirement`)**
    *   **Problem:** Initial `echo mistralai >> requirements.txt` command introduced hidden characters or encoding issues.
    *   **Resolution:** Overwrote `requirements.txt` with clean text content and reinstalled dependencies.
*   **Issue 2: `MistralAsyncClient` and `ChatMessage` import errors (various `ModuleNotFoundError`s)**
    *   **Problem:** The `mistralai` client had undergone a significant API change between versions (`0.*.*` to `1.*.*`). Web examples and previous attempts were based on an older API.
    *   **Resolution:** Consulted the official Mistral AI client migration guide (`https://github.com/mistralai/client-python/blob/main/MIGRATION.md`).
        *   Updated `src/response_generator.py`:
            *   Changed client class to unified `Mistral` (from `mistralai import Mistral`).
            *   Corrected message class imports to `from mistralai.models import UserMessage, SystemMessage` (after thorough inspection of the installed package).
            *   Adapted the chat method call to `await self.client.chat.complete_async(...)`.
        *   Updated `src/api.py` to reflect `mistral_configured`.
        *   Updated `src/config.py` to define `MISTRAL_MODEL` and validate `MISTRAL_API_KEY`.
        *   Updated `src/interview_service.py` to pass Mistral API keys and model to `ResponseGenerator`.

### 5. Debugging and Resolution during Gemini CLI Interaction

This section details the issues identified and resolved during the interactive session with the Gemini CLI.

**Issue 5.1: `pytest` Installation and Module Not Found Errors**
*   **Problem:** `pytest` was initially not found, leading to command execution failure. Subsequent attempts to run tests resulted in `ModuleNotFoundError: No module named 'src'` because the project root was not correctly in the Python path for `pytest`.
*   **Resolution:** Added `pytest` to `requirements.txt` and ensured tests were run by navigating to the project root (`mai-interview-ai/`) and executing `python -m pytest tests`.

**Issue 5.2: API Test Failures in `tests/test_api.py`**
*   **Problem:** The `test_health_check` and `test_root` functions in `test_api.py` failed due to assertions expecting outdated JSON response structures from the FastAPI endpoints.
*   **Resolution:** Updated the expected JSON responses in `test_api.py` to accurately reflect the current output of the `/health` and `/` FastAPI endpoints.

**Issue 5.3: FastAPI `TypeError: 'coroutine' object is not subscriptable`**
*   **Problem:** When calling the `/process-interview` endpoint, the FastAPI server returned an "Internal Server Error." Logs revealed a `TypeError` because `service.transcription.transcribe_file()` and `service.response_gen.generate_interview_response()` (which are `async` methods) were being called without the `await` keyword in `src/api.py`, leading to coroutine objects being treated as dictionaries.
*   **Resolution:** Added the `await` keyword before both calls in the `process_interview` function within `src/api.py`.

**Issue 5.4: Streamlit UI "Invalid file format" Error**
*   **Problem:** When attempting to upload an audio file via the Streamlit UI, the FastAPI backend rejected it with a "400 Bad Request" and "Invalid file format" error, despite the file being valid and working via direct `curl` requests. This indicated that the Streamlit UI was not correctly sending the file's metadata (filename, MIME type) to FastAPI.
*   **Resolution:** Modified `ui/app.py` to pass the `uploaded_audio.name`, `uploaded_audio.getvalue()`, and `uploaded_audio.type` explicitly as a tuple to the `requests.post` `files` parameter. This ensured FastAPI received the correct file information for validation.

**Overall Outcome:** The application is now fully functional and robust. The FastAPI backend correctly processes audio transcription using Deepgram and generates AI-powered interview response suggestions using Mistral AI. The Streamlit frontend successfully interacts with the backend, allowing users to upload audio and receive feedback.
## Product Roadmap

This outlines the planned development for SpeekAI.

## ✅ Phase 1: MVP (COMPLETE - Feb 6-7)
- [x] Audio transcription (Deepgram)
- [x] AI response generation (Mistral)
- [x] REST API
- [x] Basic web UI

## 🚧 Phase 2: Core Features (In Progress - Feb 8-16)
- [ ] Deploy to Streamlit Cloud (Feb 8)
- [ ] Speaker diarization (Feb 10-11)
- [ ] Real-time recording (Feb 12-13)
- [ ] Session history (Feb 14-15)

## 📋 Phase 3: Advanced Features (Planned - Feb 17-23)
- [ ] Analytics dashboard
- [ ] Mock interview mode
- [ ] STAR method analysis
- [ ] Multi-language support

## 💰 Phase 4: Monetization (Planned - Feb 24 - Mar 2)
- [ ] Public launch (Product Hunt)
- [ ] Payment integration (Razorpay)
- [ ] Pricing tiers
- [ ] First paying customers

## 🎯 Future (Month 2+)
- [ ] Mobile app
- [ ] Video recording
- [ ] Team accounts
- [ ] API marketplace integration

**Last Updated**: Feb 6, 2026