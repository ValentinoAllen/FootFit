from core.card_detector import detect_and_warp_card
from core.foot_segmentation import extract_foot_grabcut # <--- Import modul baru
import cv2
import base64

def process_foot_measurement(image_path: str) -> dict:
    """
    Fungsi utama untuk dipanggil oleh endpoint API (misal: FastAPI / Flask).
    Mengembalikan dictionary berisi status, ukuran, dan gambar Base64.
    """
    # Deteksi Kartu & Warping
    warped_image, ppm = detect_and_warp_card(image_path)
    
    if warped_image is None:
        return {
            "status": "error",
            "message": "Gagal mendeteksi kartu referensi pada gambar."
        }

    # MODUL 2: Segmentasi K-Means & GrabCut
    result_img, foot_dimensions = extract_foot_grabcut(warped_image)
    
    if result_img is None:
        return {
            "status": "error",
            "message": "Gagal memisahkan objek kaki dari background."
        }

    # MODUL MATEMATIKA
    px_length, px_width = foot_dimensions
    length_mm = px_length / ppm
    width_mm = px_width / ppm
    ratio = width_mm / length_mm

    # ENCODING GAMBAR KE BASE64 UNTUK FRONTEND
    # 1. Konversi dari NumPy array ke format file .jpg di dalam memori
    success, encoded_image = cv2.imencode('.jpg', result_img)
    if not success:
         return {
            "status": "error",
            "message": "Gagal melakukan encoding gambar hasil."
        }
    
    # 2. Ubah bytes gambar menjadi string Base64
    base64_string = base64.b64encode(encoded_image).decode('utf-8')

    # OUTPUT TERSTRUKTUR
    return {
        "status": "success",
        "data": {
            "length_mm": round(length_mm, 2),
            "width_mm": round(width_mm, 2),
            "ratio": round(ratio, 2),
            "image_base64": base64_string
        }
    }

# Local Test doang
if __name__ == "__main__":
    target_image = "imgs/michael2.jpg"
    
    print("[INFO] Memulai proses pengukuran...")
    hasil = process_foot_measurement(target_image)
    
    if hasil["status"] == "success":
        print("Pengukuran Berhasil!")
        print(f"Length     : {hasil['data']['length_mm']} mm")
        print(f"Width      : {hasil['data']['width_mm']} mm")
        print(f"Ratio(L/W) : {hasil['data']['ratio']}")
        print(f"Base64 (preview): {hasil['data']['image_base64'][:50]}...\n")
    else:
        print(f"Error: {hasil['message']}")