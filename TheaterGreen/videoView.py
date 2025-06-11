import customtkinter as ctk

class VideoView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent") # Hace que el fondo del frame sea transparente

        # Configuración de la cuadrícula
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="¡Bienvenido a la Vista de Video!",
                                  font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20)

        self.info_label = ctk.CTkLabel(self, text="Aquí irán los controles y visualización de video.")
        self.info_label.grid(row=1, column=0, padx=20, pady=10)