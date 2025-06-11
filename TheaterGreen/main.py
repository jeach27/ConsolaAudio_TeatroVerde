import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
import pygame
import numpy as np
import os
import time
import threading
from tkinter import filedialog, messagebox
from datetime import timedelta
from audioView import AudioView
from videoView import VideoView

try:
    from PIL import Image
except ImportError:
    print("Pillow no está instalado. Los iconos no se mostrarán.")
    Image = None

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, audio_app, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.app = audio_app

        self.sample_rate = 44100
        self.channels = 1
        self.is_recording = False
        self.recording_thread = None
        self.recorded_audio_data = None
        self.recording_start_time = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.control_panel = ctk.CTkFrame(self, corner_radius=10)
        self.control_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.control_panel.grid_columnconfigure(0, weight=1)

        self.record_title = ctk.CTkLabel(self.control_panel, text="Gestión de Audio",
                                         font=ctk.CTkFont(size=18, weight="bold"))
        self.record_title.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        self.input_label = ctk.CTkLabel(self.control_panel, text="Entrada de Audio:")
        self.input_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.audio_input_dropdown = ctk.CTkOptionMenu(self.control_panel,
                                                      values=["Micrófono (Predeterminado)"])
        self.audio_input_dropdown.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.level_meter_label = ctk.CTkLabel(self.control_panel, text="Nivel de Entrada:")
        self.level_meter_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.level_meter = ctk.CTkProgressBar(self.control_panel, orientation="horizontal")
        self.level_meter.set(0.0)
        self.level_meter.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.record_button = ctk.CTkButton(self.control_panel, text="Grabar",
                                           command=self.toggle_recording,
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           fg_color="red", hover_color="#C20000")
        self.record_button.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        self.recording_status = ctk.CTkLabel(self.control_panel, text="Listo para grabar", font=ctk.CTkFont(size=14))
        self.recording_status.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="w")

        self.name_label = ctk.CTkLabel(self.control_panel, text="Nombre del Audio:")
        self.name_label.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        self.audio_name_entry = ctk.CTkEntry(self.control_panel, placeholder_text="Ej: Efecto de sonido 'Wow!'")
        self.audio_name_entry.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.desc_label = ctk.CTkLabel(self.control_panel, text="Descripción:")
        self.desc_label.grid(row=9, column=0, padx=20, pady=(10, 0), sticky="w")
        self.audio_desc_textbox = ctk.CTkTextbox(self.control_panel, height=80, wrap="word")
        self.audio_desc_textbox.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.audio_desc_textbox.insert("0.0", "Breve descripción del contenido del audio...")

        self.save_button = ctk.CTkButton(self.control_panel, text="Guardar Audio",
                                         command=self.save_audio,
                                         font=ctk.CTkFont(size=16, weight="bold"),
                                         state="disabled")
        self.save_button.grid(row=11, column=0, padx=20, pady=20, sticky="ew")

        self.upload_button = ctk.CTkButton(self.control_panel, text="Subir Audio",
                                          command=self.upload_audio,
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self.upload_button.grid(row=12, column=0, padx=20, pady=10, sticky="ew")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(text="Detener Grabación", fg_color="#E67E22", hover_color="#D35400")
        self.recording_status.configure(text="Grabando... 00:00")
        self.save_button.configure(state="disabled")
        self.recorded_audio_data = []
        self.recording_start_time = time.time()

        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        self.update_timer_and_level()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Grabar", fg_color="red", hover_color="#C20000")
        self.recording_status.configure(text="Grabación detenida.")
        self.save_button.configure(state="normal")
        if self.recording_thread:
            self.recording_thread.join()
        if self.recorded_audio_data:
            self.recorded_audio_data = np.concatenate(self.recorded_audio_data, axis=0)
        else:
            self.recorded_audio_data = None

    def record_audio(self):
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels) as stream:
                while self.is_recording:
                    data, _ = stream.read(1024)
                    self.recorded_audio_data.append(data)
        except Exception as e:
            print(f"Error durante la grabación: {e}")
            messagebox.showerror("Error", f"No se pudo grabar el audio: {e}")
            self.is_recording = False
            self.after(50, self.stop_recording)

    def update_timer_and_level(self):
        if self.is_recording:
            elapsed = int(time.time() - self.recording_start_time)
            timer_str = str(timedelta(seconds=elapsed))[2:7]
            self.recording_status.configure(text=f"Grabando... {timer_str}")
            if self.recorded_audio_data:
                level = np.abs(np.array(self.recorded_audio_data[-1])).mean()
                self.level_meter.set(min(level * 2, 1.0))
            else:
                self.level_meter.set(0.0)
            self.after(100, self.update_timer_and_level)
        else:
            self.level_meter.set(0.0)

    def save_audio(self):
        audio_name = self.audio_name_entry.get().strip()
        audio_desc = self.audio_desc_textbox.get("0.0", "end").strip()

        if not audio_name:
            messagebox.showerror("Error", "El nombre del audio no puede estar vacío.")
            return
        if self.recorded_audio_data is None or len(self.recorded_audio_data) == 0:
            messagebox.showerror("Error", "No hay audio grabado para guardar.")
            return

        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", f"{audio_name}.wav")

        try:
            sf.write(file_path, self.recorded_audio_data, self.sample_rate, format='WAV')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el audio: {e}")
            return

        self.app.audios.append({"name": audio_name, "file_path": file_path, "description": audio_desc})
        self.app.refresh_audio_view()  # Refresh Audio View

        self.audio_name_entry.delete(0, "end")
        self.audio_desc_textbox.delete("0.0", "end")
        self.save_button.configure(state="disabled")
        self.recorded_audio_data = None

    def upload_audio(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if not file_path:
            return

        audio_name = self.audio_name_entry.get().strip() or os.path.splitext(os.path.basename(file_path))[0]
        audio_desc = self.audio_desc_textbox.get("0.0", "end").strip()

        if not audio_name:
            messagebox.showerror("Error", "El nombre del audio no puede estar vacío.")
            return

        try:
            os.makedirs("data", exist_ok=True)
            new_file_path = os.path.join("data", f"{audio_name}{os.path.splitext(file_path)[1]}")
            with open(file_path, "rb") as src, open(new_file_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el audio: {e}")
            return

        self.app.audios.append({"name": audio_name, "file_path": new_file_path, "description": audio_desc})
        self.app.refresh_audio_view()  # Refresh Audio View

        self.audio_name_entry.delete(0, "end")
        self.audio_desc_textbox.delete("0.0", "end")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Controlador Audiovisual")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.audios = []

        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=0)
        self.main_container.grid_columnconfigure(1, weight=1)

        self.navigation_frame = ctk.CTkFrame(self.main_container, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.app_title = ctk.CTkLabel(self.navigation_frame, text="AV Controller",
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.app_title.grid(row=0, column=0, padx=20, pady=20)

        self.audio_button = ctk.CTkButton(self.navigation_frame, text="Audio",
                                          command=self.show_audio_view,
                                          font=ctk.CTkFont(size=16))
        self.audio_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.video_button = ctk.CTkButton(self.navigation_frame, text="Video",
                                          command=self.show_video_view,
                                          font=ctk.CTkFont(size=16))
        self.video_button.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        self.settings_button = ctk.CTkButton(self.navigation_frame, text="Ajustes",
                                             command=self.show_settings_view,
                                             font=ctk.CTkFont(size=14))
        self.settings_button.grid(row=5, column=0, sticky="s", padx=10, pady=10)

        self.content_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.audio_view = AudioView(self.content_frame, app=self)
        self.video_view = VideoView(self.content_frame)
        self.settings_view = SettingsView(self.content_frame, audio_app=self)

        self.show_audio_view()

    def load_icon(self, icon_name):
        if Image is None:
            return None
        try:
            icon_path = os.path.join("assets", icon_name)
            if not os.path.exists(icon_path):
                return None
            image = ctk.CTkImage(light_image=Image.open(icon_path),
                                 dark_image=Image.open(icon_path),
                                 size=(20, 20))
            return image
        except Exception as e:
            print(f"Error loading icon '{icon_name}': {e}")
            return None

    def show_audio_view(self):
        self.audio_view.pack(fill="both", expand=True)
        self.video_view.pack_forget()
        self.settings_view.pack_forget()
        self.audio_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        self.video_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.settings_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

    def show_video_view(self):
        self.video_view.pack(fill="both", expand=True)
        self.audio_view.pack_forget()
        self.settings_view.pack_forget()
        self.video_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        self.audio_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.settings_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

    def show_settings_view(self):
        self.settings_view.pack(fill="both", expand=True)
        self.audio_view.pack_forget()
        self.video_view.pack_forget()
        self.settings_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        self.audio_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.video_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])

    def refresh_audio_view(self):
        self.audio_view.load_existing_audios()  # Refresh the Audio View with updated audios

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    app = App()
    app.mainloop()

