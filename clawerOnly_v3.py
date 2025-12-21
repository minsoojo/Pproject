#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
v3 크롤러: 최소 동작 버전 (HTML + 첨부파일 direct download + v3 metadata.jsonl 기록)

목표
- HTML 페이지를 BFS로 순회 (동일 도메인)
- 각 HTML마다 meta_id 생성 (canonical_url 기반, 재수집해도 불변)
- HTML에 달린 첨부파일은 "같은 meta_id"로 file metadata 저장
- metadata_v3.jsonl 생성
- text는 data/text/{meta_id}.txt 로 저장
- 파일은 data/files/sha1(original+url)+ext 로 저장

주의
- 이 버전은 Selenium 없이 requests 기반 (최소 동작)
- JS 렌더링/iframe 내부/특수 뷰어(synap 등)는 수집 품질이 떨어질 수 있음
- 그래도 "v3 메타데이터 구조"와 "안정적인 ID/묶음"은 완성된 형태

실행:
  python crawler_v3_min.py

필요 패키지:
  pip install requests beautifulsoup4 lxml
  (선택) pip install trafilatura  # HTML 본문 추출 품질 개선
"""

import os
import re
import json
import time
import hashlib
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

# =========================
# 설정
# =========================
START_URL = "https://www.gachon.ac.kr/kor/3120/subview.do"
DOMAIN = "www.gachon.ac.kr"

DATA_DIR = "data_v3"
TEXT_DIR = os.path.join(DATA_DIR, "text")
FILES_DIR = os.path.join(DATA_DIR, "files")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

METADATA_PATH = os.path.join(DATA_DIR, "metadata_v3.jsonl")
VISITED_PATH = os.path.join(LOGS_DIR, "visited.txt")
QUEUE_PATH = os.path.join(LOGS_DIR, "queue.txt")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

TIMEOUT = 20
SLEEP_BETWEEN = 0.1
MAX_PAGES = 2000  # 최소 동작 버전이라 안전장치 (원하면 늘려도 됨)

FILE_EXTS = {
    ".pdf", ".hwp", ".hwpx",
    ".doc", ".docx",
    ".xls", ".xlsx",
    ".ppt", ".pptx",
    ".zip",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",  # 일단 모으되 doc_role=skip 권장
}

# “HTML로 크롤링할 만한 URL” 필터(최소)
TARGET_KEYWORDS = ["bbs", "artclview.do", "subview.do"]

# 차단(최소 동작 기준)
BLOCK_PATTERNS = [
    "synapview.do", "synapviewer", "synap",
    "/eng/", "/english/",
    "/chi/", "/chn/", "/china/",
]

DOWNLOAD_URL_PATTERNS = ["download.do"]

# canonicalize에서 남길 query key
ALLOWED_QUERY_KEYS = {"article", "articleId", "pageIndex", "bbsIdx", "id"}


# =========================
# 유틸
# =========================
def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def make_meta_id(canonical_url: str) -> str:
    # v3 핵심: URL 기반 고정 ID
    return "html_" + sha1(canonical_url)

def canonicalize(url: str) -> str:
    # 1) fragment 제거
    url, _ = urldefrag(url)

    # 2) 중복 슬래시 정리 (:// 제외)
    url = re.sub(r'(?<!:)//+', '/', url)

    p = urlparse(url)

    # 3) query 정리
    qs = parse_qs(p.query)
    cleaned = {k: v for k, v in qs.items() if k in ALLOWED_QUERY_KEYS}
    encoded = urlencode(cleaned, doseq=True)

    # 4) path 정리
    path = re.sub(r"/+", "/", p.path)
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    p = p._replace(path=path, query=encoded, fragment="")
    return p.geturl()

def is_blocked_url(url: str) -> bool:
    lower = url.lower()
    if any(p in lower for p in BLOCK_PATTERNS):
        return True
    return False

def is_download_url(url: str) -> bool:
    lower = url.lower()
    return any(pat in lower for pat in DOWNLOAD_URL_PATTERNS)

def is_file_url(url: str) -> bool:
    lower = url.lower()
    # 명확한 확장자
    path = urlparse(lower).path
    ext = os.path.splitext(path)[1]
    if ext in FILE_EXTS:
        return True
    # download.do
    if is_download_url(lower):
        return True
    return False

def is_target_html(url: str) -> bool:
    u = url.lower()
    if any(k in u for k in TARGET_KEYWORDS):
        return True
    # START_URL은 항상 허용
    if canonicalize(url) == canonicalize(START_URL):
        return True
    return False

def write_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def save_text(meta_id: str, text: str) -> str:
    text_path = os.path.join(TEXT_DIR, f"{meta_id}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text_path

def load_set(path: str) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_set_add(path: str, value: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(value + "\n")

def load_queue(path: str) -> deque:
    if not os.path.exists(path):
        return deque()
    with open(path, encoding="utf-8") as f:
        return deque(line.strip() for line in f if line.strip())

def save_queue(path: str, q: deque):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(list(q)))

# def guess_doc_role(text: str, title: str) -> str:
#     t = (title or "").strip()
#     length = len((text or "").strip())

#     if length < 120:
#         return "skip"
#     # 아주 가벼운 규칙 (원하면 확장)
#     if any(k in t for k in ["신청서", "서식", "양식", "제출서류", "Form"]):
#         return "form"
#     return "information"

def try_trafilatura_extract(html: str) -> str | None:
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html,
            include_links=False,
            include_tables=True,
            favor_recall=True
        )
        if extracted and extracted.strip():
            return extracted.strip()
        return None
    except Exception:
        return None

def bs4_extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # header/footer/nav 제거(최소)
    for tag in soup.find_all(["header", "footer", "nav"]):
        tag.decompose()

    main = None
    for sel in ["#content", "#contents", ".content", ".contents", ".board-view", "#container"]:
        m = soup.select_one(sel)
        if m:
            main = m
            break
    if main is None:
        main = soup

    text = main.get_text("\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

def extract_html_text(html: str) -> str:
    # 1) trafilatura 우선
    t = try_trafilatura_extract(html)
    if t:
        return t
    # 2) fallback
    return bs4_extract_text(html)

def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""

def extract_links(html: str, base_url: str) -> list[tuple[str, str | None]]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        txt = a.get_text(strip=True) or None
        abs_url = urljoin(base_url, href)
        links.append((abs_url, txt))
    return links

def guess_ext_from_content_type(ct: str) -> str:
    c = (ct or "").lower()
    if "pdf" in c:
        return ".pdf"
    if "hwp" in c or "hangul" in c:
        return ".hwp"
    if "word" in c or "msword" in c:
        return ".doc"
    if "excel" in c or "sheet" in c:
        return ".xls"
    if "powerpoint" in c or "presentation" in c:
        return ".ppt"
    if "zip" in c:
        return ".zip"
    if c.startswith("image/"):
        sub = c.split("/", 1)[1].split(";")[0].strip()
        if sub == "jpeg":
            return ".jpg"
        if sub in ("png", "gif", "webp"):
            return "." + sub
    return ".bin"

def guess_ext_from_magic_bytes(data: bytes) -> str | None:
    if data.startswith(b"\xFF\xD8\xFF"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and b"WEBP" in data[:16]:
        return ".webp"
    return None

def extract_filename_from_headers(url: str, headers: dict, hint_name: str | None) -> tuple[str, str]:
    # 1) URL 확장자 우선
    base = os.path.basename(urlparse(url).path) or "downloaded_file"
    url_ext = os.path.splitext(base)[1].lower()
    if url_ext in FILE_EXTS:
        return base, url_ext

    # 2) Content-Disposition
    cd = headers.get("content-disposition") or headers.get("Content-Disposition") or ""
    if "filename=" in cd:
        fname = cd.split("filename=")[-1].strip().strip('"\'')
        ext = os.path.splitext(fname)[1].lower()
        if ext:
            return fname, ext

    # 3) hint_name 확장자
    if hint_name:
        ext = os.path.splitext(hint_name)[1].lower()
        if ext:
            return hint_name, ext

    # 4) fallback
    return base, os.path.splitext(base)[1].lower()

def download_file_direct(url: str, hint_name: str | None) -> tuple[str, str, str] | tuple[None, None, None]:
    """
    url에서 파일을 GET으로 내려받아 저장하고 (original_filename, ext, saved_path) 반환
    실패 시 (None, None, None)
    """
    try:
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
    except Exception:
        return None, None, None

    ct = resp.headers.get("content-type", "")
    # download.do가 HTML로 리다이렉트되는 경우 방지
    if "text/html" in (ct or "").lower() and is_download_url(url):
        return None, None, None

    original, ext = extract_filename_from_headers(url, resp.headers, hint_name)
    # 확장자 보정
    if not ext or ext in (".do", ""):
        ext = guess_ext_from_content_type(ct)

    # 그래도 bin이면 magic bytes로 이미지 등 보정
    if ext == ".bin":
        magic = guess_ext_from_magic_bytes(resp.content[:32])
        if magic:
            ext = magic

    # original_filename도 ext로 정리
    original_stem = os.path.splitext(original)[0] or "downloaded_file"
    original = original_stem + ext

    saved_filename = sha1(original + url) + ext
    saved_path = os.path.join(FILES_DIR, saved_filename)

    try:
        with open(saved_path, "wb") as f:
            f.write(resp.content)
    except Exception:
        return None, None, None

    return original, ext, saved_path


# =========================
# v3 크롤러 본체
# =========================
def crawl():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    visited = load_set(VISITED_PATH)
    q = load_queue(QUEUE_PATH)

    if not q:
        q = deque([canonicalize(START_URL)])

    pages = 0
    print("[START] v3 minimal crawl")
    print(f" - start: {q[0]}")
    print(f" - visited: {len(visited)}")

    while q and pages < MAX_PAGES:
        url = q.popleft()
        canonical_url = canonicalize(url)

        if canonical_url in visited:
            continue

        # 도메인 제한
        p = urlparse(canonical_url)
        if p.netloc and p.netloc != DOMAIN:
            continue

        if is_blocked_url(canonical_url):
            visited.add(canonical_url)
            save_set_add(VISITED_PATH, canonical_url)
            continue

        if not is_target_html(canonical_url):
            visited.add(canonical_url)
            save_set_add(VISITED_PATH, canonical_url)
            continue

        pages += 1
        print(f"[{pages}] GET {canonical_url}")

        # HTML GET
        try:
            resp = session.get(canonical_url, timeout=TIMEOUT)
            html = resp.text
        except Exception as e:
            print(f"  [ERROR] HTML fetch failed: {e}")
            visited.add(canonical_url)
            save_set_add(VISITED_PATH, canonical_url)
            save_queue(QUEUE_PATH, q)
            continue

        title = extract_title(html)
        text = extract_html_text(html)
        meta_id = make_meta_id(canonical_url)
        text_path = save_text(meta_id, text)
        # doc_role = guess_doc_role(text, title)
        doc_role = None

        # HTML 메타데이터 기록 (v3)
        write_jsonl(METADATA_PATH, {
            "meta_id": meta_id,
            "source_type": "html",
            "url": canonical_url,
            "canonical_url": canonical_url,
            "title": title,
            "text_path": text_path,
            "doc_role": doc_role,
            "ref_page_meta_id": None,
            "file_ext": None,
            "original_filename": None,
            "saved_path": None,
            "timestamp": time.time(),
        })

        # 링크 추출
        links = extract_links(html, canonical_url)

        for raw_link, link_text in links:
            next_url = canonicalize(urljoin(canonical_url, raw_link))
            pp = urlparse(next_url)

            if pp.netloc and pp.netloc != DOMAIN:
                continue
            if is_blocked_url(next_url):
                continue

            # 파일이면: 같은 meta_id로 저장
            if is_file_url(next_url):
                original, ext, saved_path = download_file_direct(next_url, hint_name=link_text)
                if saved_path:
                    # 파일은 기본 skip 권장 (RAG 텍스트는 별도 extractor에서 만들기)
                    write_jsonl(METADATA_PATH, {
                        "meta_id": meta_id,
                        "source_type": "file",
                        "url": next_url,
                        "canonical_url": next_url,
                        "title": original,
                        "text_path": None,
                        "doc_role": None,
                        "ref_page_meta_id": meta_id,
                        "file_ext": ext,
                        "original_filename": original,
                        "saved_path": saved_path,
                        "timestamp": time.time(),
                    })
                continue

            # HTML이면 큐
            if is_target_html(next_url) and (next_url not in visited):
                q.append(next_url)

        visited.add(canonical_url)
        save_set_add(VISITED_PATH, canonical_url)
        save_queue(QUEUE_PATH, q)
        time.sleep(SLEEP_BETWEEN)

    save_queue(QUEUE_PATH, q)
    print("\n[DONE]")
    print(f" - pages crawled: {pages}")
    print(f" - visited total: {len(visited)}")
    print(f" - metadata: {METADATA_PATH}")
    print(f" - text dir: {TEXT_DIR}")
    print(f" - files dir: {FILES_DIR}")


if __name__ == "__main__":
    crawl()
