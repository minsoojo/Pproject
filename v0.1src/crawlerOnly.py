# # 크롤링 수행 코드

# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

# import os
# import time
# import json
# from urllib.parse import urljoin, urlparse, urldefrag
# from bs4 import BeautifulSoup

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import UnexpectedAlertPresentException
# from webdriver_manager.chrome import ChromeDriverManager


# # ============================================================
# # 설정
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
#     # "synap",
#     "synapview.do",
#     # "synapviewer",

#     "/eng/",
#     "/english/",
#     "/chi/",
#     "/chn/",
#     "/china/",
# ]


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
# # 드라이버 생성
# # ============================================================
# def create_driver():
#     chrome_options = Options()

#     # headless 금지
#     chrome_options.add_argument("--headless=new")

#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-notifications")
#     chrome_options.add_argument("--disable-popup-blocking")

#     chrome_options.binary_location = "/home/t25315/chromium-portable/chrome-linux/chrome"
    

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

#     # service = Service(ChromeDriverManager().install())
#     service = Service("/home/t25315/chromium-portable/chromedriver_linux64/chromedriver")
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     driver.set_page_load_timeout(14)
#     driver.set_script_timeout(14)

#     return driver


# # ============================================================
# # 유틸 함수
# # ============================================================
# # def canonicalize(url):
# #     url, _ = urldefrag(url)
# #     return url
# import re
# from urllib.parse import urlparse, urlunparse, urldefrag
# def canonicalize(url: str) -> str:
#     # 1) fragment 제거 (# 뒤 제거)
#     url, _ = urldefrag(url)

#     # 2) 중복 슬래시 정리 (:// 제외)
#     url = re.sub(r'(?<!:)//+', '/', url)

#     # 3) '..' 같은 이상한 dot 패턴 정리
#     url = url.replace("..do", ".do")
#     url = url.replace("..html", ".html")
#     url = url.replace("..php", ".php")
    
#     # 4) 마지막에 '/' 붙지 않게
#     if url.endswith("/"):
#         url = url[:-1]

#     # 5) URL 구조 다시 조합
#     parsed = urlparse(url)
#     normalized = urlunparse(parsed)

#     return normalized


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


# # def html_to_text(html):
# #     soup = BeautifulSoup(html, "html.parser")
# #     for tag in soup(["script", "style", "noscript", "footer", "nav"]):
# #         tag.decompose()

# #     text = soup.get_text(separator="\n")
# #     return "\n".join(x.strip() for x in text.splitlines() if x.strip())


# def html_to_text(html: str) -> str:
#     # soup = BeautifulSoup(html, "html.parser")
#     soup = BeautifulSoup(html, "lxml")

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

#     # for selector in header_footer_selectors:
#     #     for tag in soup.select(selector):
#     #         tag.decompose()
#     for selector in header_footer_selectors:
#         try:
#             for tag in soup.select(selector):
#                 tag.decompose()
#         except Exception:
#             continue

#     # 4) 가천대 본문 영역(#content, #contents, .content-wrapper 등)
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
#         candidates = soup.find_all(["article", "section"])
#         if candidates:
#             main = max(
#                 candidates,
#                 key=lambda c: len(c.get_text(strip=True))
#             )

#     if main is None:  
#         main = soup  # fallback

#     markdown_tables = []

#     tables = main.find_all("table")
#     for t in tables:
#         rows = t.find_all("tr")
#         table_lines = []
#         for i, row in enumerate(rows):
#             cells = row.find_all(["th", "td"])
#             cell_texts = [c.get_text(strip=True) for c in cells]
#             # 빈 행은 스킵
#             if not any(cell_texts):
#                 continue

#             # 본문
#             table_lines.append("| " + " | ".join(cell_texts) + " |")

#             # 첫 행을 헤더로 보고 구분선 추가
#             if i == 0:
#                 table_lines.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")

#         if table_lines:
#             markdown_tables.append("\n".join(table_lines))

#     # 5-2) table 을 DOM에서 제거해서 본문 텍스트와 중복 방지
#     for t in tables:
#         t.decompose()

#     # 6) 본문 텍스트
#     text = main.get_text(separator="\n")
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
#     body_text = "\n".join(lines)

