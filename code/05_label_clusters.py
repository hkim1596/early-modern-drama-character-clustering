"""Stage 05 — Label each cluster with top distinguishing words.

Uses class-based TF-IDF (treats each cluster's concatenated speech text as a
single document, then runs TF-IDF across clusters). This surfaces the words
that *distinguish* one cluster from the others rather than the words most
common in the corpus.

Inputs (in DATA_DIR):
  - cluster_xy_table__<preset>.csv

Outputs (in DATA_DIR):
  - cluster_labels__<preset>.csv         per-cluster top words + label
  - cluster_xy_table__<preset>.csv       updated with topic_label and top_words columns
"""

from __future__ import annotations
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

# Drop empty / 1-2 char fragments that sometimes survive tokenization
STOPWORDS = {w for w in STOPWORDS if len(w) >= 2}


def label_for(top_words: list[str], cluster_id: int) -> str:
    if cluster_id == -1:
        return "-1: outliers"
    head = ", ".join(top_words[:3]) if top_words else ""
    return f"{cluster_id}: {head}".rstrip(": ")


def label_one_preset(name: str) -> None:
    path = config.DATA_DIR / f"cluster_xy_table__{name}.csv"
    if not path.exists():
        print(f"⚠ {name}: missing {path.name}")
        return

    df = pd.read_csv(path)
    df["cluster"] = df["cluster"].astype(int)

    grouped = (
        df.groupby("cluster")["speech_text"]
        .apply(lambda s: " ".join(s.fillna("")))
        .reset_index()
    )

    vec = CountVectorizer(
        stop_words=list(STOPWORDS),
        token_pattern=r"\b[a-zA-Z]{3,}\b",
        min_df=2,
        max_df=0.95,
    )
    counts = vec.fit_transform(grouped["speech_text"])
    words = np.array(vec.get_feature_names_out())
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
            "top_words": ", ".join(top_words),
            "top_characters": " | ".join(map(str, top_chars)),
            "label": label_for(top_words, int(cluster_id)),
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
    for preset in config.PRESETS:
        label_one_preset(preset["name"])


if __name__ == "__main__":
    main()
