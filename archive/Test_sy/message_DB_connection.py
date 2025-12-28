#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import pymysql
from db_config import get_conn

import sys
import os
import time
import json
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from Pproject.Test_sy.raw_db_selenium import extract_main_text


# ============================================================
# DB 연결
# ============================================================

def insert_raw_document(conn, url, title, raw_text, meta_dict=None):
    """
    한 페이지 크롤링 결과를 documents 테이블에 저장.
    이미 같은 url이 있으면 업데이트.
    """
    meta_json = json.dumps(meta_dict, ensure_ascii=False) if meta_dict else None

    sql = """
    INSERT INTO documents (url, source_type, title, raw_text, meta_json, crawled_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        title      = VALUES(title),
        raw_text   = VALUES(raw_text),
        meta_json  = VALUES(meta_json),
        crawled_at = VALUES(crawled_at)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            url,
            "html",   # 지금은 HTML 페이지라서 고정
            title,
            raw_text,
            meta_json,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
    conn.commit()

# ============================================================
# 설정
# ============================================================
START_URL = "https://www.gachon.ac.kr/kor/3120/subview.do"
DOMAIN = "www.gachon.ac.kr"

DATA_DIR = "data"
HTML_DIR = os.path.join(DATA_DIR, "html")
TEXT_DIR = os.path.join(DATA_DIR, "text")
FILE_DIR = os.path.join(DATA_DIR, "files")
FILE_TEXT_DIR = os.path.join(DATA_DIR, "file_text")

os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(FILE_DIR, exist_ok=True)
os.makedirs(FILE_TEXT_DIR, exist_ok=True)

VISITED_FILE = "data/visited.txt"
METADATA_FILE = "data/metadata.jsonl"
QUEUE_FILE = "data/queue.txt"


# ============================================================
# 파일 확장자 + 다운로드 URL 패턴
# ============================================================
FILE_EXTS = [
    ".pdf", ".hwp", ".hwpx",
    ".doc", ".docx",
    ".xls", ".xlsx",
    ".ppt", ".pptx",
    ".zip"
]

DOWNLOAD_URL_PATTERNS = [
    "download.do",
]

# 추가 차단 패턴: synap 뷰어 + 영어/중국어 사이트
BLOCK_PATTERNS = [
    "synap",
    "synapview.do",
    "synapviewer",

    "/eng/",
    "/english/",
    "/chi/",
    "/chn/",
    "/china/",
]


def is_file(url: str) -> bool:
    u = url.lower()

    if any(u.endswith(ext) for ext in FILE_EXTS):
        return True

    if any(pat in u for pat in DOWNLOAD_URL_PATTERNS):
        return True

    return False


def is_download_url(url: str) -> bool:
    u = url.lower()
    return any(pat in u for pat in DOWNLOAD_URL_PATTERNS)


def is_blocked_url(url: str) -> bool:
    """HTML 방문에서 제외해야 할 URL"""
    u = url.lower()

    # 1) download.do → HTML 방문 금지
    if any(pat in u for pat in DOWNLOAD_URL_PATTERNS):
        return True

    # 2) synap 문서뷰어 페이지
    if any(pat in u for pat in ["synap", "synapview", "synapviewer"]):
        return True

    # 3) 영어/중국어 사이트
    if any(pat in u for pat in ["/eng/", "/english/", "/chi/", "/chn/", "/china/"]):
        return True

    return False


# ============================================================
# 드라이버 생성
# ============================================================
def create_driver():
    chrome_options = Options()

    # headless 금지
    # chrome_options.add_argument("--headless=new")

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

    # PDF 뷰어 끄고 자동 다운로드
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


def load_visited():
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE) as f:
            return set(line.strip() for line in f)
    return set()


def save_visited(url):
    with open(VISITED_FILE, "a") as f:
        f.write(url + "\n")


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            return [line.strip() for line in f if line.strip()]
    return []


def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        f.write("\n".join(queue))


def html_to_text(html):

    return extract_main_text(html)


def save_text(content, idx):
    fpath = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return fpath


# ============================================================
# 안전 GET
# ============================================================
def safe_get(driver, url):
    try:
        driver.get(url)
        time.sleep(0.1)

        try:
            alert = driver.switch_to.alert
            print("[ALERT FOUND]", alert.text)
            alert.accept()
            return False
        except:
            pass

        return True

    except Exception as e:
        print(f"[ERROR safe_get] {e}")
        return False


# ============================================================
# 메인 크롤러
# ============================================================
def crawl():
    driver = create_driver()
    conn = get_conn()

    visited = load_visited()
    queue = load_queue()

    start = canonicalize(START_URL)
    if not queue:
        queue.append(start)

    seen = set(visited) | set(queue)
    idx = len(visited)

    print("[INFO] 가천대 전체 크롤링 시작")
    print(f"[INFO] 방문 완료 {len(visited)}개")
    print(f"[INFO] 대기 중 {len(queue)}개\n")

    while queue:
        url = queue.pop(0)
        idx += 1

        print(f"\n[{idx}] GET {url}")

        # 🔥 HTML 차단 패턴
        if is_blocked_url(url):
            print("    [SKIP] 차단된 URL:", url)
            visited.add(url)
            save_visited(url)
            save_queue(queue)
            continue

        # 🔥 download.do 자체는 HTML 방문 금지
        if is_download_url(url):
            print("    [SKIP] download URL:", url)
            visited.add(url)
            save_visited(url)
            save_queue(queue)
            continue

        # 방문
        success = safe_get(driver, url)
        if not success:
            print("[SKIP] alert/오류:", url)
            visited.add(url)
            save_visited(url)
            save_queue(queue)
            continue

        html = driver.page_source

        # HTML → TEXT 저장
        html_text = html_to_text(html)
        html_text_path = save_text(html_text, idx)

        # metadata 저장
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else ""

        metadata = {
            "id": idx,
            "type": "html",
            "url": url,
            "text": html_text_path,
            "title": title,
            "timestamp": time.time()
        }
        with open(METADATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

        page_meta = {
            "local_text_path": html_text_path,
            "crawler_id": idx,
        }
        insert_raw_document(conn, url, title, html_text, page_meta)

        

        # -------------------------
        # 링크 탐색
        # -------------------------
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if href.startswith("javascript:") or href.startswith("mailto:"):
                continue

            next_url = canonicalize(urljoin(url, href))

            # 🔥 파일 처리
            if is_file(next_url):
                print(f"    [FILE LINK] {next_url}")

                ext = os.path.splitext(next_url)[1].lower()
                if ext == "":
                    ext = ".temp"

                try:
                    driver.execute_script("window.open(arguments[0]);", next_url)
                except:
                    pass

                file_meta = {
                    "id": f"file-{idx}-{len(os.listdir(FILE_DIR))+1}",
                    "type": f"file:{ext}",
                    "url": next_url,
                    "ref_page_url": url,
                    "ref_page_id": idx,
                    "file_path": None,
                    "timestamp": time.time()
                }
                with open(METADATA_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(file_meta, ensure_ascii=False) + "\n")
                continue

            # 🔥 HTML 차단 URL은 방문 금지
            if is_blocked_url(next_url):
                continue

            # 🔥 외부 도메인 금지
            if urlparse(next_url).netloc != DOMAIN:
                continue

            if next_url not in seen:
                seen.add(next_url)
                queue.append(next_url)
                save_queue(queue)

        visited.add(url)
        save_visited(url)
        save_queue(queue)

    driver.quit()
    conn.close()
    print("\n[DONE] 가천대 전체 크롤링 완료")


# 실행
if __name__ == "__main__":
    crawl()