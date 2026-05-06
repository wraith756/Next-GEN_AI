# CLAUDE.md
# Next Gen AI Assistant — Project Specification

---

## Overview

**Next Gen AI** is a full-stack AI voice assistant.

- **Backend:** FastAPI
- **Frontend:** Next.js
- **Database:** SQLite
- **AI Providers:** Groq
- **Integrations:** Google Workspace, YouTube, Windows Automation and other tools we can add in our JARVIS

---

## Folder Structure

```
nextgen-ai/
├── backend/       # FastAPI
└── frontend/      # Next.js
```

---

## Assistant Behavior

- Wake word **"Next Gen"** activates the assistant
- Replies in both **text and speech**
- Users can create and manage **chat sessions** (like ChatGPT)
- Assistant remembers context within a session
- After **10 messages**, session history is compressed to save tokens

---

## Features

### AI
- Support Groq
- Proper error messages — no silent failures

### Voice
- Wake word detection — **"Next Gen"**
- Speech-to-text input
- Text-to-speech output

### Chat Sessions
- Create, rename, delete sessions
- Session history stored in SQLite
- Context-aware responses
- Compress history after 10 messages

### Google Workspace
- Gmail — read, send, search
- Google Calendar — create, fetch events
- Google Drive — upload, list, search
- Google Docs / Sheets — read and write

### YouTube
- Search videos
- Get video details and transcripts
- Summarize video content via AI

### Windows Automation
- Open and close applications
- Mouse and keyboard control
- Take screenshots
- Manage windows
- Run system commands
- Read system info (CPU, RAM, disk)

Add more features into it.
---

## Known Issues

### AI Response Instability
- Blank or incomplete responses
- No voice output
- Delayed response
- Silent exception handling (`except: pass`) — must be fixed

### Gemini API
- Invalid or expired API key
- Unsupported model
- Quota exceeded
- Billing restrictions
- Network timeout

### xAI / Grok
- Invalid model name
- No API credits
- Invalid API key
- Model access restriction

---

## Removed

- ~~WhatsApp Automation~~
- ~~Eel~~
- Use only Groq api