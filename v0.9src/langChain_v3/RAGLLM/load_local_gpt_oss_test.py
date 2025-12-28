import os
import torch

# Force transformers to ignore TensorFlow/Keras (Keras 3 is unsupported).
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from transformers import logging
logging.set_verbosity_info()
# ✅ 로컬 모델 경로
model_path = "/home/t25315/models/gpt-oss-20b"

# 4bit bitsandbytes 설정 (MXFP4 덮어쓰기)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,  # RTX A5000 OK
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

# 토크나이저 (로컬)
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True,
)

# 모델 로드 (로컬 + 4bit)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

prompt = "Explain what RAG is in simple terms."

inputs = tokenizer(
    prompt,
    return_tensors="pt",
).to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
    )

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
