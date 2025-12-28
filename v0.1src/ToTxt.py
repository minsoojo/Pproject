from langChain_v3.db import get_connection
import os

OUTPUT_DIR = "/home/t25315/data/dumped_chunks"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def dump_all_chunks():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1) chunks 테이블에 존재하는 모든 meta_id 조회
            cur.execute("""
                SELECT DISTINCT meta_id
                FROM chunks
                ORDER BY meta_id
            """)
            meta_ids = [row["meta_id"] for row in cur.fetchall()]

        print(f"[INFO] 발견된 meta_id 수: {len(meta_ids)}")

        for meta_id in meta_ids:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT chunk_index, text
                    FROM chunks
                    WHERE meta_id = %s
                    ORDER BY chunk_index
                """, (meta_id,))
                rows = cur.fetchall()

            if not rows:
                print(f"[SKIP] {meta_id}: chunk 없음")
                continue
                continue

            out_path = os.path.join(OUTPUT_DIR, f"{meta_id}.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(f"\n\n----- CHUNK {r['chunk_index']} -----\n\n")
                    f.write(r["text"])

            print(f"[OK] 저장 완료: {out_path} ({len(rows)} chunks)")

    finally:
        conn.close()


if __name__ == "__main__":
    dump_all_chunks()
