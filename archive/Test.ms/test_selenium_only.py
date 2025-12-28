# 학교 서버 세그멘테이션 오류 해결을 위한 크롬 테스트

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import faulthandler
faulthandler.enable()  # 세그폴트 날 때 C 스택까지 같이 찍어줌

FILE_DIR = "downloads_test"

import os
os.makedirs(FILE_DIR, exist_ok=True)

def main():
    chrome_options = Options()

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
    chrome_options.binary_location = "/home/t25315/chromium-portable/chrome-linux/chrome"
    service = Service("/home/t25315/chromium-portable/chromedriver_linux64/chromedriver")

    print("[DEBUG] before webdriver.Chrome")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("[DEBUG] after webdriver.Chrome")

    print("[DEBUG] driver.get() 시작")
    driver.get("https://www.gachon.ac.kr")
    print("[DEBUG] driver.get() 끝")

    driver.quit()
    print("[DEBUG] quit 완료")

if __name__ == "__main__":
    main()
