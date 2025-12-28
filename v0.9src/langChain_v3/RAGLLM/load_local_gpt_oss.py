# load_local_gpt_oss.py
import os

# Force transformers to ignore TensorFlow/Keras to bypass the Keras 3 incompatibility.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline,
    AutoConfig,
)

def load_local_gpt_oss(
    model_path: str = "/home/t25315/models/gpt-oss-20b-bf16",
    max_new_tokens: int = 256,
    debug_print: bool = False,
):
    """
    GPT-OSS 로컬 로더 (4bit + 2GPU 분배 + 안정 프롬프트)

    포함:
    1) chat_template 강제 덮어쓰기 (오염 제거, 포맷 정합)
    2) eos_token_id 리스트 지원 (generation_config에 있는 eos 그대로 사용)
    3) repetition_penalty 적용 (반복/붕괴 완화)
    4) return_full_text=False + 메타(We need to answer...) 첫 줄 제거 후처리
    """

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    # 0) tokenizer
    tok = AutoTokenizer.from_pretrained(model_path, use_fast=True)

    # pad_token 없으면 eos로 대체
    if tok.pad_token_id is None and tok.eos_token_id is not None:
        tok.pad_token = tok.eos_token

    # ✅ 1) chat_template 강제 덮어쓰기 (중요)
    # 토크나이저에 이상한 시스템 프롬프트(OpenAI style)가 섞이는 문제를 차단
    tok.chat_template = (
        "{% for message in messages %}"
        "{% if message['role'] == 'system' %}"
        "<|start|>system<|message|>\n{{ message['content'] }}\n<|end|>\n"
        "{% elif message['role'] == 'user' %}"
        "<|start|>user<|message|>\n{{ message['content'] }}\n<|end|>\n"
        "{% elif message['role'] == 'assistant' %}"
        "<|start|>assistant<|message|>\n{{ message['content'] }}\n<|end|>\n"
        "{% endif %}"
        "{% endfor %}"
        "<|start|>assistant<|message|>\n"
    )

    # 1) offload 폴더
    offload_dir = os.path.expanduser("~/offload_gptoss")
    os.makedirs(offload_dir, exist_ok=True)

    # 2) 4bit quant config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        # 안정성 우선: fp16 compute 권장
        bnb_4bit_compute_dtype=torch.float16,
    )

    # 3) 레이어 수 확인
    cfg = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    n_layers = int(getattr(cfg, "num_hidden_layers", 0)) or 24

    # 4) device_map (레이어 반반)
    device_map = {
        "model.embed_tokens": 0,
        "model.norm": 1,
        "lm_head": 1,
    }
    split = n_layers // 2
    for i in range(n_layers):
        device_map[f"model.layers.{i}"] = 0 if i < split else 1

    # 5) 모델 로딩
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map=device_map,
        quantization_config=bnb_config,
        max_memory={0: "19GiB", 1: "19GiB"},
        offload_folder=offload_dir,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    # 6) 파이프라인 생성
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tok,
    )

    # 🔥 generation_config 강제 덮어쓰기
    # (샘플링 끄고, 확률 샘플링 관련 파라미터는 None으로 정리)
    gc = pipe.model.generation_config
    gc.do_sample = False
    gc.temperature = None
    gc.top_p = None
    gc.top_k = None
    gc.typical_p = None
    gc.max_new_tokens = max_new_tokens

    # ✅ eos_token_id 리스트 적용 (generation_config에서 가져오기)
    gen_cfg = getattr(pipe.model, "generation_config", None)
    eos_ids = None
    if gen_cfg is not None:
        eos_ids = getattr(gen_cfg, "eos_token_id", None)
    if eos_ids is None:
        eos_ids = tok.eos_token_id

    if debug_print:
        print("model_path:", model_path)
        print("is_loaded_in_4bit:", getattr(model, "is_loaded_in_4bit", False))
        print("quant_config:", getattr(model, "quantization_config", None))
        try:
            print("dtype:", next(model.parameters()).dtype)
        except Exception as e:
            print("dtype: (could not read)", repr(e))
        print("has_chat_template:", bool(getattr(tok, "chat_template", None)))
        print("has 4bit linear:", any("Linear4bit" in str(type(m)) for m in model.modules()))
        print("eos_ids:", eos_ids)
        if gen_cfg is not None:
            try:
                d = gen_cfg.to_dict()
                print("generation_config.do_sample:", d.get("do_sample"))
                print("generation_config.temperature:", d.get("temperature"))
            except Exception:
                pass

    class LocalOSSModel:
        def __init__(self, pipe, tokenizer, max_new_tokens, eos_ids, debug_print):
            self.pipe = pipe
            self.tok = tokenizer
            self.max_new_tokens = max_new_tokens
            self.eos_ids = eos_ids
            self.debug_print = debug_print

        def _build_prompt(self, system_prompt: str, user_prompt: str) -> str:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            return self.tok.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        def generate(self, system_prompt: str, user_prompt: str) -> str:
            prompt = self._build_prompt(system_prompt, user_prompt)

            if self.debug_print:
                print("[DEBUG prompt head]", prompt[:300])
                print("[DEBUG prompt tail]", prompt[-300:])

            outputs = self.pipe(
                prompt,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.10,
                return_full_text=False,
                eos_token_id=self.eos_ids,
                pad_token_id=self.tok.pad_token_id,
            )

            text = outputs[0]["generated_text"].strip()

            return text

    return LocalOSSModel(pipe, tok, max_new_tokens, eos_ids, debug_print)
