import cv2
import numpy as np
from core.geometry_utils import get_homography_and_ppm

# Filter constants (di-loosen agar lebih toleran terhadap foto HP real)
AREA_MIN_RATIO = 0.005   # 0.5% dari total area
AREA_MAX_RATIO = 0.30    # 30% dari total area
EXTENT_MIN = 0.65        # kontur fill minimum dalam bounding box
ASPECT_MIN = 1.25        # ID-1 ratio = 1.586
ASPECT_MAX = 1.85


def _try_match_card_contour(contours, total_image_area, tag=""):
    """Iterasi kontur, log alasan rejection, return kontur kartu pertama yang lolos."""
    print(f"[card_detector:{tag}] found {len(contours)} contours, checking top 10")
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    for idx, c in enumerate(contours):
        contour_area = cv2.contourArea(c)
        area_ratio = contour_area / total_image_area

        if area_ratio < AREA_MIN_RATIO or area_ratio > AREA_MAX_RATIO:
            print(f"[card_detector:{tag}]  #{idx} reject: area {area_ratio:.4f} outside [{AREA_MIN_RATIO}, {AREA_MAX_RATIO}]")
            continue

        rect = cv2.minAreaRect(c)
        (x, y), (w, h), angle = rect
        if w == 0 or h == 0:
            print(f"[card_detector:{tag}]  #{idx} reject: zero w/h")
            continue

        box_area = w * h
        extent = contour_area / box_area
        aspect_ratio = max(w, h) / min(w, h)

        if extent < EXTENT_MIN:
            print(f"[card_detector:{tag}]  #{idx} reject: extent {extent:.3f} < {EXTENT_MIN}")
            continue

        if not (ASPECT_MIN < aspect_ratio < ASPECT_MAX):
            print(f"[card_detector:{tag}]  #{idx} reject: aspect {aspect_ratio:.3f} outside [{ASPECT_MIN}, {ASPECT_MAX}]")
            continue

        # Kartu match
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

        print(f"[card_detector:{tag}]  #{idx} MATCH: area={area_ratio:.4f}, extent={extent:.3f}, aspect={aspect_ratio:.3f}")
        return np.array([tl, tr, br, bl], dtype="int32")

    print(f"[card_detector:{tag}] no contour passed all filters")
    return None


def process_reference_object_robust(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"[card_detector:robust] cv2.imread FAILED for {image_path}")
        return None, None

    original_h, original_w = image.shape[:2]
    print(f"[card_detector:robust] image loaded: {image.shape}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe.apply(gray)
    blurred = cv2.bilateralFilter(gray_clahe, 11, 17, 17)
    edged = cv2.Canny(blurred, 30, 200)

    # Adaptive kernel: scale dengan resolusi
    kernel_size = max(15, int(min(original_w, original_h) / 100))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total_image_area = original_w * original_h
    card_contour = _try_match_card_contour(contours, total_image_area, tag="robust")

    if card_contour is not None:
        cv2.drawContours(image, [card_contour], -1, (0, 255, 0), 3)
        M, ppm, _, _ = get_homography_and_ppm(image, card_contour.reshape(4, 2))
        warped_full_image = cv2.warpPerspective(image, M, (original_w, original_h))
        return warped_full_image, ppm

    return None, None


def process_reference_object_hardcore(image_path):
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"[card_detector:hardcore] cv2.imread FAILED for {image_path}")
        return None, None

    orig_h, orig_w = original_image.shape[:2]
    print(f"[card_detector:hardcore] image loaded: {original_image.shape}")

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
    total_image_area = process_width * process_height
    card_contour_small = _try_match_card_contour(contours, total_image_area, tag="hardcore")

    if card_contour_small is not None:
        card_contour_original = card_contour_small.astype(np.float32) * ratio
        card_contour_original = np.int32(card_contour_original)

        cv2.drawContours(original_image, [card_contour_original], -1, (0, 255, 0), 5)
        M, ppm, _, _ = get_homography_and_ppm(original_image, card_contour_original.reshape(4, 2))
        warped_full_image = cv2.warpPerspective(original_image, M, (orig_w, orig_h))
        return warped_full_image, ppm

    return None, None


def detect_and_warp_card(image_path):
    warped_img, ppm = process_reference_object_robust(image_path)
    if warped_img is not None:
        return warped_img, ppm

    warped_img, ppm = process_reference_object_hardcore(image_path)
    if warped_img is not None:
        return warped_img, ppm

    return None, None
