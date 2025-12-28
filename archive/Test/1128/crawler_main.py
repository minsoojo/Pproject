#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
import pymysql  # [추가] DB 연동 라이브러리

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

from extract import extract_by_ext

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
    # "synap",
    "synapview.do",
    # "synapviewer",

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

    chrome_bin = "/home/t25315/chromium-portable/chrome-linux/chrome"
    chrome_options.binary_location = chrome_bin

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-gpu-driver-bug-workarounds")
    chrome_options.add_argument("--remote-debugging-port=9222")

    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
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

    service = Service("/home/t25315/chromium-portable/chromedriver_linux64/chromedriver")

    print("[DEBUG] create_driver: before webdriver.Chrome")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd(
    "Page.setDownloadBehavior",
    {
        "behavior": "allow",
        "downloadPath": os.path.abspath(FILE_DIR),
    },
)
    print("[DEBUG] create_driver: after webdriver.Chrome")

    driver.implicitly_wait(5)
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


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # 1) 확실히 필요 없는 태그 제거
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # 2) header/footer 태그 직접 제거
    for tag in soup.find_all(["header", "footer"]):
        tag.decompose()

    # 3) 사이트에서 자주 쓰는 헤더/푸터 CSS ID/class 제거
    header_footer_selectors = [
        "#header",          # 가천대 최상단 헤더
        "#footer",          # 페이지 푸터
        ".header",          # 공통 header class
        ".footer",          # 공통 footer class
        ".gnb",             # 글로벌 네비게이션 바
        "#gnb",             # 메뉴
        ".logo",            # 상단 로고 영역
        ".site-map",        # 사이트맵
        ".sub-visual",      # 서브 비주얼 이미지
        ".top-banner",      # 상단 배너
        ".bottom-banner",   # 하단 배너
        ".quick-menu",      # 퀵메뉴
        ".breadcrumb",      # 현재 위치 breadcrumb
        ".location",        # 위치 표시 UI
        ".nav",             # 네비게이션
        ".menu",            # 메뉴 전체
        ".wrap-header",
        ".wrap-footer",
        "#wrap-header",
        "#wrap-footer",
        ".sns-area",
        ".top-menu",
    ]

    for selector in header_footer_selectors:
        for tag in soup.select(selector):
            tag.decompose()

    # 4) 가천대 본문 영역(#content, #contents, .content-wrapper 등)
    main_candidates = [
        "#content",
        "#contents",
        ".content",
        ".contents",
        ".content-area",
        ".content-wrapper",
        ".sub-content",
        ".sub-contents",
        ".article",
        ".board-view",     # 게시판 본문
        "#container",
    ]

    main = None

    for sel in main_candidates:
        area = soup.select_one(sel)
        if area:
            main = area
            break   
        
    if main is None:
        candidates = soup.find_all(["article", "section"])
        if candidates:
            main = max(
                candidates,
                key=lambda c: len(c.get_text(strip=True))
            )

    if main is None:  
        main = soup  # fallback

    markdown_tables = []

    tables = main.find_all("table")
    for t in tables:
        rows = t.find_all("tr")
        table_lines = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [c.get_text(strip=True) for c in cells]
            # 빈 행은 스킵
            if not any(cell_texts):
                continue

            # 본문
            table_lines.append("| " + " | ".join(cell_texts) + " |")

            # 첫 행을 헤더로 보고 구분선 추가
            if i == 0:
                table_lines.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")

        if table_lines:
            markdown_tables.append("\n".join(table_lines))

    # 5-2) table 을 DOM에서 제거해서 본문 텍스트와 중복 방지
    for t in tables:
        t.decompose()

    # 6) 본문 텍스트
    text = main.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    body_text = "\n".join(lines)

    # 7) 테이블을 markdown으로 붙여줌
    if markdown_tables:
        return body_text + "\n\n" + "\n\n".join(markdown_tables)
    return body_text    


def save_text(content, idx):
    fpath = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return fpath


# ============================================================
# 안전 GET (수정 금지 영역)
# ============================================================
def safe_get(driver, url):
    try:
        driver.get(url)

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
# 다운로드 폴더에서 새 파일 기다리기
# ============================================================
def wait_for_new_file(download_dir, before_files, timeout=30):
    """
    download_dir: 다운로드 폴더 경로
    before_files: 다운로드 전 파일 목록 (set)
    timeout: 최대 대기 시간(초)

    새로 생긴 '완성된' 파일 경로를 반환.
    새 파일이 없거나, 전부 .crdownload/.tmp 상태에서 timeout 나면 None.
    """
    start = time.time()

    while time.time() - start < timeout:
        after_files = set(os.listdir(download_dir))
        new_files = after_files - before_files
        if new_files:
            for fname in new_files:
                lower = fname.lower()
                if lower.endswith(".crdownload") or lower.endswith(".tmp"):
                    continue
                return os.path.join(download_dir, fname)
        time.sleep(0.3)

    return None


