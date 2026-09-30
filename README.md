# FootFit 👟📏

**FootFit** measures foot length and width from a single photo using classical computer vision, and classifies the result into a fit category (narrow / normal / wide). The user places a standard ID-1 card — a KTP, ATM or credit card — next to their foot; the card provides both the scale reference and the perspective correction needed to turn pixels into millimetres.

Built as a Computer Vision course project (team of 5).

**Live demo:** https://footfit.onrender.com

---

## How it works

A photo alone cannot tell you the real size of anything: there is no scale, and the camera is almost never perfectly perpendicular to the floor. A card of known dimensions solves both problems at once.

```
Photo (foot + ID-1 card on the floor)
  │
  ├─ 1. Card detection        core/card_detector.py
  │     Find the card contour by area, extent and aspect-ratio filtering
  │
  ├─ 2. Homography + scale    core/geometry_utils.py
  │     Order the 4 corners, compute the perspective transform,
  │     derive pixels-per-millimetre from the card's known 85.60 mm width
  │
  ├─ 3. Foot segmentation     core/foot_segmentation.py
  │     Gray-world auto white balance, then GrabCut to separate
  │     the foot from the floor
  │
  ├─ 4. Measurement           main.py
  │     Foot length and width in pixels ÷ ppm → millimetres
  │
  └─ 5. Fit classification    main.py
        Foot Index = width / length × 100
```

### The reference card

FootFit uses the **ISO/IEC 7810 ID-1** standard, which every KTP, ATM and credit card follows: **85.60 × 53.98 mm**, aspect ratio 1.586.

The detector scans contours and keeps the first one that passes three filters:

| Filter | Range | Why |
| --- | --- | --- |
| Area | 0.5%–30% of the image | Rejects noise specks and the floor itself |
| Extent | ≥ 0.65 | A card fills most of its bounding box; irregular shapes do not |
| Aspect ratio | 1.25–1.85 | Brackets the true ID-1 ratio of 1.586, with tolerance for camera tilt |

Once the four corners are found, `cv2.getPerspectiveTransform` rectifies the image and the scale follows directly: `ppm = card_width_in_pixels / 85.60`.

### Fit classification

The **Foot Index** is the width-to-length ratio as a percentage:

| Foot Index | Category |
| --- | --- |
| < 37.71% | Narrow-Fit |
| 37.71% – 42.17% | Normal-Fit |
| ≥ 42.17% | Wide-Fit |

The API returns the measurements and the fit category. It does **not** convert to EU/US/UK numbering or to brand-specific sizing — that would require per-brand last data, which this project does not have.

---

## Technology stack

- **Python 3.10+**
- **OpenCV** (`opencv-python`, `opencv-contrib-python`) — contour detection, perspective transform, GrabCut segmentation
- **NumPy** — geometry and array maths
- **Pillow** + **pillow-heif** — image loading, EXIF rotation, HEIC support for iPhone photos
- **FastAPI** + **Uvicorn** — REST API
- **Docker** — containerised build, deployed on Render

No deep-learning framework is used. Segmentation is GrabCut, an iterative graph-cut algorithm built into OpenCV.

---

## API

### `GET /`
Serves the web interface (`footfit.html`).

### `POST /measure`

Multipart upload, field name `file`.

Accepts JPEG, PNG and HEIC. The image is EXIF-rotated, converted to RGB and downscaled so the longest side is at most 2000 px. Maximum upload size 15 MB.

**Success — `200`**

```json
{
  "status": "success",
  "data": {
    "length_mm": 254.13,
    "width_mm": 99.42,
    "ratio": 0.3912,
    "fi_percent": 39.12,
    "fit_category": "normal",
    "fit_label": "Normal-Fit",
    "image_base64": "/9j/4AAQSkZJRgABAQ..."
  }
}
```

`image_base64` is the annotated result image, JPEG-encoded, ready to drop straight into an `<img src="data:image/jpeg;base64,...">`.

**Errors**

| Status | Cause |
| --- | --- |
| `400` | Not an image, or larger than 15 MB |
| `422` | Image unreadable, reference card not detected, or foot could not be segmented |
| `500` | Unexpected failure in the CV pipeline |

Error responses carry a human-readable `message` — for example, if the card is missing the API explains that it must be fully visible, contrasting with the floor, and not tilted.

---

## Running it

### Local

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

To test the pipeline directly without the API:

```bash
python main.py
```

### Docker

```bash
docker build -t footfit .
docker run -p 8000:8000 footfit
```

---

## Project structure

```
app.py                       FastAPI application and endpoints
main.py                      Pipeline orchestration and fit classification
process_image.py             Image helpers
core/
  card_detector.py           Reference-card detection
  geometry_utils.py          Corner ordering, homography, pixels-per-mm
  foot_segmentation.py       White balance and GrabCut segmentation
footfit.html                 Web interface
uml_diagram/                 Class and sequence diagrams
Dockerfile                   Container build
render.yaml                  Render deployment config
```

---

## Known limitations

These are real and worth stating plainly:

- **No measurement accuracy has been formally validated.** There is no benchmark against physically measured feet, so no error margin can be quoted.
- **Detection depends on conditions.** The card must be fully visible, lying flat, and contrasting with the floor. Patterned or dark floors cause failures.
- **GrabCut is sensitive to background.** Feet photographed against a similarly coloured floor may segment poorly.
- **Single reference card only.** A4 paper and other reference objects are not supported.
- **`scikit-learn` appears in `requirements.txt` but is not currently used** by the pipeline.

## Possible next steps

- Validate against manually measured feet to establish an error margin
- Support a second reference object (A4 paper) for users without a card
- Map measurements to EU/US/UK sizing using published brand last charts
