import customtkinter as ctk
import pygame
import os
import sys
import time
from tkinter import messagebox

def resource_path(relative_path):
    """Obtiene la ruta absoluta, compatible con PyInstaller o entorno local."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AudioView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.app = app
        self.currently_playing = None
        self.play_queue = []
        self.is_paused = False
        self.paused_position = 0
        self.after_id = None
        self.last_played_frame = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.console_panel = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.console_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.console_panel.grid_columnconfigure(0, weight=1)

        # Header frame with title and refresh button
        self.header_frame = ctk.CTkFrame(self.console_panel, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(15, 5))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        self.console_title = ctk.CTkLabel(self.header_frame, text="Consola de Audios",
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.console_title.grid(row=0, column=0, sticky="w")
        
        self.refresh_button = ctk.CTkButton(self.header_frame, text="⟳", width=30, height=30,
                                          command=self.refresh_audios)
        self.refresh_button.grid(row=0, column=1, padx=(10, 0))

        self.audio_buttons_container = ctk.CTkFrame(self.console_panel, fg_color="transparent")
        self.audio_buttons_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        for i in range(4):
            self.audio_buttons_container.grid_columnconfigure(i, weight=1)

        self.load_existing_audios()

    def refresh_audios(self):
        """Reload all audios from disk"""
        self.stop_current_audio()
        self.load_existing_audios()
    
    def stop_current_audio(self):
        """Stop any currently playing audio and clean up resources"""
        if self.currently_playing:
            try:
                # Detener y descargar la música
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                
                # Esperar un breve momento para liberar recursos
                time.sleep(0.1)
                
                # Reiniciar el mixer para asegurar la liberación del archivo
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                
            except Exception as e:
                print(f"Error al detener audio: {e}")
            
            finally:
                self.currently_playing = None
                self.is_paused = False
                self.paused_position = 0
                if self.after_id:
                    self.after_cancel(self.after_id)
                    self.after_id = None
                
                # Reset buttons on last played frame
                if self.last_played_frame:
                    self.last_played_frame.pause_button.configure(
                        text="⏸️", 
                        command=lambda p=self.last_played_frame: self.pause_audio(p)
                    )
    
    def add_audio_button(self, name, file_path):
        row_count = len(self.audio_buttons_container.grid_slaves()) // 4
        col_count = len(self.audio_buttons_container.grid_slaves()) % 4

        audio_frame = ctk.CTkFrame(self.audio_buttons_container, width=150, height=120,
                                 corner_radius=8, fg_color="#393E46")
        audio_frame.grid(row=row_count, column=col_count, padx=8, pady=8, sticky="nsew")
        audio_frame.grid_propagate(False)
        audio_frame.file_path = file_path

        audio_frame.grid_rowconfigure(0, weight=0)
        audio_frame.grid_rowconfigure(1, weight=1)
        audio_frame.grid_rowconfigure(2, weight=0)
        audio_frame.grid_columnconfigure(0, weight=1)
        audio_frame.grid_columnconfigure(1, weight=0)

        # Audio Name
        name_label = ctk.CTkLabel(audio_frame, text=name, font=ctk.CTkFont(size=12, weight="bold"),
                                wraplength=110)
        name_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="n")

        # Play Button (Always Enabled)
        play_button = ctk.CTkButton(audio_frame, text="▶️",
                                  command=lambda p=audio_frame: self.enqueue_audio(p),
                                  width=120, height=70, corner_radius=5, fg_color="#3498DB")
        play_button.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Pause/Stop Button
        pause_button = ctk.CTkButton(audio_frame, text="⏸️",
                                   command=lambda p=audio_frame: self.pause_audio(p),
                                   width=120, height=20, corner_radius=5, fg_color="#27AE46")
        pause_button.grid(row=2, column=0, padx=5, pady=(0, 5), sticky="nsew")

        # Config Gear Button
        config_button = ctk.CTkButton(audio_frame, text="⚙️",
                                    command=lambda p=audio_frame: self.show_context_menu(p),
                                    width=30, height=30, corner_radius=5)
        config_button.grid(row=0, column=1, padx=5, pady=5, sticky="ne")

        # Store buttons for state management
        audio_frame.play_button = play_button
        audio_frame.pause_button = pause_button

    def enqueue_audio(self, audio_frame):
        """Add audio to queue and play if nothing is playing"""
        file_path = audio_frame.file_path
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"El archivo {os.path.basename(file_path)} no existe.")
            return

        # If the same audio is paused, resume it instead of playing again
        if self.currently_playing == file_path and self.is_paused:
            self.resume_audio(audio_frame)
            return
        
        # Stop current audio if playing
        if pygame.mixer.music.get_busy():
            self.stop_current_audio()
        
        # Play the new audio immediately (no queue in this version)
        self.play_audio_directly(audio_frame)

    def play_audio_directly(self, audio_frame):
        """Play audio immediately (bypassing queue)"""
        file_path = audio_frame.file_path
        try:
            self.stop_current_audio()  # Stop any currently playing audio
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.currently_playing = file_path
            self.last_played_frame = audio_frame
            self.is_paused = False
            self.paused_position = 0
            
            # Update button states
            audio_frame.pause_button.configure(
                text="⏸️", 
                command=lambda p=audio_frame: self.pause_audio(p)
            )
            
            self.monitor_playback()
        except pygame.error as e:
            messagebox.showerror("Error", f"No se pudo reproducir el audio: {e}")
            self.currently_playing = None

    def monitor_playback(self):
        """Check playback status and update UI"""
        if pygame.mixer.music.get_busy():
            self.after_id = self.after(100, self.monitor_playback)
        else:
            # Playback finished
            if self.last_played_frame:
                self.last_played_frame.pause_button.configure(
                    text="⏸️", 
                    command=lambda p=self.last_played_frame: self.pause_audio(p)
                )
            self.currently_playing = None
            self.is_paused = False
            self.paused_position = 0

    def pause_audio(self, audio_frame):
        """Pause current audio"""
        if self.currently_playing == audio_frame.file_path and pygame.mixer.music.get_busy():
            self.paused_position = pygame.mixer.music.get_pos()
            pygame.mixer.music.pause()
            audio_frame.pause_button.configure(
                text="▶️", 
                command=lambda p=audio_frame: self.resume_audio(p)
            )
            self.is_paused = True
            if self.after_id:
                self.after_cancel(self.after_id)
        else:
            messagebox.showwarning("Advertencia", "El audio no está en reproducción.")

    def resume_audio(self, audio_frame):
        """Resume paused audio"""
        if self.currently_playing == audio_frame.file_path and self.is_paused:
            pygame.mixer.music.unpause()
            audio_frame.pause_button.configure(
                text="⏸️", 
                command=lambda p=audio_frame: self.pause_audio(p)
            )
            self.is_paused = False
            self.monitor_playback()
        else:
            messagebox.showwarning("Advertencia", "El audio no está pausado o no puede reanudarse.")

    def show_context_menu(self, audio_frame):
        """Show context menu for audio options"""
        menu = ctk.CTkOptionMenu(self, values=["Eliminar"],
                               command=lambda option: self.delete_audio(audio_frame) if option == "Eliminar" else None)
        menu._dropdown_menu.post(self.winfo_pointerx(), self.winfo_pointery())

    def delete_audio(self, audio_frame):
        """Delete audio file and update UI"""
        file_path = audio_frame.file_path
        
        # Detener y liberar el audio si es el que se está reproduciendo
        if self.currently_playing == file_path:
            self.stop_current_audio()
        
        # Verificar si el archivo existe
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"El archivo {os.path.basename(file_path)} no existe.")
            return

        # Intentar eliminar con múltiples estrategias
        max_attempts = 5
        deleted = False
        
        for attempt in range(max_attempts):
            try:
                # Estrategia 1: Eliminación directa
                os.remove(file_path)
                deleted = True
                break
                
            except PermissionError:
                # Estrategia 2: Forzar liberación de recursos
                try:
                    pygame.mixer.quit()
                    pygame.mixer.init()
                    time.sleep(0.2 * (attempt + 1))  # Espera incremental
                    os.remove(file_path)
                    deleted = True
                    break
                except Exception:
                    continue
                    
            except Exception as e:
                if attempt == max_attempts - 1:  # Último intento
                    messagebox.showerror("Error", 
                        f"No se pudo eliminar el archivo. Error: {str(e)}")
                time.sleep(0.3)
                continue

        if deleted:
            # Actualizar la lista de audios y la interfaz
            self.app.audios = [audio for audio in self.app.audios if audio["file_path"] != file_path]
            self.load_existing_audios()
            messagebox.showinfo("Éxito", "Audio eliminado correctamente")

    def load_existing_audios(self):
        """Load all audio files from data directory"""
        # Clear current buttons
        for widget in self.audio_buttons_container.winfo_children():
            widget.destroy()

        # Load from data directory
        data_dir = resource_path("data")
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.lower().endswith(('.wav', '.mp3')):
                    file_path = os.path.join(data_dir, filename)
                    name = os.path.splitext(filename)[0]
                    
                    # Add to app's audio list if not already there
                    if not any(a["file_path"] == file_path for a in self.app.audios):
                        self.app.audios.append({
                            "name": name, 
                            "file_path": file_path, 
                            "description": ""
                        })

        # Create buttons for each audio
        for audio in self.app.audios:
            if os.path.exists(audio["file_path"]):
                self.add_audio_button(audio["name"], audio["file_path"])

def is_file_locked(self, filepath):
    """Check if a file is locked by another process"""
    try:
        with open(filepath, 'rb+') as f:
            pass
        return False
    except IOError:
        return True