"""Stage 05 — Label each cluster with top distinguishing words + curated names.

Uses class-based TF-IDF (treats each cluster's concatenated speech text as a
single document, then runs TF-IDF across clusters). This surfaces the words
that *distinguish* one cluster from the others rather than the words most
common in the corpus.

c-TF-IDF runs on the MASKED, MODERNIZED text (`speech_text_embedding`) — the
same text the clustering itself used — so labels describe register rather than
leaking character names ("minos", "faustus") or unmodernized spellings ("ane",
"scho"). Mask placeholders ("someone", "the god", …) are stopworded.

If data/cluster_names__<name>.json exists (hand-curated archetype names), the
`label` column becomes "<id>: <curated name>" and a `name` column is added;
otherwise labels fall back to the top c-TF-IDF words.

Inputs (in DATA_DIR):
  - cluster_xy_table__<name>.csv
  - cluster_names__<name>.json           optional, hand-curated

Outputs (in DATA_DIR):
  - cluster_labels__<name>.csv           per-cluster top words + name + label
  - cluster_xy_table__<name>.csv         updated with topic_label and top_words columns
"""

from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

import config


# Stopwords: modern English function words + early-modern spelling variants.
# Drama-specific high-frequency words (lord, sir, etc.) and salutations are included
# because c-TF-IDF otherwise floods every cluster's top words with them.
STOPWORDS = set("""
the and to of i a my you that in is it for he she his her him not be with as so but at by are have was were thee thou thy
ye yet do doth dost shall will would should could me we us our ours yours hers theirs they them their this that these those
o oh ah good lord sir madam lady king queen man wife son boy how when where why what who which from upon if then now no
hath hast art come go went made make take give see say said one out only such all
yes nay aye truly indeed verily prithee pray let
even ever never
much many more most less least very too quite rather still even
mine thine ours yours thee thou ye
been being am are was were art beest art wast
""".split())

# Early-modern spelling variants that the standard stoplist misses entirely.
# These appear in nearly every cluster's top words otherwise.
STOPWORDS |= set("""
haue hauing hath haste hauen
doe doth dost doost doeth doost
ile ill ilet ilee
loue loued louing loues louer
selfe selues
giue geue giuing giuen giueth gaue
wyll wol wolde wold woldst wil wee wee'l wele
thys thou thy thyne thine thee
hys hym
vs vnto vntil vntill vntyl
whych whyche wyche
sayd saith sayth sayes sez
quoth quod
mee hee shee wee yee ye yt
fro
ben don wol nyl nylle nyll yt yif
shal shal
mighte ight ought
els elles
neuer neuere
syr syrra sirra
god goddes godd ye
canst couldst wouldst shouldst durst
yea yeas nay
prythee
euer ouer auer ere ere euery euerie euerey
heere theere wheere ther there here whence hither thither whither
againe agayne agen agayn
heauen heauens heauenly hell helles
soule soules
spirite spirites spirit spirits
faith ifaith yfaith verily
forth fourth
whose whom thence
thing things nothing somthing somewhat
first onely only once now
oh ah aye nay yea
hither thither whither
liue liues liued liuing dye dyed dyeth dies dye dying
better worse worser best worst
saith sayed
although though
althoughe althoghe
gone going goes goest cometh cometh came comest
""".split())

# Mask placeholders written by stage 02 (person -> "someone", place -> "that
# place", nation -> "foreign(ers)", deity -> "the god"): their counts are
# artifacts of masking, never register.
STOPWORDS |= {"someone", "someones", "foreign", "foreigners", "god", "gods",
              "goddess", "place", "places"}

# Latin function words — Latin and macaronic plays otherwise flood their
# clusters' top words with "ego, qui, hoc".
STOPWORDS |= set("""
ego tu qui quae quod quid quis hoc haec hic ille illa est sunt esse erat fuit
mihi tibi te se nos vos meus tuus suus et in non cum si sed ut ad per pro nunc
iam tamen atque enim nec neque autem ergo quam quia sic ita nam vel aut o
vero tua tuae tuum tuis meum meam mea meae meis noster nostri vestra deus deo
dei rex pater mater ecce quoque etiam ubi ibi unde inter super sine contra
""".split())

# Modernization gaps: contractions and dialect spellings MorphAdorner leaves
STOPWORDS |= set("""
hes shes ile bot tey mester mesters ick icke sall sud gud mun hae wad dee
henly bollux sesu plesse hee shee wee bee mee yow
""".split())

# Residual unmodernized / dialect fragments that survive MorphAdorner
STOPWORDS |= set("""
ane scho quhat quhen quhilk thu tou chyll chill iche ich icham chad gogs
hollidam coossen cuze whaw begar gor vench aull awl ump ohe huh heigh whoop
scilicet videlicet
""".split())

# Drop empty / 1-2 char fragments that sometimes survive tokenization
STOPWORDS = {w for w in STOPWORDS if len(w) >= 2}


def load_curated_names(name: str) -> dict[int, str]:
    path = config.DATA_DIR / f"cluster_names__{name}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {int(k): v["name"] for k, v in data.get("clusters", {}).items()}


