# Next-Gen AI Assistant

A sophisticated AI-powered personal assistant inspired by JARVIS, featuring voice interaction, face authentication, automation capabilities, and a modern web interface.

## 🚀 Features

- **Voice Interaction**: Wake word detection ("Next Gen"), speech-to-text (Groq Whisper), and text-to-speech (pyttsx3)
- **Face Authentication**: Secure login using DeepFace and OpenCV
- **AI Conversations**: Dual-model Groq integration for commands and complex queries
- **Automation**: Windows automation, YouTube controls, web browsing, and more
- **Real-time WebSocket Communication**: Seamless frontend-backend sync
- **Session Management**: Persistent chat sessions with tabbed interface
- **Modern UI**: Next.js frontend with Bootstrap styling and animated components

## 🏗️ Architecture

- **Backend**: FastAPI with WebSocket support, SQLAlchemy database, background threads for hotword detection
- **Frontend**: Next.js with TypeScript, React components, Bootstrap UI
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: Groq API for LLM and speech processing
- **Automation**: PyAutoGUI, PyGetWindow for desktop control

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- Git

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd Next-GEN_AI
   ```

2. **Set up Python environment**:

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**:

   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure environment**:
   - Set `GROQ_API_KEY` in your environment or config
   - Train face recognition model if needed (see face auth setup)

## 🚀 Running the Application

Simply run:

```bash
python run.py
```

This will:

- Start the FastAPI backend on port 8000
- Start the Next.js frontend on port 3000
- Open your browser to the application

## 📁 Project Structure

```
Next-GEN_AI/
├── backend/                 # FastAPI backend
│   ├── api/                # REST API endpoints
│   ├── db/                 # Database models and setup
│   └── engine/             # Core AI and automation logic
├── frontend/               # Next.js frontend
│   ├── components/         # React components
│   ├── hooks/             # Custom React hooks
│   ├── pages/             # Next.js pages
│   └── styles/            # CSS styles
├── docs/                   # Documentation and specs
├── tests/                  # Unit tests
├── run.py                  # Application launcher
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

Key settings in `backend/engine/config.py`:

- GROQ_API_KEY: Your Groq API key
- Model configurations for different AI tasks
- Assistant name and wake word settings

## 🧪 Testing

Run tests with:

```bash
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by JARVIS from Iron Man
- Built with Groq, FastAPI, Next.js, and various open-source libraries

# Create virtual environment

python -m venv venv

# Activate environment

# Windows

venv\Scripts\activate

# Install dependencies

pip install -r requirements.txt

# Run application

streamlit run app.py

```

---

## 🤝 Contribution

Contributions are welcome! Feel free to fork the repo and submit a pull request.

---

## 📜 License

This project is licensed under the MIT License.

---

## 🙌 Acknowledgements

- OpenAI GPT Documentation
- LangChain Documentation
- FAISS Research Paper

---

## 👨‍💻 Authors

- Anurag Sharma
- Gaurangi Tripathi
- Ayush Sharma

---

If you want, I can also:

- 🔥 Add **badges (GitHub style)**
- 💎 Make it **ATS-friendly for resume**
- ⚡ Create a **portfolio description version**
```
