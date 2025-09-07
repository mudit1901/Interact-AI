# 🤖 InterAct AI – Virtual Interview Assistant  

InterAct AI is a **virtual AI-powered interview system** that conducts professional job interviews through **voice interaction**. It integrates **FastAPI WebSockets**, **Anthropic Claude**, **Deepgram TTS**, and **Whisper ASR** to simulate a realistic interview experience.  

The system allows candidates to **speak naturally**, get **transcribed responses**, and receive **real-time AI interview questions and feedback**.  

---

## 🚀 Features  

- 🎙️ **Voice-based Interview** – Speak directly, no typing needed.  
- 🧠 **AI Interviewer (Claude-powered)** – Asks structured and adaptive interview questions.  
- 📝 **Speech-to-Text (Whisper)** – Converts candidate audio into text.  
- 🔊 **Text-to-Speech (Deepgram TTS)** – Streams AI interviewer’s voice in real-time.  
- 🌐 **WebSocket Communication** – Smooth bi-directional audio & text streaming.  
- 🎨 **Frontend UI** – Simple, clean interface for interview simulation.  

---

## 🏗️ Tech Stack  

### **Backend**  
- [FastAPI](https://fastapi.tiangolo.com/) – WebSocket server  
- [Anthropic Claude](https://docs.anthropic.com/) – AI interviewer logic  
- [OpenAI Whisper (Faster-Whisper)](https://github.com/guillaumekln/faster-whisper) – Speech-to-Text  
- [Deepgram TTS](https://developers.deepgram.com/) – AI voice responses  
- [Ollama (optional)](https://ollama.ai/) – Local model chat integration  

### **Frontend**  
- Vanilla **HTML, CSS, JS**  
- WebSocket-based client for audio & text streaming  

---

## **Installation**   

### 1. Clone Repository  
```bash
git clone https://github.com/mudit1901/Interact-AI.git
cd interact-ai
```


### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
pip install -r requirements.txt
```


### 3. Setup Environment Variables
Create a .env file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
```

### 4. Run Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```



### 5. Open Frontend
```bash
Simply open index.html in your browser.
```

### 🎯 How It Works
```bash
Candidate clicks Start Interview.
Audio stream is captured and sent via WebSocket to FastAPI.
Whisper ASR transcribes candidate’s speech into text.
Claude AI processes transcript & generates next interview question.
Deepgram TTS converts AI response into real-time speech.
Candidate hears the interviewer’s voice and continues conversation.
```
### 🔮 Future Improvements
```bash
Add multi-role interviewers (HR, Technical, Manager).
Support multiple languages.
Add interview summary & scoring report.
Improve frontend UI with React/Next.js.
```

