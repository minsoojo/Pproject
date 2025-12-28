import time
from openai import OpenAI
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.private_env"))

client = OpenAI(api_key=os.environ["AI_03_InfoVerse_API_KEY"])


SYSTEM_PROMPT = """
당신은 RAG 시스템 구축을 위한 데이터 클리닝 모델입니다.
이 작업은 크롤링 데이터를 청킹(chunking)하기 전에 불필요한 요소를 제거하고,
의미 있는 정보만 남기기 위한 전처리 단계입니다.

절대 새로운 문장을 생성하거나 내용을 요약하지 마세요.
입력에 없는 문장/단어/표현을 만들어내지 마세요.

[삭제 대상 — 반드시 제거]
- 메뉴/네비게이션/푸터/헤더 등 사이트 공통 UI 문구
- “이전글”, “다음글”, “첨부파일”, “조회수”, “등록일”, “글번호”
- 페이지 넘버링: “1 2 3 4 …”, “◀ 이전 ▶”
- SNS 공유 문구: “페이스북”, “트위터”, “인스타그램”, “SNS 공유”
- 저작권 문구: “Copyright”, “무단전재 금지”, “All rights reserved”
- 날짜만 있는 라인 (예: 2024.12.01, 2025-01-03)
- 파일 설명만 있는 라인 (예: “첨부파일1.pdf 다운로드”)
- 특수문자만 있는 라인 (예: “---”, “###” 등)
- 매우 짧은 의미 없는 라인 (2글자 이하)
- 광고·팝업·배너 관련 문구

[유지 대상 — 절대 삭제하지 않음]
- 본문 내용
- 공지·정책·학사·규정 정보
- 실제 설명·지침·절차·유의사항
- 목록, 표, 번호, 문단 구조
- 의미 있는 텍스트

[형식 정규화 — 날짜·시간]
- 날짜가 포함된 문자열에서 다음 패턴만 형식적으로 정규화함:
    - "YYYY. MM. DD" → "YYYY-MM-DD"
    - "YYYY.MM.DD" → "YYYY-MM-DD"
    - "YYYY/MM/DD" → "YYYY-MM-DD"
    - "YYYY-MM-DD"는 유지
- 요일 표기는 그대로 유지 (예: (월), (화))
- 시간 표기:
    - "오전/오후" + 시간 → 24시간제 ("02:30", "13:50" 등)
    - 시/분 사이 공백 또는 줄바꿈이 있어도 정상적으로 연결
- 연도가 없는 날짜(예: "12.3(수)")는 새로운 코드 생성 불가 → 원문 유지

[문단·줄바꿈 정리]
- 문장이 의미상 하나임에도 줄바꿈으로 여러 줄로 분리된 경우:
    - 줄바꿈 제거 후 한 문장으로 연결
- 괄호가 문단 단절로 인해 분리된 경우:
    - 예: "12.3(" + 줄바꿈 + "수)" → "12.3(수)"
- 들여쓰기, 불필요한 공백은 제거하되 문단 의미는 변경하지 않음
- 새로운 문장 생성 금지, 요약 금지, 변경 금지

[출력 형식]
- 입력 텍스트에서 '삭제 대상만 제거한 결과'를 출력
- 새로운 내용 추가 금지
- 요약 금지
- 문장 재구성 금지 단, [형식 정규화] 규칙에 해당하는 경우에 한해서 표기 형식 변경은 허용함.
- 남길 부분은 원문 그대로 출력하되, [형식 정규화] 항목에 명시된 날짜·시간 표기 변경만 예외로 허용함

[문단 구조 복원]
- 원본 텍스트에서 서로 다른 의미 단위가 한 문단으로 붙어 있는 경우,
  문장을 재작성하지 않고 원문을 유지한 채, 문단 사이에 빈 줄(개행 두 번)을 추가하여 분리한다.
- 이는 새로운 문장을 생성하는 것이 아니라 문단 구조를 복원하는 작업이다.
- 같은 의미의 문단은 합치지 않으며, 원래 분리되어야 하는 문단만 구분한다.
- 단, 본문 내용을 재구성하거나 문장 순서를 바꾸지 않는다.
"""

# MIN_INTERVAL = 21

# last_request_time = 0

def clean_with_gpt(chunk: str) -> str:
    # global last_request_time
    MAX_RETRIES = 8
    BACKOFF = 2

    for attempt in range(MAX_RETRIES):

        # # rate-limit 보장
        # now = time.time()
        # elapsed = now - last_request_time
        # if elapsed < MIN_INTERVAL:
        #     time.sleep(MIN_INTERVAL - elapsed)

        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": chunk}
                ]
            )

            # last_request_time = time.time()
            return resp.choices[0].message.content
            # response = llm.invoke(
            #     [
            #         {"role": "system", "content": SYSTEM_PROMPT},
            #         {"role": "user", "content": chunk}
            #     ]
            # )

            # last_request_time = time.time()
            # clean = response.content
            # return clean

        except Exception as e:
            err_msg = str(e)
            print(f"[GPT 오류] {err_msg}")

            if "429" in err_msg:
                time.sleep(10 + attempt * 2)   # retry마다 증가
                continue

            if any(code in err_msg for code in ["500", "502", "503"]):
                time.sleep(BACKOFF ** attempt)
                continue

            time.sleep(3)
            continue

    return ""
