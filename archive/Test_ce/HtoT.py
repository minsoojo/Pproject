#한글 파일을 텍스트로 변환하는 코드입니다.

# hwp_to_txt_batch.py
import win32com.client as win32
from pathlib import Path

# HWP 파일들이 들어 있는 폴더
ROOT_DIR = Path(r"C:\Users\s7302\OneDrive\바탕 화면\2-1\SW 기초교양 조교")
OUT_DIR = ROOT_DIR / "_txt"
OUT_DIR.mkdir(exist_ok=True)


def main():
    # 한글 객체 생성
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    # 보안 모듈 등록 (버전에 따라 안 먹어도 됨)
    try:
        hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
    except Exception:
        pass

    # 폴더 내 모든 .hwp 파일 찾기 (하위폴더까지)
    hwp_files = list(ROOT_DIR.rglob("*.hwp"))
    print(f"[INFO] 발견한 HWP 개수: {len(hwp_files)}")

    for idx, hwp_path in enumerate(hwp_files, start=1):
        # 출력 txt 경로 (구조 유지 or 단순 이름만 쓸지 선택)
        # 여기서는 파일명만 따서 ROOT/_txt 아래에 저장
        out_txt = OUT_DIR / (hwp_path.stem + ".txt")

        print(f"[{idx}/{len(hwp_files)}] {hwp_path} → {out_txt}")

        try:
            # 파일 열기
            hwp.Open(str(hwp_path), "", "forceopen:true")

            # 텍스트로 저장
            hwp.SaveAs(str(out_txt), "TEXT")

            # 문서 닫기 (프로그램은 유지)
            hwp.XHwpDocuments.Close(isDirty=False)
        except Exception as e:
            print(f"  [ERROR] 변환 실패: {hwp_path} -> {e}")

    # 작업 끝난 후 한글 종료
    hwp.Quit()
    print("[DONE] 모든 HWP 변환 완료.")


if __name__ == "__main__":
    main()
