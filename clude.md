# CLUDE.md

# Jarvis AI Assistant - Debug Notes & n8n Automation Integration

---

# Project Overview

Jarvis is a Python-based AI voice assistant using:

- Python
- Eel
- SQLite
- Gemini AI
- xAI / Grok
- Speech Recognition
- WhatsApp Automation
- Voice Commands
- Desktop Automation

---

# Current Issues

The assistant starts correctly but AI responses are unstable.

---

# Problems Found

## AI Service Errors

Assistant sometimes returns:

- "AI service error"
- blank response
- incomplete output
- no voice output
- delayed response

---

# Gemini API Issues

Gemini API may fail because of:

- invalid API key
- expired API key
- unsupported model
- quota exceeded
- billing restrictions
- network timeout

---

# xAI / Grok Issues

xAI sometimes fails because:

- invalid model name
- no API credits
- invalid API key
- model access restriction

---

# Hidden Exception Problem

Old code used:

```python
except:
    pass
```
