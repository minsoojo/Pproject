#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
가천대학교 전체 크롤링 - 최종 통합 완성본 (100% 통합)
해결된 이슈:
- URL 중복 크롤링 방지(canonicalize 강화)
- 게시판 페이지네이션(현재페이지: 1/191) 파싱 기반 전 페이지 큐 삽입
- download.do direct 다운로드(requests) + synap/html 리다이렉트 차단
- download.do 파일명 "download.do" / 확장자 ".do" 오인 방지(헤더/힌트/Content-Type 보정)
- 일반 파일 URL(.../xxx.pdf) 확장자 최우선 확정(절대 .bin으로 오인하지 않음)
- 파일 저장명 충돌 방지(sha1(original_filename + url) 기반 저장)
- 임시 파일(.crdownload) 제외하고 완료 파일만 처리
- Selenium alert 무한 루프 방지(alert 발생 시 해당 URL 실패 처리)
- metadata에 original_filename 필수 저장 + saved_path + type(file:.pdf 등)
"""

import os
import time
import json
import re
import uuid
import hashlib
from collections import defaultdict
from urllib.parse import urljoin, urlparse, urldefrag, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

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

for d in [DATA_DIR, HTML_DIR, TEXT_DIR, FILE_DIR, FILE_TEXT_DIR]:
    os.makedirs(d, exist_ok=True)

VISITED_FILE = os.path.join(DATA_DIR, "visited.txt")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.jsonl")
QUEUE_FILE = os.path.join(DATA_DIR, "queue.txt")


# ============================================================
# 크롤링 타겟 / 제외 규칙
# ============================================================
FILE_EXTS = [
    ".pdf", ".hwp", ".hwpx",
    ".doc", ".docx",
    ".xls", ".xlsx",
    ".ppt", ".pptx",
    ".zip",
]

TARGET_KEYWORDS = [
    "bbs",
    "artclview.do",
    "subview.do",
]

BLOCK_PATTERNS = [
    "synapview.do",
    "synapviewer",
    "synap",
    "/eng/", "/english/",
    "/chi/", "/chn/", "/china/",
]

DOWNLOAD_URL_PATTERNS = ["download.do"]

# canonicalize에서 남길 쿼리 키(중복 URL 대량 생성 방지)
ALLOWED_QUERY_KEYS = {"article", "articleId", "pageIndex", "bbsIdx", "id"}


# ============================================================
# URL / 방문 제어
# ============================================================
def is_target_html_url(url: str) -> bool:
    return any(kw in url.lower() for kw in TARGET_KEYWORDS)

def is_download_url(url: str) -> bool:
    return any(pat in url.lower() for pat in DOWNLOAD_URL_PATTERNS)

def is_file(url: str) -> bool:
    lower = url.lower()
    if any(lower.endswith(ext) for ext in FILE_EXTS):
        return True
    if any(pat in lower for pat in DOWNLOAD_URL_PATTERNS):
        return True
    return False

def is_blocked_url(url: str) -> bool:
    lower = url.lower()
    # download.do 자체는 HTML로 방문 금지
    if is_download_url(lower):
        return True
    # synap / 다국어 사이트 차단
    if any(pat in lower for pat in BLOCK_PATTERNS):
        return True
    return False


# ============================================================
# canonicalize (URL 중복 제거 핵심)
# ============================================================
def canonicalize(url: str) -> str:
    # 1) fragment 제거
    url, _ = urldefrag(url)

    # 2) 중복 슬래시 정리 (:// 제외)
    url = re.sub(r'(?<!:)//+', '/', url)

    parsed = urlparse(url)

    # 3) query 정리: 필요한 키만 남기고 정렬
    qs = parse_qs(parsed.query)
    cleaned = {k: v for k, v in qs.items() if k in ALLOWED_QUERY_KEYS}
    encoded = urlencode(cleaned, doseq=True)

    # 4) path 정리
    path = re.sub(r'/+', '/', parsed.path)
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    parsed = parsed._replace(path=path, query=encoded, fragment="")
    return parsed.geturl()


# ============================================================
# visited / queue 파일 관리
# ============================================================
def load_visited():
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_visited(url: str):
    with open(VISITED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_queue(queue):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(queue))


# ============================================================
# Selenium 드라이버
# ============================================================
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--no-sandbox")

    # 서버 환경의 portable chromium 경로 (사용 환경에 맞게 유지)
    # chrome_options.binary_location = "/home/t25315/chromium-portable/chrome-linux/chrome"

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

    # service = Service("/home/t25315/chromium-portable/chromedriver_linux64/chromedriver")
    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(45)
    driver.set_script_timeout(45)
    return driver


# ============================================================
# alert 루프 방지 safe_get
# ============================================================
def safe_get(driver, url: str) -> bool:
    try:
        driver.get(url)
        time.sleep(0.2)

        # alert 감지 시 즉시 실패 처리 (무한 루프 방지)
        try:
            alert = driver.switch_to.alert
            print("[ALERT] 발생:", alert.text)
            alert.accept()
            return False
        except:
            pass

        return True

    except Exception as e:
        print(f"[ERROR safe_get] {e}")
        return False


# ============================================================
# 다운로드 관련 유틸
# ============================================================
def wait_for_download_complete(path: str, timeout=25):
    """
    새 파일이 생성되고, .crdownload가 아닌 파일이 등장하면 반환.
    """
    start = time.time()
    before = set(os.listdir(path))

    while time.time() - start < timeout:
        time.sleep(0.25)
        after = set(os.listdir(path))
        new = after - before
        if not new:
            continue

        done = [f for f in new if not f.endswith(".crdownload")]
        if done:
            newest = max(done, key=lambda f: os.path.getctime(os.path.join(path, f)))
            return os.path.join(path, newest)

    return None


def generate_file_id():
    return "file-" + uuid.uuid4().hex


def sha1(s: str):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def guess_ext_from_content_type(ct: str):
    c = (ct or "").lower()
    if "pdf" in c:
        return ".pdf"
    if "hwp" in c or "hangul" in c:
        return ".hwp"
    if "excel" in c or "sheet" in c or "ms-excel" in c:
        return ".xls"
    if "word" in c or "msword" in c:
        return ".doc"
    if "presentation" in c or "powerpoint" in c:
        return ".ppt"
    if "zip" in c:
        return ".zip"
    return ".bin"


def extract_filename_from_all_sources(url: str, headers=None, hint_name=None):
    """
    파일명/확장자 결정 우선순위 (핵심 패치 반영):
    1) URL path에 확장자가 명확히 존재하면 즉시 확정 (예: .../xxx.pdf)
    2) Content-Disposition: filename=...
    3) a 태그 텍스트(hint_name)에서 확장자
    4) 마지막 fallback: URL basename (확장자는 있을 수도/없을 수도)
    """
    # 1) URL 최우선
    url_path = os.path.basename(urlparse(url).path)
    url_ext = os.path.splitext(url_path)[1].lower()
    if url_ext in FILE_EXTS:
        return url_path, url_ext

    # 2) Content-Disposition
    if headers:
        cd = headers.get("content-disposition") or headers.get("Content-Disposition")
        if cd and "filename=" in cd:
            fname = cd.split("filename=")[-1].strip().strip('"\'')
            ext = os.path.splitext(fname)[1].lower()
            if ext in FILE_EXTS:
                return fname, ext

    # 3) hint_name
    if hint_name:
        hint_ext = os.path.splitext(hint_name)[1].lower()
        if hint_ext in FILE_EXTS:
            return hint_name, hint_ext

    # 4) fallback: URL basename
    base = url_path or "downloaded_file"
    ext = os.path.splitext(base)[1].lower()
    return base, ext


def download_file_direct(url: str, save_dir: str, hint_name=None):
    """
    requests로 직접 다운로드.
    - download.do 뿐 아니라 일반 파일 URL에도 적용 가능
    - text/html이면 synap viewer 등 리다이렉트로 판단하고 실패
    - 파일명은 URL 확장자 최우선 확정 + 헤더/힌트/ctype 보정
    """
    try:
        resp = requests.get(url, timeout=15, allow_redirects=True)
    except Exception as e:
        print(f"  [ERROR] direct download failed: {e}")
        return None, None, None

    ctype = resp.headers.get("content-type", "")
    if "text/html" in ctype.lower():
        # synap viewer 등으로 리다이렉트된 경우
        return None, None, None

    original, ext = extract_filename_from_all_sources(url, headers=resp.headers, hint_name=hint_name)

    # 확장자 이상(.do, 없음) → Content-Type 기반 추론
    if not ext or ext == ".do":
        ext = guess_ext_from_content_type(ctype)
        original = os.path.splitext(original)[0] + ext

    # 저장 파일명: 충돌 방지
    saved_filename = sha1(original + url) + ext
    save_path = os.path.join(save_dir, saved_filename)

    with open(save_path, "wb") as f:
        f.write(resp.content)

    return original, ext, save_path


def safe_open_new_tab(driver, url: str) -> bool:
    try:
        driver.execute_script("window.open(arguments[0]);", url)
        return True
    except UnexpectedAlertPresentException:
        return False
    except:
        return False


# ============================================================
# HTML → 텍스트
# ============================================================
def html_to_text(html: str):
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for tag in soup.find_all(["header", "footer"]):
        tag.decompose()

    selectors = [
        "#header", "#footer",
        ".header", ".footer",
        ".gnb", "#gnb",
        ".logo", ".site-map",
        ".sub-visual",
        ".top-banner", ".bottom-banner",
        ".quick-menu",
        ".breadcrumb", ".location",
        ".nav", ".menu",
        ".wrap-header", ".wrap-footer",
        "#wrap-header", "#wrap-footer",
    ]
    for s in selectors:
        try:
            for t in soup.select(s):
                t.decompose()
        except:
            pass

    main = None
    for sel in [
        "#content", "#contents",
        ".content", ".contents",
        ".article", ".board-view",
        "#container",
    ]:
        area = soup.select_one(sel)
        if area:
            main = area
            break

    if main is None:
        main = soup

    # 테이블을 markdown으로 변환 (선택)
    markdown_tables = []
    tables = main.find_all("table")
    for t in tables:
        rows = t.find_all("tr")
        table_lines = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [c.get_text(strip=True) for c in cells]
            if not any(cell_texts):
                continue
            table_lines.append("| " + " | ".join(cell_texts) + " |")
            if i == 0:
                table_lines.append("| " + " | ".join(["---"] * len(cell_texts)) + " |")
        if table_lines:
            markdown_tables.append("\n".join(table_lines))
    for t in tables:
        t.decompose()

    text = main.get_text("\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    body = "\n".join(lines)

    if markdown_tables:
        return body + "\n\n" + "\n\n".join(markdown_tables)
    return body


def save_text(content: str, idx: int):
    path = os.path.join(TEXT_DIR, f"{idx:05d}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ============================================================
# 게시판 페이지네이션 (현재페이지: 1/191)
# ============================================================
def enqueue_board_pages(current_url: str, soup: BeautifulSoup, seen: set, queue: list, stats: dict):
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"현재페이지:\s*(\d+)\s*/\s*(\d+)", txt)
    if not m:
        return

    total = int(m.group(2))
    base = current_url.split("?", 1)[0]

    for page in range(1, total + 1):
        u = canonicalize(f"{base}?pageIndex={page}")
        if u not in seen:
            seen.add(u)
            queue.append(u)

    stats[base].update(range(1, total + 1))


# ============================================================
# 메타데이터 저장
# ============================================================
def write_metadata(obj: dict):
    with open(METADATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ============================================================
# 메인 크롤러
# ============================================================
def crawl():
    driver = create_driver()

    # 매번 깨끗하게 시작(원하면 주석 처리)
    for p in [VISITED_FILE, QUEUE_FILE]:
        if os.path.exists(p):
            os.remove(p)

    visited = set()
    queue = [canonicalize(START_URL)]
    seen = set(queue)
    stats = defaultdict(set)

    idx = 0
    print("[START] Crawling Gachon University")

    while queue:
        url = queue.pop(0)
        idx += 1
        print(f"\n[{idx}] GET {url}")

        # 차단
        if is_blocked_url(url):
            print("  [SKIP] Blocked URL")
            visited.add(url)
            save_visited(url)
            save_queue(queue)
            continue

        # download.do는 HTML로 방문 금지
        if is_download_url(url):
            visited.add(url)
            save_visited(url)
            continue

        ok = safe_get(driver, url)
        if not ok:
            print("  [SKIP] alert/오류")
            save_queue(queue)
            continue

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")

        text_path = save_text(html_to_text(html), idx)
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # HTML 메타데이터 저장
        write_metadata({
            "id": idx,
            "type": "html",
            "url": url,
            "text": text_path,
            "title": title,
            "timestamp": time.time()
        })

        # 게시판 페이지네이션 처리
        enqueue_board_pages(url, soup, seen, queue, stats)
        save_queue(queue)

        # -------- 링크 탐색 --------
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            link_text = a.get_text(strip=True) or None

            if not href:
                continue
            if href.startswith("mailto:") or href.startswith("tel:"):
                continue
            if href.startswith("javascript:"):
                continue

            next_url = canonicalize(urljoin(url, href))
            parsed = urlparse(next_url)

            # 외부 도메인 제외
            if parsed.netloc and parsed.netloc != DOMAIN:
                continue

            # ---- 파일 처리 ----
            if is_file(next_url):
                file_id = generate_file_id()

                # 1) download.do는 direct 우선
                # 2) 일반 파일 URL도 direct 가능(여기서는 download.do 실패 시 fallback만 selenium)
                if "download.do" in next_url:
                    original, ext, save_path = download_file_direct(next_url, FILE_DIR, hint_name=link_text)
                    if save_path:
                        write_metadata({
                            "id": file_id,
                            "type": f"file:{ext}",
                            "url": next_url,
                            "ref_page_url": url,
                            "ref_page_id": idx,
                            "original_filename": original,
                            "saved_path": save_path,
                            "timestamp": time.time(),
                        })
                        continue
                    else:
                        print("  direct(download.do) 실패 → Selenium fallback")

                    ok2 = safe_open_new_tab(driver, next_url)
                    if not ok2:
                        print("  [ERROR] 탭 열기 실패")
                        continue

                    downloaded = wait_for_download_complete(FILE_DIR)
                    if not downloaded:
                        print("  [ERROR] 파일 다운로드 실패")
                        continue

                    # Selenium fallback도 filename 추론 우선순위 적용
                    original, ext = extract_filename_from_all_sources(next_url, headers=None, hint_name=link_text)
                    if not ext or ext == ".do":
                        # selenium fallback은 content-type을 모르는 경우가 많으니 .bin으로 두되,
                        # URL에 확장자가 있었다면 위에서 이미 잡혔음(패치)
                        ext = ".bin"
                        original = os.path.splitext(original)[0] + ext

                    saved_filename = sha1(original + next_url) + ext
                    save_path = os.path.join(FILE_DIR, saved_filename)

                    try:
                        os.rename(downloaded, save_path)
                    except:
                        save_path = downloaded

                    write_metadata({
                        "id": file_id,
                        "type": f"file:{ext}",
                        "url": next_url,
                        "ref_page_url": url,
                        "ref_page_id": idx,
                        "original_filename": original,
                        "saved_path": save_path,
                        "timestamp": time.time(),
                    })
                    continue

                # ---- 일반 파일 URL(.pdf 등)은 Selenium 쓰지 말고 direct로 처리 (가장 안정적) ----
                original, ext, save_path = download_file_direct(next_url, FILE_DIR, hint_name=link_text)
                if save_path:
                    write_metadata({
                        "id": file_id,
                        "type": f"file:{ext}",
                        "url": next_url,
                        "ref_page_url": url,
                        "ref_page_id": idx,
                        "original_filename": original,
                        "saved_path": save_path,
                        "timestamp": time.time(),
                    })
                else:
                    # direct 실패하면 최후 fallback: selenium
                    print("  direct(file) 실패 → Selenium fallback")

                    ok2 = safe_open_new_tab(driver, next_url)
                    if not ok2:
                        print("  [ERROR] 탭 열기 실패")
                        continue

                    downloaded = wait_for_download_complete(FILE_DIR)
                    if not downloaded:
                        print("  [ERROR] 파일 다운로드 실패")
                        continue

                    original, ext = extract_filename_from_all_sources(next_url, headers=None, hint_name=link_text)
                    if not ext or ext == ".do":
                        ext = ".bin"
                        original = os.path.splitext(original)[0] + ext

                    saved_filename = sha1(original + next_url) + ext
                    save_path = os.path.join(FILE_DIR, saved_filename)

                    try:
                        os.rename(downloaded, save_path)
                    except:
                        save_path = downloaded

                    write_metadata({
                        "id": file_id,
                        "type": f"file:{ext}",
                        "url": next_url,
                        "ref_page_url": url,
                        "ref_page_id": idx,
                        "original_filename": original,
                        "saved_path": save_path,
                        "timestamp": time.time(),
                    })

                continue

            # ---- HTML만 BFS 대상 ----
            if is_blocked_url(next_url):
                continue

            if not is_target_html_url(next_url) and next_url != START_URL:
                continue

            if next_url not in seen:
                seen.add(next_url)
                queue.append(next_url)

        visited.add(url)
        save_visited(url)
        save_queue(queue)

    driver.quit()

    print("\n[PAGINATION STATS]")
    for base, pages in stats.items():
        print(f"{base} → {len(pages)} pages")

    print("\n[DONE] Gachon full crawl complete.")


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    crawl()