#     # 7) 테이블을 markdown으로 붙여줌
#     if markdown_tables:
#         return body_text + "\n\n" + "\n\n".join(markdown_tables)
#     return body_text    

# def save_text(content, idx):
#     fpath = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
#     with open(fpath, "w", encoding="utf-8") as f:
#         f.write(content)
#     return fpath


# # ============================================================
# # 안전 GET
# # ============================================================
# def safe_get(driver, url):
#     try:
#         driver.get(url)
#         time.sleep(0.1)

#         try:
#             alert = driver.switch_to.alert
#             print("[ALERT FOUND]", alert.text)
#             alert.accept()
#             return False
#         except:
#             pass

#         return True

#     except Exception as e:
#         print(f"[ERROR safe_get] {e}")
#         return False
    
# # ============================================================
# # wait_for_download
# # ============================================================

# def wait_for_download(dir_path, timeout=15):
#     """
#     다운로드 디렉토리를 감시하여 새 파일이 생성되면 해당 경로를 반환
#     """
#     before = set(os.listdir(dir_path))
#     for _ in range(timeout * 10):  # 0.1초 간격
#         time.sleep(0.1)
#         after = set(os.listdir(dir_path))
#         new_files = after - before
#         if new_files:
#             return os.path.join(dir_path, list(new_files)[0])
#     return None
# # ============================================================
# # 메인 크롤러
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

#     print("[INFO] 가천대 전체 크롤링 시작")
#     print(f"[INFO] 방문 완료 {len(visited)}개")
#     print(f"[INFO] 대기 중 {len(queue)}개\n")

#     while queue:
#         url = queue.pop(0)
#         idx += 1

#         print(f"\n[{idx}] GET {url}")
        
#         # 🔥 HTML 차단 패턴
#         if is_blocked_url(url):
#             print("    [SKIP] 차단된 URL:", url)
#             visited.add(url)
#             save_visited(url)
#             save_queue(queue)
#             continue

#         # 🔥 download.do 자체는 HTML 방문 금지
#         if is_download_url(url):
#             print("    [SKIP] download URL:", url)
#             visited.add(url)
#             save_visited(url)
#             save_queue(queue)
#             continue

#         # 방문
#         success = safe_get(driver, url)
#         if not success:
#             print("[SKIP] alert/오류:", url)
#             visited.add(url)
#             save_visited(url)
#             save_queue(queue)
#             continue

#         html = driver.page_source

#         # HTML → TEXT 저장
#         html_text = html_to_text(html)
#         html_text_path = save_text(html_text, idx)

#         # metadata 저장
#         soup = BeautifulSoup(html, "lxml")
#         title = soup.title.string if soup.title else ""

#         metadata = {
#             "id": idx,
#             "type": "html",
#             "url": url,
#             "text": html_text_path,
#             "title": title,
#             "timestamp": time.time()
#         }
#         with open(METADATA_FILE, "a", encoding="utf-8") as f:
#             f.write(json.dumps(metadata, ensure_ascii=False) + "\n")    

#         # -------------------------
#         # 링크 탐색
#         # -------------------------
#         for a in soup.find_all("a", href=True):
#             href = a["href"].strip()

#             if href.startswith("javascript:") or href.startswith("mailto:"):
#                 continue

#             next_url = canonicalize(urljoin(url, href))

#             if next_url.startswith("http://"):
#                 continue

#             # 🔥 파일 처리
#             if is_file(next_url):
#                 print(f"    [FILE LINK] {next_url}")

#                 ext = os.path.splitext(next_url)[1].lower()
#                 if ext == "":
#                     ext = ".temp"

#                 try:
#                     driver.execute_script("window.open(arguments[0]);", next_url)
#                 except:
#                     pass
                
#                 downloaded_path = wait_for_download(FILE_DIR)

#                 file_meta = {
#                     "id": f"file-{idx}-{len(os.listdir(FILE_DIR))+1}",
#                     "type": f"file:{ext}",
#                     "url": next_url,
#                     "ref_page_url": url,
#                     "ref_page_id": idx,
#                     "file_path": downloaded_path,
#                     "timestamp": time.time()
#                 }
#                 with open(METADATA_FILE, "a", encoding="utf-8") as f:
#                     f.write(json.dumps(file_meta, ensure_ascii=False) + "\n")
#                 continue

