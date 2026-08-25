from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import uuid
import base64
import asyncio
import threading
from typing import List
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from agents.state import AgentState
from agents.orchestrator_agent import (
    orchestrate_conversion_process,
    get_progress,
    clear_progress,
)
from database import Base, engine, get_db
from models import ConversionHistory
from auth import get_optional_user, User as AuthUser
from routers import auth as auth_router, history as history_router

Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(history_router.router)

_CONVERTED_DIR = os.path.join(os.path.dirname(__file__), "converted")
os.makedirs(_CONVERTED_DIR, exist_ok=True)
app.mount("/converted", StaticFiles(directory=_CONVERTED_DIR), name="converted")

_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(_UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOADS_DIR), name="uploads")

# In-memory store for background conversion results
_conversion_results: dict[str, dict] = {}


def _run_conversion(
    conversion_id: str,
    image_b64s: list[str],
    user_id: int | None,
    first_filename: str,
    export_format: str,
):
    """Run conversion in background thread."""
    try:
        initial_state: AgentState = {
            "images": image_b64s,
            "messages": [],
            "export_format": "pdf",
            "diagram_regions": [],
            "classified_regions": [],
            "rendered_images": [],
            "final_pdf_path": "",
            "final_word_path": "",
            "_conversion_id": conversion_id,
        }

        result = orchestrate_conversion_process(initial_state, conversion_id)

        pdf_path = result.get("final_pdf_path", "") or ""
        if not pdf_path:
            raise RuntimeError("PDF generation result path is empty.")

        pdf_url = f"/converted/{os.path.basename(pdf_path)}"

        _conversion_results[conversion_id] = {
            "status": "done",
            "pdfUrl": pdf_url,
            "wordUrl": "",
            "user_id": user_id,
            "first_filename": first_filename,
        }

    except Exception as e:
        print(f"[ERROR] conversion {conversion_id}: {e}")
        _conversion_results[conversion_id] = {
            "status": "error",
            "error": str(e),
        }


@app.post("/api/convert-images")
async def convert_images(
    images: List[UploadFile] = File(...),
    export_format: str = Form("pdf"),
    user: AuthUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Start conversion in background and return conversion_id for progress polling."""
    export_format = (export_format or "pdf").lower()

    if export_format != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Currently only PDF is supported.",
        )

    try:
        image_b64s: list[str] = []
        for img in images:
            raw = await img.read()
            if not raw:
                continue
            image_b64s.append(base64.b64encode(raw).decode())

        if not image_b64s:
            raise HTTPException(status_code=400, detail="No images were uploaded.")

        conversion_id = str(uuid.uuid4())
        first_filename = images[0].filename or "Converted Document"
        user_id = user.id if user else None

        # Start conversion in background thread
        thread = threading.Thread(
            target=_run_conversion,
            args=(conversion_id, image_b64s, user_id, first_filename, export_format),
            daemon=True,
        )
        thread.start()

        return {"conversionId": conversion_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] convert_images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/convert-progress/{conversion_id}")
async def convert_progress(conversion_id: str):
    """Poll conversion progress."""
    # Check if conversion is done
    result = _conversion_results.get(conversion_id)
    if result:
        status = result.get("status")
        if status == "done":
            return {
                "percent": 100,
                "message": "완료",
                "status": "done",
                "pdfUrl": result.get("pdfUrl", ""),
                "wordUrl": result.get("wordUrl", ""),
            }
        elif status == "error":
            return {
                "percent": 0,
                "message": "오류 발생",
                "status": "error",
                "error": result.get("error", "알 수 없는 오류"),
            }

    # Still in progress
    progress = get_progress(conversion_id)
    return {
        "percent": progress.get("percent", 0),
        "message": progress.get("message", ""),
        "status": "processing",
    }


@app.post("/api/convert-complete/{conversion_id}")
async def convert_complete(
    conversion_id: str,
    user: AuthUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Save conversion history and clean up after frontend confirms completion."""
    result = _conversion_results.get(conversion_id)
    if not result or result.get("status") != "done":
        raise HTTPException(status_code=404, detail="Conversion not found or not done.")

    pdf_url = result.get("pdfUrl", "")
    user_id = result.get("user_id")
    first_filename = result.get("first_filename", "Converted Document")

    if user and user_id == user.id and pdf_url:
        title = first_filename.rsplit(".", 1)[0][:50] if first_filename else "Converted Document"
        db.add(
            ConversionHistory(
                user_id=user.id,
                title=title,
                file_type="pdf",
                file_url=pdf_url,
            )
        )
        db.commit()

    # Clean up
    _conversion_results.pop(conversion_id, None)
    clear_progress(conversion_id)

    return {"pdfUrl": pdf_url, "wordUrl": ""}


@app.get("/")
def read_root():
    return {"message": "AI Report Maker API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
