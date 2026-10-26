## 📹 Video Demonstration

<video src="https://github.com/PrasadKonale/PortalwizApi/raw/main/demo.mp4" controls width="100%"></video>

# Document AI Backend

A RESTful backend service built with FastAPI, OpenCV, and EasyOCR that accepts identity card images, processes document boundaries, extracts structured fields (Full Name, Document Number, Date of Birth, Expiry Date), crops face thumbnails, and stores extracted records in SQLite.

## Features
- **POST `/api/v1/process-id`**: Uploads, validates, detects document, runs OCR, extracts metadata, saves face thumbnail, and persists record.
- **GET `/api/v1/records/{record_id}`**: Retrieves stored document extraction records by ID from SQLite.
- **GET `/health`**: Returns API health status.
- **Swagger Documentation**: Accessible at `http://127.0.0.1:8000/docs`.

## Tech Stack
- **Python 3.11**
- **FastAPI & Uvicorn**: REST API framework & server
- **OpenCV & EasyOCR**: Computer vision preprocessing, face thumbnail extraction, and OCR text recognition
- **SQLite**: Persistent database storage
- **Pytest**: Automated API unit tests

## Quickstart

### 1. Activate Environment
```bash
conda activate document_ai