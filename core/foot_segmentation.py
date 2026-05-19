import cv2
import numpy as np

def apply_gray_world_awb(image):
    b, g, r = cv2.split(image)
    
    m_b = np.mean(b)
    m_g = np.mean(g)
    m_r = np.mean(r)
    
    mean_gray = (m_b + m_g + m_r) / 3.0
    
    b = cv2.convertScaleAbs(b, alpha=(mean_gray / max(m_b, 1e-5)))
    g = cv2.convertScaleAbs(g, alpha=(mean_gray / max(m_g, 1e-5)))
    r = cv2.convertScaleAbs(r, alpha=(mean_gray / max(m_r, 1e-5)))
    
    return cv2.merge((b, g, r))

def extract_foot_grabcut(warped_image):
    
    orig_h, orig_w = warped_image.shape[:2]
    
    process_width = 400
    ratio = orig_w / process_width
    process_height = int(orig_h / ratio)
    
    resized_img = cv2.resize(warped_image, (process_width, process_height))
    
    balanced_img = apply_gray_world_awb(resized_img)
    
    mask = np.zeros(resized_img.shape[:2], np.uint8)
    mask[:] = cv2.GC_PR_BGD 
    
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
    mask[gray < 15] = cv2.GC_BGD

    h_res, w_res = resized_img.shape[:2]
    cv2.rectangle(mask, (0, 0), (w_res, h_res), cv2.GC_BGD, thickness=5)
    
    ycrcb = cv2.cvtColor(balanced_img, cv2.COLOR_BGR2YCrCb)
    
    lower_skin = np.array([0, 135, 85], dtype=np.uint8)
    upper_skin = np.array([255, 180, 135], dtype=np.uint8)
    
    skin_mask = cv2.inRange(ycrcb, lower_skin, upper_skin)
    
    kernel_skin = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel_skin)
    skin_dilated = cv2.dilate(skin_mask, kernel_skin, iterations=2)

    h, w = resized_img.shape[:2]
    safe_zone = np.zeros((h, w), dtype=np.uint8)
    
    margin_x = int(w * 0.05)
    margin_y = int(h * 0.05)
    cv2.rectangle(safe_zone, (margin_x, margin_y), (w - margin_x, h - margin_y), 255, -1)
    
    foot_skin = cv2.bitwise_and(skin_dilated, skin_dilated, mask=safe_zone)
    calf_skin = cv2.subtract(skin_dilated, foot_skin)
    
    mask[foot_skin == 255] = cv2.GC_PR_FGD  # Kulit di tengah layar = Mungkin Kaki
    mask[calf_skin == 255] = cv2.GC_BGD     # Kulit di pinggir layar = Betis 
    
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    
    cv2.grabCut(resized_img, mask, None, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_MASK)
    
    mask_binary = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')
    
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    
    mask_cleaned = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel_open)
    mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel_close)
    
    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None
        
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    foot_contour_small = contours[0]
    
    toe_point = tuple(foot_contour_small[foot_contour_small[:, :, 1].argmin()][0])
    heel_point = tuple(foot_contour_small[foot_contour_small[:, :, 1].argmax()][0])
    
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
    
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    abs_sobel_y = cv2.convertScaleAbs(sobel_y)
    
    _, thresh_sobel = cv2.threshold(abs_sobel_y, 50, 255, cv2.THRESH_BINARY)
    
    row_sums = np.sum(thresh_sobel, axis=1)
    
    h, w = gray.shape
    
    row_sums[:int(h * 0.50)] = 0
    
    bottom_margin = int(h * 0.05)
    row_sums[h - bottom_margin:] = 0
    
    wall_line_y = np.argmax(row_sums)
    max_energy = row_sums[wall_line_y]
    
    if max_energy < (w * 255 * 0.1): # Minimal 10% dari lebar layar adalah garis jelas
        wall_line_y = heel_point[1]
   
    pixel_length_small = abs(toe_point[1] - wall_line_y)
    
    y_top = int(toe_point[1])
    y_bottom = int(wall_line_y)
    
    contour_points = foot_contour_small.reshape(-1, 2)
    
    margin_top = int((y_bottom - y_top) * 0.05)
    
    limit_bottom = int((y_bottom - y_top) * 0.70)
    
    valid_points = contour_points[
        (contour_points[:, 1] > (y_top + margin_top)) & 
        (contour_points[:, 1] < (y_top + limit_bottom))
    ]
    
    if len(valid_points) > 0:
        leftmost_pt = tuple(valid_points[valid_points[:, 0].argmin()])
        rightmost_pt = tuple(valid_points[valid_points[:, 0].argmax()])
        pixel_width_small = rightmost_pt[0] - leftmost_pt[0]
    else:
        leftmost_pt = (0, 0)
        rightmost_pt = (0, 0)
        pixel_width_small = 0
    
    foot_pixel_length = pixel_length_small * ratio
    foot_pixel_width = pixel_width_small * ratio
    
    wall_y_orig = int(wall_line_y * ratio)
    toe_y_orig = int(toe_point[1] * ratio)
    toe_x_orig = int(toe_point[0] * ratio)
    
    left_x_orig = int(leftmost_pt[0] * ratio)
    left_y_orig = int(leftmost_pt[1] * ratio)
    right_x_orig = int(rightmost_pt[0] * ratio)
    right_y_orig = int(rightmost_pt[1] * ratio)
    
    result_img = warped_image.copy()
    cv2.line(result_img, (0, wall_y_orig), (orig_w, wall_y_orig), (0, 0, 255), 6) # Dinding
    cv2.circle(result_img, (toe_x_orig, toe_y_orig), 15, (0, 255, 0), -1) # Titik Jari
    cv2.line(result_img, (toe_x_orig, toe_y_orig), (toe_x_orig, wall_y_orig), (255, 0, 0), 4) # Panjang
    
    cv2.line(result_img, (left_x_orig, toe_y_orig), (left_x_orig, wall_y_orig), (0, 255, 255), 2)
    cv2.line(result_img, (right_x_orig, toe_y_orig), (right_x_orig, wall_y_orig), (0, 255, 255), 2)
    
    mid_y = int((toe_y_orig + wall_y_orig) / 2)
    cv2.line(result_img, (left_x_orig, mid_y), (right_x_orig, mid_y), (0, 255, 255), 4)
    
    cv2.circle(result_img, (left_x_orig, left_y_orig), 12, (0, 165, 255), -1) # Orange dot Kiri
    cv2.circle(result_img, (right_x_orig, right_y_orig), 12, (0, 165, 255), -1) # Orange dot Kanan
    
    return result_img, (foot_pixel_length, foot_pixel_width)