import cv2
import numpy as np
from core.geometry_utils import get_homography_and_ppm

def process_reference_object_robust(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None, None

    original_h, original_w = image.shape[:2]

    # 1. Grayscale Conversion
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray_clahe = clahe.apply(gray)

    # 3. Bilateral Filter 
    blurred = cv2.bilateralFilter(gray_clahe, 11, 17, 17)

    # 4. Edge Detection
    edged = cv2.Canny(blurred, 30, 200)

    # 5. AGGRESSIVE MORPHOLOGICAL CLOSING
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    # 6. Contour Approximation
    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    card_contour = None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    target_ratio = 85.60 / 53.98  # Ideal Card Ratio = ~1.586
    
    # Canvas Area Total
    total_image_area = original_w * original_h

    for c in contours:
        contour_area = cv2.contourArea(c)
        
        # Area Filter: 1% sampai 20%
        if contour_area < (0.01 * total_image_area) or contour_area > (0.20 * total_image_area):
            continue
            
        rect = cv2.minAreaRect(c)
        (x, y), (w, h), angle = rect
        if w == 0 or h == 0:
            continue
            

        # FILTER EXTENT
        box_area = w * h
        if box_area == 0: 
            continue
            
        extent = contour_area / box_area
        aspect_ratio = max(w, h) / min(w, h)
        
        if extent < 0.75:
            continue
            
        if 1.3 < aspect_ratio < 1.8:
            s = c.sum(axis=2)
            diff = np.diff(c, axis=2)

            tl = c[np.argmin(s)][0]
            br = c[np.argmax(s)][0]
            tr = c[np.argmin(diff)][0]
            bl = c[np.argmax(diff)][0]

            padding = 2
            tl = [tl[0] - padding, tl[1] - padding]
            br = [br[0] + padding, br[1] + padding]
            tr = [tr[0] + padding, tr[1] - padding]
            bl = [bl[0] - padding, bl[1] + padding]

            card_contour = np.array([tl, tr, br, bl], dtype="int32")
            break  # Card found

    if card_contour is not None:
        cv2.drawContours(image, [card_contour], -1, (0, 255, 0), 3)

        M, ppm, _, _ = get_homography_and_ppm(image, card_contour.reshape(4, 2))
        warped_full_image = cv2.warpPerspective(image, M, (original_w, original_h))

        return warped_full_image, ppm
    else:
        return None, None
    pass

def process_reference_object_hardcore(image_path):
    original_image = cv2.imread(image_path)
    if original_image is None:
        return None, None

    orig_h, orig_w = original_image.shape[:2]

    # DOWNSCALING

    process_width = 800
    ratio = orig_w / process_width
    process_height = int(orig_h / ratio)

    resized_img = cv2.resize(original_image, (process_width, process_height))

    shifted = cv2.pyrMeanShiftFiltering(resized_img, sp=21, sr=51)

    gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    edged = cv2.Canny(thresh, 50, 150)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    card_contour_small = None

    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    total_image_area = process_width * process_height

    for c in contours:
        contour_area = cv2.contourArea(c)
        
        if contour_area < (0.01 * total_image_area) or contour_area > (0.20 * total_image_area):
            continue
            
        rect = cv2.minAreaRect(c)
        (x, y), (w, h), angle = rect
        if w == 0 or h == 0:
            continue
            
        box_area = w * h
        if box_area == 0: 
            continue
            
        extent = contour_area / box_area
        aspect_ratio = max(w, h) / min(w, h)
        
        if extent < 0.75:
            continue    
        
        if 1.3 < aspect_ratio < 1.8:
            s = c.sum(axis=2)
            diff = np.diff(c, axis=2)

            tl = c[np.argmin(s)][0]
            br = c[np.argmax(s)][0]
            tr = c[np.argmin(diff)][0]
            bl = c[np.argmax(diff)][0]

            card_contour_small = np.array([tl, tr, br, bl], dtype="float32")
            break

    if card_contour_small is not None:
        card_contour_original = card_contour_small * ratio
        card_contour_original = np.int32(card_contour_original)

        cv2.drawContours(original_image, [card_contour_original], -1, (0, 255, 0), 5)

        M, ppm, _, _ = get_homography_and_ppm(original_image, card_contour_original.reshape(4, 2))
        warped_full_image = cv2.warpPerspective(original_image, M, (orig_w, orig_h))

        return warped_full_image, ppm
    else:
        return None, None

def detect_and_warp_card(image_path):
    
    warped_img, ppm = process_reference_object_robust(image_path)
    if warped_img is not None:
        return warped_img, ppm
        
    warped_img, ppm = process_reference_object_hardcore(image_path)
    if warped_img is not None:
        return warped_img, ppm
        
    return None, None