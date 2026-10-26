from fastapi import FastAPI, HTTPException, UploadFile, File
import sqlite3
import json
import os
import uuid

# Import cv2 safely
try:
    import cv2
except ImportError:
    cv2 = None

from app.document_detector import detect_document
from app.ocr_engine import extract_text
from app.field_extractor import extract_fields

app = FastAPI(
    title="Document AI Backend",
    description="ID card detection and OCR API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "records.db")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
FACES_DIR = os.path.join(PROJECT_ROOT, "outputs", "faces")
CASCADE_PATH = os.path.join(PROJECT_ROOT, "haarcascade_frontalface_default.xml")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)


def get_face_cascade():
    if cv2 is None or not hasattr(cv2, "CascadeClassifier"):
        return None
    if os.path.exists(CASCADE_PATH):
        try:
            cascade = cv2.CascadeClassifier(CASCADE_PATH)
            if not cascade.empty():
                return cascade
        except Exception:
            pass
    return None


def extract_face_thumbnail(image_path, record_id):
    cascade = get_face_cascade()
    if cascade is None or cv2 is None:
        return None

    image = cv2.imread(image_path)
    if image is None:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=3,
        minSize=(30, 30)
    )

    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    
    margin = int(0.15 * w)
    img_h, img_w = image.shape[:2]
    y1 = max(0, y - margin)
    y2 = min(img_h, y + h + margin)
    x1 = max(0, x - margin)
    x2 = min(img_w, x + w + margin)

    face_img = image[y1:y2, x1:x2]
    face_filename = f"{record_id}_face.jpg"
    face_path = os.path.join(FACES_DIR, face_filename)

    cv2.imwrite(face_path, face_img)
    return f"outputs/faces/{face_filename}"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(records)")
        columns = [column[1] for column in cursor.fetchall()]

        if not columns:
            conn.execute("""
                CREATE TABLE records (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """)
        elif "result" in columns and "data" not in columns:
            conn.execute("ALTER TABLE records RENAME COLUMN result TO data")
        conn.commit()


init_db()


@app.get("/")
def home():
    return {
        "message": "Document AI Backend is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/v1/process-id")
async def process_id(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload an image."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty"
        )

    record_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, record_id + extension)

    try:
        with open(file_path, "wb") as image_file:
            image_file.write(content)

        document_detected = detect_document(file_path)
        ocr_results = extract_text(file_path)
        extracted_fields = extract_fields(ocr_results)
        face_thumbnail_path = extract_face_thumbnail(file_path, record_id)

        record = {
            "record_id": record_id,
            "status": "success",
            "extracted_fields": extracted_fields,
            "face_thumbnail": face_thumbnail_path,
            "ocr_text": ocr_results,
            "image_metadata": {
                "filename": file.filename,
                "document_detected": bool(document_detected)
            }
        }

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO records (id, data) VALUES (?, ?)",
                (record_id, json.dumps(record))
            )
            conn.commit()

        return record

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )


@app.get("/api/v1/records/{record_id}")
def get_record(record_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT data FROM records WHERE id = ?",
            (record_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )

    return json.loads(row[0])