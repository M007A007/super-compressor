from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/compress")
async def compress_file(file: UploadFile = File(...), license_key: str = Form(None)):
    input_path = f"in_{file.filename}"
    output_path = f"out_{file.filename}"
    
    try:
        # حفظ الملف المرفوع
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # التأكد من حجم الملف قبل المعالجة
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        if file.filename.lower().endswith(".pdf"):
            doc = fitz.open(input_path)
            # إذا الملف ضخم جداً، نستخدم "الضغط السريع" فقط
            if file_size_mb > 50:
                # ضغط الفهارس والجداول فقط بدون لمس الصور لتوفير الرام
                doc.save(output_path, garbage=4, deflate=True, clean=True)
            else:
                # للملفات المتوسطة، نطبق ضغط الصور الداخلي
                doc.save(output_path, garbage=3, deflate=True)
            doc.close()
            
            return FileResponse(output_path, filename=f"M_{file.filename}")
        
        else:
            # معالجة الصور
            from PIL import Image
            img = Image.open(input_path)
            if img.mode != 'RGB': img = img.convert('RGB')
            img.save(output_path, "JPEG", optimize=True, quality=40)
            return FileResponse(output_path, filename=f"M_{file.filename}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
