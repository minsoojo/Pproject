#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 🔥 텍스트 추출 모듈 import (extract.py)
from extract_v2 import extract_by_ext

# ============================================================
# 설정: 딱 이 URL 한 페이지만 테스트
# ============================================================
START_URL = "https://www.gachon.ac.kr/kor/1071/subview.do"
DOMAIN = "www.gachon.ac.kr"

DATA_DIR = "data_test"  # 본 크롤러랑 섞이지 않게 폴더 분리
HTML_DIR = os.path.join(DATA_DIR, "html")
TEXT_DIR = os.path.join(DATA_DIR, "text")
FILE_DIR = os.path.join(DATA_DIR, "files")
FILE_TEXT_DIR = os.path.join(DATA_DIR, "file_text")

os.makedirs(FILE_TEXT_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(FILE_DIR, exist_ok=True)

METADATA_FILE = os.path.join(DATA_DIR, "metadata.jsonl")


# ============================================================
# 파일 확장자 + 다운로드 URL 패턴
# ============================================================
FILE_EXTS = [
    ".pdf",
    ".hwp",
    ".hwpx",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
]

DOWNLOAD_URL_PATTERNS = ["download.do"]


def is_file(url: str) -> bool:
    u = url.lower()
    if any(u.endswith(ext) for ext in FILE_EXTS):
        return True
    if any(pat in u for pat in DOWNLOAD_URL_PATTERNS):
        return True
    return False


# ============================================================
# 드라이버 생성
# ============================================================
def create_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # 필요 시 활성화

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    prefs = {
        "download.default_directory": os.path.abspath(FILE_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(4)
    driver.set_script_timeout(4)
    return driver


# ============================================================
# 유틸 함수
# ============================================================
def canonicalize(url):
    url, _ = urldefrag(url)
    return url


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return "\n".join(x.strip() for x in text.splitlines() if x.strip())


def save_text(content, idx):
    fpath = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return fpath


def safe_get(driver, url):
    try:
        driver.get(url)
        time.sleep(0.2)
        return True
    except:
        return False


# ============================================================
# 다운로드 새 파일 대기
# ============================================================
def wait_for_new_file(download_dir, before_files, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        after_files = set(os.listdir(download_dir))
        new_files = after_files - before_files
        for fname in new_files:
            lower = fname.lower()
            if not (lower.endswith(".crdownload") or lower.endswith(".tmp")):
                return os.path.join(download_dir, fname)
        time.sleep(0.5)
    return None


# ============================================================
# 한 페이지 테스트 크롤러
# ============================================================
def crawl_one_page():
    driver = create_driver()

    url = canonicalize(START_URL)
    idx = 1

    print(f"[INFO] 한 페이지 테스트 크롤링 시작: {url}")

    success = safe_get(driver, url)
    if not success:
        print("[ERROR] 요청 실패")
        driver.quit()
        return

    html = driver.page_source
    html_text_path = save_text(html_to_text(html), idx)

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    metadata = {
        "id": idx,
        "type": "html",
        "url": url,
        "text": html_text_path,
        "title": title,
        "timestamp": time.time(),
    }
    with open(METADATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

    print(f"[OK] HTML 저장: {html_text_path}")

    file_count = 0

    for a in soup.find_all("a", href=True):
        next_url = canonicalize(urljoin(url, a["href"].strip()))

        if urlparse(next_url).netloc and urlparse(next_url).netloc != DOMAIN:
            continue
        if not is_file(next_url):
            continue

        file_count += 1
        print(f"[FILE] {next_url}")

        before = set(os.listdir(FILE_DIR))
        driver.execute_script("window.open(arguments[0]);", next_url)

        file_path = wait_for_new_file(FILE_DIR, before)
        print("   → 다운로드:", file_path)

        # ⬇⬇⬇ 텍스트 추출 파트 추가 (extract.py 사용)
        if file_path and os.path.exists(file_path):
            text = extract_by_ext(file_path)

            if text.strip():
                out_txt = os.path.join(
                    FILE_TEXT_DIR,
                    os.path.splitext(os.path.basename(file_path))[0] + ".txt",
                )

                with open(out_txt, "w", encoding="utf-8") as f:
                    f.write(text)

                print("   → 텍스트 추출 완료:", out_txt)

                # TODO: (나중에 DB INSERT)
                # insert_document(...)
            else:
                print("   → 추출된 텍스트 없음")

        file_meta = {
            "id": f"file-{idx}-{file_count}",
            "type": os.path.splitext(next_url)[1].lower(),
            "url": next_url,
            "ref_page_id": idx,
            "file_path": file_path,
            "timestamp": time.time(),
        }
        with open(METADATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(file_meta, ensure_ascii=False) + "\n")

    driver.quit()
    print("[DONE] 종료")


if __name__ == "__main__":
    crawl_one_page()
