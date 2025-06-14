import tkinter as tk
from tkinter import filedialog, messagebox, ttk, DISABLED, NORMAL
from PIL import Image, ImageTk
import cv2
import numpy as np
from inpainting import inpainting_criminisi
import threading

class ImageAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Création du Masque")
        self.root.configure(bg='#ffffff')  # Fond blanc
        
        # Configuration des couleurs
        self.colors = {
            'primary': '#2196F3',      # Bleu principal
            'primary_dark': '#1976D2',  # Bleu foncé
            'accent': '#FF4081',       # Rose accent
            'text': '#212121',         # Texte principal
            'text_light': '#757575',   # Texte secondaire
            'background': '#ffffff',   # Fond blanc
            'surface': '#f5f5f5',      # Surface gris clair
            'border': '#e0e0e0'        # Bordure grise
        }
        
        # Variables de zoom
        self.zoom_factor = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.zoom_step = 0.1
        
        # Configuration du style
        self.style = ttk.Style()
        self.style.configure('Modern.TButton', 
                           padding=10, 
                           font=('Segoe UI', 10),
                           background=self.colors['primary'])
        
        # Variables
        self.image = None
        self.photo = None
        self.mask = None
        self.points = []
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.current_mode = tk.StringVar(value="continuous")
        self.temp_line = None
        self.polygon_lines = []
        self.continuous_lines = []  # Pour stocker les lignes du mode continu
        self.mask_validated = False
        
        # Barre de progression pour l'inpainting
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        
        # Création de l'interface
        self.create_widgets()
        
    def create_widgets(self):
        # Header moderne avec ombre
        header = tk.Frame(self.root, bg='#f8fafc', height=60, highlightbackground='#e0e0e0', highlightthickness=1)
        header.pack(fill=tk.X, side=tk.TOP)
        title_label = tk.Label(header, text="Création du mask + Inpainting", font=('Segoe UI', 26, 'bold'), bg='#f8fafc', fg='#222', pady=10)
        title_label.pack(pady=5, side=tk.TOP, expand=True)
        # Bouton Reset en haut à droite
        reset_btn = tk.Button(header, text="Reset", font=('Segoe UI', 11, 'bold'), bg=self.colors['accent'], fg='white', padx=18, pady=7, borderwidth=0, relief='flat', cursor='hand2', activebackground='#e91e63', activeforeground='white', highlightthickness=0, command=self.reset_all)
        reset_btn.pack(side=tk.RIGHT, padx=18, pady=10)
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(bg='#e91e63'))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(bg=self.colors['accent']))

        # Frame principale avec padding et fond moderne
        self.main_frame = tk.Frame(self.root, bg='#f4f6fb', padx=30, pady=30)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame pour le canvas et le masque avec ombre et coins arrondis
        canvas_frame = tk.Frame(self.main_frame, bg='#f4f6fb', highlightbackground='#e0e0e0', highlightthickness=2, bd=0)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame pour l'image originale et le masque validé
        self.image_and_mask_frame = tk.Frame(canvas_frame, bg='#f4f6fb')
        self.image_and_mask_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ajout des scrollbars
        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas pour l'image dans une card
        image_card = tk.Frame(self.image_and_mask_frame, bg='white', bd=0, highlightbackground='#d1d5db', highlightthickness=2)
        image_card.pack(side=tk.LEFT, padx=20, pady=10)
        self.canvas = tk.Canvas(image_card, bg='white', highlightthickness=0, xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        # Card pour l'aperçu du masque validé
        mask_card = tk.Frame(self.image_and_mask_frame, bg='white', bd=0, highlightbackground='#d1d5db', highlightthickness=2)
        mask_card.pack(side=tk.LEFT, padx=20, pady=10)
        self.mask_preview_label = tk.Label(mask_card, bg='white', anchor='n')
        self.mask_preview_label.pack(padx=8, pady=8)

        # Card pour les KPI/statistiques
        kpi_card = tk.Frame(self.main_frame, bg='white', bd=0, highlightbackground='#d1d5db', highlightthickness=2)
        kpi_card.pack(side=tk.RIGHT, padx=20, pady=10, anchor='n')
        kpi_title = tk.Label(kpi_card, text="Statistiques", font=('Segoe UI', 13, 'bold'), bg='white', fg=self.colors['primary'])
        kpi_title.pack(pady=(10, 5))
        self.kpi_time = tk.Label(kpi_card, text="⏱ Temps d'exécution : -", font=('Segoe UI', 11), bg='white', fg='#222')
        self.kpi_time.pack(anchor='w', padx=12, pady=2)
        self.kpi_pixels = tk.Label(kpi_card, text="🟦 Taux de pixels remplis : -", font=('Segoe UI', 11), bg='white', fg='#222')
        self.kpi_pixels.pack(anchor='w', padx=12, pady=2)
        self.kpi_iter = tk.Label(kpi_card, text="🔁 Nombre d'itérations : -", font=('Segoe UI', 11), bg='white', fg='#222')
        self.kpi_iter.pack(anchor='w', padx=12, pady=2)
        # Variables d'état pour les KPI
        self.kpi_total_time = None
        self.kpi_nb_iter = None
        self.kpi_pixel_rate = None

        # Frame pour les contrôles avec style moderne
        controls_frame = tk.Frame(self.main_frame, bg='#f4f6fb')
        controls_frame.pack(fill=tk.X, pady=25)

        # Frame pour les modes de sélection
        mode_frame = tk.Frame(controls_frame, bg='#f4f6fb')
        mode_frame.pack(side=tk.LEFT, padx=10)
        mode_label = tk.Label(mode_frame, text="Mode de sélection :", font=('Segoe UI', 11), bg='#f4f6fb', fg='#222')
        mode_label.pack(side=tk.LEFT, padx=5)

        # --- NOUVEAU : Boutons personnalisés avec animation ---
        self.selection_mode = tk.StringVar(value="continuous")
        def animate_button(btn, from_color, to_color, steps=8, step=0):
            if step > steps:
                btn.config(bg=to_color)
                return
            r1, g1, b1 = self.root.winfo_rgb(from_color)
            r2, g2, b2 = self.root.winfo_rgb(to_color)
            r = int(r1 + (r2 - r1) * step / steps) // 256
            g = int(g1 + (g2 - g1) * step / steps) // 256
            b = int(b1 + (b2 - b1) * step / steps) // 256
            color = f'#{r:02x}{g:02x}{b:02x}'
            btn.config(bg=color)
            self.root.after(15, lambda: animate_button(btn, from_color, to_color, steps, step+1))

        def select_mode(mode):
            self.selection_mode.set(mode)
            # Animation et style
            if mode == "continuous":
                animate_button(continuous_btn, "#e0e7ef", self.colors['primary'])
                animate_button(polygon_btn, self.colors['primary'], "#e0e7ef")
                continuous_btn.config(fg="white", font=('Segoe UI', 11, 'bold'), relief='sunken', bd=0)
                polygon_btn.config(fg="#222", font=('Segoe UI', 11), relief='flat', bd=0)
            else:
                animate_button(polygon_btn, "#e0e7ef", self.colors['primary'])
                animate_button(continuous_btn, self.colors['primary'], "#e0e7ef")
                polygon_btn.config(fg="white", font=('Segoe UI', 11, 'bold'), relief='sunken', bd=0)
                continuous_btn.config(fg="#222", font=('Segoe UI', 11), relief='flat', bd=0)
            self.current_mode.set(mode)
            self.on_mode_change()

        btn_style = {
            'relief': 'flat',
            'bd': 0,
            'width': 18,
            'height': 2,
            'font': ('Segoe UI', 11),
            'bg': '#e0e7ef',
            'fg': '#222',
            'activebackground': self.colors['primary_dark'],
            'activeforeground': 'white',
            'cursor': 'hand2',
            'highlightthickness': 0
        }
        continuous_btn = tk.Button(mode_frame, text="Dessin continu", command=lambda: select_mode("continuous"), **btn_style)
        polygon_btn = tk.Button(mode_frame, text="Polygone par points", command=lambda: select_mode("polygon"), **btn_style)
        continuous_btn.pack(side=tk.LEFT, padx=(10, 0))
        polygon_btn.pack(side=tk.LEFT, padx=(10, 0))
        # Arrondi visuel (simulé par padding et couleur)
        continuous_btn.config(overrelief='ridge')
        polygon_btn.config(overrelief='ridge')
        # Effet de survol
        def on_enter(btn):
            if self.selection_mode.get() == "continuous" and btn == continuous_btn:
                return
            if self.selection_mode.get() == "polygon" and btn == polygon_btn:
                return
            btn.config(bg="#dbeafe")
        def on_leave(btn):
            if self.selection_mode.get() == "continuous" and btn == continuous_btn:
                btn.config(bg=self.colors['primary'])
            elif self.selection_mode.get() == "polygon" and btn == polygon_btn:
                btn.config(bg=self.colors['primary'])
            else:
                btn.config(bg="#e0e7ef")
        continuous_btn.bind('<Enter>', lambda e: on_enter(continuous_btn))
        continuous_btn.bind('<Leave>', lambda e: on_leave(continuous_btn))
        polygon_btn.bind('<Enter>', lambda e: on_enter(polygon_btn))
        polygon_btn.bind('<Leave>', lambda e: on_leave(polygon_btn))
        # --- FIN NOUVEAU ---

        # Frame pour les boutons
        self.button_frame = tk.Frame(controls_frame, bg='#f4f6fb')
        self.button_frame.pack(side=tk.RIGHT)
        button_style = {
            'font': ('Segoe UI', 11, 'bold'),
            'bg': self.colors['primary'],
            'fg': 'white',
            'padx': 24,
            'pady': 12,
            'borderwidth': 0,
            'relief': 'flat',
            'cursor': 'hand2',
            'activebackground': self.colors['primary_dark'],
            'activeforeground': 'white',
            'highlightthickness': 0
        }
        # Boutons stylisés et arrondis
        self.load_button = tk.Button(self.button_frame, text="Charger Image", command=self.load_image, **button_style)
        self.load_button.pack(side=tk.LEFT, padx=8)
        self.clear_button = tk.Button(self.button_frame, text="Effacer Sélection", command=self.clear_selection, **button_style)
        self.clear_button.pack(side=tk.LEFT, padx=8)
        self.validate_button = tk.Button(self.button_frame, text="Valider le masque", command=self.validate_mask, **button_style)
        self.validate_button.pack(side=tk.LEFT, padx=8)
        self.download_mask_button = tk.Button(self.button_frame, text="Télécharger le masque", command=self.save_mask, **button_style)
        self.download_mask_button.pack(side=tk.LEFT, padx=8)
        self.inpaint_button = tk.Button(self.button_frame, text="Inpainting", command=self.run_inpainting, **button_style, state=DISABLED)
        self.inpaint_button.pack(side=tk.LEFT, padx=8)
        self.back_button = tk.Button(self.button_frame, text="Retour", command=self.remove_last_point, **button_style)
        self.back_button.pack(side=tk.LEFT, padx=8)
        self.back_button.pack_forget()
        # Effet hover pour tous les boutons
        for button in [self.load_button, self.clear_button, self.validate_button, self.download_mask_button, self.inpaint_button, self.back_button]:
            button.bind('<Enter>', lambda e, b=button: b.configure(bg=self.colors['primary_dark']))
            button.bind('<Leave>', lambda e, b=button: b.configure(bg=self.colors['primary']))

        # NOUVEAU : Frame pour la taille du patch sur une nouvelle ligne
        patch_line = tk.Frame(self.main_frame, bg='#f4f6fb')
        patch_line.pack(fill=tk.X, pady=(0, 10))
        patch_frame = tk.Frame(patch_line, bg='#f4f6fb')
        patch_frame.pack(anchor='w', padx=30)
        patch_label = tk.Label(patch_frame, text="Taille du patch :", font=('Segoe UI', 11), bg='#f4f6fb', fg='#222')
        patch_label.pack(side=tk.LEFT, padx=(0, 5))
        self.patch_mode = tk.StringVar(value="auto")
        patch_auto_btn = tk.Radiobutton(patch_frame, text="Automatique", variable=self.patch_mode, value="auto", font=('Segoe UI', 10), bg='#f4f6fb', fg='#222', selectcolor='#f4f6fb', activebackground='#e3eafc', command=lambda: toggle_patch_mode_patch())
        patch_manual_btn = tk.Radiobutton(patch_frame, text="Manuel", variable=self.patch_mode, value="manual", font=('Segoe UI', 10), bg='#f4f6fb', fg='#222', selectcolor='#f4f6fb', activebackground='#e3eafc', command=lambda: toggle_patch_mode_patch())
        patch_auto_btn.pack(side=tk.LEFT)
        patch_manual_btn.pack(side=tk.LEFT)
        self.patch_manual_value = tk.StringVar(value="21")
        self.patch_entry = tk.Entry(patch_frame, textvariable=self.patch_manual_value, width=5, font=('Segoe UI', 11), state='disabled', justify='center')
        self.patch_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.patch_min = 7
        self.patch_max = 99  # valeur large par défaut, pas de dépendance à l'image
        # Fonction de validation (appelée à la demande)
        def validate_patch_value():
            try:
                val = int(self.patch_manual_value.get())
            except Exception:
                self.status_bar.config(text="Veuillez entrer un nombre entier pour la taille du patch.")
                return False
            if val <= 0:
                self.status_bar.config(text="La taille du patch doit être positive.")
                return False
            if val % 2 == 0:
                self.status_bar.config(text="La taille du patch doit être un nombre impair.")
                return False
            # Limite dynamique : 50% de la largeur de l'image si image chargée
            if self.image is not None:
                max_patch = int(self.image.shape[1] * 0.5)
                if val > max_patch:
                    self.status_bar.config(text=f"Taille du patch trop grande (max {max_patch})")
                    return False
            self.status_bar.config(text="Taille du patch valide.")
            return True
        self.validate_patch_value = validate_patch_value
        # On ne fait plus de correction automatique dans le trace
        def on_patch_entry_focus_out(event):
            self.validate_patch_value()
        self.patch_entry.bind('<FocusOut>', on_patch_entry_focus_out)
        def toggle_patch_mode_patch():
            if self.patch_mode.get() == "auto":
                self.patch_entry.config(state='disabled')
            else:
                self.patch_entry.config(state='normal')
                self.validate_patch_value()
        self.toggle_patch_mode_patch = toggle_patch_mode_patch
        self.patch_manual_value.trace_add('write', lambda *args: self.validate_patch_value())
        self.toggle_patch_mode_patch()

        # Barre de statut stylisée
        self.status_bar = tk.Label(self.root, text="Prêt", bd=0, relief=tk.FLAT, anchor=tk.W, bg='#e0e7ef', fg='#222', font=('Segoe UI', 10), padx=12, pady=7, highlightbackground='#d1d5db', highlightthickness=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # Barre de progression pour l'inpainting
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        
        # Sélection initiale du mode (doit être APRES la création de status_bar)
        select_mode("continuous")
        
        # Bind des événements
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.canvas.bind("<Motion>", self.update_preview)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        # Déplacement par clic droit
        self.canvas.bind("<ButtonPress-3>", self.pan_start)
        self.canvas.bind("<B3-Motion>", self.pan_move)
        self.canvas.bind("<ButtonRelease-3>", self.pan_end)
        
    def on_mode_change(self):
        # Réinitialiser l'état
        self.clear_selection()
        
        # Afficher ou cacher le bouton retour selon le mode
        if self.current_mode.get() == "polygon":
            self.back_button.pack(side=tk.LEFT, padx=5)
        else:
            self.back_button.pack_forget()
        
    def remove_last_point(self):
        if self.current_mode.get() == "polygon" and len(self.points) > 0:
            # Supprimer le dernier point
            self.points.pop()
            
            # Supprimer la dernière ligne
            if self.polygon_lines:
                self.canvas.delete(self.polygon_lines.pop())
            
            # Supprimer la ligne de prévisualisation
            if self.temp_line:
                self.canvas.delete(self.temp_line)
                self.temp_line = None
            
            # Mettre à jour le statut
            if len(self.points) > 0:
                self.status_bar.config(text=f"Point {len(self.points)} supprimé")
            else:
                self.status_bar.config(text="Tous les points ont été supprimés")
                self.drawing = False
            
            # Mettre à jour le masque
            self.update_mask()
        
    def canvas_to_image_coords(self, x, y):
        # Convertit des coordonnées canvas vers image d'origine
        img_x = int((x - self.image_offset_x) / (self.image_scale * self.zoom_factor))
        img_y = int((y - self.image_offset_y) / (self.image_scale * self.zoom_factor))
        return img_x, img_y

    def image_to_canvas_coords(self, x, y):
        # Convertit des coordonnées image d'origine vers canvas
        canvas_x = int(x * self.image_scale * self.zoom_factor + self.image_offset_x)
        canvas_y = int(y * self.image_scale * self.zoom_factor + self.image_offset_y)
        return canvas_x, canvas_y

    def start_draw(self, event):
        if self.current_mode.get() == "continuous":
            self.drawing = True
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            self.last_x, self.last_y = event.x, event.y
            self.points = [(img_x, img_y)]
            self.continuous_lines = []
            self.status_bar.config(text="Dessin en cours...")
        else:  # Mode polygone
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            if not self.drawing:
                self.drawing = True
                self.points = [(img_x, img_y)]
                self.status_bar.config(text="Premier point ajouté")
            else:
                self.points.append((img_x, img_y))
                if len(self.points) > 1:
                    x1, y1 = self.image_to_canvas_coords(*self.points[-2])
                    x2, y2 = self.image_to_canvas_coords(*self.points[-1])
                    line = self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True)
                    self.polygon_lines.append(line)
                self.status_bar.config(text=f"Point {len(self.points)} ajouté")
            
    def draw(self, event):
        if self.current_mode.get() == "continuous" and self.drawing:
            img_x, img_y = self.canvas_to_image_coords(event.x, event.y)
            x1, y1 = self.last_x, self.last_y
            x2, y2 = event.x, event.y
            self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True)
            self.points.append((img_x, img_y))
            self.last_x, self.last_y = event.x, event.y
            
    def update_preview(self, event):
        if self.current_mode.get() == "polygon" and len(self.points) > 0:
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            x1, y1 = self.image_to_canvas_coords(*self.points[-1])
            self.temp_line = self.canvas.create_line(x1, y1, event.x, event.y, fill=self.colors['accent'], width=2, smooth=True, dash=(4, 4))
            
    def stop_draw(self, event):
        if self.current_mode.get() == "continuous" and self.drawing:
            self.drawing = False
            # Fermer visuellement le masque
            if len(self.points) > 2:
                x1, y1 = self.image_to_canvas_coords(*self.points[-1])
                x2, y2 = self.image_to_canvas_coords(*self.points[0])
                self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True, tags="lines")
            self.update_mask()
            self.status_bar.config(text="Sélection terminée")
        elif self.current_mode.get() == "polygon" and self.drawing:
            self.update_mask()
            self.status_bar.config(text="Point ajouté")
            
    def update_mask(self):
        if self.image is None or not self.points:
            return
        self.mask = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint8)
        closed_points = self.points[:]
        # Toujours fermer le polygone en mode polygone
        if self.current_mode.get() == "polygon" and len(closed_points) > 2 and closed_points[0] != closed_points[-1]:
            closed_points.append(closed_points[0])
        # En mode continu, la fermeture est déjà gérée
        scaled_points = []
        for x, y in closed_points:
            original_x = int(x)
            original_y = int(y)
            scaled_points.append([original_x, original_y])
        points = np.array(scaled_points, np.int32)
        cv2.fillPoly(self.mask, [points], 255)
        
    def save_mask(self):
        if self.mask is None:
            messagebox.showwarning("Attention", "Aucun masque à sauvegarder")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )
        
        if file_path:
            cv2.imwrite(file_path, self.mask)
            messagebox.showinfo("Succès", "Masque sauvegardé avec succès")
            self.status_bar.config(text=f"Masque sauvegardé: {file_path}")
            
    def clear_selection(self):
        self.points = []
        self.polygon_lines = []
        self.continuous_lines = []
        self.drawing = False
        self.mask = np.zeros_like(self.mask) if self.mask is not None else None
        self.canvas.delete("all")
        self.display_image()
        self.status_bar.config(text="Sélection effacée")
        
    def on_resize(self, event):
        self.display_image()
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.image = cv2.imread(file_path)
            if self.image is None:
                messagebox.showerror("Erreur", "Impossible de charger l'image")
                return
                
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.mask = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint8)
            self.display_image()
            self.status_bar.config(text=f"Image chargée: {file_path}")
            
    def display_image(self):
        if self.image is None:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width > 1 and canvas_height > 1:
            img_height, img_width = self.image.shape[:2]
            base_scale = min(canvas_width/img_width, canvas_height/img_height)
            scale = base_scale * self.zoom_factor
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            resized = cv2.resize(self.image, (new_width, new_height))
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(resized))
            # Afficher l'image à l'origine du canvas (0,0)
            x, y = 0, 0
            self.canvas.delete("all")
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            self.image_offset_x = x
            self.image_offset_y = y
            self.image_scale = base_scale
            # Redessiner les points et les lignes existants
            self.redraw_points_and_lines()
            # Adapter la zone scrollable exactement à la taille de l'image zoomée
            self.canvas.config(scrollregion=(0, 0, new_width, new_height))
            
    def redraw_points_and_lines(self):
        self.canvas.delete("lines")
        if not self.points:
            return
        # Redessiner les lignes du polygone ou du tracé continu
        for i in range(len(self.points) - 1):
            x1, y1 = self.image_to_canvas_coords(*self.points[i])
            x2, y2 = self.image_to_canvas_coords(*self.points[i + 1])
            self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True, tags="lines")
        # Fermer la boucle visuellement si besoin
        if self.current_mode.get() == "continuous" and len(self.points) > 2:
            x1, y1 = self.image_to_canvas_coords(*self.points[-1])
            x2, y2 = self.image_to_canvas_coords(*self.points[0])
            self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True, tags="lines")
        elif self.current_mode.get() == "polygon" and len(self.points) > 2 and self.points[0] == self.points[-1]:
            x1, y1 = self.image_to_canvas_coords(*self.points[-1])
            x2, y2 = self.image_to_canvas_coords(*self.points[0])
            self.canvas.create_line(x1, y1, x2, y2, fill=self.colors['accent'], width=2, smooth=True, tags="lines")
            
    def on_mousewheel(self, event):
        # Déterminer la direction du zoom
        if event.num == 5 or event.delta < 0:  # Zoom out
            self.zoom_factor = max(self.min_zoom, self.zoom_factor - self.zoom_step)
        elif event.num == 4 or event.delta > 0:  # Zoom in
            self.zoom_factor = min(self.max_zoom, self.zoom_factor + self.zoom_step)
            
        # Mettre à jour l'affichage
        self.display_image()
        # Mettre à jour le masque avec les nouvelles coordonnées
        self.update_mask()
        self.status_bar.config(text=f"Zoom: {int(self.zoom_factor * 100)}%")

    def pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor="fleur")

    def pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def pan_end(self, event):
        self.canvas.config(cursor="") 

    def validate_mask(self):
        if self.image is None or self.mask is None or not np.any(self.mask):
            self.status_bar.config(text="Veuillez charger une image et tracer un masque avant de valider.")
            return
        self.mask_validated = True
        self.inpaint_button.config(state=NORMAL)
        self.status_bar.config(text="Masque validé. Vous pouvez lancer l'inpainting.")
        # Affiche le masque validé à droite de l'image originale
        self.update_mask_preview()
        # Calcul du taux de pixels remplis
        total_pixels = self.mask.size
        filled_pixels = np.sum(self.mask == 255)
        self.kpi_pixel_rate = filled_pixels / total_pixels * 100
        self.kpi_pixels.config(text=f"🟦 Taux de pixels remplis : {self.kpi_pixel_rate:.2f} %")
        # Mise à jour de la borne max du patch
        min_dim = min(self.image.shape[:2])
        self.patch_max = int(min_dim * 0.3)
        if self.patch_max % 2 == 0:
            self.patch_max -= 1
        if int(self.patch_manual_value.get()) > self.patch_max:
            self.patch_manual_value.set(str(self.patch_max))
        self.patch_entry.config(state='normal' if not self.patch_mode.get() == "auto" else 'disabled')
        self.toggle_patch_mode_patch()

    def update_mask_preview(self):
        from PIL import ImageTk, Image
        mask_visu = self.mask.copy()
        mask_pil = Image.fromarray(mask_visu)
        # Récupérer la taille d'affichage réelle de l'image sur le canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_height, img_width = self.image.shape[:2]
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        # Redimensionner le masque à la même taille que l'image affichée
        mask_pil = mask_pil.resize((new_width, new_height))
        mask_tk = ImageTk.PhotoImage(mask_pil)
        self.mask_preview_label.configure(image=mask_tk, width=new_width, height=new_height)
        self.mask_preview_label.image = mask_tk

    def run_inpainting(self):
        if not self.mask_validated:
            self.status_bar.config(text="Veuillez d'abord valider le masque.")
            return
        if self.image is None or self.mask is None or not np.any(self.mask):
            self.status_bar.config(text="Veuillez charger une image et tracer un masque avant l'inpainting.")
            return
        self.status_bar.config(text="Inpainting en cours...")
        self.progress_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress_bar.start(10)
        # Ouvre la fenêtre d'aperçu temps réel
        self.open_inpaint_preview_window()
        # Déterminer la taille du patch
        if self.patch_mode.get() == "auto":
            patch_size = 21
        else:
            if not self.validate_patch_value():
                return
            patch_size = int(self.patch_manual_value.get())
        # Lancer l'inpainting dans un thread séparé
        threading.Thread(target=lambda: self._inpainting_thread(patch_size), daemon=True).start()

    def open_inpaint_preview_window(self):
        from PIL import ImageTk, Image
        self.inpaint_preview_win = tk.Toplevel(self.root)
        self.inpaint_preview_win.title("Aperçu Inpainting en temps réel")
        self.inpaint_preview_win.configure(bg=self.colors['background'])
        self.inpaint_preview_label = tk.Label(self.inpaint_preview_win, bg=self.colors['background'])
        self.inpaint_preview_label.pack(padx=10, pady=10, expand=True)
        self.inpaint_preview_imgtk = None

    def _inpainting_thread(self, patch_size):
        import cv2
        import time
        try:
            image_rgb = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR) if self.image.shape[2] == 3 else self.image.copy()
            mask_uint8 = self.mask.copy()
            # Appel modifié pour passer la taille du patch
            result, nb_iter, total_time = inpainting_criminisi(
                image_rgb, mask_uint8, patch_size=patch_size, verbose=False,
                progress_callback=self._inpainting_progress_callback)
            self.kpi_total_time = total_time
            self.kpi_nb_iter = nb_iter
            self.root.after(0, lambda: self._inpainting_done(result))
        except Exception as e:
            self.root.after(0, lambda: self._inpainting_error(str(e)))

    def _inpainting_progress_callback(self, img, iteration=None, elapsed=None):
        from PIL import ImageTk, Image
        # Taille cible pour affichage (80% de la largeur/hauteur de l'écran)
        screen_w = self.inpaint_preview_win.winfo_screenwidth()
        screen_h = self.inpaint_preview_win.winfo_screenheight()
        target_w = int(screen_w * 0.6)
        target_h = int(screen_h * 0.7)
        # Conversion pour affichage
        if img.shape[2] == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img
        img_pil = Image.fromarray(img_rgb)
        # Redimensionnement pour occuper la fenêtre (en gardant le ratio)
        ratio = min(target_w / img_pil.width, target_h / img_pil.height, 1)
        new_w = int(img_pil.width * ratio)
        new_h = int(img_pil.height * ratio)
        img_pil = img_pil.resize((new_w, new_h))
        img_tk = ImageTk.PhotoImage(img_pil)
        def update():
            self.inpaint_preview_label.configure(image=img_tk, width=new_w, height=new_h)
            self.inpaint_preview_label.image = img_tk
            self.inpaint_preview_win.geometry(f"{new_w+40}x{new_h+100}")
            # Mise à jour live des KPI si info fournie
            if iteration is not None:
                self.kpi_iter.config(text=f"🔁 Nombre d'itérations : {iteration}")
            if elapsed is not None:
                self.kpi_time.config(text=f"⏱ Temps d'exécution : {elapsed:.2f} s")
        self.root.after(0, update)

    def _inpainting_done(self, result):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.show_inpaint_result(result)
        self.status_bar.config(text="Inpainting terminé !")
        # Affichage final des KPI
        if self.kpi_total_time is not None:
            self.kpi_time.config(text=f"⏱ Temps d'exécution : {self.kpi_total_time:.2f} s")
        if self.kpi_nb_iter is not None:
            self.kpi_iter.config(text=f"🔁 Nombre d'itérations : {self.kpi_nb_iter}")

    def _inpainting_error(self, msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_bar.config(text=f"Erreur inpainting : {msg}")

    def show_inpaint_result(self, result):
        win = tk.Toplevel(self.root)
        win.title("Résultat Inpainting")
        win.configure(bg=self.colors['background'])
        # Taille cible pour affichage (80% de la largeur/hauteur de l'écran)
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        target_w = int(screen_w * 0.6)
        target_h = int(screen_h * 0.7)
        # Conversion pour affichage
        if result.shape[2] == 3:
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        else:
            result_rgb = result
        img_pil = Image.fromarray(result_rgb)
        # Redimensionnement pour occuper la fenêtre (en gardant le ratio)
        ratio = min(target_w / img_pil.width, target_h / img_pil.height, 1)
        new_w = int(img_pil.width * ratio)
        new_h = int(img_pil.height * ratio)
        img_pil = img_pil.resize((new_w, new_h))
        img_tk = ImageTk.PhotoImage(img_pil)
        label = tk.Label(win, image=img_tk, bg=self.colors['background'])
        label.image = img_tk
        label.pack(padx=10, pady=10, expand=True)
        win.geometry(f"{new_w+40}x{new_h+100}")
        # Bouton pour télécharger l'image inpaintée
        def save_inpainted():
            from tkinter import filedialog, messagebox
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            if file_path:
                img_pil.save(file_path)
                messagebox.showinfo("Succès", f"Image inpaintée sauvegardée : {file_path}")
        save_btn = tk.Button(win, text="Télécharger l'image inpaintée", command=save_inpainted,
                             font=('Segoe UI', 10), bg=self.colors['primary'], fg='white', padx=20, pady=10,
                             borderwidth=0, relief='flat', cursor='hand2')
        save_btn.pack(pady=(0, 15))

    def reset_all(self):
        # Réinitialise tout : image, masque, points, KPI, interface
        self.image = None
        self.photo = None
        self.mask = None
        self.points = []
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.temp_line = None
        self.polygon_lines = []
        self.continuous_lines = []
        self.mask_validated = False
        self.canvas.delete('all')
        self.mask_preview_label.config(image='', width=1, height=1)
        self.kpi_time.config(text="⏱ Temps d'exécution : -")
        self.kpi_pixels.config(text="🟦 Taux de pixels remplis : -")
        self.kpi_iter.config(text="🔁 Nombre d'itérations : -")
        self.patch_mode.set("auto")
        self.patch_manual_value.set("21")
        self.patch_entry.config(state='disabled')
        self.status_bar.config(text="Prêt")
        self.inpaint_button.config(state=DISABLED)
        self.toggle_patch_mode_patch() 