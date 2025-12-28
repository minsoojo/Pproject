#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

VISITED_FILE = "/home/t25315/data/visited.txt"
VISITED_NEW  = "/home/t25315/data/visited_new.txt"
REMOVED_FILE = "/home/t25315/data/visited_removed.txt"  # unvisit(다시 돌릴) 대상들

# def should_unvisit(url: str) -> bool:
#     """
#     '다시 크롤링하고 싶은 URL'만 True가 되게 조건을 설정하는 부분.

#     지금은 예시로:
#     - subview.do 이면서
#     - enc= 파라미터가 있는 URL
#     => 게시글 상세/리스트 페이지일 가능성이 높은 애들을 다시 돌리도록 설정.

#     필요하면 나중에 조건을 더 좁혀도 됨.
#     """
#     if "subview.do" in url and "enc=" in url:
#         return True

#     return False

def should_unvisit(url: str) -> bool:
    """
    가천대 사이트에서
    - /kor/ 밑에 있고
    - subview.do 로 끝나는 페이지들

    => 거의 전부 게시판/콘텐츠 페이지라 보고,
       다시 크롤링 대상(unvisit)으로 잡는다.
    """

    if "www.gachon.ac.kr" in url and "/kor/" in url and "subview.do" in url:
        return True

    return False


def main():
    if not os.path.exists(VISITED_FILE):
        print(f"[ERROR] {VISITED_FILE} not found")
        return

    keep = []
    removed = []

    with open(VISITED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue

            if should_unvisit(url):
                removed.append(url)
            else:
                keep.append(url)

    print(f"[INFO] keep  : {len(keep)}개")
    print(f"[INFO] unvisit 대상: {len(removed)}개")

    # 새 visited.txt 후보
    with open(VISITED_NEW, "w", encoding="utf-8") as f:
        for url in keep:
            f.write(url + "\n")

    # 참고용: 제거된 URL 모음
    with open(REMOVED_FILE, "w", encoding="utf-8") as f:
        for url in removed:
            f.write(url + "\n")

    print(f"[INFO] {VISITED_NEW} / {REMOVED_FILE} 생성 완료")


if __name__ == "__main__":
    main()



