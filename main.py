from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import os
import shutil

app = FastAPI()

# السماح للواجهة بالاتصال بالسيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_KEYS = ["PRO-2026", "VIP-MAX", "ZABDA100"]

@app.post("/compress")
async def compress_file(file: UploadFile = File(...), license_key: str = Form(...)):
    # التأكد من كود التفعيل
    if license_key.upper() not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="كود التفعيل خطأ")

    input_path = f"temp_{file.filename}"
    output_path = f"compressed_{file.filename}"

    try:
        # حفظ الملف المرفوع تدريجياً لتوفير الذاكرة (RAM)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if file.filename.lower().endswith(".pdf"):
            # الضغط بطريقة إعادة الرندرة (أقوى طريقة لتقليل الحجم)
            src = fitz.open(input_path)
            doc = fitz.open()
            
            for page in src:
                # خفضنا الـ DPI إلى 72 للملفات الضخمة لضمان عدم حدوث Crash
                pix = page.get_pixmap(dpi=72) 
                new_page = doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(page.rect, pixmap=pix)
            
            # ضغط الملف وحذف البيانات الزائدة
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            src.close()
            
            return FileResponse(output_path, filename=f"COMPRESSED_{file.filename}")
        
        else:
            # إذا كان ملف صورة وليس PDF
            from PIL import Image
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.save(output_path, "JPEG", optimize=True, quality=50)
            return FileResponse(output_path, filename=f"COMPRESSED_{file.filename}")

    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"فشل الكبس: {str(e)}")
    
    finally:
        # تنظيف الملفات المؤقتة بعد الانتهاء
        if os.path.exists(input_path): os.remove(input_path)
