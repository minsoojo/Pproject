#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime
from pathlib import Path
import time

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ============================
# 설정
# ============================
BASE_DIR = Path("/Users/kaia/Desktop/학교/Pp")
DB_PATH = BASE_DIR / "gachon_raw_test.db"

TEST_URLS = [
    "https://www.gachon.ac.kr/kor/1004/subview.do",
    "https://www.gachon.ac.kr/kor/7966/subview.do",
]


# ============================
# 1) DB 초기화
# ============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            url          TEXT NOT NULL,
            source_type  TEXT,
            title        TEXT,
            raw_text     TEXT NOT NULL,
            clean_text   TEXT,
            meta_json    TEXT,
            crawled_at   TEXT,
            processed_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    print(f"[INFO] DB 초기화 완료: {DB_PATH}")


# ============================
# 2) Selenium 드라이버 생성
# ============================
def create_driver():
    options = Options()

    # 가천대는 headless 막는 경우 있으니 일단 눈에 보이게 띄우자
    # 필요하면 나중에 headless 시도
    # options.add_argument("--headless=new")

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    # User-Agent 브라우저처럼
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    return driver


# ============================
# 3) HTML → 본문 텍스트 추출
# ============================
def extract_main_text(html: str) -> str:
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
        main = soup  # fallback

    # 5) 텍스트 정리
    text = main.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    return "\n".join(lines)



# ============================
# 4) Selenium으로 페이지 열고 DB에 저장
# ============================
def crawl_with_selenium(driver, url: str):
    print(f"[CRAWL] {url}")

    driver.get(url)
    # 페이지 로드 및 JS 렌더링 여유
    time.sleep(3)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""

    raw_text = extract_main_text(html)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents (url, source_type, title, raw_text, crawled_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            url,
            "html",  # 소스 타입
            title,
            raw_text,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()

    print(f"[DONE] INSERT 완료 (url={url}, text_len={len(raw_text)})")


# ============================
# 5) DB 내용 미리보기
# ============================
def print_preview(limit: int = 5):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, url,
               substr(raw_text, 1, 120) || '...' AS preview
        FROM documents
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    print("\n[DB 내용 미리보기]")
    if not rows:
        print("(행이 없습니다)")
        return

    for doc_id, url, preview in rows:
        print(f"- id={doc_id}")
        print(f"  url={url}")
        print(f"  raw_preview={preview}")
        print("-" * 40)


# ============================
# 실행
# ============================
def main():
    init_db()

    driver = create_driver()

    try:
        for url in TEST_URLS:
            try:
                crawl_with_selenium(driver, url)
            except Exception as e:
                print(f"[ERROR] {url} 크롤링 실패: {e}")
    finally:
        driver.quit()

    print_preview(limit=10)


if __name__ == "__main__":
    main()
