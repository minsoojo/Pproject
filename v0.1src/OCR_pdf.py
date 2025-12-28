# !pip install easyocr pdf2image
# !apt-get install -y poppler-utils

import os
from pdf2image import convert_from_path
import easyocr
import numpy as np  # 추가!

reader = easyocr.Reader(['ko', 'en']) 
# GPU 쓸거면 True, 안 쓸 거면 gpu 이하로 그냥 지워도 됨

# /home/t25315/data/img_pdf/seg_files : 이것도 그냥 OCR로 읽어버리죠 
PDF_DIR = "/home/t25315/data/img_pdf" 
OUTPUT_DIR = "/home/t25315/data/text_new/pdf"  # 결과 txt 저장 폴더

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 폴더 내 모든 PDF 파일 목록
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
print(f"[INFO] 총 {len(pdf_files)}개의 PDF 파일 발견")

for pdf_name in pdf_files:
    PDF_PATH = os.path.join(PDF_DIR, pdf_name)
    
    # 결과 txt 파일 이름 생성
    base = os.path.splitext(pdf_name)[0]
    OUTPUT_TXT = os.path.join(OUTPUT_DIR, f"{base}.txt")

    print(f"\n==============================")
    print(f"[START] {pdf_name} 변환 시작")
    print(f"==============================")


    # PDF → 이미지 리스트
    pages = convert_from_path(PDF_PATH, dpi=300)
    print(f"[INFO] 총 {len(pages)} 페이지 변환 완료")

    all_text = []

    for i, page in enumerate(pages, start=1):
        print(f"[INFO] page {i} OCR 진행 중...")

        # 🔹 PIL.Image → numpy array 로 변환
        img_np = np.array(page)
        # 🔹 numpy array를 바로 전달
        result = reader.readtext(img_np, detail=0)

        page_text = "\n".join(result)
        all_text.append(f"\n\n===== PAGE {i} =====\n\n" + page_text)

    # 3) 텍스트 파일로 저장
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

print(f"[DONE] OCR 텍스트 저장 완료 → {OUTPUT_TXT}")

