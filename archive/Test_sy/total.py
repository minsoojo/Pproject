# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

# import os
# import time
# import json
# import sqlite3
# from datetime import datetime
# from pathlib import Path
# from urllib.parse import urljoin, urlparse, urldefrag

# from bs4 import BeautifulSoup

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import UnexpectedAlertPresentException
# from webdriver_manager.chrome import ChromeDriverManager


# # ============================================================
# # 크롤링 설정
# # ============================================================
# START_URL = "https://www.gachon.ac.kr/kor/3120/subview.do"
# DOMAIN = "www.gachon.ac.kr"

# DATA_DIR = "data"
# HTML_DIR = os.path.join(DATA_DIR, "html")
# TEXT_DIR = os.path.join(DATA_DIR, "text")
# FILE_DIR = os.path.join(DATA_DIR, "files")
# FILE_TEXT_DIR = os.path.join(DATA_DIR, "file_text")

# os.makedirs(HTML_DIR, exist_ok=True)
# os.makedirs(TEXT_DIR, exist_ok=True)
# os.makedirs(FILE_DIR, exist_ok=True)
# os.makedirs(FILE_TEXT_DIR, exist_ok=True)

# VISITED_FILE = "data/visited.txt"
# METADATA_FILE = "data/metadata.jsonl"
# QUEUE_FILE = "data/queue.txt"


# # ============================================================
# # DB 설정
# #   - 필요하면 BASE_DIR / DB_PATH 수정해서 사용
# # ============================================================
# BASE_DIR = Path("/Users/kaia/Desktop/학교/Pp")
# BASE_DIR.mkdir(parents=True, exist_ok=True)
# DB_PATH = BASE_DIR / "gachon_raw_test.db"


# # ============================================================
# # 파일 확장자 + 다운로드 URL 패턴
# # ============================================================
# FILE_EXTS = [
#     ".pdf", ".hwp", ".hwpx",
#     ".doc", ".docx",
#     ".xls", ".xlsx",
#     ".ppt", ".pptx",
#     ".zip"
# ]

# DOWNLOAD_URL_PATTERNS = [
#     "download.do",
# ]

# # 추가 차단 패턴: synap 뷰어 + 영어/중국어 사이트
# BLOCK_PATTERNS = [
#     "synap",
#     "synapview.do",
#     "synapviewer",

#     "/eng/",
#     "/english/",
#     "/chi/",
#     "/chn/",
#     "/china/",
# ]


# # ============================================================
# # DB 초기화
# # ============================================================
# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute(
#         """
#         CREATE TABLE IF NOT EXISTS documents (
#             id           INTEGER PRIMARY KEY AUTOINCREMENT,
#             url          TEXT NOT NULL,
#             source_type  TEXT,
#             title        TEXT,
#             raw_text     TEXT NOT NULL,
#             clean_text   TEXT,
#             meta_json    TEXT,
#             crawled_at   TEXT,
#             processed_at TEXT
#         );
#         """
#     )
#     conn.commit()
#     conn.close()
#     print(f"[INFO] DB 초기화 완료: {DB_PATH}")


# # ============================================================
# # URL 필터링 함수
# # ============================================================
# def is_file(url: str) -> bool:
#     u = url.lower()

#     if any(u.endswith(ext) for ext in FILE_EXTS):
#         return True

#     if any(pat in u for pat in DOWNLOAD_URL_PATTERNS):
#         return True

#     return False


# def is_download_url(url: str) -> bool:
#     u = url.lower()
#     return any(pat in u for pat in DOWNLOAD_URL_PATTERNS)


# def is_blocked_url(url: str) -> bool:
#     """HTML 방문에서 제외해야 할 URL"""
#     u = url.lower()

#     # 1) download.do → HTML 방문 금지
#     if any(pat in u for pat in DOWNLOAD_URL_PATTERNS):
#         return True

#     # 2) synap 문서뷰어 페이지
#     if any(pat in u for pat in ["synap", "synapview", "synapviewer"]):
#         return True

#     # 3) 영어/중국어 사이트
#     if any(pat in u for pat in ["/eng/", "/english/", "/chi/", "/chn/", "/china/"]):
#         return True

#     return False


# # ============================================================
# # Selenium 드라이버 생성 (1번 스크립트 기반)
# # ============================================================
# def create_driver():
#     chrome_options = Options()

#     # headless 금지 (필요하면 주석 해제해서 사용)
#     # chrome_options.add_argument("--headless=new")

#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-notifications")
#     chrome_options.add_argument("--disable-popup-blocking")

#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/120.0.0.0 Safari/537.36"
#     )

