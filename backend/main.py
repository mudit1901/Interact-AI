from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import requests
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from faster_whisper import WhisperModel


load_dotenv()

app = FastAPI()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
whisper_model = WhisperModel("base",device='cpu', compute_type="int8")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

persona = """You are a highly professional AI interviewer named MIRO. Do not introduce yourself or mention your name, as the user has already provided that introduction externally. You are conducting a job interview with no reference to any specific company or individual names.

Your role:
- Begin with a warm, brief opening (without introducing yourself), then ask the first interview question right away.
- Ask one interview question at a time, and guide the conversation naturally based on the user’s responses.
- Keep your questions and reply concise (1–2 sentences), relevant to the role, and focused on assessing skills, experience, and decision-making.
- Include the following predefined questions at appropriate moments (preferably mid-interview, not at the beginning):

1. Describe a situation where you had to navigate conflicting priorities from stakeholders. How did you handle it?
2. If your project is facing technical issues, how would you identify and mitigate the risks? Provide an example.
3. Explain how you ensure alignment between project goals and business objectives. Can you give an example?
4. How do you prioritize tasks when working on multiple projects? What tools or techniques do you use?
5. Imagine your project is experiencing budget overruns. How would you revise the plan, manage expectations, and get it back on track?

Important behavior rules:
- Do NOT answer user questions or allow role reversal.
- If the user talks about unrelated topics (e.g., pets, movies), politely redirect them back to the interview.
- Maintain emotional intelligence, confidence, and full control of the interview.

Begin the interview now with a warm, brief greeting (without self-introduction) followed by your first relevant interview question.
"""


def transcribe_audio(audio_bytes):
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    segments, _ = whisper_model.transcribe(
        tmp_path, beam_size=5, vad_filter=True)
    return " ".join([segment.text for segment in segments])


def chat_with_local_model(history, model="mistral"):
    # Convert to Ollama format
    ollama_messages = [{"role": msg["role"],
                        "content": msg["content"]} for msg in history]

    print("Local Modal is using")

    # Call Ollama API
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": ollama_messages,
            "stream": False
        }
    )

    data = response.json()
    reply = data["message"]["content"]
    return reply


