import cv2
import numpy as np

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect
    pass

def get_homography_and_ppm(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    if maxWidth > maxHeight:
        true_width = maxWidth
        true_height = int(maxWidth * (53.98 / 85.60)) 
        ppm = true_width / 85.60
    else:
        true_height = maxHeight
        true_width = int(maxHeight * (53.98 / 85.60)) 
        ppm = true_height / 85.60

    dx = tr[0] - tl[0]
    dy = tr[1] - tl[1]
    angle = np.arctan2(dy, dx)
    
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)

    dst_tl = tl
    
    dst_tr = [tl[0] + true_width * cos_a, tl[1] + true_width * sin_a]
    
    dst_bl = [tl[0] - true_height * sin_a, tl[1] + true_height * cos_a]

    dst_br = [dst_tr[0] - true_height * sin_a, dst_tr[1] + true_height * cos_a]

    dst = np.array([dst_tl, dst_tr, dst_br, dst_bl], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    return M, ppm, int(true_width), int(true_height)
    pass