# ============================================================
# [추가] DB 연결 및 삽입 함수
# ============================================================
def get_connection():
    
    import pymysql
    
    return pymysql.connect(
        host="localhost",
        user="dbid253",
        password="dbpass253",
        database="db25322",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_html_document(url, title, raw_text, meta_id):

#    -----------------------------------------------------------
#     [수정사항]
#     - 인자로 받은 raw_text(추출된 텍스트)를 DB의 raw_text 컬럼에 저장
#     - clean_text 컬럼은 추후 처리를 위해 NULL로 비워둠
#    -----------------------------------------------------------
   
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO documents (source_type, url, title, raw_text, clean_text, meta_id)
            VALUES ('html', %s, %s, %s, NULL, %s)
            """
            cur.execute(sql, (url, title, raw_text, meta_id))
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        print(f"[DB ERROR HTML] {e}")
        return None
    finally:
        conn.close()

def insert_file_document(meta_id,source_type, url, file_path, clean_text=None, ref_html_id=None, raw_text=None, title=None):
    #    -----------------------------------------------------------
    #     [수정사항]
    #     - 인자로 받은 raw_text(추출된 텍스트)를 DB의 raw_text 컬럼에 저장
    #     - clean_text 컬럼은 추후 처리를 위해 NULL로 비워둠
    #    -----------------------------------------------------------
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
            INSERT INTO documents
            (meta_id, source_type, url, ref_html_id, title, raw_text, clean_text, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, NULL, %s)
            """
            cur.execute(sql, (
                meta_id, source_type, url, ref_html_id, title, raw_text, file_path
            ))
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        print(f"[DB ERROR FILE] {e}")
        return None
    finally:
        conn.close()


# ============================================================
# 메인 크롤러
# ============================================================
def crawl():
    driver = create_driver()

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

        # HTML 차단 패턴
        if is_blocked_url(url):
            print("    [SKIP] 차단된 URL:", url)
            visited.add(url)
            save_visited(url)
            save_queue(queue)
            continue

        # download.do 자체는 HTML 방문 금지
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

        # HTML → TEXT 저장 (로컬 파일)
        html_text = html_to_text(html)
        html_text_path = save_text(html_text, idx)

        # -----------------------------------------------------------
        # [추가] HTML DB 저장
        # -----------------------------------------------------------
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else ""
        current_db_id = None  # DB에 저장된 HTML의 ID (파일 연결용)

        try:
            # -----------------------------------------------------------
            # html_text(추출 텍스트)를 raw_text 인자로 전달
            # -----------------------------------------------------------
            current_db_id = insert_html_document(
                url=url,
                title=title,
                raw_text=html_text,
                meta_id=idx
            )
            print(f"    [DB] HTML Inserted (ID: {current_db_id})")
        except Exception as e:
            print(f"    [DB FAIL] HTML Insert failed: {e}")

        # metadata 저장 (JSONL - 기존 유지)
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

        # --------------------------
        # 링크 탐색
        # -------------------------
        file_seq = 0  # 이 페이지에서 발견한 파일 순번

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if href.startswith("javascript:") or href.startswith("mailto:"):
                continue

            next_url = canonicalize(urljoin(url, href))

            # 파일 링크 처리
            if is_file(next_url):
                file_seq += 1
                print(f"    [FILE LINK] {next_url}")

                # window.open 호출 전 다운로드 폴더 상태 저장
                before = set(os.listdir(FILE_DIR))
                file_path = None
                text_path = None
                extracted_text = ""

                try:
                    # 브라우저에 다운로드 시도 요청
                    driver.execute_script("window.open(arguments[0]);", next_url)
                    print("        → window.open으로 다운로드 시도")

                    # 새 파일이 생길 때까지 기다림
                    file_path = wait_for_new_file(FILE_DIR, before, timeout=30)
                    if file_path:
                        print("        → 다운로드 완료 파일:", file_path)
                    else:
                        print("        → 새 파일을 찾지 못함 (timeout)")
                except Exception as e:
                    print("        → 다운로드 시도 실패:", e)
                    file_path = None

                # 텍스트 추출
                if file_path and os.path.exists(file_path):
                    extracted_text = extract_by_ext(file_path)
                    if extracted_text.strip():
                        base = os.path.splitext(os.path.basename(file_path))[0]
                        text_path = os.path.join(FILE_TEXT_DIR, base + ".txt")

                        with open(text_path, "w", encoding="utf-8") as tf:
                            tf.write(extracted_text)

                        print("        → 텍스트 추출 완료:", text_path)

                        # -------------------------------------------------------
                        # [추가] 파일 DB 저장 (텍스트가 있을 경우만)
                        # -------------------------------------------------------
                        if current_db_id: # 부모 HTML이 정상적으로 DB에 들어갔다면
                            file_ext = os.path.splitext(file_path)[1].lower()
                            file_title = os.path.basename(file_path)
                            
                            # extracted_text(추출 텍스트)를 raw_text 인자로 전달
                            insert_file_document(
                                meta_id=f"file-{idx}-{file_seq}",
                                source_type=f"file:{file_ext}",
                                url=next_url,
                                file_path=file_path,
                                raw_text=extracted_text,
                                ref_html_id=idx,
                                title=file_title,
                            )
                            print(f"        → [DB] File Inserted Linked to ID {current_db_id}")
                    else:
                        print("        → 추출된 텍스트 없음")
                else:
                    print("        → 파일 경로 없음, 텍스트 추출 건너뜀")

                # 파일 메타데이터 기록 (JSONL - 기존 유지)
                ext = os.path.splitext(next_url)[1].lower()
                if not ext:
                    ext = ".unknown"

                file_meta = {
                    "id": f"file-{idx}-{file_seq}",
                    "type": f"file:{ext}",
                    "url": next_url,
                    "ref_page_url": url,
                    "ref_page_id": idx,
                    "file_path": file_path,      # 실제 저장된 파일 경로 (또는 None)
                    "text_path": text_path,      # 추출 텍스트 파일 경로 (또는 None)
                    "timestamp": time.time(),
                }
                with open(METADATA_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(file_meta, ensure_ascii=False) + "\n")

                # 이 링크는 파일이므로 HTML 큐에는 넣지 않고 다음 링크로
                continue

            # HTML 차단 URL은 방문 금지
            if is_blocked_url(next_url):
                continue

            # 외부 도메인 금지
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
    print("\n[DONE] 가천대 전체 크롤링 완료")


# 실행
if __name__ == "__main__":
    crawl()