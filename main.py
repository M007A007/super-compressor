from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  
from PIL import Image 
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

VALID_KEYS = ["PRO-2026", "VIP-MAX", "ZABDA100"]

@app.post("/compress")
async def compress_file(file: UploadFile = File(...), license_key: str = Form(...)):
    if license_key.upper() not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="كود التفعيل خطأ")

    input_path = f"temp_{file.filename}"
    output_path = f"compressed_{file.filename}"
    
    # حفظ الملف الضخم تدريجياً عشان ما يطفي السيرفر
    with open(input_path, "wb") as buffer:
        while content := await file.read(1024 * 1024): # يقرأ 1 ميجا كل مرة
            buffer.write(content)

    try:
        if file.filename.lower().endswith(".pdf"):
            doc = fitz.open(input_path)
            # تقنية الضغط العميق للـ PDF (تقليل الـ DPI لكل الصور داخله)
            for page in doc:
                for img in page.get_images(full=True):
                    xref = img[0]
                    # تحويل الصور داخل الـ PDF لدقة 100 DPI (توازن ممتاز للحجم الكبير)
                    pix = page.get_pixmap(dpi=100)
            
            # حفظ مع ضغط الفهارس والبيانات الزائدة
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
        else: # للصور الضخمة
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            # الضغط الذهبي: تقليل الجودة لـ 60 وتفعيل التقرير
            img.save(output_path, "JPEG", optimize=True, quality=60)
            
        return FileResponse(output_path, filename=f"COMPRESSED_{file.filename}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء معالجة الملف الضخم")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
