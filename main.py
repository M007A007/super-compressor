from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import os
import shutil
from datetime import datetime
import random
import string

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def generate_unique_name(original_name):
    now = datetime.now().strftime("%Y%m%d_%H%M")
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"M_Safe_{now}_{random_code}_{original_name}"

@app.post("/compress")
async def compress_file(file: UploadFile = File(...), license_key: str = Form(None)):
    input_path = f"temp_{file.filename}"
    output_filename = generate_unique_name(file.filename)
    output_path = f"out_{output_filename}"
    
    try:
        # حفظ الملف المرفوع بطريقة لا تستهلك الرام
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # فتح الملف وتطبيق إعداداتك "الآمنة"
        doc = fitz.open(input_path)
        
        # إذا كان الملف ضخماً جداً (200MB)، نطبق ضغط الهيكل فقط لضمان الاستقرار
        # إعداداتك الآمنة (garbage=3) هي الأفضل هنا لمنع التلف
        doc.save(
            output_path,
            garbage=3,
            deflate=True,
            linear=True # أضفت linear لتحسين سرعة فتح الملفات الكبيرة بعد تحميلها
        )
        doc.close()
        
        return FileResponse(output_path, filename=output_filename)

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="السيرفر لم يستطع معالجة هذا الحجم، جرب ملفاً أصغر قليلاً.")
    
    finally:
        # تنظيف الملفات لعدم ملء مساحة السيرفر
        if os.path.exists(input_path): os.remove(input_path)