#             # 🔥 HTML 차단 URL은 방문 금지
#             if is_blocked_url(next_url):
#                 continue

#             # 🔥 외부 도메인 금지
#             if urlparse(next_url).netloc != DOMAIN:
#                 continue

#             if next_url not in seen:
#                 seen.add(next_url)
#                 queue.append(next_url)
#                 save_queue(queue)

#         visited.add(url)
#         save_visited(url)
#         save_queue(queue)

#     driver.quit()
#     print("\n[DONE] 가천대 전체 크롤링 완료")


# # 실행
# if __name__ == "__main__":
#     crawl()

# 크롤링 수행 코드

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager


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
# 타겟 HTML URL 판별 (bbs, artclView.do 등)
# ============================================================
TARGET_KEYWORDS = [
    "bbs",
    "artclview.do",   # 실제 소스는 대소문자 섞여있을 수 있으니 소문자로 통일
    "artclVIew.do",
    "subview.do",
]

def is_target_html_url(url: str) -> bool:
    u = url.lower()
    return any(kw.lower() in u for kw in TARGET_KEYWORDS)


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

    # headless 금지
    chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    chrome_options.binary_location = "/home/t25315/chromium-portable/chrome-linux/chrome"
    

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

    # service = Service(ChromeDriverManager().install())
    service = Service("/home/t25315/chromium-portable/chromedriver_linux64/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)

    return driver


# ============================================================
# 유틸 함수
# ============================================================
# def canonicalize(url):
#     url, _ = urldefrag(url)
#     return url
import re
from urllib.parse import urlparse, urlunparse, urldefrag
def canonicalize(url: str) -> str:
    # 1) fragment 제거 (# 뒤 제거)
    url, _ = urldefrag(url)

    # 2) 중복 슬래시 정리 (:// 제외)
    url = re.sub(r'(?<!:)//+', '/', url)

    # 3) '..' 같은 이상한 dot 패턴 정리
    url = url.replace("..do", ".do")
    url = url.replace("..html", ".html")
    url = url.replace("..php", ".php")
    
    # 4) 마지막에 '/' 붙지 않게
    if url.endswith("/"):
        url = url[:-1]

    # 5) URL 구조 다시 조합
    parsed = urlparse(url)
    normalized = urlunparse(parsed)

    return normalized

def extract_pagination_urls(current_url: str, href: str):
    """
    javascript:로 된 페이지네이션 링크에서 실제 페이지 URL을 만들어내는 함수.

    예시 패턴 (가정):
      - javascript:fnList('3120','2')
      - javascript:goPage(2)

    실제로 가천대 소스에서 페이지네이션 href를 보고
    아래 정규식/URL 생성 부분을 맞춰서 조정하면 됨.
    """
    urls = []

    # 패턴 1) fnList('게시판ID','페이지번호')
    m = re.search(r"fnList\('(\d+)'\s*,\s*'(\d+)'\)", href)
    if m:
        board_id = m.group(1)   # 3120
        page_no  = m.group(2)   # 2
        base = current_url.split("?", 1)[0]

        # ⚠️ 가천대 실제 파라미터 이름에 맞게 수정 필요
        # 예: pageIndex, page, pageNo 등
        urls.append(f"{base}?pageIndex={page_no}")
        return urls

    # 패턴 2) goPage(2) 같은 형태
    m = re.search(r"goPage\((\d+)\)", href)
    if m:
        page_no = m.group(1)
        base = current_url.split("?", 1)[0]
        urls.append(f"{base}?pageIndex={page_no}")
        return urls

    return urls


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


# def html_to_text(html):
#     soup = BeautifulSoup(html, "html.parser")
#     for tag in soup(["script", "style", "noscript", "footer", "nav"]):
#         tag.decompose()

#     text = soup.get_text(separator="\n")
#     return "\n".join(x.strip() for x in text.splitlines() if x.strip())


def html_to_text(html: str) -> str:
    # soup = BeautifulSoup(html, "html.parser")
    soup = BeautifulSoup(html, "lxml")

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

    # for selector in header_footer_selectors:
    #     for tag in soup.select(selector):
    #         tag.decompose()
    for selector in header_footer_selectors:
        try:
            for tag in soup.select(selector):
                tag.decompose()
        except Exception:
            continue

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
# wait_for_download
# ============================================================

def wait_for_download(dir_path, timeout=15):
    """
    다운로드 디렉토리를 감시하여 새 파일이 생성되면 해당 경로를 반환
    """
    before = set(os.listdir(dir_path))
    for _ in range(timeout * 10):  # 0.1초 간격
        time.sleep(0.1)
        after = set(os.listdir(dir_path))
        new_files = after - before
        if new_files:
            return os.path.join(dir_path, list(new_files)[0])
    return None

# ============================================================
# 메인 크롤러
# ============================================================
def crawl():
    driver = create_driver()
    
    for path in [VISITED_FILE, QUEUE_FILE]:
        if os.path.exists(path):
            os.remove(path)

    # visited = load_visited()
    # queue = load_queue()
    
    start = canonicalize(START_URL)

    visited = set()
    queue = [start]

    seen = set(queue)
    idx = len(visited)

    # if not queue:
    #     queue.append(start)

    # seen = set(visited) | set(queue)
    # idx = len(visited)

    pagination_stats = defaultdict(set)

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
            print("[SKIP] alert/오류 (재시도 후보):", url)
            # ❗ 실패한 URL은 visited에 넣지 않는다 (나중에 다시 돌릴 수 있게)
            save_queue(queue)
            continue

        html = driver.page_source

        # HTML → TEXT 저장
        html_text = html_to_text(html)
        html_text_path = save_text(html_text, idx)

        # metadata 저장
        soup = BeautifulSoup(html, "lxml")
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

        # -------------------------
        # 링크 탐색
        # -------------------------
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            # 1) javascript: 링크 → 페이지네이션만 특별 처리
            if href.startswith("javascript:"):
                paginated_urls = extract_pagination_urls(url, href)
                if paginated_urls:
                    for p in paginated_urls:
                        next_url = canonicalize(urljoin(url, p))

                        # 외부 도메인 방지
                        if urlparse(next_url).netloc != DOMAIN:
                            continue

                        if next_url not in seen:
                            seen.add(next_url)
                            queue.append(next_url)
                            save_queue(queue)

                            # 통계용: base_url + pageIndex 기록
                            base = next_url.split("?", 1)[0]
                            m_page = re.search(r"pageIndex=(\d+)", next_url)
                            if m_page:
                                page_no = int(m_page.group(1))
                                pagination_stats[base].add(page_no)

                            print(f"    [PAGINATION] {href} -> {next_url}")

                # 페이지네이션이 아니거나, 처리 실패한 javascript:는 그냥 스킵
                continue

            # 2) mailto:는 그대로 스킵
            if href.startswith("mailto:"):
                continue

            # 3) 나머지 일반 href는 기존과 동일
            next_url = canonicalize(urljoin(url, href))

            if next_url.startswith("http://"):
                continue

            if is_file(next_url):
                print(f"    [FILE LINK] {next_url}")

                ext = os.path.splitext(next_url)[1].lower()
                if ext == "":
                    ext = ".temp"

                try:
                    driver.execute_script("window.open(arguments[0]);", next_url)
                except:
                    pass
                
                downloaded_path = wait_for_download(FILE_DIR)

                file_meta = {
                    "id": f"file-{idx}-{len(os.listdir(FILE_DIR))+1}",
                    "type": f"file:{ext}",
                    "url": next_url,
                    "ref_page_url": url,
                    "ref_page_id": idx,
                    "file_path": downloaded_path,
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

            if not is_target_html_url(next_url) and next_url != START_URL:
                # 게시글/게시판 URL이 아니면 BFS 대상에서 제외
                # (파일 링크는 위에서 이미 처리했으므로 도달 X)
                continue

            if next_url not in seen:
                seen.add(next_url)
                queue.append(next_url)
                save_queue(queue)


        visited.add(url)
        save_visited(url)
        save_queue(queue)

    
    driver.quit()

    # 📊 페이지네이션 요약
    print("\n[PAGINATION STATS]")
    if not pagination_stats:
        print("  (no pagination info collected)")
    else:
        for base, pages in pagination_stats.items():
            if not pages:
                continue
            pages_sorted = sorted(pages)
            print(f"  {base}: visited pages {pages_sorted} (total {len(pages_sorted)})")

    print("\n[DONE] 가천대 전체 크롤링 완료")



# 실행
if __name__ == "__main__":
    crawl()