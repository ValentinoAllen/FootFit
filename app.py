import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from main import process_foot_measurement

app = FastAPI(title="FootFit API")


@app.get("/")
async def root():
    return FileResponse("footfit.html")


@app.post("/measure")
async def measure(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran gambar maksimal 10 MB.")

    suffix = os.path.splitext(file.filename or ".jpg")[1] or ".jpg"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        result = process_foot_measurement(tmp_path)
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Terjadi kesalahan internal saat memproses gambar."},
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    if result.get("status") == "error":
        return JSONResponse(status_code=422, content=result)

    return JSONResponse(content=result)


# Static files mount SETELAH semua route API agar /measure tetap prioritas
app.mount("/", StaticFiles(directory=".", html=True), name="static")
