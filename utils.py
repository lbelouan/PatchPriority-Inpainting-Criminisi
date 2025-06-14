import numpy as np
import cv2
import matplotlib.pyplot as plt

def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image non trouvée: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def load_mask(path):
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"Masque non trouvé: {path}")
    _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    return binary_mask

def show_image_and_mask(image, mask):
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(image)
    axes[0].set_title("Image")
    axes[0].axis("off")
    axes[1].imshow(mask, cmap='gray')
    axes[1].set_title("Masque")
    axes[1].axis("off")
    plt.show()

def show_image(image, title="Image"):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)
    ax.set_title(title)
    ax.axis("off")
    plt.show() 