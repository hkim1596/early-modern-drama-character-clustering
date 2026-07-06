"""Stage 03 — Embed each character's speech with gte-Qwen2-1.5B-instruct.

Two modes, controlled by config.EMBED_CHUNK_TOKENS:

CHUNKED (default, EMBED_CHUNK_TOKENS = 1024):
    Each character's speech is split into ~1k-token windows (token-aligned,
    a tail shorter than 25% of the window merges into the previous one).
    Every window is embedded with the instruction prefix, then the character's
    vector is the token-weighted mean of its window embeddings, L2-normalized.
    WHY: with one embedding per whole document, log(word count) was
    recoverable from the top-5 PCs with R²=0.90 — the space encoded document
    length, not character. Chunk+mean-pool puts every character in the same
    length regime. It also removes the need for a 40k context window
    (CELESTINA becomes ~38 ordinary chunks) and lets us batch properly.

LEGACY (EMBED_CHUNK_TOKENS = None):
    One embedding per whole document, exactly as the first full run. Kept for
    control comparison. Pre-flight length check ABORTS, naming offenders, if
    any document exceeds EMBED_MAX_TOKENS — project rule #1 is never to
    truncate a character's speech.

Run this on the GPU server. From inside the khj Docker:
    pip install -r requirements.txt
    pip install accelerate                       # recommended
    CHAR_CLUSTERING_BASE=/home/khj/character_clustering python 03_embed.py

Inputs (in DATA_DIR):
  - character_documents.csv

Outputs (in DATA_DIR):
  - embeddings.npy                  shape [n_characters, dim]
  - embeddings_metadata.json        model, dim, mode, chunk stats
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


def chunk_document(text: str, tokenizer, chunk_tokens: int) -> list[tuple[str, int]]:
    """Split `text` into ~chunk_tokens windows on token boundaries.

    Returns [(substring, n_tokens), ...]. Slices the ORIGINAL text via the
    tokenizer's offset mapping (no decode/re-encode drift). A tail window
    shorter than 25% of chunk_tokens is merged into the previous window, so
    windows are chunk_tokens long except the last (0.25–1.25 × chunk_tokens).
    """
    enc = tokenizer(text, truncation=False, add_special_tokens=False,
                    return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    n = len(offsets)
    if n == 0:
        return [(text, 0)]
    starts = list(range(0, n, chunk_tokens))
    if len(starts) > 1 and (n - starts[-1]) < chunk_tokens // 4:
        starts.pop()          # merge short tail into the previous window
    out = []
    for si, s in enumerate(starts):
        e = starts[si + 1] if si + 1 < len(starts) else n
        out.append((text[offsets[s][0]: offsets[e - 1][1]], e - s))
    return out


def load_model(device: str, dtype: torch.dtype):
    print(f"⏳ Loading model: {config.EMBED_MODEL}")
    # Newer transformers releases stopped auto-populating default attributes on
    # Config objects, but Alibaba's custom modeling_qwen.py still reads
    # `config.rope_theta` directly. Patch it in if missing.
    hf_cfg = AutoConfig.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)
    if not hasattr(hf_cfg, "rope_theta") or getattr(hf_cfg, "rope_theta", None) is None:
        hf_cfg.rope_theta = 1000000.0     # Qwen2-1.5B default for long context
        print("ℹ️  Patched missing rope_theta on config (1000000.0)")

    # gte-Qwen2 does not support flash_attention_2 in transformers; SDPA is
    # the right choice and handles these lengths fine.
    model = AutoModel.from_pretrained(
        config.EMBED_MODEL,
        config=hf_cfg,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    print("ℹ️  Using SDPA attention")
    return model.to(device).eval()


def embed_texts(texts: list[str], model, tokenizer, device: str,
                batch_size: int, max_length: int) -> np.ndarray:
    """Embed a list of instruction-formatted texts → [n, dim] float32 (L2-normed)."""
    embs: list[np.ndarray] = []
    with torch.inference_mode():
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
            batch = texts[i: i + batch_size]
            tok = tokenizer(
                batch,
                max_length=max_length,
                padding=True,
                truncation=True,   # safety net; inputs are pre-sized
                return_tensors="pt",
            ).to(device)
            out = model(**tok)
            emb = last_token_pool(out.last_hidden_state, tok["attention_mask"])
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            embs.append(emb.float().cpu().numpy())
    return np.vstack(embs)


def main() -> None:
    df = pd.read_csv(config.DATA_DIR / "character_documents.csv", low_memory=False)
    print(f"📄 Documents: {len(df)}")

    if torch.cuda.is_available():
        device, dtype = "cuda", torch.bfloat16
    elif torch.backends.mps.is_available():
        # fp16 halves memory (~3 GB weights) and is safe for ≤1.3k-token
        # chunks; fp32 would double both memory and runtime on Apple Silicon.
        device, dtype = "mps", torch.float16
    else:
        device, dtype = "cpu", torch.float32
    print(f"🖥 Device: {device}  dtype: {dtype}")

    print(f"⏳ Loading tokenizer: {config.EMBED_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(config.EMBED_MODEL, trust_remote_code=True)

    # Embed the de-referenced text (proper nouns masked by stage 02) so
    # clusters reflect register, not shared names. Falls back to raw speech
    # if the documents table predates the masking stage.
    text_col = "speech_text_embedding" if "speech_text_embedding" in df.columns \
        else "speech_text"
    print(f"🗂 Embedding column: {text_col}")
    raw_texts = df[text_col].fillna("").tolist()
    ids = df["character_id"] if "character_id" in df.columns else df.index

    chunk_tokens = config.EMBED_CHUNK_TOKENS

    # ------------------------------------------------------------------
    # CHUNKED MODE (default)
    # ------------------------------------------------------------------
    if chunk_tokens is not None:
        print(f"✂️  Chunked mode: windows of {chunk_tokens} tokens, "
              f"token-weighted mean-pool per character")
        chunk_texts: list[str] = []
        owners: list[int] = []
        weights: list[int] = []
        for i, t in enumerate(tqdm(raw_texts, desc="Chunking")):
            for sub, ntok in chunk_document(t, tokenizer, chunk_tokens):
                chunk_texts.append(format_with_instruction(sub))
                owners.append(i)
                weights.append(max(ntok, 1))

        owners_a = np.asarray(owners)
        weights_a = np.asarray(weights, dtype=np.float32)
        per_doc = np.bincount(owners_a, minlength=len(df))
        assert per_doc.min() >= 1, "every document must yield at least one chunk"
        print(f"   {len(chunk_texts):,} chunks from {len(df):,} characters "
              f"(max/doc={per_doc.max()}, mean/doc={per_doc.mean():.2f})")

        instr_len = len(tokenizer(format_with_instruction(""))["input_ids"])
        # window ≤ 1.25×chunk_tokens by construction; + instruction + margin
        max_length = int(chunk_tokens * 1.25) + instr_len + 16

        batch_size = config.EMBED_CHUNK_BATCH_SIZE
        if device == "mps" and batch_size > 8:
            batch_size = 8   # unified memory on Apple Silicon; avoids OOM
            print(f"   ℹ️  MPS: capping chunk batch size at {batch_size}")

        model = load_model(device, dtype)
        chunk_emb = embed_texts(chunk_texts, model, tokenizer, device,
                                batch_size, max_length)

        # token-weighted mean-pool per character, then L2-normalize
        dim = chunk_emb.shape[1]
        arr = np.zeros((len(df), dim), dtype=np.float64)
        np.add.at(arr, owners_a, chunk_emb * weights_a[:, None])
        arr /= np.bincount(owners_a, weights=weights_a, minlength=len(df))[:, None]
        arr = (arr / np.clip(np.linalg.norm(arr, axis=1, keepdims=True), 1e-12, None)
               ).astype(np.float32)

        meta_extra = {
            "mode": "chunked",
            "chunk_tokens": chunk_tokens,
            "chunk_batch_size": config.EMBED_CHUNK_BATCH_SIZE,
            "n_chunks": int(len(chunk_texts)),
            "max_chunks_per_doc": int(per_doc.max()),
            "mean_chunks_per_doc": round(float(per_doc.mean()), 3),
            "pooling": "token-weighted mean of window embeddings, L2-normalized",
        }
        longest_note = f"{per_doc.max()} chunks (largest character)"

    # ------------------------------------------------------------------
    # LEGACY WHOLE-DOCUMENT MODE (EMBED_CHUNK_TOKENS = None)
    # ------------------------------------------------------------------
    else:
        print("📜 Legacy mode: one embedding per whole document")
        texts = [format_with_instruction(t) for t in raw_texts]

        # Pre-flight length check: never silently truncate a character.
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
                f"positions), or use chunked mode (EMBED_CHUNK_TOKENS)."
            )
        print(f"✅ length check: {len(texts)} docs, longest {max(token_lens):,} "
              f"tokens ≤ EMBED_MAX_TOKENS ({config.EMBED_MAX_TOKENS:,})")

        model = load_model(device, dtype)
        arr = embed_texts(texts, model, tokenizer, device,
                          config.EMBED_BATCH_SIZE, config.EMBED_MAX_TOKENS)

        meta_extra = {
            "mode": "whole-document",
            "max_tokens": config.EMBED_MAX_TOKENS,
            "max_doc_tokens": int(max(token_lens)),
            "truncated_count": 0,   # guaranteed by the pre-flight length check
        }
        longest_note = f"longest document {max(token_lens):,} tokens"

    np.save(config.DATA_DIR / "embeddings.npy", arr)
    meta = {
        "model": config.EMBED_MODEL,
        "dim": int(arr.shape[1]),
        "n_rows": int(arr.shape[0]),
        "instruction": config.EMBED_INSTRUCTION,
        **meta_extra,
    }
    with open(config.DATA_DIR / "embeddings_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print()
    print(f"✅ embeddings.npy   shape={arr.shape}   ({meta['mode']}; {longest_note})")


if __name__ == "__main__":
    main()
