"""Stage 03 — Embed each character's full speech with gte-Qwen2-1.5B-instruct.

No chunking. Each character is a single document; the model's 32k-token
context comfortably holds even very long parts.

Run this on the GPU server. From inside the khj Docker:
    pip install -r requirements.txt
    pip install accelerate                       # recommended
    pip install flash-attn --no-build-isolation  # optional, lowers memory
    CHAR_CLUSTERING_BASE=/home/khj/character_clustering python 03_embed.py

Inputs (in DATA_DIR):
  - character_documents.csv

Outputs (in DATA_DIR):
  - embeddings.npy                  shape [n_characters, dim]
  - embeddings_metadata.json        model name, dim, row count, truncation count
"""

from __future__ import annotations
import json

import numpy as np
import pandas as pd
import torch
from torch import Tensor
from transformers import AutoConfig, AutoTokenizer, AutoModel
from tqdm import tqdm

import config


def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """gte-Qwen2 pools from the *last* non-padding token (it's a causal LM encoder)."""
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    seq_lengths = attention_mask.sum(dim=1) - 1
    batch_size = last_hidden_states.shape[0]
    return last_hidden_states[
        torch.arange(batch_size, device=last_hidden_states.device), seq_lengths
    ]


def format_with_instruction(text: str) -> str:
    return f"Instruct: {config.EMBED_INSTRUCTION}\nQuery: {text}"


def main() -> None:
    df = pd.read_csv(config.DATA_DIR / "character_documents.csv")
    print(f"📄 Documents: {len(df)}")

    if torch.cuda.is_available():
        device = "cuda"
        dtype = torch.bfloat16
    elif torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float32
    else:
        device = "cpu"
        dtype = torch.float32
    print(f"🖥 Device: {device}  dtype: {dtype}")

    print(f"⏳ Loading model: {config.EMBED_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)

    # Newer transformers releases stopped auto-populating default attributes on
    # Config objects, but Alibaba's custom modeling_qwen.py still reads
    # `config.rope_theta` directly. Patch it in if missing.
    hf_cfg = AutoConfig.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)
    if not hasattr(hf_cfg, "rope_theta") or getattr(hf_cfg, "rope_theta", None) is None:
        hf_cfg.rope_theta = 1000000.0     # Qwen2-1.5B default for 32k context
        print("ℹ️  Patched missing rope_theta on config (1000000.0)")

    # Note: gte-Qwen2 does not support flash_attention_2 in transformers. SDPA
    # (PyTorch's built-in scaled dot-product attention) is the right choice
    # here; it's memory-efficient and handles 32k context fine on RTX 6000.
    model = AutoModel.from_pretrained(
        config.EMBED_MODEL,
        config=hf_cfg,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    print("ℹ️  Using SDPA attention")
    model = model.to(device).eval()

    texts = [format_with_instruction(t or "") for t in df["speech_text"].fillna("").tolist()]

    truncated = 0
    embs: list[np.ndarray] = []

    with torch.inference_mode():
        for i in tqdm(range(0, len(texts), config.EMBED_BATCH_SIZE), desc="Embedding"):
            batch = texts[i : i + config.EMBED_BATCH_SIZE]

            # Detect (and count) any truncation
            for t in batch:
                full = tokenizer(t, truncation=False, return_tensors="pt")["input_ids"]
                if full.shape[1] > config.EMBED_MAX_TOKENS:
                    truncated += 1

            tok = tokenizer(
                batch,
                max_length=config.EMBED_MAX_TOKENS,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(device)
            out = model(**tok)
            emb = last_token_pool(out.last_hidden_state, tok["attention_mask"])
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            embs.append(emb.float().cpu().numpy())

    arr = np.vstack(embs)
    np.save(config.DATA_DIR / "embeddings.npy", arr)

    meta = {
        "model": config.EMBED_MODEL,
        "dim": int(arr.shape[1]),
        "n_rows": int(arr.shape[0]),
        "max_tokens": config.EMBED_MAX_TOKENS,
        "truncated_count": int(truncated),
        "instruction": config.EMBED_INSTRUCTION,
    }
    with open(config.DATA_DIR / "embeddings_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print()
    print(f"✅ embeddings.npy   shape={arr.shape}")
    print(f"   truncated characters (> {config.EMBED_MAX_TOKENS} tokens): {truncated}")


if __name__ == "__main__":
    main()
