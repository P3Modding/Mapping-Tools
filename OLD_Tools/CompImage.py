import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

class MapOverlayApp:
    def __init__(self, root, bg_border=64):
        self.root = root
        self.root.title("Mappa Sovrapposta con Opacità Regolabile")
        
        # Imposta la dimensione massima della finestra a 1920x1080
        self.screen_width = 1080
        self.screen_height = 850
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.root.resizable(False, False)   

        # 🔹 Seleziona i file da aprire
        background_path = filedialog.askopenfilename(
            title="Seleziona immagine di sfondo",
            filetypes=[("Immagini", "*.bmp;*.png;*.jpg;*.jpeg;*.tif;*.tiff")]
        )
        overlay_path = filedialog.askopenfilename(
            title="Seleziona immagine overlay",
            filetypes=[("Immagini", "*.bmp;*.png;*.jpg;*.jpeg;*.tif;*.tiff")]
        )

        # Carica le immagini
        self.background = Image.open(background_path)
        self.overlay = Image.open(overlay_path)

        # Calcola le dimensioni UTILI della mappa grande (senza bordi)
        self.bg_border = bg_border
        bg_usable_width = self.background.width - 2 * bg_border
        bg_usable_height = self.background.height - 2 * bg_border

        # Ridimensiona l'overlay per adattarlo all'area utile
        self.overlay = self.overlay.resize((bg_usable_width, bg_usable_height), Image.NEAREST)

        # Ridimensiona lo sfondo per adattarlo alla finestra (mantenendo aspect ratio)
        bg_ratio = min(
            self.screen_width / self.background.width,
            self.screen_height / self.background.height
        )
        self.bg_display_width = int(self.background.width * bg_ratio)
        self.bg_display_height = int(self.background.height * bg_ratio)
        self.background_display = self.background.resize(
            (self.bg_display_width, self.bg_display_height), Image.LANCZOS
        )

        # Ridimensiona anche l'overlay in proporzione
        overlay_ratio = bg_ratio
        self.overlay_display = self.overlay.resize(
            (int(bg_usable_width * overlay_ratio), int(bg_usable_height * overlay_ratio)),
            Image.NEAREST
        )

        # Calcola la posizione dell'overlay (scalata)
        self.overlay_pos = (
            int(bg_border * overlay_ratio),
            int(bg_border * overlay_ratio)
        )

        # Crea la Label per l'immagine
        self.image_label = tk.Label(root)
        self.image_label.pack()

        # Imposta opacità iniziale al 50%
        self.composite = self.background_display.copy()
        self.update_overlay(opacity=0.5)

        # Slider per regolare l'opacità
        self.opacity_slider = ttk.Scale(
            root,
            from_=0.0,
            to=1.0,
            value=0.5,
            command=self.on_slider_change
        )
        self.opacity_slider.pack(fill=tk.X, padx=10, pady=10)

    def update_overlay(self, opacity):
        """Sovrappone l'immagine con opacità regolabile"""
        overlay_rgba = self.overlay_display.convert("RGBA")
        overlay_rgba.putalpha(int(opacity * 255))  # Imposta trasparenza

        # Incolla l'overlay sulla mappa grande
        self.composite = self.background_display.copy()
        self.composite.paste(overlay_rgba, self.overlay_pos, overlay_rgba)

        # Aggiorna l'immagine visualizzata
        self.tk_image = ImageTk.PhotoImage(self.composite)
        self.image_label.config(image=self.tk_image)

    def on_slider_change(self, value):
        """Aggiorna l'opacità quando lo slider viene mosso"""
        self.update_overlay(float(value))

if __name__ == "__main__":
    root = tk.Tk()
    app = MapOverlayApp(root, bg_border=64)
    root.mainloop()
