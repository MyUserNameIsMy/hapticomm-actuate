import tkinter as tk
from tkinter import font as tkfont
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import os
import random
import threading
from typing import Tuple, Dict
from PIL import Image, ImageDraw, ImageFont, ImageTk

# --- Configuration Constants ---
DEVICES = ["HSD mk.I", "HSD mk.ii", "SKINETIC"]
APIS = ["Windows WDM-KS", "Windows WASAPI"]
SPR = 48000
CHANNELS = {
    13: ('t1', '-'), 11: ('t2', '-'), 9: ('ff1', '-'), 8: ('ff2', '-'),
    18: ('ff3', '-'), 5: ('mf1', '+'), 17: ('mf2', '+'), 4: ('rf1', '+'),
    7: ('rf2', '+'), 3: ('p1', '-'), 6: ('p2', '+'), 10: ('palm11', '-'),
    1: ('palm12', '+'), 2: ('palm13', '-'), 12: ('palm21', '-'),
    0: ('palm22', '-'), 16: ('palm23', '-'), 14: ('palm31', '+'),
    15: ('palm32', '+'), 19: ('palm33', '+')
}

# --- Language Translations (UPDATED) ---
LANGUAGES = {
    'en': {
        "title": "Haptic Learning Game", "initializing": "Getting ready...", "select_language": "Select a Language",
        "device_ready": "Device connected. Ready to play!", "start_learning": "Start Learning",
        "start_game": "Let's Play!", "learning_complete": "All done learning!",
        "click_start_game": "Click 'Let's Play!' when you're ready.", "starting_learning": "Let's start learning...",
        "feel_the_letter": "Feel the letter: {letter}", "next_letter": "Next Letter",
        "replay_letter": "Replay '{letter}'", "trial": "Round: {current} / {total}",
        "what_letter": "What letter did you feel?", "correct": "Correct!", "incorrect": "Nope. Try again!",
        "replay_signal": "Replay Signal", "game_over": "Game Over!", "well_done": "Great job!",
        "start_over": "Play Again", "error": "Error: {e}"
    },
    'ru': {
        "title": "Тактильная игра", "initializing": "Готовлюсь...", "select_language": "Выбери язык",
        "device_ready": "Устройство подключено. Готово к игре!", "start_learning": "Начать обучение",
        "start_game": "Давай поиграем!", "learning_complete": "Обучение закончено!",
        "click_start_game": "Когда будешь готов, нажми 'Давай поиграем!'", "starting_learning": "Начинаем учиться...",
        "feel_the_letter": "Почувствуй букву: {letter}", "next_letter": "Следующая",
        "replay_letter": "Повторить '{letter}'", "trial": "Раунд: {current} / {total}",
        "what_letter": "Какую букву ты почувствовал?", "correct": "Правильно!", "incorrect": "Неа. Попробуй еще раз!",
        "replay_signal": "Повторить сигнал", "game_over": "Игра окончена!", "well_done": "Молодец!",
        "start_over": "Сыграть снова", "error": "Ошибка: {e}"
    },
    'kz': {
        "title": "Тактильді ойын", "initializing": "Дайындалуда...", "select_language": "Тілді таңда",
        "device_ready": "Құрылғы қосылды. Ойынға дайын!", "start_learning": "Оқуды бастау",
        "start_game": "Ойнайық!", "learning_complete": "Оқу аяқталды!",
        "click_start_game": "Дайын болсаң, 'Ойнайық!' деп бас.", "starting_learning": "Оқуды бастаймыз...",
        "feel_the_letter": "Мына әріпті сезін: {letter}", "next_letter": "Келесі",
        "replay_letter": "'{letter}' қайталау", "trial": "Раунд: {current} / {total}",
        "what_letter": "Қандай әріпті сездің?", "correct": "Дұрыс!", "incorrect": "Жоқ. Қайталап көр!",
        "replay_signal": "Сигналды қайталау", "game_over": "Ойын аяқталды!", "well_done": "Жарайсың!",
        "start_over": "Қайта ойнау", "error": "Қате: {e}"
    }
}

class HapticTutorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- App Config ---
        self.geometry("700x550")
        self.configure(bg="#f0f8ff")
        self.language = 'en'
        self.title(LANGUAGES[self.language]["title"])

        # --- Audio State ---
        self.device_id = -1
        self.out_stream = None
        self.signals = {}
        self.current_signal_data = None
        self.X = 0
        self.is_playing = False

        # --- App State ---
        self.app_state = "idle"
        self.test_letters = ['A', 'B', 'C', 'D']
        self.learning_index = 0
        self.current_trial = 0
        self.total_trials = 10
        self.correct_answer = ''
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # --- UI Initialization ---
        self.create_language_selection_ui()

    # --- UI Creation ---
    def create_language_selection_ui(self):
        self.lang_frame = tk.Frame(self, bg="#f0f8ff", padx=20, pady=20)
        self.lang_frame.pack(expand=True, fill="both")
        
        tk.Label(self.lang_frame, text=LANGUAGES['ru']['select_language'], font=("Helvetica", 20, "bold"), bg="#f0f8ff").pack(pady=30)
        
        btn_frame = tk.Frame(self.lang_frame, bg="#f0f8ff")
        btn_frame.pack(pady=20)

        self.create_rounded_button(btn_frame, "English", "#4a90e2", lambda: self.set_language('en')).pack(pady=10)
        self.create_rounded_button(btn_frame, "Русский", "#50e3c2", lambda: self.set_language('ru')).pack(pady=10)
        self.create_rounded_button(btn_frame, "Қазақша", "#f5a623", lambda: self.set_language('kz')).pack(pady=10)

    def set_language(self, lang_code):
        self.language = lang_code
        self.title(LANGUAGES[self.language]["title"])
        self.lang_frame.destroy()
        self.create_main_widgets()
        threading.Thread(target=self.setup_haptics, daemon=True).start()

    def create_main_widgets(self):
        lang_dict = LANGUAGES[self.language]
        self.main_frame = tk.Frame(self, bg="#f0f8ff", padx=20, pady=20)
        self.main_frame.pack(expand=True, fill="both")

        self.status_label = tk.Label(self.main_frame, text=lang_dict["initializing"], font=("Helvetica", 18, "bold"), bg="#f0f8ff", fg="#333")
        self.status_label.pack(pady=(10, 20))

        self.progress_label = tk.Label(self.main_frame, font=("Helvetica", 14), bg="#f0f8ff", fg="#555")
        self.progress_label.pack(pady=(0, 25))

        # --- Learning Phase Buttons ---
        self.learning_controls_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        self.replay_learn_button = self.create_rounded_button(self.learning_controls_frame, lang_dict["replay_letter"].format(letter="A"), "#f5a623", self.replay_learning_signal)
        self.replay_learn_button.pack(side="left", padx=10)
        self.next_learn_button = self.create_rounded_button(self.learning_controls_frame, lang_dict["next_letter"], "#4a90e2", self.advance_learning)
        self.next_learn_button.pack(side="left", padx=10)
        
        # --- Main Action Buttons ---
        self.learn_button = self.create_rounded_button(self.main_frame, lang_dict["start_learning"], "#4a90e2", self.start_learning)
        self.learn_button.pack(pady=10)
        self.learn_button.config(state="disabled")

        self.play_button = self.create_rounded_button(self.main_frame, lang_dict["start_game"], "#2e7d32", self.start_game)
        
        # --- Answer Buttons ---
        self.answer_frame = tk.Frame(self.main_frame, bg="#f0f8ff")
        self.answer_buttons = {}
        for letter in self.test_letters:
            btn = self.create_rounded_button(self.answer_frame, letter, "#7f8c8d", lambda l=letter: self.check_answer(l), width=80, height=80, font_size=30)
            btn.pack(side="left", padx=10, pady=10)
            self.answer_buttons[letter] = btn

        # --- Game Replay Button ---
        self.replay_game_button = self.create_rounded_button(self.main_frame, lang_dict["replay_signal"], "#f5a623", self.replay_current_signal)
        
    def _create_button_image(self, text, color, width, height, font_size):
        """Helper function to generate a button image with text."""
        font = None
        font_names = ["verdana.ttf", "arial.ttf"]
        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue
        if font is None:
            print(f"WARNING: Fonts {font_names} not found. Using default font.")
            font = ImageFont.load_default()

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, width, height), radius=height//2, fill=color)
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_pos = ((width - text_width) / 2, (height - text_height) / 2 - 4)
        draw.text(text_pos, text, font=font, fill="white")
        
        return ImageTk.PhotoImage(image=image)

    def create_rounded_button(self, parent, text, color, command, width=250, height=50, font_size=16):
        """Creates a modern, rounded button using PIL."""
        photo = self._create_button_image(text, color, width, height, font_size)
        
        button = tk.Button(parent, image=photo, command=command, borderwidth=0, highlightthickness=0, relief="flat", activebackground=parent.cget('bg'))
        button.image = photo
        button.creation_params = {
            "color": color, "width": width, "height": height, "font_size": font_size
        }
        return button

    def update_button_text(self, button, new_text):
        """Redraws the button with new text."""
        params = button.creation_params
        new_photo = self._create_button_image(new_text, **params)
        button.config(image=new_photo)
        button.image = new_photo

    # --- Haptic Logic ---
    def find_device(self, dev_list, api_list):
        for i, device in enumerate(dev_list):
            if api_list[device['hostapi']]['name'] in APIS:
                for d in DEVICES:
                    if d in device['name']: return i
        raise OSError("No compatible device found.")

    def load_audio_files(self):
        signals = {}
        for key in self.test_letters:
            file_path = f'Actuat_Let{key}.wav'
            if os.path.exists(file_path):
                fs, data = wavfile.read(file_path)
                assert data.ndim == 2 and data.shape[1] == 20
                mod_sig = [(data[:, i]).astype('int16') for i in range(20)]
                for ch, (_, op) in CHANNELS.items():
                    if op == '-': mod_sig[ch] = -1 * np.abs(mod_sig[ch])
                    elif op == '+': mod_sig[ch] = np.abs(mod_sig[ch])
                signals[key] = mod_sig
            else:
                raise FileNotFoundError(f"{file_path}")
        return signals

    def setup_haptics(self):
        try:
            self.device_id = self.find_device(sd.query_devices(), sd.query_hostapis())
            self.signals = self.load_audio_files()
            self.out_stream = sd.OutputStream(
                samplerate=SPR, device=self.device_id, channels=20,
                dtype='int16', latency='low', callback=self.stream_callback,
                finished_callback=self.on_stream_finished)
            self.status_label.config(text=LANGUAGES[self.language]["device_ready"])
            self.learn_button.config(state="normal")
        except Exception as e:
            self.status_label.config(text=LANGUAGES[self.language]["error"].format(e=e), fg="red")

    def stream_callback(self, data, frames, _, __):
        rem = len(self.current_signal_data[0]) - self.X
        chunk = min(frames, rem)
        for c in range(data.shape[1]):
            data[:chunk, c] = self.current_signal_data[c][self.X : self.X + chunk]
        data[chunk:, :].fill(0)
        if chunk < frames: raise sd.CallbackStop
        self.X += frames

    def play_signal(self, signal_key):
        if self.is_playing: return
        if signal_key in self.signals:
            self.is_playing = True
            self.set_ui_state("playing")
            self.current_signal_data = self.signals[signal_key]
            self.X = 0
            self.out_stream.start()

    def on_stream_finished(self):
        self.is_playing = False
        self.set_ui_state(self.app_state)

    # --- Application Flow ---
    def start_learning(self):
        self.app_state = "learning"
        self.learning_index = 0
        self.learn_button.pack_forget()
        self.learning_controls_frame.pack(pady=20)
        self.learning_step()

    def learning_step(self):
        self.set_ui_state("idle")
        if self.learning_index < len(self.test_letters):
            letter = self.test_letters[self.learning_index]
            lang_dict = LANGUAGES[self.language]
            self.status_label.config(text=lang_dict["feel_the_letter"].format(letter=letter))
            self.update_button_text(self.replay_learn_button, lang_dict["replay_letter"].format(letter=letter))
            self.play_signal(letter)
        else:
            lang_dict = LANGUAGES[self.language]
            self.status_label.config(text=lang_dict["learning_complete"])
            self.progress_label.config(text=lang_dict["click_start_game"])
            self.learning_controls_frame.pack_forget()
            self.play_button.pack(pady=10)
            self.play_button.config(state="normal")

    def advance_learning(self):
        if self.is_playing: return
        self.learning_index += 1
        self.learning_step()

    def replay_learning_signal(self):
        if self.is_playing: return
        letter = self.test_letters[self.learning_index]
        self.play_signal(letter)

    def start_game(self):
        self.app_state = "testing" # Internal state name remains
        self.current_trial = 0
        self.play_button.pack_forget()
        self.progress_label.config(text="")
        self.answer_frame.pack(pady=20)
        self.replay_game_button.pack(pady=10)
        self.next_trial()

    def next_trial(self):
        self.current_trial += 1
        if self.current_trial > self.total_trials:
            self.end_game()
            return
        lang_dict = LANGUAGES[self.language]
        self.progress_label.config(text=lang_dict["trial"].format(current=self.current_trial, total=self.total_trials))
        self.status_label.config(text=lang_dict["what_letter"], fg="#333")
        self.correct_answer = random.choice(self.test_letters)
        self.after(1000, lambda: self.play_signal(self.correct_answer))

    def check_answer(self, chosen_letter):
        if self.is_playing: return
        lang_dict = LANGUAGES[self.language]
        if chosen_letter == self.correct_answer:
            self.status_label.config(text=lang_dict["correct"], fg="#2e7d32")
            self.set_ui_state("idle")
            self.after(2000, self.next_trial)
        else:
            self.status_label.config(text=lang_dict["incorrect"], fg="#ff8f00")
            self.after(500, self.replay_current_signal)
    
    def replay_current_signal(self):
        if self.correct_answer and not self.is_playing:
            self.play_signal(self.correct_answer)

    def end_game(self):
        self.app_state = "finished"
        lang_dict = LANGUAGES[self.language]
        self.status_label.config(text=lang_dict["game_over"], fg="#4a90e2")
        self.progress_label.config(text=lang_dict["well_done"])
        self.answer_frame.pack_forget()
        self.replay_game_button.pack_forget()
        self.update_button_text(self.learn_button, lang_dict["start_over"])
        self.learn_button.pack(pady=10)

    def set_ui_state(self, state):
        all_buttons = list(self.answer_buttons.values()) + [self.replay_game_button, self.next_learn_button, self.replay_learn_button]
        
        if state == "playing":
            for btn in all_buttons: btn.config(state="disabled")
        elif state == "learning":
            self.next_learn_button.config(state="normal")
            self.replay_learn_button.config(state="normal")
        elif state == "testing": # Internal state name remains
            for btn in self.answer_buttons.values(): btn.config(state="normal")
            self.replay_game_button.config(state="normal")
        else: # idle, finished
            for btn in all_buttons: btn.config(state="disabled")

    def on_closing(self):
        if self.out_stream:
            self.out_stream.stop()
            self.out_stream.close()
        self.destroy()

if __name__ == "__main__":
    app = HapticTutorApp()
    app.mainloop()