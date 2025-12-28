import importlib.util
import tiktoken

# preprocess.py를 "파일 경로로" 직접 로드 (패키지 __init__ 안 탐)
spec = importlib.util.spec_from_file_location(
    "preprocess",
    "/home/t25315/Pproject/langChain_v3/preprocess.py"
)
preprocess = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preprocess)

enc = tiktoken.get_encoding("cl100k_base")
def token_len(s): return len(enc.encode(s))

text = "안녕하세요 " * 200
chunks = preprocess.chunk_text(text, chunk_size=350, overlap=60)

print("chunk 개수:", len(chunks))
print("각 chunk 문자 길이:", [len(c) for c in chunks])
print("각 chunk 토큰 길이:", [token_len(c) for c in chunks])
