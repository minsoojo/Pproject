# 임시 hwp2pdf

import os
import win32com.client as win32

# ✅ 여기만 너 파일 경로로 바꿔줘
HWP_PATH = r"C:\temp\test.hwp"      # 변환할 HWP 파일
PDF_PATH = r"C:\temp\test.pdf"      # 저장할 PDF 경로

PDF_FORMAT_CANDIDATES = ["PDF", "HWP_PDF", "PDF2"]  # 버전별 후보

def main():
    if not os.path.isfile(HWP_PATH):
        print("[ERROR] HWP 파일을 찾을 수 없습니다:", HWP_PATH)
        return

    # 출력 폴더 만들기
    os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)

    print("=== HWP → PDF 단일 테스트 ===")
    print("HWP:", HWP_PATH)
    print("PDF:", PDF_PATH)
    print("============================")

    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    try:
        # (옵션) 보안 모듈 등록 - 에러 나면 무시
        try:
            hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
        except Exception as e:
            print("[INFO] RegisterModule 실패 (무시):", repr(e))

        print("[INFO] HWP 열기 시도...")
        hwp.Open(HWP_PATH, "", "forceopen:true")
        print("[OK] 문서 열기 성공")

        ok = False
        for fmt in PDF_FORMAT_CANDIDATES:
            try:
                print(f"[INFO] SaveAs 시도: format={fmt}")
                hwp.SaveAs(PDF_PATH, fmt)
                print(f"[OK] PDF 저장 성공 (format={fmt})")
                ok = True
                break
            except Exception as e:
                print(f"[WARN] SaveAs 실패 (format={fmt}):", repr(e))

        if not ok:
            print("[ERROR] 어떤 포맷으로도 PDF 저장에 실패했습니다.")
        else:
            print("[DONE] 최종 PDF 경로:", PDF_PATH)

    finally:
        try:
            hwp.XHwpDocuments.Close(isDirty=False)
        except:
            pass
        try:
            hwp.Quit()
        except:
            pass


if __name__ == "__main__":
    main()
