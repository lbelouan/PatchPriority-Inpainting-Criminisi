import tkinter as tk
from image_annotator import ImageAnnotator

def main():
    root = tk.Tk()
    app = ImageAnnotator(root)
    
    # Configurer la gestion du redimensionnement
    root.bind("<Configure>", app.on_resize)
    
    # Définir la taille minimale de la fenêtre
    root.minsize(800, 600)
    
    root.mainloop()

if __name__ == "__main__":
    main() 