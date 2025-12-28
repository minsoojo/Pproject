# !pip install easyocr pdf2image
# !apt-get install -y poppler-utils

import easyocr

# 한글 + 영어 인식 (중요!)
reader = easyocr.Reader(['ko', 'en'])

result = reader.readtext('이미지 파일 경로', detail=0)  # detail=0 → 텍스트만 리스트로
print("\n".join(result)) 

# 이거는 이미지 OCR 하는 거 