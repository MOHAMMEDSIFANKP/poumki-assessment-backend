from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
import os
import shutil
from starlette.websockets import WebSocketDisconnect
from database.database import engine, Base, SessionLocal
from models import Thumbnail

import uuid
from pathlib import Path
# Utilities
from utils.utils import reverse_string 

app = FastAPI(
    title="Pomki Assesments Api",
    description="Cloud Storage API",
    version="1.0.0"
)

# Mount static files directory
app.mount("/media", StaticFiles(directory="media"), name="media")
MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)

BASE_URL = "http://localhost:8000"
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

Base.metadata.create_all(bind=engine)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to DriveNest API"}

@app.post(
    "/reverse/",
    status_code=status.HTTP_200_OK)
async def reverse_text(text: str = Form(...)):
    try:
        reversed_text = reverse_string(text.strip())
        return JSONResponse(content={"reversed": reversed_text}, status_code=status.HTTP_200_OK)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back received data (optional)
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")

    
@app.post("/upload/",status_code = status.HTTP_201_CREATED)
async def upload_thumbnail(file: UploadFile = File(...)):
    try:
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        file_path = os.path.join(MEDIA_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        db = SessionLocal()
        new_thumbnail = Thumbnail(
            filename=unique_filename, 
        )
        db.add(new_thumbnail)
        db.commit()
        db.refresh(new_thumbnail)
        db.close()

        file_url = f"{BASE_URL}/media/{unique_filename}"
        
        # Notify all connected clients
        for connection in active_connections:
            try:
                await connection.send_json({
                    "thumbnail": {
                        "id": new_thumbnail.id,
                        "filename": file.filename,
                        "url": file_url
                    }
                })
            except Exception as e:
                print(f"Error sending WebSocket notification: {e}")

        return {"url": file_url, "id": new_thumbnail.id, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/thumbnails/")
async def list_thumbnails(request: Request):
    db = SessionLocal()
    thumbnails = db.query(Thumbnail).all()
    db.close()

    if not thumbnails:
        raise HTTPException(status_code=404, detail="No images found")

    return JSONResponse(content={
        "images": [
            {"id": t.id, "filename": t.filename, "url": f"{BASE_URL}/media/{t.filename}"} 
            for t in thumbnails
        ]
    })