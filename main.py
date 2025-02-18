import tkinter as tk
from tkinter import scrolledtext
from openai import OpenAI
import requests
import io
import pygame
import speech_recognition as sr
import threading
import time
import webbrowser

client = OpenAI(api_key="[Redacted]")

pygame.init()
pygame.mixer.init()

class ZorenAssistant:
    def __init__(self, root):
        self.root = root
        root.title("Zoren's Assistant")
        root.configure(bg='#2E2E2E')

        self.chat_log = scrolledtext.ScrolledText(root, state='disabled', width=70, height=20, bg='#414141', fg='white')
        self.chat_log.grid(row=0, column=0, columnspan=2)

        self.user_input = tk.Entry(root, width=70, bg='#414141', fg='white')
        self.user_input.grid(row=1, column=0)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(root, text="Send", bg='#414141', fg='white', command=self.send_message)
        self.send_button.grid(row=1, column=1)

        self.voice_button = tk.Button(root, text="Speech", bg='#414141', fg='white', command=self.recognize_speech)
        self.voice_button.grid(row=2, column=0, columnspan=2)

    def play_audio(self, audio_content):
        with io.BytesIO(audio_content) as audio_file:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

    def send_message(self, event=None):
        command_executed = False
        user_text = self.user_input.get().lower()
        self.user_input.delete(0, tk.END)
        self.update_chat_log("You: " + user_text + "\n")

        response = None

        if user_text == "open google":
            webbrowser.open("https://www.google.com")
            command_executed = True
        elif user_text == "open youtube":
            webbrowser.open("https://www.youtube.com")
            command_executed = True
        elif "search" in user_text and "on google" in user_text:
            query = user_text.split("search")[1].split("on google")[0].strip()
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            command_executed = True
        elif "play" in user_text and "on youtube" in user_text:
            query = user_text.split("play")[1].split("on youtube")[0].strip()
            search_url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(search_url)
            command_executed = True

        if "what is the weather outside" in user_text:
            location = user_text.replace("weather in ", "") if "weather in" in user_text else None
            weather_info = self.get_weather(location)  # Assumes get_weather handles None as auto-location
            self.update_chat_log("Zoren's Assistant: " + weather_info + "\n")
            self.generate_and_play_audio(weather_info)
            command_executed = True

        if not command_executed:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "Your system message here."},
                    {"role": "user", "content": user_text}
                ]
            )
            response_text = response.choices[0].message.content
            self.update_chat_log("Zoren's Assistant: " + response_text + "\n")
            self.generate_and_play_audio(response_text)

    def update_chat_and_play_audio(self, response_text):
        sentences = response_text.split('. ')
        for sentence in sentences:
            self.update_chat_log("Zoren's Assistant: " + sentence + ".\n")
            self.generate_and_play_audio(sentence + ".")
            time.sleep(len(sentence.split()) / 2)

    def generate_and_play_audio(self, text):
        api_url = "[Redacted]"
        payload = {
            "model_id": "eleven_monolingual_v1",
            "text": text,
            "voice_settings": {
                "similarity_boost": 1,
                "stability": 1,
                "style": 1,
                "use_speaker_boost": True
            }
        }
        headers = {
            "xi-api-key": "[Redacted]",
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            audio_content = response.content
            self.play_audio(audio_content)
        else:
            print("Error in text-to-speech API call")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
        pass
    def update_chat_log(self, message):
        self.chat_log.configure(state='normal')
        self.chat_log.insert(tk.END, message)
        self.chat_log.configure(state='disabled')
        self.chat_log.see(tk.END)
    def recognize_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                print("Adjusting for ambient noise, please wait...")
                recognizer.adjust_for_ambient_noise(source)
                print("Listening... Please start speaking.")
                audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                print("You said: " + text)

                command_handled = self.handle_command(text)
                if not command_handled:
                    self.user_input.delete(0, tk.END)
                    self.user_input.insert(0, text)
                    self.send_message()

            except sr.WaitTimeoutError:
                print("No speech detected within the timeout period.")
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio.")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
            except KeyboardInterrupt:
                print("Speech recognition interrupted.")
    def handle_command(self, text):
        lower_text = text.lower()
        if "open youtube" in lower_text:
            webbrowser.open("https://www.youtube.com")
            return True
        elif "open google" in lower_text:
            webbrowser.open("https://www.google.com")
            return True
        elif "search" in lower_text and "on google" in lower_text:
            query = lower_text.split("search")[1].split("on google")[0].strip()
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            return True
        elif "play" in lower_text and "on youtube" in lower_text:
            query = lower_text.split("play")[1].split("on youtube")[0].strip()
            search_url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(search_url)
    def get_weather(self, location=None):
        api_key = "[Redacted]"
        base_url = "http://api.openweathermap.org/data/2.5/weather?"

        if not location:
            city, region, country = self.get_location()
            if city:
                location = city
            else:
                return "Unable to fetch location."

        complete_url = base_url + "appid=" + api_key + "&q=" + location
        response = requests.get(complete_url)
        weather_data = response.json()

        if "main" in weather_data:
            main = weather_data["main"]
            temperature = main["temp"] - 273.15
            humidity = main["humidity"]
            weather_description = weather_data["weather"][0]["description"]
            weather_message = f"Temperature: {temperature:.2f}°C\nHumidity: {humidity}%\nDescription: {weather_description}"
        elif "cod" in weather_data and weather_data["cod"] != 200:
            error_message = weather_data.get("message", "Unknown error occurred.")
            weather_message = f"Failed to fetch weather data: {error_message}"
        else:
            weather_message = "Weather data format is unexpected."

        return weather_message
        pass
    def get_location(self):
        try:
            ipinfo_token = "d3198aa4e479e8"
            response = requests.get(f'https://ipinfo.io?token={ipinfo_token}')
            data = response.json()
            return data['city'], data['region'], data['country']
        except Exception as e:
            print(f"Error fetching location: {e}")
            return None, None, None

root = tk.Tk()
app = ZorenAssistant(root)

root.mainloop()