#     # PDF 뷰어 끄고 자동 다운로드
#     prefs = {
#         "download.default_directory": os.path.abspath(FILE_DIR),
#         "download.prompt_for_download": False,
#         "download.directory_upgrade": True,
#         "plugins.always_open_pdf_externally": True,
#     }
#     chrome_options.add_experimental_option("prefs", prefs)

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     driver.set_page_load_timeout(10)
#     driver.set_script_timeout(10)

#     return driver


# # ============================================================
# # 유틸 함수
# # ============================================================
# def canonicalize(url):
#     url, _ = urldefrag(url)
#     return url


# def load_visited():
#     if os.path.exists(VISITED_FILE):
#         with open(VISITED_FILE) as f:
#             return set(line.strip() for line in f)
#     return set()


# def save_visited(url):
#     with open(VISITED_FILE, "a") as f:
#         f.write(url + "\n")


# def load_queue():
#     if os.path.exists(QUEUE_FILE):
#         with open(QUEUE_FILE) as f:
#             return [line.strip() for line in f if line.strip()]
#     return []


# def save_queue(queue):
#     with open(QUEUE_FILE, "w") as f:
#         f.write("\n".join(queue))


# def save_text(content, idx):
#     """텍스트 파일로 저장 (기존 로직 유지)"""
#     fpath = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
#     with open(fpath, "w", encoding="utf-8") as f:
#         f.write(content)
#     return fpath


# # ============================================================
# # HTML → "본문" 텍스트 추출 (2번 스크립트의 extract_main_text 사용)
# # ============================================================
# def extract_main_text(html: str) -> str:
#     soup = BeautifulSoup(html, "html.parser")

#     # 1) 확실히 필요 없는 태그 제거
#     for tag in soup(["script", "style", "noscript"]):
#         tag.decompose()

#     # 2) header/footer 태그 직접 제거
#     for tag in soup.find_all(["header", "footer"]):
#         tag.decompose()

#     # 3) 사이트에서 자주 쓰는 헤더/푸터 CSS ID/class 제거
#     header_footer_selectors = [
#         "#header",          # 가천대 최상단 헤더
#         "#footer",          # 페이지 푸터
#         ".header",          # 공통 header class
#         ".footer",          # 공통 footer class
#         ".gnb",             # 글로벌 네비게이션 바
#         "#gnb",             # 메뉴
#         ".logo",            # 상단 로고 영역
#         ".site-map",        # 사이트맵
#         ".sub-visual",      # 서브 비주얼 이미지
#         ".top-banner",      # 상단 배너
#         ".bottom-banner",   # 하단 배너
#         ".quick-menu",      # 퀵메뉴
#         ".breadcrumb",      # 현재 위치 breadcrumb
#         ".location",        # 위치 표시 UI
#         ".nav",             # 네비게이션
#         ".menu",            # 메뉴 전체
#         ".wrap-header",
#         ".wrap-footer",
#         "#wrap-header",
#         "#wrap-footer",
#         ".sns-area",
#         ".top-menu",
#     ]

#     for selector in header_footer_selectors:
#         for tag in soup.select(selector):
#             tag.decompose()

#     # 4) 가천대 본문 영역 (#content, #contents, .content-wrapper 등)
#     main_candidates = [
#         "#content",
#         "#contents",
#         ".content",
#         ".contents",
#         ".content-area",
#         ".content-wrapper",
#         ".sub-content",
#         ".sub-contents",
#         ".article",
#         ".board-view",     # 게시판 본문
#         "#container",
#     ]

#     main = None
#     for sel in main_candidates:
#         area = soup.select_one(sel)
#         if area:
#             main = area
#             break

#     if main is None:
#         main = soup  # fallback

#     text = main.get_text(separator="\n")
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

#     return "\n".join(lines)


# # ============================================================
# # 안전 GET
# # ============================================================
# def safe_get(driver, url):
#     try:
#         driver.get(url)
#         # JS 렌더링 여유
#         time.sleep(2)

#         try:
#             alert = driver.switch_to.alert
#             print("[ALERT FOUND]", alert.text)
#             alert.accept()
#             return False
#         except Exception:
#             pass

#         return True

#     except Exception as e:
#         print(f"[ERROR safe_get] {e}")
#         return False


# # ============================================================
# # 메인 크롤러 (DB 저장 포함)
# # ============================================================
# def crawl():
#     driver = create_driver()

#     visited = load_visited()
#     queue = load_queue()

#     start = canonicalize(START_URL)
#     if not queue:
#         queue.append(start)

#     seen = set(visited) | set(queue)
#     idx = len(visited)

#     # DB 연결
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()

#     print("[INFO] 가천대 전체 크롤링 시작")
#     print(f"[INFO] 방문 완료 {len(visited)}개")
#     print(f"[INFO] 대기 중 {len(queue)}개\n")

#     try:
#         while queue:
#             url = queue.pop(0)
#             idx += 1

