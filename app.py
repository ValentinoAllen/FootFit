import os
import tempfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from main import process_foot_measurement

register_heif_opener()

BASE_DIR = Path(__file__).parent
MAX_DIMENSION = 2000

app = FastAPI(title="FootFit API")

# Serve static image assets (foot guide overlay, etc.) at /imgs/<filename>.
# Guarded so a missing assets dir degrades to 404s instead of crashing startup.
IMGS_DIR = BASE_DIR / "imgs"
if IMGS_DIR.is_dir():
    app.mount("/imgs", StaticFiles(directory=IMGS_DIR), name="imgs")


def _preprocess_upload(contents: bytes) -> str:
    """Load gambar (HEIC/JPEG/PNG), apply EXIF rotation, resize, save as JPEG temp file."""
    img = Image.open(BytesIO(contents))
    print(f"[app] PIL opened: format={img.format}, mode={img.mode}, size={img.size}", flush=True)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(tmp.name, format="JPEG", quality=92)
    tmp.close()
    print(f"[app] preprocessed: final_size={img.size}, saved={tmp.name}", flush=True)
    return tmp.name


@app.get("/")
async def root():
    # no-cache: browser may store but must revalidate (ETag) before use, so a
    # new deploy of footfit.html is picked up on the next load, not served stale.
    return FileResponse(
        BASE_DIR / "footfit.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.post("/measure")
async def measure(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar.")

    contents = await file.read()
    print(f"[app] upload: content_type={file.content_type}, size={len(contents)}B, filename={file.filename}", flush=True)
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran gambar maksimal 15 MB.")

    tmp_path = None
    try:
        try:
            tmp_path = _preprocess_upload(contents)
        except Exception as e:
            print(f"[app] preprocess failed: {e}", flush=True)
            return JSONResponse(
                status_code=422,
                content={"status": "error", "message": "Format gambar tidak dikenali atau file rusak."},
            )

        result = process_foot_measurement(tmp_path)
    except Exception as e:
        print(f"[app] CV pipeline crashed: {e}", flush=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Terjadi kesalahan internal saat memproses gambar."},
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    if result.get("status") == "error":
        return JSONResponse(status_code=422, content=result)

    return JSONResponse(content=result)
