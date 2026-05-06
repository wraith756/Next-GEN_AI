# ==============================
# features.py (FULL OPTIMIZED)
# ==============================

import os
import re
import time
import json
import sqlite3
import struct
import traceback
import subprocess
import webbrowser
from datetime import datetime
from urllib.parse import quote, quote_plus

import eel
import pyaudio
import pyautogui
import pvporcupine
import requests
from playsound import playsound

from engine.command import speak
from engine.config import (
    ASSISTANT_NAME,
    LLM_PROVIDER,
    GEMINI_API_KEY,
    XAI_API_KEY,
    GROK_MODEL,
)

from engine.helper import (
    extract_yt_term,
    markdown_to_text,
    remove_words,
)

# ==========================================
# DATABASE
# ==========================================

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sys_command(
    id INTEGER PRIMARY KEY,
    name TEXT,
    path TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS web_command(
    id INTEGER PRIMARY KEY,
    name TEXT,
    url TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS contacts(
    id INTEGER PRIMARY KEY,
    name TEXT,
    mobile_no TEXT,
    email TEXT,
    address TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS info(
    name TEXT,
    designation TEXT,
    mobileno TEXT,
    email TEXT,
    city TEXT
)
""")

con.commit()

# ==========================================
# CONSTANTS
# ==========================================

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

XAI_URL = "https://api.x.ai/v1/chat/completions"

# ==========================================
# DEBUG LOGGER
# ==========================================


def log_error(error):

    print("\n========== ERROR ==========")
    print("ERROR:", str(error))
    traceback.print_exc()
    print("===========================\n")


# ==========================================
# HELPERS
# ==========================================


def clean_query(query):

    query = str(query).lower()

    query = query.replace(ASSISTANT_NAME.lower(), "")

    remove_words_list = [
        "please",
        "tell me",
        "answer",
        "search",
        "explain",
    ]

    for word in remove_words_list:
        query = query.replace(word, "")

    return query.strip()


def normalize_mobile_number(mobile_no):

    mobile_no = str(mobile_no).strip()

    mobile_no = re.sub(r"[^\d+]", "", mobile_no)

    if mobile_no.startswith("+"):
        return mobile_no

    return "+91" + mobile_no


# ==========================================
# START SOUND
# ==========================================

@eel.expose
def playAssistantSound():

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))

        sound_path = os.path.join(
            current_dir,
            "..",
            "www",
            "assets",
            "audio",
            "start_sound.mp3",
        )

        sound_path = os.path.abspath(sound_path)

        playsound(sound_path)

    except Exception as e:
        log_error(e)


# ==========================================
# OPEN COMMAND
# ==========================================

def openCommand(query):

    try:

        query = query.lower()

        query = query.replace(ASSISTANT_NAME.lower(), "")
        query = query.replace("open", "")

        app_name = query.strip()

        if not app_name:
            return

        # SYSTEM APPS
        cursor.execute(
            "SELECT path FROM sys_command WHERE LOWER(name)=?",
            (app_name,),
        )

        result = cursor.fetchone()

        if result:

            speak(f"Opening {app_name}")

            os.startfile(result[0])

            return

        # WEB APPS
        cursor.execute(
            "SELECT url FROM web_command WHERE LOWER(name)=?",
            (app_name,),
        )

        result = cursor.fetchone()

        if result:

            speak(f"Opening {app_name}")

            webbrowser.open(result[0])

            return

        # WINDOWS SEARCH
        speak(f"Opening {app_name}")

        os.system(f"start {app_name}")

    except Exception as e:
        log_error(e)
        speak("Unable to open")


# ==========================================
# YOUTUBE
# ==========================================

def PlayYoutube(query):

    try:

        import pywhatkit as kit

        search_term = extract_yt_term(query)

        speak(f"Playing {search_term}")

        kit.playonyt(search_term)

    except Exception as e:
        log_error(e)
        speak("Unable to play video")


# ==========================================
# WEB SEARCH
# ==========================================

def webSearch(query):

    try:

        query = clean_query(query)

        if not query:
            speak("What should I search?")
            return

        speak(f"Searching {query}")

        url = (
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

        webbrowser.open(url)

    except Exception as e:
        log_error(e)


# ==========================================
# AI PROVIDER
# ==========================================

def has_valid_gemini_key():

    return (
        GEMINI_API_KEY
        and GEMINI_API_KEY.startswith("AIza")
    )


def has_valid_xai_key():

    return (
        XAI_API_KEY
        and XAI_API_KEY.startswith("xai-")
    )


def get_provider():

    if LLM_PROVIDER == "gemini":
        return "gemini"

    if LLM_PROVIDER in ("xai", "grok"):
        return "xai"

    # AUTO MODE
    if has_valid_xai_key():
        return "xai"

    if has_valid_gemini_key():
        return "gemini"

    return None


# ==========================================
# GROK AI
# ==========================================

def grokAnswer(query):

    response = requests.post(
        XAI_URL,
        headers={
            "Authorization": f"Bearer {XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are {ASSISTANT_NAME}, "
                        "a concise AI assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            "temperature": 0.5,
            "max_tokens": 200,
        },
        timeout=30,
    )

    if response.status_code != 200:

        raise Exception(
            f"xAI ERROR {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    return data["choices"][0]["message"]["content"]


# ==========================================
# GEMINI AI
# ==========================================

def geminiAnswer(query):

    last_error = None

    for model in GEMINI_MODELS:

        try:

            response = requests.post(
                GEMINI_URL.format(model=model),
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": (
                                        f"You are {ASSISTANT_NAME}. "
                                        f"Answer briefly.\n\n"
                                        f"User: {query}"
                                    )
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.5,
                        "maxOutputTokens": 220,
                        "thinkingConfig": {
                            "thinkingBudget": 0,
                        },
                    },
                },
                timeout=30,
            )

            if response.status_code != 200:

                raise Exception(
                    f"Gemini ERROR "
                    f"{response.status_code}: "
                    f"{response.text}"
                )

            data = response.json()

            candidates = data.get("candidates")

            if not candidates:
                continue

            parts = (
                candidates[0]
                .get("content", {})
                .get("parts", [])
            )

            text = "".join(
                part.get("text", "")
                for part in parts
            )

            finish_reason = candidates[0].get("finishReason")
            if finish_reason == "MAX_TOKENS":
                raise Exception(
                    f"Gemini model {model} reached max tokens"
                )

            if text and len(text.split()) >= 5:
                return text

        except Exception as e:

            last_error = e

            log_error(e)

    raise Exception(last_error)


# ==========================================
# MAIN AI FUNCTION
# ==========================================

def geminai(query):

    try:

        query = clean_query(query)

        print("\n======================")
        print("USER QUERY:", query)

        if not query:
            speak("Please say something")
            return

        provider = get_provider()

        print("PROVIDER:", provider)

        if provider == "xai":

            print("Using GROK")

            response = grokAnswer(query)

        elif provider == "gemini":

            print("Using GEMINI")

            response = geminiAnswer(query)

        else:

            speak("No AI provider configured")

            return

        print("RAW RESPONSE:", response)

        response = markdown_to_text(response)

        if response:

            speak(response)

        else:

            speak("No response generated")

    except Exception as e:

        log_error(e)

        speak("AI service error")


# ==========================================
# STATUS
# ==========================================

def assistantStatus():

    provider = get_provider()

    if provider == "gemini":

        speak("Gemini configured")

    elif provider == "xai":

        speak("Grok configured")

    else:

        speak("No AI configured")


# ==========================================
# HOTWORD
# ==========================================

def hotword():

    porcupine = None
    paud = None
    audio_stream = None

    try:

        porcupine = pvporcupine.create(
            keywords=["jarvis", "alexa"]
        )

        paud = pyaudio.PyAudio()

        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        while True:

            pcm = audio_stream.read(
                porcupine.frame_length
            )

            pcm = struct.unpack_from(
                "h" * porcupine.frame_length,
                pcm,
            )

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:

                print("HOTWORD DETECTED")

                pyautogui.press("f9")

                time.sleep(2)

    except Exception as e:

        log_error(e)

    finally:

        if porcupine:
            porcupine.delete()

        if audio_stream:
            audio_stream.close()

        if paud:
            paud.terminate()


# ==========================================
# WHATSAPP
# ==========================================

def whatsApp(mobile_no, message, flag, name):

    try:

        mobile_no = normalize_mobile_number(
            mobile_no
        )

        encoded_message = quote(message)

        url = (
            f"whatsapp://send?"
            f"phone={mobile_no}"
            f"&text={encoded_message}"
        )

        subprocess.run(
            f'start "" "{url}"',
            shell=True,
        )

        time.sleep(5)

        if flag == "message":

            pyautogui.press("enter")

            speak(f"Message sent to {name}")

    except Exception as e:

        log_error(e)

        speak("Unable to send message")


# ==========================================
# CONTACT SEARCH
# ==========================================

def findContact(query):

    try:

        query = query.lower()

        cursor.execute(
            "SELECT name, mobile_no FROM contacts"
        )

        contacts = cursor.fetchall()

        for name, mobile in contacts:

            if name.lower() in query:

                return (
                    normalize_mobile_number(
                        mobile
                    ),
                    name,
                )

        return 0, 0

    except Exception as e:

        log_error(e)

        return 0, 0


# ==========================================
# CLOSE APP
# ==========================================

def closeCommand(query):

    try:

        import pygetwindow as gw

        query = query.lower()

        query = (
            query.replace("close", "")
            .replace(ASSISTANT_NAME.lower(), "")
            .strip()
        )

        windows = gw.getAllTitles()

        for title in windows:

            if query in title.lower():

                app = gw.getWindowsWithTitle(
                    title
                )

                if app:

                    app[0].close()

                    speak(f"Closed {query}")

                    return

        os.system(
            f"taskkill /f /im {query}.exe"
        )

    except Exception as e:

        log_error(e)

        speak("Unable to close app")


# ==========================================
# SETTINGS / UI DATABASE APIs
# ==========================================

@eel.expose
def personalInfo():

    try:

        cursor.execute("SELECT * FROM info LIMIT 1")

        result = cursor.fetchone()

        if not result:

            result = ("", "", "", "", "")

        eel.getData(json.dumps(result))

        return 1

    except Exception as e:

        log_error(e)

        eel.getData(json.dumps(("", "", "", "", "")))

        return 0


@eel.expose
def updatePersonalInfo(name, designation, mobileno, email, city):

    try:

        cursor.execute("SELECT COUNT(*) FROM info")

        count = cursor.fetchone()[0]

        if count:

            cursor.execute(
                """
                UPDATE info
                SET name=?, designation=?, mobileno=?, email=?, city=?
                """,
                (name, designation, mobileno, email, city),
            )

        else:

            cursor.execute(
                """
                INSERT INTO info(name, designation, mobileno, email, city)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, designation, mobileno, email, city),
            )

        con.commit()

        personalInfo()

        return 1

    except Exception as e:

        log_error(e)

        return 0


@eel.expose
def displaySysCommand():

    cursor.execute("SELECT id, name, path FROM sys_command")

    eel.displaySysCommand(json.dumps(cursor.fetchall()))

    return 1


@eel.expose
def addSysCommand(key, value):

    cursor.execute(
        "INSERT INTO sys_command(name, path) VALUES (?, ?)",
        (key, value),
    )

    con.commit()

    return 1


@eel.expose
def deleteSysCommand(id):

    cursor.execute("DELETE FROM sys_command WHERE id=?", (id,))

    con.commit()

    return 1


@eel.expose
def displayWebCommand():

    cursor.execute("SELECT id, name, url FROM web_command")

    eel.displayWebCommand(json.dumps(cursor.fetchall()))

    return 1


@eel.expose
def addWebCommand(key, value):

    cursor.execute(
        "INSERT INTO web_command(name, url) VALUES (?, ?)",
        (key, value),
    )

    con.commit()

    return 1


@eel.expose
def deleteWebCommand(id):

    cursor.execute("DELETE FROM web_command WHERE id=?", (id,))

    con.commit()

    return 1


@eel.expose
def displayPhoneBookCommand():

    cursor.execute(
        "SELECT id, name, mobile_no, email, address FROM contacts"
    )

    eel.displayPhoneBookCommand(json.dumps(cursor.fetchall()))

    return 1


@eel.expose
def InsertContacts(Name, MobileNo, Email, City):

    cursor.execute(
        """
        INSERT INTO contacts(name, mobile_no, email, address)
        VALUES (?, ?, ?, ?)
        """,
        (Name, MobileNo, Email, City),
    )

    con.commit()

    return 1


@eel.expose
def deletePhoneBookCommand(id):

    cursor.execute("DELETE FROM contacts WHERE id=?", (id,))

    con.commit()

    return 1


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    geminai("hello")