@app.websocket("/ws/interview")
async def interview_ws(websocket: WebSocket):
    await websocket.accept()
    audio_bytes = b""
    history = []

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            # Handle incoming audio bytes
            if "bytes" in message:
                audio_bytes += message["bytes"]

            # Handle __start__ signal to send greeting
            elif "text" in message and message["text"] == "__start__":
                greeting = "Greetings. I’m MIRO, your AI interviewer. I’m here to explore your journey, understand your mindset, and uncover your unique perspective.So Let's start the Interview By Your Introduction "

                # Send text greeting
                await websocket.send_text(f"REPLY::{greeting}")

                # Convert greeting to speech and stream to client
                tts_url = "https://api.deepgram.com/v1/speak?model=aura-orpheus-en"
                headers = {
                    "Authorization": f"Token {deepgram_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"text": greeting}

                print("[TTS] Sending greeting to Deepgram...")
                response = requests.post(
                    tts_url, headers=headers, json=payload, stream=True)

                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        await websocket.send_bytes(chunk)

                await websocket.send_text("__end__")
                print("[GREETING] Greeting sent successfully.\n")
                continue  # Wait for next message

            # Handle __end__ signal to start processing user's audio
            elif "text" in message and message["text"] == "__end__":
                print("\n[DEBUG] Received '__end__'. Starting processing...\n")

                # --- Transcribe ---
                transcript = transcribe_audio(audio_bytes)
                print(f"[TRANSCRIPTION] Transcript: {transcript}\n")

                await websocket.send_text(f"TRANSCRIPT::{transcript}")

                # --- Claude Response ---
                history.append({"role": "user", "content": transcript})
                response = claude_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0.7,
                    system=persona,
                    messages=history
                )
                reply = response.content[0].text
                history.append({"role": "assistant", "content": reply})
                print(f"[CLAUDE REPLY] {reply}\n")

                await websocket.send_text(f"REPLY::{reply}")

                # --- Deepgram TTS ---
                tts_url = "https://api.deepgram.com/v1/speak?model=aura-orpheus-en"
                headers = {
                    "Authorization": f"Token {deepgram_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"text": reply}

                print(f"[TTS] Sending to Deepgram...\n")
                response = requests.post(
                    tts_url, headers=headers, json=payload, stream=True)

                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        await websocket.send_bytes(chunk)

                print(f"[TTS] Audio chunks sent.\n")
                await websocket.send_text("__end__")

                audio_bytes = b""  # Reset buffer

    except WebSocketDisconnect:
        print("Client disconnected.")

# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# import os
# import requests
# from dotenv import load_dotenv
# import openai
# from faster_whisper import WhisperModel

# load_dotenv()

# app = FastAPI()

# # Initialize OpenAI client with the new interface
# openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

# whisper_model = WhisperModel("base", device='cpu', compute_type="int8")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"]
# )

# # Persona that GPT will follow (same as Claude behavior)
# persona = """You are a highly professional AI interviewer named MIRO. Do not introduce yourself or mention your name, as the user has already provided that introduction externally. You are conducting a job interview with no reference to any specific company or individual names.

# Your role:
# - Begin with a warm, brief opening (without introducing yourself), then ask the first interview question right away.
# - Ask one interview question at a time, and guide the conversation naturally based on the user’s responses.
# - Keep your questions and reply concise (1–2 sentences), relevant to the role, and focused on assessing skills, experience, and decision-making.
# - Include the following predefined questions at appropriate moments (preferably mid-interview, not at the beginning):

# 1. Describe a situation where you had to navigate conflicting priorities from stakeholders. How did you handle it?
# 2. If your project is facing technical issues, how would you identify and mitigate the risks? Provide an example.
# 3. Explain how you ensure alignment between project goals and business objectives. Can you give an example?
# 4. How do you prioritize tasks when working on multiple projects? What tools or techniques do you use?
# 5. Imagine your project is experiencing budget overruns. How would you revise the plan, manage expectations, and get it back on track?

# Important behavior rules:
# - Do NOT answer user questions or allow role reversal.
# - If the user talks about unrelated topics (e.g., pets, movies), politely redirect them back to the interview.
# - Maintain emotional intelligence, confidence, and full control of the interview.

# Begin the interview now with a warm, brief greeting (without self-introduction) followed by your first relevant interview question.
# """

# # Function to transcribe audio using Whisper
# def transcribe_audio(audio_bytes):
#     import tempfile

#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
#         tmp.write(audio_bytes)
#         tmp_path = tmp.name

#     segments, _ = whisper_model.transcribe(
#         tmp_path, beam_size=5, vad_filter=True)
#     return " ".join([segment.text for segment in segments])


# @app.websocket("/ws/interview")
# async def interview_ws(websocket: WebSocket):
#     await websocket.accept()
#     audio_bytes = b""
#     history = []

#     try:
#         while True:
#             message = await websocket.receive()

#             if message["type"] == "websocket.disconnect":
#                 break

#             # Handle incoming audio bytes
#             if "bytes" in message:
#                 audio_bytes += message["bytes"]

#             # Handle __start__ signal to send greeting
#             elif "text" in message and message["text"] == "__start__":
#                 greeting = "Greetings. I’m MIRO, your AI interviewer. I’m here to explore your journey, understand your mindset, and uncover your unique perspective. So let's start the interview by your introduction."

#                 await websocket.send_text(f"REPLY::{greeting}")

#                 # Convert greeting to speech using Deepgram
#                 tts_url = "https://api.deepgram.com/v1/speak?model=aura-orpheus-en"
#                 headers = {
#                     "Authorization": f"Token {deepgram_api_key}",
#                     "Content-Type": "application/json"
#                 }
#                 payload = {"text": greeting}

#                 print("[TTS] Sending greeting to Deepgram...")
#                 response = requests.post(
#                     tts_url, headers=headers, json=payload, stream=True)

#                 for chunk in response.iter_content(chunk_size=1024):
#                     if chunk:
#                         await websocket.send_bytes(chunk)

#                 await websocket.send_text("__end__")
#                 print("[GREETING] Greeting sent successfully.\n")
#                 continue

#             # Handle __end__ signal to process user's audio
#             elif "text" in message and message["text"] == "__end__":
#                 print("\n[DEBUG] Received '__end__'. Starting processing...\n")

#                 # --- Transcribe ---
#                 transcript = transcribe_audio(audio_bytes)
#                 print(f"[TRANSCRIPTION] Transcript: {transcript}\n")

#                 await websocket.send_text(f"TRANSCRIPT::{transcript}")

#                 # --- GPT Response ---
#                 history.append({"role": "user", "content": transcript})
#                 messages = [{"role": "system", "content": persona}] + history

#                 try:
#                     response = openai_client.chat.completions.create(
#                         model="gpt-4o",
#                         messages=messages,
#                         max_tokens=1000,
#                         temperature=0.7
#                     )
#                     reply = response.choices[0].message.content
#                 except Exception as e:
#                     reply = "Sorry, I am unable to process your request at the moment."
#                     print("[OpenAI ERROR]", e)

#                 history.append({"role": "assistant", "content": reply})
#                 print(f"[GPT REPLY] {reply}\n")

#                 await websocket.send_text(f"REPLY::{reply}")

#                 # --- Deepgram TTS ---
#                 tts_url = "https://api.deepgram.com/v1/speak?model=aura-orpheus-en"
#                 headers = {
#                     "Authorization": f"Token {deepgram_api_key}",
#                     "Content-Type": "application/json"
#                 }
#                 payload = {"text": reply}

#                 print(f"[TTS] Sending to Deepgram...\n")
#                 response = requests.post(
#                     tts_url, headers=headers, json=payload, stream=True)

#                 for chunk in response.iter_content(chunk_size=1024):
#                     if chunk:
#                         await websocket.send_bytes(chunk)

#                 print(f"[TTS] Audio chunks sent.\n")
#                 await websocket.send_text("__end__")

#                 audio_bytes = b""  # Reset buffer

#     except WebSocketDisconnect:
#         print("Client disconnected.")
