# inpainting.py
import numpy as np
import cv2
import time

def get_patch(image, centre, taille):
    x, y = centre
    demi = taille // 2
    h, w = image.shape[:2]
    xgauche = max(x - demi, 0)
    xdroit  = min(x + demi + 1, w)
    ygauche = max(y - demi, 0)
    ydroit  = min(y + demi + 1, h)
    patch = image[ygauche:ydroit, xgauche:xdroit]
    return patch

def get_fill_front(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    front_points = []
    for contour in contours:
        for point in contour:
            x, y = point[0]
            front_points.append((x, y))
    return front_points

def initialize_confidence(mask):
    confidence = np.where(mask == 0, 1.0, 0.0).astype(np.float32)
    return confidence

def calcul_Cp(confidence_map, p, patch_size=9):
    patch = get_patch(confidence_map, p, patch_size)
    if patch is None:
        return 0
    Cp = np.mean(patch)
    return Cp

def calcul_Dp(image, mask, p, patch_size):
    x, y = p
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_p = np.array([grad_x[y, x], grad_y[y, x]])
    mask_blur = cv2.GaussianBlur(mask, (3, 3), 0)
    grad_mask_x = cv2.Sobel(mask_blur, cv2.CV_64F, 1, 0, ksize=3)
    grad_mask_y = cv2.Sobel(mask_blur, cv2.CV_64F, 0, 1, ksize=3)
    normal_p = np.array([-grad_mask_y[y, x], grad_mask_x[y, x]])
    norm = np.linalg.norm(normal_p)
    if norm != 0:
        normal_p = normal_p / norm
    Dp = abs(np.dot(grad_p, normal_p)) / 255.0
    return Dp

def calcul_priorites(image, mask, confidence_map, front, patch_size):
    priorites = {}
    alpha=2
    for p in front:
        Cp = calcul_Cp(confidence_map, p, patch_size)
        Dp = calcul_Dp(image, mask, p, patch_size)
        Pp = (Cp**alpha) * Dp
        priorites[p] = Pp
        print(f"Point {p} → Cp = {Cp:.3f}, Dp = {Dp:.3f}, Pp = {Pp:.3f}")
    return priorites

def trouver_meilleur_patch_precis(image, mask, p_target, patch_size, tolérance_inconnus, rayon_recherche):
    h, w = image.shape[:2]
    demi = patch_size // 2
    patch_target = get_patch(image, p_target, patch_size)
    mask_target = get_patch(mask, p_target, patch_size)
    if patch_target is None or mask_target is None:
        return None
    valid_pixels = (mask_target == 0)
    best_score = float('inf')
    best_patch_position = None
    x_cible, y_cible = p_target
    for y in range(max(demi, y_cible - rayon_recherche), min(h - demi, y_cible + rayon_recherche)):
        for x in range(max(demi, x_cible - rayon_recherche), min(w - demi, x_cible + rayon_recherche)):
            patch_candidate_mask = get_patch(mask, (x, y), patch_size)
            if patch_candidate_mask is None:
                continue
            fraction_inconnus = np.mean(patch_candidate_mask == 255)
            if fraction_inconnus > tolérance_inconnus:
                continue
            patch_candidate = get_patch(image, (x, y), patch_size)
            if patch_candidate is None:
                continue
            if patch_candidate.shape != patch_target.shape:
                continue
            diff = (patch_target - patch_candidate) * valid_pixels[..., np.newaxis]
            ssd = np.sum(diff ** 2)
            if ssd < best_score:
                best_score = ssd
                best_patch_position = (x, y)
    return best_patch_position

# def copier_patch(image, mask, p_source, p_cible, patch_size):
#     demi = patch_size // 2
#     h, w = image.shape[:2]
#     x_src, y_src = p_source
#     x1_src = max(x_src - demi, 0)
#     x2_src = min(x_src + demi + 1, w)
#     y1_src = max(y_src - demi, 0)
#     y2_src = min(y_src + demi + 1, h)
#     x_cible, y_cible = p_cible
#     x1_cible = max(x_cible - demi, 0)
#     x2_cible = min(x_cible + demi + 1, w)
#     y1_cible = max(y_cible - demi, 0)
#     y2_cible = min(y_cible + demi + 1, h)
#     patch_source = image[y1_src:y2_src, x1_src:x2_src]
#     patch_mask = mask[y1_cible:y2_cible, x1_cible:x2_cible]
#     for j in range(patch_source.shape[0]):
#         for i in range(patch_source.shape[1]):
#             if patch_mask[j, i] == 255:
#                 image[y1_cible + j, x1_cible + i] = patch_source[j, i]

def copier_patch(image, mask, p_source, p_cible, patch_size):
    demi = patch_size // 2
    h, w = image.shape[:2]

    # Coordonnées source
    x_src, y_src = p_source
    x1_src = max(x_src - demi, 0)
    x2_src = min(x_src + demi + 1, w)
    y1_src = max(y_src - demi, 0)
    y2_src = min(y_src + demi + 1, h)

    # Coordonnées cible
    x_cible, y_cible = p_cible
    x1_cible = max(x_cible - demi, 0)
    x2_cible = min(x_cible + demi + 1, w)
    y1_cible = max(y_cible - demi, 0)
    y2_cible = min(y_cible + demi + 1, h)

    # Extraction des patchs
    patch_source = image[y1_src:y2_src, x1_src:x2_src]
    patch_mask = mask[y1_cible:y2_cible, x1_cible:x2_cible]

    # Création du masque binaire
    masque_binaire = (patch_mask == 255)[..., np.newaxis]  # (h, w, 1) pour broadcasting

    # Remplacement vectorisé
    image[y1_cible:y2_cible, x1_cible:x2_cible] = (
        patch_source * masque_binaire +
        image[y1_cible:y2_cible, x1_cible:x2_cible] * (~masque_binaire)
    )


# def update_confidence(confidence_map, p_star, patch_size, Cp):
#     demi = patch_size // 2
#     h, w = confidence_map.shape
#     x, y = p_star
#     x1 = max(x - demi, 0)
#     x2 = min(x + demi + 1, w)
#     y1 = max(y - demi, 0)
#     y2 = min(y + demi + 1, h)
#     for j in range(y1, y2):
#         for i in range(x1, x2):
#             if confidence_map[j, i] == 0:
#                 confidence_map[j, i] = Cp

def update_confidence(confidence_map, p_star, patch_size, Cp):
    patch = get_patch(confidence_map, p_star, patch_size)
    mask = (patch == 0)
    patch[mask] = Cp


def combler_petits_trous(image, mask):
    h, w = mask.shape
    for y in range(1, h-1):
        for x in range(1, w-1):
            if mask[y, x] == 255:
                voisins = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if not (dx == 0 and dy == 0) and mask[y+dy, x+dx] == 0:
                            voisins.append(image[y+dy, x+dx])
                if voisins:
                    image[y, x] = np.mean(voisins, axis=0)
                    mask[y, x] = 0
    return image, mask

def inpainting_criminisi(image, mask, patch_size=11, verbose=False, progress_callback=None):
    confidence = initialize_confidence(mask)
    working_image = image.copy()
    working_mask = mask.copy()
    iteration = 0
    start_time = time.time()
    # Calcul automatique du rayon de recherche (10% de la plus petite dimension)
    rayon_recherche_auto = int(min(image.shape[:2]) * 0.1)
    # rayon_recherche_auto = 10
    while np.any(working_mask == 255):
        iteration += 1
        front = get_fill_front(working_mask)
        if len(front) == 0:
            if np.any(working_mask == 255):
                blancs = np.argwhere(working_mask == 255)
                if blancs.size == 0:
                    break
                p_star = tuple(blancs[np.random.choice(len(blancs))])
            else:
                break
        else:
            priorites = calcul_priorites(working_image, working_mask, confidence, front, patch_size)
            p_star = max(priorites, key=priorites.get)
            Cp = calcul_Cp(confidence, p_star, patch_size)
            p_source = trouver_meilleur_patch_precis(
                working_image, working_mask, p_star,
                patch_size=patch_size,
                tolérance_inconnus=0.1,
                rayon_recherche=rayon_recherche_auto
            )
            if p_source is None:
                p_source = trouver_meilleur_patch_precis(
                    working_image, working_mask, p_star,
                    patch_size=patch_size,
                    tolérance_inconnus=1,
                    rayon_recherche=rayon_recherche_auto
                )
                if p_source is None:
                    working_image, working_mask = combler_petits_trous(working_image, working_mask)
                    break
            copier_patch(working_image, working_mask, p_source, p_star, patch_size)
            update_confidence(confidence, p_star, patch_size, Cp)
            patch_mask = get_patch(working_mask, p_star, patch_size)
            if patch_mask is not None:
                x, y = p_star
                demi = patch_size // 2
                h_img, w_img = working_mask.shape
                x1 = max(x - demi, 0)
                x2 = min(x + demi + 1, w_img)
                y1 = max(y - demi, 0)
                y2 = min(y + demi + 1, h_img)
                working_mask[y1:y2, x1:x2] = np.where(patch_mask == 255, 0, patch_mask)
        # Appel du callback de progression si fourni
        if progress_callback is not None:
            elapsed = time.time() - start_time
            progress_callback(working_image.copy(), iteration, elapsed)
    total_time = time.time() - start_time
    return working_image, iteration, total_time

# ... (autres dépendances nécessaires) 