from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  
from PIL import Image 
import os

app = FastAPI(title="المكبس الخارق API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_KEYS = ["PRO-2026", "VIP-MAX", "ZABDA100"]

@app.post("/compress")
async def compress_file(file: UploadFile = File(...), license_key: str = Form(...)):
    if license_key.upper() not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="كود التفعيل غير صحيح")

    input_path = f"temp_{file.filename}"
    output_path = f"compressed_{file.filename}"
    
    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        if file.filename.lower().endswith(".pdf"):
            doc = fitz.open(input_path)
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
        elif file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            img = Image.open(input_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, format="JPEG", optimize=True, quality=60)
            
        else:
            raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم")

    except Exception as e:
        raise HTTPException(status_code=500, detail="خطأ في السيرفر")
    
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

    return FileResponse(output_path, filename=f"PRO_{file.filename}")
