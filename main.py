from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  
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
    
    with open(input_path, "wb") as buffer:
        while content := await file.read(1024 * 1024):
            buffer.write(content)

    try:
        if file.filename.lower().endswith(".pdf"):
            # فتح الملف الأصلي
            src = fitz.open(input_path)
            # إنشاء ملف جديد فارغ
            doc = fitz.open()
            
            for page in src:
                # تحويل كل صفحة لصورة بدقة منخفضة (150 DPI) ثم إعادتها لـ PDF
                # هذي الطريقة تخسف بالحجم الأرض وتحافظ على القراءة
                pix = page.get_pixmap(dpi=150) 
                new_page = doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(page.rect, pixmap=pix)
            
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            src.close()
            
            return FileResponse(output_path, filename=f"COMPRESSED_{file.filename}")
        else:
            raise HTTPException(status_code=400, detail="يرجى رفع ملف PDF فقط لتجربة هذا المكبس")

    except Exception as e:
        raise HTTPException(status_code=500, detail="خطأ في المعالجة العملاقة")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
