"""Stage 03 — Embed each character's full speech with gte-Qwen2-1.5B-instruct.

No chunking: each character is a single document. Before embedding, every
document is length-checked against config.EMBED_MAX_TOKENS and the run ABORTS,
naming the offenders, if any would be truncated. Project rule #1 is never to
truncate a character's speech, so the fix for an over-length document is to
raise the cap (the model supports up to 131072 positions) or chunk it — never
to silently drop text.

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

    print(f"⏳ Loading tokenizer: {config.EMBED_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)

    # Embed the de-referenced text (proper nouns masked by stage 02) so
    # clusters reflect register, not shared names. Falls back to raw speech
    # if the documents table predates the masking stage.
    text_col = "speech_text_embedding" if "speech_text_embedding" in df.columns \
        else "speech_text"
    print(f"🗂 Embedding column: {text_col}")
    texts = [format_with_instruction(t or "") for t in df[text_col].fillna("").tolist()]

    # ---- Pre-flight length check: never silently truncate a character ----
    # Tokenize every document once (no truncation) and refuse to run if any
    # exceeds EMBED_MAX_TOKENS, naming the offenders. This enforces project
    # rule #1 in code rather than reporting a truncation after the fact.
    ids = df["character_id"] if "character_id" in df.columns else df.index
    token_lens = [len(tokenizer(t, truncation=False)["input_ids"]) for t in texts]
    over = sorted(
        ((str(ids.iloc[i] if hasattr(ids, "iloc") else ids[i]), n)
         for i, n in enumerate(token_lens) if n > config.EMBED_MAX_TOKENS),
        key=lambda kv: -kv[1],
    )
    if over:
        detail = "\n".join(
            f"    {cid}: {n:,} tokens (+{n - config.EMBED_MAX_TOKENS:,} over)"
            for cid, n in over[:20]
        )
        raise SystemExit(
            f"❌ Refusing to truncate: {len(over)} document(s) exceed "
            f"EMBED_MAX_TOKENS={config.EMBED_MAX_TOKENS:,}:\n{detail}\n"
            f"    Raise config.EMBED_MAX_TOKENS (gte-Qwen2 supports 131072 "
            f"positions) or chunk these documents, then re-run."
        )
    print(f"✅ length check: {len(texts)} docs, longest {max(token_lens):,} "
          f"tokens ≤ EMBED_MAX_TOKENS ({config.EMBED_MAX_TOKENS:,})")

    print(f"⏳ Loading model: {config.EMBED_MODEL}")
    # Newer transformers releases stopped auto-populating default attributes on
    # Config objects, but Alibaba's custom modeling_qwen.py still reads
    # `config.rope_theta` directly. Patch it in if missing.
    hf_cfg = AutoConfig.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)
    if not hasattr(hf_cfg, "rope_theta") or getattr(hf_cfg, "rope_theta", None) is None:
        hf_cfg.rope_theta = 1000000.0     # Qwen2-1.5B default for long context
        print("ℹ️  Patched missing rope_theta on config (1000000.0)")

    # Note: gte-Qwen2 does not support flash_attention_2 in transformers. SDPA
    # (PyTorch's built-in scaled dot-product attention) is the right choice
    # here; it's memory-efficient and handles long context fine on RTX 6000.
    model = AutoModel.from_pretrained(
        config.EMBED_MODEL,
        config=hf_cfg,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    print("ℹ️  Using SDPA attention")
    model = model.to(device).eval()

    embs: list[np.ndarray] = []

    with torch.inference_mode():
        for i in tqdm(range(0, len(texts), config.EMBED_BATCH_SIZE), desc="Embedding"):
            batch = texts[i : i + config.EMBED_BATCH_SIZE]
            # truncation=True is a safety net only; the pre-flight check above
            # guarantees no batch is ever actually cut.
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
        "max_doc_tokens": int(max(token_lens)),
        "truncated_count": 0,   # guaranteed by the pre-flight length check
        "instruction": config.EMBED_INSTRUCTION,
    }
    with open(config.DATA_DIR / "embeddings_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print()
    print(f"✅ embeddings.npy   shape={arr.shape}")
    print(f"   longest document {max(token_lens):,} tokens "
          f"(limit {config.EMBED_MAX_TOKENS:,}); truncated: 0")


if __name__ == "__main__":
    main()
