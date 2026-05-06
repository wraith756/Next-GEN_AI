import pyttsx3
import speech_recognition as sr
import eel
import re
import time

_tts_engine = None


def get_tts_engine():
    global _tts_engine

    if _tts_engine is None:
        _tts_engine = pyttsx3.init('sapi5')
        voices = _tts_engine.getProperty('voices')
        if voices:
            _tts_engine.setProperty('voice', voices[0].id)
        _tts_engine.setProperty('rate', 174)

    return _tts_engine


def speak(text):
    text = str(text)
    eel.DisplayMessage(text)
    engine = get_tts_engine()
    engine.say(text)
    eel.receiverText(text)
    engine.runAndWait()


def takecommand():

    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    r.phrase_threshold = 0.3
    r.non_speaking_duration = 0.5

    try:
        with sr.Microphone() as source:
            print('listening....')
            eel.DisplayMessage('listening....')
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, timeout=8, phrase_time_limit=12)

        print('recognizing')
        eel.DisplayMessage('recognizing....')
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        time.sleep(0.5)
    except sr.WaitTimeoutError:
        eel.DisplayMessage("I did not hear anything.")
        return ""
    except sr.UnknownValueError:
        eel.DisplayMessage("Sorry, I could not understand that.")
        return ""
    except sr.RequestError as e:
        print("Speech recognition service error:", e)
        eel.DisplayMessage("Speech recognition service is not reachable.")
        return ""
    except Exception as e:
        print("Speech recognition error:", e)
        eel.DisplayMessage("Microphone or speech recognition failed.")
        return ""
    
    return query.lower()


def extract_inline_message(query, contact_name):
    contact_name = str(contact_name).strip().lower()
    contact_index = query.lower().find(contact_name)

    if contact_index == -1:
        return ""

    inline_message = query[contact_index + len(contact_name):].strip()
    inline_message = re.sub(r"^(on\s+)?(whatsapp|mobile|sms)\b", "", inline_message).strip()
    inline_message = re.sub(r"^(saying|say|that|message|msg|text)\b", "", inline_message).strip()
    return inline_message

@eel.expose
def allCommands(message=1):

    is_voice_command = message == 1

    if is_voice_command:
        query = takecommand()
        print(query)
        eel.senderText(query)
    else:
        query = str(message).strip().lower()
        eel.senderText(query)

    if not query:
        speak("I did not receive any command. Please try again.")
        eel.ShowHood()
        return

    try:
        is_message_command = "send message" in query or "send sms" in query or "whatsapp message" in query

        wants_browser_search = (
            "search web" in query
            or "search browser" in query
            or "open google search" in query
            or "search on google" in query
            or "google it" in query
        )

        if "open" in query and not wants_browser_search:
            from engine.features import openCommand
            openCommand(query)
        elif "ai status" in query or "api status" in query or "assistant status" in query:
            from engine.features import assistantStatus
            assistantStatus()
        elif wants_browser_search:
            from engine.features import webSearch
            webSearch(query)
        elif "on youtube" in query:
            from engine.features import PlayYoutube
            PlayYoutube(query)
        
        elif is_message_command or "phone call" in query or "video call" in query:
            from engine.features import findContact, whatsApp, makeCall, sendMessage
            contact_no, name = findContact(query)
            if(contact_no != 0):
                if "whatsapp" in query:
                    preferance = "whatsapp"
                elif "mobile" in query or "sms" in query:
                    preferance = "mobile"
                else:
                    speak("Which mode you want to use whatsapp or mobile")
                    preferance = takecommand()
                print(preferance)

                if "mobile" in preferance:
                    if is_message_command:
                        inline_message = extract_inline_message(query, name)
                        if inline_message:
                            message = inline_message
                        else:
                            speak("what message to send")
                            message = takecommand()
                        if not message:
                            speak("Message is empty. Please try again.")
                            eel.ShowHood()
                            return
                        sendMessage(message, contact_no, name)
                    elif "phone call" in query:
                        makeCall(name, contact_no)
                    else:
                        speak("please try again")
                elif "whatsapp" in preferance:
                    message = ""
                    if is_message_command:
                        message = 'message'
                        inline_message = extract_inline_message(query, name)
                        if inline_message:
                            query = inline_message
                        else:
                            speak("what message to send")
                            query = takecommand()
                            if not query:
                                speak("Message is empty. Please try again.")
                                eel.ShowHood()
                                return
                                        
                    elif "phone call" in query:
                        message = 'call'
                    else:
                        message = 'video call'
                                        
                    whatsApp(contact_no, query, message, name)

        else:
            from engine.features import geminai
            geminai(query)
    except Exception as e:
        print("Command error:", e)
        speak("Something went wrong while running that command.")
    
    eel.ShowHood()