def label_for(top_words: list[str], cluster_id: int, curated: dict[int, str]) -> str:
    if cluster_id == -1:
        return "-1: not clustered (short part or duplicate edition)"
    if cluster_id in curated:
        return f"{cluster_id}: {curated[cluster_id]}"
    head = ", ".join(top_words[:3]) if top_words else ""
    return f"{cluster_id}: {head}".rstrip(": ")


def label_one_preset(name: str) -> None:
    path = config.DATA_DIR / f"cluster_xy_table__{name}.csv"
    if not path.exists():
        print(f"⚠ {name}: missing {path.name}")
        return

    df = pd.read_csv(path, low_memory=False)
    df["cluster"] = df["cluster"].astype(int)
    curated = load_curated_names(name)

    # Character-name blocklist: stage-02 masking misses many non-English names
    # (petruchio, bajazet), which then dominate c-TF-IDF. Block any token that
    # occurs in the cast lists of only a few plays (a proper name), but KEEP
    # tokens used as names across many plays (king, mayor, clown — generic
    # role words that are genuine register signals).
    name_plays: dict[str, set] = {}
    name_src = (df["normalized_name"].fillna("").astype(str) + " " +
                df.get("raw_names", pd.Series("", index=df.index)).fillna("").astype(str)
                ).str.lower().str.replace(r"[|.,;·]", " ", regex=True)
    for nm, tcp in zip(name_src, df["TCP"].astype(str)):
        for tok in nm.replace("-", " ").split():
            if len(tok) >= 3 and tok.isalpha():
                name_plays.setdefault(tok, set()).add(tcp)
                # also block the token minus a trailing 'h'/'e' (bajazeth→bajazet)
                for alt in (tok.rstrip("h"), tok.rstrip("e")):
                    if len(alt) >= 3 and alt != tok:
                        name_plays.setdefault(alt, set()).add(tcp)
    name_block = {t for t, plays in name_plays.items() if len(plays) <= 4}
    print(f"   name blocklist: {len(name_block)} proper-name tokens "
          f"(kept {sum(1 for p in name_plays.values() if len(p) > 4)} generic name-words)")

    # Label from the masked+modernized text the clustering itself used
    text_col = "speech_text_embedding" if "speech_text_embedding" in df.columns \
        else "speech_text"
    print(f"🗂 c-TF-IDF column: {text_col} | curated names: {len(curated)}")

    grouped = (
        df.groupby("cluster")[text_col]
        .apply(lambda s: " ".join(s.fillna("")))
        .reset_index()
        .rename(columns={text_col: "speech_text"})
    )

    vec = CountVectorizer(
        stop_words=list(STOPWORDS | name_block),
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        min_df=2,
        max_df=0.95,
    )
    counts = vec.fit_transform(grouped["speech_text"])
    words = np.array(vec.get_feature_names_out())

    # Second-pass name filter: block vocabulary whose normalized 5-prefix
    # matches a blocked proper name (catches spelling variants the exact
    # blocklist misses: desdemon/desdemona, ieoffry/jeffrey, cutberd/cutbeard).
    def norm5(t: str) -> str:
        return t.replace("j", "i").replace("v", "u")[:5]
    prefix5 = {norm5(t) for t in name_block if len(t) >= 5}
    keep = np.array([not (len(w) >= 5 and norm5(w) in prefix5) for w in words])
    counts = counts[:, keep]
    words = words[keep]

    tfidf = TfidfTransformer().fit_transform(counts).toarray()

    rows: list[dict] = []
    for i, cluster_id in enumerate(grouped["cluster"]):
        n_members = int((df["cluster"] == cluster_id).sum())
        top_idx = tfidf[i].argsort()[-10:][::-1]
        top_words = [str(w) for w in words[top_idx]]
        top_chars = (
            df[df["cluster"] == cluster_id]
            .sort_values("n_chars", ascending=False)["normalized_name"]
            .head(5)
            .tolist()
        )
        rows.append({
            "cluster": int(cluster_id),
            "n_members": n_members,
            "name": curated.get(int(cluster_id), ""),
            "top_words": ", ".join(top_words),
            "top_characters": " | ".join(map(str, top_chars)),
            "label": label_for(top_words, int(cluster_id), curated),
        })

    labels_df = pd.DataFrame(rows).sort_values("cluster")
    labels_df.to_csv(config.DATA_DIR / f"cluster_labels__{name}.csv", index=False)

    label_map = dict(zip(labels_df["cluster"], labels_df["label"]))
    words_map = dict(zip(labels_df["cluster"], labels_df["top_words"]))
    df["topic_label"] = df["cluster"].map(label_map)
    df["top_words"]   = df["cluster"].map(words_map)
    df.to_csv(path, index=False)

    print(f"✅ {name}: {len(labels_df)} clusters labeled")


def main() -> None:
    for name in config.CLUSTER_TABLES:
        label_one_preset(name)


if __name__ == "__main__":
    main()