#             print(f"\n[{idx}] GET {url}")

#             # 🔥 HTML 차단 패턴
#             if is_blocked_url(url):
#                 print("    [SKIP] 차단된 URL:", url)
#                 visited.add(url)
#                 save_visited(url)
#                 save_queue(queue)
#                 continue

#             # 🔥 download.do 자체는 HTML 방문 금지
#             if is_download_url(url):
#                 print("    [SKIP] download URL:", url)
#                 visited.add(url)
#                 save_visited(url)
#                 save_queue(queue)
#                 continue

#             # 방문
#             success = safe_get(driver, url)
#             if not success:
#                 print("[SKIP] alert/오류:", url)
#                 visited.add(url)
#                 save_visited(url)
#                 save_queue(queue)
#                 continue

#             html = driver.page_source
#             soup = BeautifulSoup(html, "html.parser")
#             title = soup.title.get_text(strip=True) if soup.title else ""

#             # ============================
#             # 1) 본문 텍스트 추출 (DB용)
#             # ============================
#             main_text = extract_main_text(html)

#             # ============================
#             # 2) 텍스트 파일로도 저장 (기존 구조 유지)
#             # ============================
#             text_file_path = save_text(main_text, idx)

#             # ============================
#             # 3) JSONL metadata 저장
#             # ============================
#             metadata = {
#                 "id": idx,
#                 "type": "html",
#                 "url": url,
#                 "text": text_file_path,
#                 "title": title,
#                 "timestamp": time.time()
#             }
#             with open(METADATA_FILE, "a", encoding="utf-8") as f:
#                 f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

#             # ============================
#             # 4) DB에 INSERT
#             # ============================
#             cur.execute(
#                 """
#                 INSERT INTO documents
#                     (url, source_type, title, raw_text, clean_text, meta_json, crawled_at, processed_at)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                 """,
#                 (
#                     url,
#                     "html",
#                     title,
#                     main_text,
#                     None,  # clean_text 아직 없음
#                     json.dumps(metadata, ensure_ascii=False),
#                     datetime.now().isoformat(timespec="seconds"),
#                     None,
#                 ),
#             )
#             conn.commit()

#             # -------------------------
#             # 링크 탐색
#             # -------------------------
#             for a in soup.find_all("a", href=True):
#                 href = a["href"].strip()

#                 if href.startswith("javascript:") or href.startswith("mailto:"):
#                     continue

#                 next_url = canonicalize(urljoin(url, href))

#                 # 🔥 파일 처리
#                 if is_file(next_url):
#                     print(f"    [FILE LINK] {next_url}")

#                     ext = os.path.splitext(next_url)[1].lower()
#                     if ext == "":
#                         ext = ".temp"

#                     try:
#                         driver.execute_script("window.open(arguments[0]);", next_url)
#                     except Exception:
#                         pass

#                     file_meta = {
#                         "id": f"file-{idx}-{len(os.listdir(FILE_DIR)) + 1}",
#                         "type": f"file:{ext}",
#                         "url": next_url,
#                         "ref_page_url": url,
#                         "ref_page_id": idx,
#                         "file_path": None,
#                         "timestamp": time.time()
#                     }
#                     with open(METADATA_FILE, "a", encoding="utf-8") as f:
#                         f.write(json.dumps(file_meta, ensure_ascii=False) + "\n")
#                     continue

#                 # 🔥 HTML 차단 URL은 방문 금지
#                 if is_blocked_url(next_url):
#                     continue

#                 # 🔥 외부 도메인 금지
#                 if urlparse(next_url).netloc != DOMAIN:
#                     continue

#                 if next_url not in seen:
#                     seen.add(next_url)
#                     queue.append(next_url)
#                     save_queue(queue)

#             visited.add(url)
#             save_visited(url)
#             save_queue(queue)

#     finally:
#         conn.close()
#         driver.quit()
#         print("\n[DONE] 가천대 전체 크롤링 + DB 저장 완료")


# # ============================================================
# # 실행
# # ============================================================
# def main():
#     init_db()
#     crawl()


# if __name__ == "__main__":
#     main()


# path = "/home/t25315/data/yo_txt/★ 2024 요람(총람 및 교양) 2024.05.24.txt"
# f = open(path, "r", encoding="cp949")
# text = f.read()
# f.close()
# print(text)

# convert_encoding.py

src_path = "/home/t25315/data/yo_txt/2020_가천대학교_요람(총람).txt"          # 원본 파일 (CP949)
dst_path = "/home/t25315/data/yo_txt/yo_txt_encoding/2020_요람(총람)_raw_utf8.txt"     # 변환해서 저장할 파일 (UTF-8)

with open(src_path, "r", encoding="cp949", errors="ignore") as f:
    text = f.read()

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(text)

print("변환 완료:", dst_path)
