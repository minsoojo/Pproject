#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform

# ========================
# 환경 설정
# ========================
OS_TYPE = platform.system()  # "Windows", "Linux", "Darwin" 등

# 기본 output 디렉토리 이름 (필요하면 수정)
DEFAULT_OUTPUT_DIR = "output"

# 전역으로 쓸 FILE_TEXT_DIR (윈도우용 함수에서 사용)
FILE_TEXT_DIR = DEFAULT_OUTPUT_DIR


# ========================
# Windows 전용 HWP/HWPX (네가 준 코드 그대로 + 약간 정리)
# ========================
def extract_hwp_windows_only(path: str) -> str:
    if OS_TYPE != "Windows":
        print("[SKIP] HWP: Windows 아님:", path)
        return ""

    try:
        import win32com.client as win32
    except ImportError:
        print("[SKIP] HWP: pywin32 미설치:", path)
        return ""

    # FILE_TEXT_DIR 안에 저장할 txt 경로 (절대 경로로!)
    base = os.path.splitext(os.path.basename(path))[0]
    out_txt_rel = os.path.join(FILE_TEXT_DIR, base + ".txt")
    out_txt = os.path.abspath(out_txt_rel)  # 여기서 절대 경로로 변환

    # 혹시 폴더가 없다면 생성
    os.makedirs(os.path.dirname(out_txt), exist_ok=True)

    hwp = None
    try:
        hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

        try:
            hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
        except Exception:
            # 이 부분은 설치 안 되어 있어도 무시 가능
            pass

        # 파일 열기
        hwp.Open(path, "", "forceopen:true")

        # 텍스트 파일로 저장 (절대 경로 사용)
        hwp.SaveAs(out_txt, "TEXT")

        # 문서 닫기
        hwp.XHwpDocuments.Close(isDirty=False)

        # 저장된 TXT 읽기
        try:
            with open(out_txt, "r", encoding="cp949", errors="ignore") as f:
                return f.read()
        except:
            with open(out_txt, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    except Exception as e:
        print("[SKIP] HWP 변환 실패:", path, e)
        return ""
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception:
                pass


# ========================
# 폴더 순회 + 일괄 크롤링
# ========================
def process_hwp_folder(input_dir: str, output_dir: str):
    """
    input_dir 아래의 모든 .hwp / .hwpx 파일을 찾아서
    extract_hwp_windows_only()로 텍스트를 추출하고
    output_dir 에 <원본이름>.txt 로 저장.
    """

    global FILE_TEXT_DIR
    FILE_TEXT_DIR = output_dir  # 윈도우용 함수에서 이 경로를 사용함

    if not os.path.isdir(input_dir):
        print("[ERROR] 입력 폴더가 존재하지 않습니다:", input_dir)
        return

    os.makedirs(output_dir, exist_ok=True)

    print("=== HWP 폴더 처리 시작 ===")
    print("입력 폴더:", os.path.abspath(input_dir))
    print("출력 폴더:", os.path.abspath(output_dir))
    print("OS_TYPE:", OS_TYPE)
    print("=========================")

    count_total = 0
    count_ok = 0

    # 하위 폴더까지 모두 순회하고 싶으면 os.walk 사용
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in [".hwp", ".hwpx"]:
                continue

            count_total += 1
            full_path = os.path.join(root, filename)
            print(f"[{count_total}] 처리 중:", full_path)

            text = extract_hwp_windows_only(full_path)

            if text.strip():
                count_ok += 1
            else:
                # 이미 extract 함수가 output_dir에 txt 저장을 시도하긴 했음.
                # 여기서는 그냥 "내용 없음" 정도만 로깅
                print("  → 추출된 텍스트가 비어 있거나 에러 발생")

    print("=========================")
    print("총 HWP/HWPX 파일 수:", count_total)
    print("성공(텍스트 비어있지 않음):", count_ok)
    print("출력 폴더:", os.path.abspath(output_dir))
    print("=== 완료 ===")


# ========================
# 엔트리 포인트
# ========================
if __name__ == "__main__":
    # 사용법:
    #   python hwp_batch_extract.py <입력_폴더> [출력_폴더]
    #
    # 예:
    #   python hwp_batch_extract.py "C:\\hwp_files" "C:\\hwp_output"
    #   python hwp_batch_extract.py ./hwp ./output

    if len(sys.argv) < 2:
        print("사용법: python hwp_batch_extract.py <입력_폴더> [출력_폴더]")
        sys.exit(1)

    input_dir = sys.argv[1]

    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        output_dir = DEFAULT_OUTPUT_DIR

    process_hwp_folder(input_dir, output_dir)



# 셸파일로 실행시켜야함 

# cd 경로\스크립트있는곳

# # 출력 폴더 지정
# python hwp_batch_extract.py "D:\data\hwp_docs(임의로 설정해둠)" "D:\data\hwp_output(임의로 설정해둠)"
