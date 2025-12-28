#HTML+양식 아닌 파일 전처리기
# htmlNotFormCleaner.py

def clean_html_NotForm(row):
    """
    임시 디버그용: 실제 클리닝은 안 하고
    들어온 row 정보를 간단히 찍고 더미 문자열만 리턴.
    """

    # row에서 파일명/URL 비슷한 거 하나 뽑아서 보여주기
    file_name = (
        row.get("file_path")
        or row.get("url")
        or row.get("title")
        or f"id={row.get('id')}"
    )

    print(f"[DEBUG] clean_html_NotForm() 잘 들어왔습니다. 파일명/URL: {file_name}")

    # 실제 클리닝은 아직 미구현이므로, 더미 텍스트 리턴
    return f"[DUMMY_HTML_CLEANED] {file_name}"
