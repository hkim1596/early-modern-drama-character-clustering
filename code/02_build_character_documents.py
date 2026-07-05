"""Stage 02 — build character documents: play metadata + embedding-ready text.

Input : data/character_table_modern.csv
        data/metadata.csv (or metadata.xlsx) — consolidated play-level metadata
Output: data/character_documents.csv  (+ character_documents_audit.md)

One row per character. `speech_text` keeps the original (modernized) speech —
the evidence site (07) shows real text. `speech_text_embedding` holds the
de-referenced version that 03_embed.py encodes, so clustering reflects
register/characterization rather than shared proper nouns. `__crowd__` rows
are dropped. QC columns allow row-level audit of every transformation.

The embedding text is produced by:

  1. TCP artifact repair    — rejoin floating-macron words (U+0304), expand
                              split abbreviations (y e -> the, y t -> that,
                              w t -> with), normalize &c. -> etc.
  2. Stage-direction strip  — leaked Exit / Exeunt / Manet / Finis / Actus /
                              Scena tokens (and "Enter <cast name>" lines).
  3. Proper-noun masking    — hybrid source:
                              (a) play-local gazetteer: every speaker's
                                  normalized_name + raw_names variants in the
                                  same play (role words protected),
                              (b) curated lists: classical deities, places,
                                  peoples/nations,
                              (c) spaCy NER (PERSON / GPE / LOC / NORP) as a
                                  catch-all on the already-masked text.
                              Typed natural placeholders:
                                  person -> someone     place  -> that place
                                  nation -> foreign(ers) deity -> the god
  4. Row policy             — __crowd__ rows dropped; all lengths kept
                              (filter with n_words at the clustering stage).

Protections:
  * Generic role words (king, servant, messenger, ...) are never masked.
  * Personification names (Love, Time, Fortune, ...) are never masked.
  * Cast names that double as common English words (Busy, Simple, Will,
    Grace, ...) are masked only as capitalized, non-sentence-initial tokens.
  * God / Christ / Jesus and generic sacred vocabulary are never masked
    (oath register); only named pagan/classical deities are.

Metadata join (from the former stage-02 script): joins metadata on TCP,
adds `display_name` (catalogue ALL-CAPS convention) and a stable
`character_id` (TCP::DISPLAY_NAME), collapses stray whitespace in
role_description/plot.

Usage:
    python 02_build_character_documents.py               # full run
    python 02_build_character_documents.py --sample 200  # quick test
    python 02_build_character_documents.py --no-ner      # skip spaCy pass
    # resumable execution on time-limited machines:
    #   --mode prep / --mode chunk --start N --end M / --mode merge
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DATA_DIR, METADATA_CSV

csv.field_size_limit(sys.maxsize)

IN_CSV = DATA_DIR / "character_table_modern.csv"
META_XLSX = DATA_DIR / "metadata.xlsx"
OUT_CSV = DATA_DIR / "character_documents.csv"
AUDIT_MD = DATA_DIR / "character_documents_audit.md"

PLACEHOLDER = {
    "person": "someone",
    "place": "that place",
    "nation": "foreign",       # plural surface forms -> "foreigners"
    "deity": "the god",
}

# ------------------------------------------------------------------
# Guard vocabularies — NEVER masked
# ------------------------------------------------------------------
ROLE_WORDS = {
    # ranks / offices / kin / occupations that appear as speech prefixes
    "king", "queen", "prince", "princess", "duke", "duchess", "emperor",
    "empress", "lord", "lords", "lady", "ladies", "earl", "count", "countess",
    "baron", "knight", "squire", "sir", "madam", "master", "mistress",
    "gentleman", "gentlemen", "gentlewoman", "gentlewomen", "citizen",
    "citizens", "courtier", "courtiers", "senator", "senators", "tribune",
    "consul", "governor", "viceroy", "ambassador", "herald", "marshal",
    "general", "captain", "lieutenant", "sergeant", "soldier", "soldiers",
    "officer", "officers", "guard", "guards", "watch", "watchman", "watchmen",
    "constable", "sheriff", "mayor", "alderman", "bailiff", "beadle",
    "justice", "judge", "lawyer", "notary", "clerk", "scrivener", "crier",
    "jailer", "jailor", "gaoler", "keeper", "executioner", "hangman",
    "messenger", "post", "nuntius", "servant", "servants", "servingman",
    "serving-man", "attendant", "attendants", "page", "boy", "boys", "girl",
    "lackey", "footman", "groom", "usher", "steward", "butler", "porter",
    "chamberlain", "hostess", "host", "drawer", "tapster", "vintner",
    "ostler", "cook", "carrier", "carter", "clown", "fool", "jester", "vice",
    "musician", "musicians", "singer", "dancer", "actor", "player", "players",
    "prologue", "epilogue", "chorus", "presenter", "poet", "author",
    "priest", "parson", "vicar", "curate", "friar", "monk", "abbot", "abbess",
    "nun", "bishop", "archbishop", "cardinal", "pope", "chaplain", "flamen",
    "prophet", "prophetess", "soothsayer", "augur", "sibyl", "oracle",
    "doctor", "physician", "surgeon", "apothecary", "scholar", "student",
    "pedant", "tutor", "schoolmaster", "merchant", "mercer", "draper",
    "goldsmith", "jeweller", "broker", "usurer", "banker", "pedlar",
    "chapman", "prentice", "apprentice", "tailor", "barber", "smith",
    "tanner", "weaver", "tinker", "cobbler", "shoemaker", "botcher",
    "miller", "baker", "butcher", "brewer", "grocer", "fishwife", "sempster",
    "shepherd", "shepherdess", "herdsman", "ploughman", "farmer", "gardener",
    "forester", "hunter", "huntsman", "falconer", "fisherman", "sailor",
    "sailors", "mariner", "mariners", "boatswain", "pilot", "pirate",
    "soldado", "beggar", "beggars", "thief", "thieves", "rogue", "rogues",
    "outlaw", "outlaws", "bandit", "gipsy", "gypsy", "pander", "bawd",
    "courtesan", "whore", "wench", "man", "men", "woman", "women", "maid",
    "maids", "maiden", "virgin", "wife", "wives", "husband", "widow",
    "widower", "mother", "father", "son", "sons", "daughter", "daughters",
    "brother", "brothers", "sister", "sisters", "uncle", "aunt", "nephew",
    "niece", "cousin", "grandam", "grandsire", "nurse", "child", "children",
    "infant", "old", "young", "first", "second", "third", "fourth", "fifth",
    "ghost", "spirit", "spirits", "angel", "angels", "devil", "devils",
    "demon", "fiend", "fury", "furies", "witch", "witches", "wizard",
    "conjurer", "magician", "enchanter", "fairy", "fairies", "nymph",
    "nymphs", "satyr", "satyrs", "muse", "muses", "genius", "shade",
    "sexton", "gravedigger", "herald", "trumpeter", "drummer", "ensign",
    "standard-bearer", "scout", "spy", "hermit", "pilgrim", "palmer",
    "traveller", "stranger", "strangers", "neighbour", "neighbours",
    "gossip", "crowd", "rabble", "mob", "omnes", "all", "both", "others",
    "another", "everyone", "chorus", "dame", "sirrah", "goodman",
    "goodwife", "gaffer", "gammer", "signior", "signor", "seignior",
    "monsieur", "madame", "mounsieur", "don", "donna", "senor", "tyrant",
    "conqueror", "champion", "warrior", "victor", "rebel", "rebels",
    "traitor", "traitors", "villain", "villains", "slave", "slaves",
    "captive", "captives", "prisoner", "prisoners", "enemy", "enemies",
    "friend", "friends", "lover", "lovers", "mistress", "paramour",
}


def in_guard(low: str) -> bool:
    """Guard check that also catches regular plurals of guarded words."""
    return low in GUARD or (low.endswith("s") and low[:-1] in GUARD)

PERSONIFICATIONS = {
    # morality-play / masque abstractions that speak as characters;
    # masking these words would gut the corpus vocabulary
    "love", "hate", "time", "death", "life", "fame", "fortune", "nature",
    "truth", "falsehood", "envy", "pride", "wrath", "anger", "lust",
    "lechery", "gluttony", "sloth", "covetousness", "avarice", "greed",
    "charity", "faith", "hope", "despair", "mercy", "justice", "peace",
    "war", "plague", "famine", "rumour", "rumor", "report", "echo",
    "conscience", "reason", "wit", "wisdom", "folly", "vanity", "virtue",
    "vice", "sin", "grace", "honour", "honor", "shame", "pleasure", "pain",
    "sorrow", "joy", "mirth", "melancholy", "youth", "age", "beauty",
    "strength", "knowledge", "ignorance", "science", "discretion",
    "perseverance", "patience", "temperance", "chastity", "humility",
    "liberality", "prodigality", "riot", "revel", "misrule", "everyman",
    "mankind", "humanity", "world", "flesh", "money", "gold", "poverty",
    "wealth", "labour", "labor", "idleness", "diligence", "hypocrisy",
    "sensuality", "simplicity", "night", "day", "morning", "evening",
    "summer", "winter", "spring", "autumn", "harvest", "sun", "moon",
    "star", "wind", "rain", "thunder", "lightning", "fire", "water",
    "earth", "air", "victory", "triumph", "revenge", "murder", "slander",
    "flattery", "friendship", "concord", "discord", "order", "chaos",
    "liberty", "security", "danger", "fear", "courage", "policy", "council",
    "counsel", "law", "equity", "opinion", "fancy", "desire", "will",
    "memory", "understanding", "imagination", "delight", "solace",
    "comfort", "care", "trouble", "mischief", "malice", "cruelty", "pity",
    "compassion", "kindness", "courtesy", "curiosity", "novelty", "custom",
    "ceremony", "majesty", "royalty", "nobility", "honesty", "plainness",
    "welcome", "holiday", "christmas", "lent", "carnival", "god", "gods",
    "goddess", "goddesses", "heaven", "hell", "purgatory", "paradise",
    "christ", "jesus", "jehovah", "providence", "destiny", "fate", "fates",
    "chance", "luck", "occasion", "opportunity", "experience", "practice",
    "study", "learning", "art", "music", "poetry", "painting", "sport",
    "game", "play", "dance", "song", "health", "sickness", "physic",
    "remedy", "medicine", "appetite", "hunger", "thirst", "sleep", "dream",
    "silence", "speech", "language", "tongue", "voice", "word", "words",
}

# Sacred names kept for oath/devotional register (see docstring).
SACRED_KEEP = {"god", "gods", "christ", "jesus", "jehovah", "lord", "heaven"}

# Closed-class words. Speech prefixes are often abbreviated ("And." for
# Androgeus, "Or." for Orlando), which would otherwise poison the gazetteer.
FUNCTION_WORDS = {
    "and", "or", "but", "if", "then", "than", "that", "this", "these",
    "those", "the", "a", "an", "of", "to", "in", "on", "at", "by", "for",
    "with", "from", "into", "unto", "not", "no", "nor", "so", "as", "is",
    "are", "was", "were", "be", "been", "being", "am", "do", "does", "did",
    "done", "have", "has", "had", "will", "shall", "would", "should",
    "can", "could", "may", "might", "must", "what", "which", "who", "whom",
    "whose", "when", "where", "why", "how", "all", "any", "some", "none",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "out", "up", "down", "off", "over", "under", "again", "more",
    "most", "less", "least", "very", "too", "now", "here", "there", "well",
    "yes", "yea", "nay", "oh", "ah", "lo", "hark", "come", "go", "see",
    "say", "let", "like", "such", "much", "many", "our", "your", "their",
    "his", "her", "its", "my", "thy", "mine", "thine", "you", "thou",
    "thee", "ye", "we", "us", "they", "them", "he", "she", "it", "i", "me",
}

GUARD = ROLE_WORDS | PERSONIFICATIONS | SACRED_KEEP | FUNCTION_WORDS

# ------------------------------------------------------------------
# Curated mask lists
# ------------------------------------------------------------------
DEITIES = {
    # Roman / Greek pantheon + underworld + frequent mythological figures
    "jove", "jupiter", "juno", "venus", "cupid", "mars", "mercury", "diana",
    "phoebus", "phebus", "phoebe", "apollo", "bacchus", "neptune", "pluto",
    "plutus",
    "proserpina", "proserpine", "ceres", "vulcan", "minerva", "pallas",
    "athena", "athene", "saturn", "saturnus", "hymen", "hercules", "alcides",
    "pan", "flora", "aurora", "luna", "sol", "titan", "cynthia", "hecate",
    "fortuna", "bellona", "victoria", "astraea", "themis", "nemesis", "ate",
    "zeus", "hera", "poseidon", "aphrodite", "artemis", "hermes", "ares",
    "hephaestus", "demeter", "persephone", "dionysus", "hades", "cronos",
    "cronus", "prometheus", "atlas", "ganymede", "adonis", "narcissus",
    "phaeton", "phaethon", "icarus", "daedalus", "orpheus", "eurydice",
    "charon", "cerberus", "rhadamanthus", "minos", "aeacus", "boreas",
    "zephyrus", "zephyr", "aeolus", "triton", "thetis", "tethys", "oceanus",
    "nereus", "amphitrite", "galatea", "morpheus", "somnus", "momus",
    "comus", "vesta", "janus", "terminus", "priapus", "silenus", "faunus",
    "sylvanus", "silvanus", "pomona", "iris", "eros", "psyche", "clotho",
    "lachesis", "atropos", "megaera", "alecto", "tisiphone", "melpomene",
    "calliope", "clio", "thalia", "erato", "terpsichore", "urania",
    "polyhymnia", "euterpe", "mnemosyne", "leda", "danae", "europa", "io",
    "semele", "alcmena", "latona", "niobe", "arachne", "medusa", "gorgon",
    "circe", "calypso", "scylla", "charybdis", "sirens", "siren", "sphinx",
    "chimera", "hydra", "pegasus", "centaur", "cyclops", "polyphemus",
    "satan", "lucifer", "beelzebub", "belial", "mephistopheles",
    "mephostophilis", "mahomet", "mahound", "termagant",
}

PLACES = {
    # classical / biblical
    "rome", "troy", "troynovant", "ilium", "ilion", "athens", "sparta",
    "thebes", "corinth", "argos", "mycenae", "delphi", "delos", "crete",
    "ithaca", "carthage", "babylon", "nineveh", "jerusalem", "judea",
    "israel", "canaan", "sodom", "gomorrah", "eden", "egypt", "memphis",
    "alexandria", "nile", "greece", "hellas", "macedon", "macedonia",
    "thessaly", "arcadia", "olympus", "parnassus", "helicon", "ida",
    "elysium", "styx", "acheron", "lethe", "avernus", "tartarus", "erebus",
    "phlegethon", "cocytus", "latium", "tiber", "capitol", "pharsalia",
    "philippi", "actium", "cannae", "numidia", "libya", "ethiopia",
    # early modern europe / mediterranean
    "italy", "naples", "venice", "florence", "milan", "milaine", "padua",
    "verona", "mantua", "genoa", "ferrara", "pisa", "siena", "urbino",
    "parma", "ravenna", "messina", "palermo", "sicily", "sicilia",
    "sardinia", "corsica", "malta", "rhodes", "cyprus", "candy", "crete",
    "constantinople", "byzantium", "turkey", "anatolia", "natolia",
    "persia", "media", "parthia", "scythia", "tartary", "cathay", "china",
    "india", "arabia", "syria", "damascus", "antioch", "tyre", "sidon",
    "phoenicia", "armenia", "colchis", "pontus", "bithynia", "epirus",
    "illyria", "dalmatia", "hungary", "bohemia", "poland", "polonia",
    "muscovy", "russia", "sweden", "denmark", "norway", "germany",
    "almaine", "saxony", "bavaria", "austria", "vienna", "prague",
    "netherlands", "holland", "flanders", "brabant", "antwerp", "brussels",
    "amsterdam", "france", "gallia", "gaul", "paris", "orleans", "rouen",
    "rheims",
    "bordeaux", "gascony", "gascoigne", "normandy", "brittany", "anjou",
    "picardy", "burgundy", "navarre", "spain", "iberia", "castile",
    "aragon", "granada", "seville", "toledo", "lisbon", "portugal",
    "morocco", "barbary", "algiers", "tunis", "fez", "africa", "afric",
    "africk", "asia", "europe", "america", "peru", "mexico",
    # britain
    "england", "britain", "britany", "albion", "london", "westminster",
    "windsor", "oxford", "cambridge", "canterbury", "york", "lancaster",
    "gloucester", "warwick", "salisbury", "winchester", "norwich",
    "bristol", "bristow", "coventry", "shrewsbury", "lincoln", "durham",
    "carlisle", "berwick", "dover", "calais", "callice", "kent", "essex",
    "sussex", "surrey", "norfolk", "suffolk", "somerset", "devonshire",
    "cornwall", "wales", "cambria", "ireland", "hibernia", "dublin",
    "scotland", "caledonia", "edinburgh", "thames", "severn", "tweed",
    "cheapside", "smithfield", "southwark", "shoreditch", "islington",
    "highgate", "tyburn", "newgate", "ludgate", "billingsgate",
    "bridewell", "bedlam", "paul's", "pauls",
}

NATIONS = {
    "roman", "romans", "grecian", "grecians", "greek", "greeks", "trojan",
    "trojans", "athenian", "athenians", "spartan", "spartans", "theban",
    "thebans", "carthaginian", "carthaginians", "egyptian", "egyptians",
    "persian", "persians", "parthian", "parthians", "scythian", "scythians",
    "tartar", "tartars", "turk", "turks", "turkish", "saracen", "saracens",
    "moor", "moors", "moorish", "jew", "jews", "jewish", "hebrew", "hebrews",
    "italian", "italians", "venetian", "venetians", "florentine",
    "florentines", "neapolitan", "neapolitans", "milanese", "paduan",
    "sicilian", "sicilians", "spaniard", "spaniards", "spanish",
    "castilian", "portuguese", "portingale", "portingales", "french",
    "frenchman", "frenchmen", "frenchwoman", "gauls", "norman",
    "normans", "breton", "burgundian", "dutch", "dutchman", "dutchmen",
    "fleming", "flemings", "flemish", "german", "germans", "almain",
    "almains", "saxon", "saxons", "dane", "danes", "danish", "norwegian",
    "swede", "swedes", "polack", "polacks", "polish", "russian", "russians",
    "muscovite", "muscovites", "hungarian", "bohemian", "bohemians",
    "english", "englishman", "englishmen", "englishwoman", "briton",
    "britons", "british", "welsh", "welshman", "welshmen", "scot", "scots",
    "scottish", "scotch", "irish", "irishman", "irishmen", "indian",
    "indians", "ethiopian", "ethiopians", "arabian", "arabians", "syrian",
    "syrians", "armenian", "armenians", "thracian", "thracians", "lydian",
    "lydians", "phrygian", "phrygians", "numidian", "numidians", "libyan",
    "african", "africans", "moroccan", "moroccans",
}
# NB: "barbarian", "christian", "pagan", "heathen", "infidel" are kept —
# they are religious/othering register, not geographic reference.

FREQUENT_CLASSICAL_PERSONS = {
    # top-up for figures NER tends to miss in early modern contexts
    "caesar", "alexander", "hector", "achilles", "priam", "hecuba", "helen",
    "paris", "troilus", "cressida", "ulysses", "agamemnon", "menelaus",
    "ajax", "nestor", "aeneas", "dido", "hannibal", "scipio", "pompey",
    "cato", "cicero", "tully", "brutus", "cassius", "antony", "cleopatra",
    "augustus", "octavius", "nero", "caligula", "tamburlaine", "tamerlane",
    "croesus", "midas", "tantalus", "ixion", "sisyphus", "leander",
    "pyramus", "thisbe", "lucrece", "lucretia", "tarquin",
    "virginius", "virginia", "coriolanus", "regulus", "fabius", "camillus",
    "romulus", "remus", "numa", "solon", "lycurgus", "socrates", "plato",
    "aristotle", "diogenes", "epicurus", "seneca", "ovid", "virgil",
    "homer", "horace", "juvenal", "martial", "plutarch", "machiavel",
    "democritus", "heraclitus", "pythagoras", "empedocles", "thales",
    "zeno", "epictetus", "galen", "hippocrates", "euclid", "archimedes",
    "ptolemy", "xerxes", "darius", "cyrus", "artaxerxes", "sardanapalus",
    "semiramis", "ninus", "nimrod", "belshazzar", "nebuchadnezzar",
    "holofernes", "herod", "pilate", "judas", "cain", "abel", "noah",
    "abraham", "isaac", "jacob", "joseph", "moses", "samson", "solomon",
    "absalom", "goliath", "jonah", "job", "daniel", "susanna",
    "machiavelli", "priamus", "andromache", "cassandra", "polyxena",
    "iphigenia", "clytemnestra", "orestes", "electra", "oedipus", "jocasta",
    "antigone", "creon", "medea", "jason", "theseus", "ariadne", "hippolyta",
    "hippolytus", "phaedra", "penelope", "telemachus", "penthesilea",
}

# ------------------------------------------------------------------
# Regex helpers
# ------------------------------------------------------------------
COMBINING = re.compile(r"[̀-ͯ]")
MACRON_SPLIT = re.compile(r"([A-Za-z]+)\s*[̀-ͯ]+\s*([a-z]+)?")
ABBREV = [
    (re.compile(r"\b([Yy]) e\b"), lambda m: "The" if m.group(1) == "Y" else "the"),
    (re.compile(r"\b([Yy]) t\b"), lambda m: "That" if m.group(1) == "Y" else "that"),
    (re.compile(r"\b([Ww]) t\b"), lambda m: "With" if m.group(1) == "W" else "with"),
    (re.compile(r"&c\.?"), lambda m: "etc."),
]
PILCROW = re.compile(r"[¶•◊]")
WS = re.compile(r"[ \t]+")

STAGE_DIR = re.compile(
    r"\b(?:Exeunt(?:\s+omnes)?|Exit|Manet|Manent|Finis|FINIS)\b\.?"
)
ACT_SCENE = re.compile(
    r"\b(?:Actus|ACTUS)\s+\w+\.?(?:\s+(?:Sc(?:e|oe|æ)na|SC(?:E|OE)NA)\s+\w+\.?)?"
    r"|\b(?:Sc(?:e|oe|æ)na|Scena)\s+\w+\.?"
)

SENT_INITIAL = re.compile(r"(?:^|[.!?;:]\s+|[\"'“‘]\s*)$")


def is_sentence_initial(text: str, pos: int) -> bool:
    return bool(SENT_INITIAL.search(text[:pos][-40:]))


# ------------------------------------------------------------------
# Lexicon for macron repair
# ------------------------------------------------------------------
def build_corpus_vocab(rows) -> set[str]:
    counts = Counter()
    token = re.compile(r"[a-z]+")
    for row in rows:
        counts.update(token.findall(row["speech_text"].lower()))
    return {w for w, c in counts.items() if c >= 5}


try:
    from wordfreq import zipf_frequency

    def known_word(w: str, vocab: set[str]) -> float:
        z = zipf_frequency(w.lower(), "en")
        if z >= 2.5:
            return z
        return 2.0 if w.lower() in vocab else 0.0

except ImportError:  # graceful degradation

    def known_word(w: str, vocab: set[str]) -> float:
        return 2.0 if w.lower() in vocab else 0.0


def repair_macrons(text: str, vocab: set[str]) -> tuple[str, int]:
    """Rejoin words split by a floating combining macron; infer omitted m/n."""
    n = 0

    def fix(m: re.Match) -> str:
        nonlocal n
        w1, w2 = m.group(1), m.group(2) or ""
        cands: list[tuple[float, str]] = []
        # macron marks omitted m/n at the join point
        if w2 and not (known_word(w2, vocab) >= 2.5 and len(w2) > 2):
            # w2 looks like a fragment -> join
            for mid in ("m", "n", ""):
                c = w1 + mid + w2
                cands.append((known_word(c, vocab), c + ""))
            best = max(cands)
            if best[0] > 0:
                n += 1
                return best[1]
        # treat w2 as an independent word; macron completes w1
        for suf in ("m", "n"):
            c = w1 + suf
            cands.append((known_word(c, vocab), c + (" " + w2 if w2 else "")))
        if w2:
            for mid in ("m", "n", ""):
                c = w1 + mid + w2
                cands.append((known_word(c, vocab), c))
        best = max(cands)
        n += 1
        if best[0] > 0:
            return best[1]
        # heuristic fallback: -io/-yo endings take n (redempcyon), else m
        suf = "n" if re.search(r"[csx]?[iy]o$", w1) else "m"
        return w1 + suf + ((" " + w2) if w2 else "")

    out = MACRON_SPLIT.sub(fix, text)
    out = COMBINING.sub("", out)  # any stragglers
    return out, n


LIGATURES = [("œ", "oe"), ("æ", "ae"), ("Œ", "Oe"), ("Æ", "Ae")]


def repair_tcp(text: str, vocab: set[str]) -> tuple[str, int]:
    n = 0
    for lig, rep in LIGATURES:
        if lig in text:
            n += text.count(lig)
            text = text.replace(lig, rep)
    if COMBINING.search(text):
        text, k = repair_macrons(text, vocab)
        n += k
    for pat, rep in ABBREV:
        text, k = pat.subn(rep, text)
        n += k
    text = PILCROW.sub(" ", text)
    return WS.sub(" ", text), n


# ------------------------------------------------------------------
# Stage directions
# ------------------------------------------------------------------
def strip_stage_directions(text: str, cast_regex: re.Pattern | None) -> tuple[str, int]:
    n = 0
    text, k = STAGE_DIR.subn(" ", text)
    n += k
    text, k = ACT_SCENE.subn(" ", text)
    n += k
    if cast_regex is not None:
        # "Enter <Name> (and <Name>)." lines leaked into speech
        def enter_fix(m: re.Match) -> str:
            nonlocal n
            span = m.group(0)
            if cast_regex.search(span):
                n += 1
                return " "
            return span

        text = re.sub(
            r"\bEnter\b[^.!?]{0,80}[.!?]", enter_fix, text
        )
    return WS.sub(" ", text).strip(), n


# ------------------------------------------------------------------
# Masking machinery
# ------------------------------------------------------------------
NAME_CLEAN = re.compile(r"[^\w' -]")


def cast_name_tokens(rows_of_play) -> set[str]:
    """All name tokens for one play from normalized_name + raw_names."""
    toks: set[str] = set()
    for row in rows_of_play:
        forms = [row["normalized_name"]] + row["raw_names"].split(" | ")
        for form in forms:
            form = NAME_CLEAN.sub(" ", form)
            for t in form.split():
                t = t.strip("'-")
                if len(t) >= 3 and not t.isdigit():
                    toks.add(t.lower())
    return {t for t in toks if t not in GUARD}


def compile_token_regex(tokens: set[str]) -> re.Pattern | None:
    """Capitalized whole-word matcher with optional genitive suffix.

    Group 1 = the name itself, group 2 = genitive marker ('s, bare s, or
    trailing apostrophe) so 'Caesars match' and "Caesar's wife" both mask.
    """
    if not tokens:
        return None
    variants = []
    for t in sorted(tokens, key=len, reverse=True):
        variants.append(t.capitalize())
        variants.append(t.upper())
        if "-" in t or "'" in t:
            variants.append(t.title())
    alts = "|".join(re.escape(v) for v in dict.fromkeys(variants))
    return re.compile(rf"\b({alts})('s|s|')?\b")


class Masker:
    """Applies typed replacements and tallies counts."""

    def __init__(self, common_check):
        self.common = common_check  # word -> True if also a common English word

    def mask_with_regex(
        self, text: str, pattern: re.Pattern, kind: str, counts: Counter,
        strict_initial: bool = True,
    ) -> str:
        """strict_initial: skip sentence-initial common-word matches.
        Play-local cast names pass strict_initial=False — cast membership
        is strong evidence of nameness even at sentence start (vocatives)."""
        def rep(m: re.Match) -> str:
            tok = m.group(1)          # the name, without genitive marker
            suffix = m.group(2) or ""
            low = tok.lower()
            if in_guard(low):
                return m.group(0)
            # common-word names: only capitalized (+ position check)
            if self.common(low):
                if not tok[0].isupper():
                    return m.group(0)
                if strict_initial and is_sentence_initial(text, m.start()):
                    return m.group(0)
            counts[kind] += 1
            if low in DEITIES:
                counts["deity"] += 1
                counts[kind] -= 1
                base = PLACEHOLDER["deity"]
            elif kind == "nation" and (tok.endswith(("s", "S")) or suffix == "s") \
                    and low not in (
                        "welsh", "english", "irish", "scottish", "dutch",
                        "french", "spanish", "danish", "turkish", "british"):
                return "foreigners"
            else:
                base = PLACEHOLDER[kind]
            return base + ("'s" if suffix else "")

        return pattern.sub(rep, text)


def collapse_placeholders(text: str) -> str:
    text = re.sub(r"\bsomeone(?:[ ,]+(?:and +)?someone)+\b", "someone", text)
    text = re.sub(r"\b(?:the god)(?:[ ,]+(?:and +)?the god)+\b", "the gods", text)
    text = re.sub(
        r"(^|[.!?]\s+)(someone|that place|foreign|the god)",
        lambda m: m.group(1) + m.group(2)[0].upper() + m.group(2)[1:],
        text,
    )
    return text


# ------------------------------------------------------------------
# Shared pipeline pieces
# ------------------------------------------------------------------
NER_TYPE = {"PERSON": "person", "GPE": "place", "LOC": "place", "NORP": "nation"}
QC_FIELDS = [
    "n_masked_person", "n_masked_place", "n_masked_nation",
    "n_masked_deity", "n_masked_total", "mask_rate",
    "n_tcp_repairs", "n_stage_dirs_removed",
]


def load_rows(path: Path) -> tuple[list[dict], list[str], int]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())
    n_crowd = sum(1 for r in rows if r["normalized_name"] == "__crowd__")
    rows = [r for r in rows if r["normalized_name"] != "__crowd__"]
    return rows, fieldnames, n_crowd


def make_common_check():
    try:
        from wordfreq import zipf_frequency

        def common(w: str) -> bool:
            return zipf_frequency(w, "en") >= 3.3

    except ImportError:
        _fallback = {
            "will", "grace", "page", "host", "busy", "simple", "sly",
            "blunt", "grey", "gray", "rivers", "scales", "band", "post",
            "quickly", "kate", "jack", "robin", "frank", "miles", "rose",
            "may", "hero", "paris", "pistol", "lacy", "ross",
        }

        def common(w: str) -> bool:
            return w in _fallback

    return common


def build_gazetteers(rows: list[dict], tcp_key: str) -> dict[str, re.Pattern | None]:
    by_play: dict[str, list] = defaultdict(list)
    for r in rows:
        by_play[r[tcp_key]].append(r)
    return {tcp: compile_token_regex(cast_name_tokens(prows))
            for tcp, prows in by_play.items()}


class Pipeline:
    def __init__(self, vocab: set[str], gaz_re: dict, use_ner: bool = True):
        self.vocab = vocab
        self.gaz_re = gaz_re
        self.masker = Masker(make_common_check())
        self.deity_re = compile_token_regex(DEITIES)
        self.place_re = compile_token_regex({p for p in PLACES if p not in GUARD})
        self.nation_re = compile_token_regex({p for p in NATIONS if p not in GUARD})
        self.classical_re = compile_token_regex(
            {p for p in FREQUENT_CLASSICAL_PERSONS if p not in GUARD})
        self.nlp = None
        if use_ner:
            import spacy

            self.nlp = spacy.load(
                "en_core_web_sm",
                disable=["tagger", "parser", "attribute_ruler", "lemmatizer"],
            )
            self.nlp.max_length = 2_500_000

    def pass1(self, text: str, tcp: str, counts: Counter) -> str:
        text, k = repair_tcp(text, self.vocab)
        counts["tcp_repairs"] += k
        text, k = strip_stage_directions(text, self.gaz_re.get(tcp))
        counts["stage_dirs"] += k
        gaz = self.gaz_re.get(tcp)
        if gaz is not None:
            text = self.masker.mask_with_regex(text, gaz, "person", counts,
                                               strict_initial=False)
        text = self.masker.mask_with_regex(text, self.deity_re, "deity", counts)
        text = self.masker.mask_with_regex(text, self.classical_re, "person", counts)
        text = self.masker.mask_with_regex(text, self.place_re, "place", counts)
        text = self.masker.mask_with_regex(text, self.nation_re, "nation", counts)
        return text

    def ner_mask(self, text: str, counts: Counter) -> str:
        if self.nlp is None:
            return text
        doc = self.nlp(text)
        spans = []
        for ent in doc.ents:
            kind = NER_TYPE.get(ent.label_)
            if not kind:
                continue
            toks = list(ent)
            placeholder_bits = {"someone", "foreign", "foreigners", "that",
                                "place", "the", "god"}
            while toks and (
                in_guard(toks[0].text.lower())
                or toks[0].text.lower() in placeholder_bits
                or not toks[0].text[0].isupper()
            ):
                toks = toks[1:]
            while toks and (
                in_guard(toks[-1].text.lower())
                or toks[-1].text.lower() in placeholder_bits
                or not toks[-1].text[0].isupper()
            ):
                toks = toks[:-1]
            if not toks:
                continue
            start, end = toks[0].idx, toks[-1].idx + len(toks[-1].text)
            frag = text[start:end]
            low = frag.lower()
            if in_guard(low) or len(frag) < 3:
                continue
            # single-token entities: early modern texts capitalize ordinary
            # nouns freely, and sm-model NER tags many of them PERSON/GPE.
            # Reject any single token that exists as an ordinary word —
            # in the corpus itself (lowercased, freq >= 5) or in modern
            # English — unless it survived to here via the curated lists.
            if len(toks) == 1 and (low in self.vocab or self.masker.common(low)):
                continue
            if self.masker.common(low) and is_sentence_initial(text, start):
                continue
            if low in DEITIES:
                kind = "deity"
            spans.append((start, end, kind, low))
        out, prev = [], 0
        for start, end, kind, low in sorted(spans):
            if start < prev:
                continue
            out.append(text[prev:start])
            if kind == "nation" and low.endswith("s"):
                out.append("foreigners")
            else:
                out.append(PLACEHOLDER[kind])
            counts[kind] += 1
            prev = end
        out.append(text[prev:])
        return "".join(out)

    def process_row(self, row: dict, tcp_key: str) -> tuple[str, Counter]:
        counts = Counter()
        text = self.pass1(row["speech_text"], row[tcp_key], counts)
        text = self.ner_mask(text, counts)
        return collapse_placeholders(WS.sub(" ", text).strip()), counts


def finalize_row(row: dict, masked: str, counts: Counter) -> dict:
    total = sum(counts[k] for k in ("person", "place", "nation", "deity"))
    n_words = max(1, int(row["n_words"]))
    new = dict(row)                      # speech_text stays original
    new["speech_text_embedding"] = masked
    new["n_masked_person"] = counts["person"]
    new["n_masked_place"] = counts["place"]
    new["n_masked_nation"] = counts["nation"]
    new["n_masked_deity"] = counts["deity"]
    new["n_masked_total"] = total
    new["mask_rate"] = round(total / n_words, 4)
    new["n_tcp_repairs"] = counts["tcp_repairs"]
    new["n_stage_dirs_removed"] = counts["stage_dirs"]
    return new


# ------------------------------------------------------------------
# Metadata join (formerly the whole of stage 02)
# ------------------------------------------------------------------
def collapse_ws(s):
    if not isinstance(s, str):
        return s
    return re.sub(r"\s+", " ", s).strip()


def canonical_display_name(name: str) -> str:
    """Catalogue convention: ALL CAPS; crowd bucket stays bracketed."""
    if not isinstance(name, str):
        return name
    if name == "__crowd__":
        return "[crowd]"
    return name.upper().strip()


def attach_metadata(out_rows: list[dict], tcp_key: str):
    """Join play-level metadata on TCP; add display_name + character_id."""
    import pandas as pd

    df = pd.DataFrame(out_rows).rename(columns={tcp_key: "TCP"})
    if METADATA_CSV.exists():
        meta = pd.read_csv(METADATA_CSV)
    elif META_XLSX.exists():
        meta = pd.read_excel(META_XLSX)
    else:
        raise FileNotFoundError(
            f"neither {METADATA_CSV} nor {META_XLSX} found — build metadata "
            f"first (code/merge_metadata.py)")
    print(f"metadata: {len(meta)} plays, {len(meta.columns)} columns", flush=True)

    merged = df.merge(meta, on="TCP", how="left", suffixes=("", "_meta"))
    matched = merged["title"].notna().sum() if "title" in merged.columns else 0
    print(f"characters matched to metadata: {matched}/{len(merged)} "
          f"({matched / len(merged):.0%})", flush=True)

    merged["display_name"] = merged["normalized_name"].apply(canonical_display_name)
    for c in ("role_description", "plot"):
        if c in merged.columns:
            merged[c] = merged[c].apply(collapse_ws)
    merged["character_id"] = (
        merged["TCP"].astype(str) + "::" + merged["display_name"].astype(str))

    front = [
        "character_id", "TCP", "brit_drama_number",
        "display_name", "normalized_name", "raw_names",
        "title", "author", "year", "Date_Decade",
        "date_first_performance", "genre", "play_type",
        "theater", "theater_type", "company",
        "role_description", "match_score",
        "n_forms", "n_chars", "n_words",
    ]
    front = [c for c in front if c in merged.columns]
    text_cols = ["speech_text", "speech_text_embedding"]
    rest = [c for c in merged.columns
            if c not in front and c not in QC_FIELDS and c not in text_cols]
    merged = merged[front + rest + QC_FIELDS + text_cols]
    return merged


def write_outputs(out_rows, rows, fieldnames_in, n_crowd, tcp_key, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    merged = attach_metadata(out_rows, tcp_key)
    merged.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"wrote {output} ({len(merged)} rows, {len(merged.columns)} columns)",
          flush=True)

    # hover-field coverage for the visualization stages
    for c in ["title", "author", "year", "Date_Decade", "genre", "play_type",
              "theater", "role_description"]:
        if c in merged.columns:
            n = merged[c].notna().sum()
            print(f"  {c:25s} {n:5d}/{len(merged)} ({n / len(merged) * 100:.0f}%)",
                  flush=True)

    totals = Counter()
    for nr in out_rows:
        for k, src in (("person", "n_masked_person"), ("place", "n_masked_place"),
                       ("nation", "n_masked_nation"), ("deity", "n_masked_deity"),
                       ("tcp_repairs", "n_tcp_repairs"),
                       ("stage_dirs", "n_stage_dirs_removed")):
            totals[k] += int(nr[src])
    rates = sorted(float(nr["mask_rate"]) for nr in out_rows)
    med = rates[len(rates) // 2] if rates else 0.0
    lines = [
        f"rows in: {len(rows) + n_crowd}   __crowd__ dropped: {n_crowd}   "
        f"rows out: {len(out_rows)}",
        f"masks  person: {totals['person']}  place: {totals['place']}  "
        f"nation: {totals['nation']}  deity: {totals['deity']}",
        f"tcp repairs: {totals['tcp_repairs']}   "
        f"stage directions removed: {totals['stage_dirs']}",
        f"mask_rate  median: {med:.4f}  max: {rates[-1]:.4f}  "
        f"rows with zero masks: {sum(1 for x in rates if x == 0)}",
    ]
    print("\n".join(lines), flush=True)

    # audit sample: 40 random + 5 highest-repair + 5 highest-mask-rate
    by_index = {i: (rows[i], out_rows[i]) for i in range(len(rows))}
    random.seed(7)
    idxs = random.sample(range(len(rows)), min(40, len(rows)))
    idxs += [i for i, _ in sorted(
        by_index.items(), key=lambda kv: -int(kv[1][1]["n_tcp_repairs"]))[:5]]
    idxs += [i for i, _ in sorted(
        by_index.items(), key=lambda kv: -float(kv[1][1]["mask_rate"]))[:5]]
    with open(AUDIT_MD, "w", encoding="utf-8") as f:
        f.write("# Audit — character_documents\n\n## Build summary\n\n")
        f.write("\n".join("- " + ln for ln in lines) + "\n\n")
        f.write("## Sample\n\nRandom 40 rows + 5 highest-repair + 5 "
                "highest-mask-rate. `BEFORE` is speech_text, `AFTER` is "
                "speech_text_embedding.\n\n")
        for i in dict.fromkeys(idxs):
            r, nr = by_index[i]
            f.write(f"### {r[tcp_key]} — {r['normalized_name']} "
                    f"({r['n_words']} words)\n\n")
            f.write(f"masks: person {nr['n_masked_person']}, "
                    f"place {nr['n_masked_place']}, "
                    f"nation {nr['n_masked_nation']}, "
                    f"deity {nr['n_masked_deity']} | "
                    f"tcp repairs {nr['n_tcp_repairs']}, "
                    f"stage dirs {nr['n_stage_dirs_removed']} | "
                    f"mask_rate {nr['mask_rate']}\n\n")
            f.write("**BEFORE**\n\n> " + r["speech_text"][:600].replace("\n", " ")
                    + "\n\n**AFTER**\n\n> " + nr["speech_text_embedding"][:600]
                    + "\n\n---\n\n")
    print(f"wrote {AUDIT_MD}", flush=True)


# ------------------------------------------------------------------
# Main — `all` mode for normal use; prep/chunk/merge for resumable runs
# ------------------------------------------------------------------
def main() -> None:
    import json
    import pickle

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["all", "prep", "chunk", "merge"],
                    default="all")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--rows", type=str, default="",
                    help="comma-separated row indices to (re)process")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--no-ner", action="store_true")
    ap.add_argument("--input", type=Path, default=IN_CSV)
    ap.add_argument("--output", type=Path, default=OUT_CSV)
    ap.add_argument("--scratch", type=Path, default=DATA_DIR / "_embed_build")
    args = ap.parse_args()

    rows, fieldnames_in, n_crowd = load_rows(args.input)
    tcp_key = fieldnames_in[0]
    if args.sample:
        random.seed(13)
        rows = random.sample(rows, min(args.sample, len(rows)))
    vocab_pkl = args.scratch / "vocab.pkl"

    if args.mode == "prep":
        args.scratch.mkdir(parents=True, exist_ok=True)
        vocab = build_corpus_vocab(rows)
        with open(vocab_pkl, "wb") as f:
            pickle.dump(vocab, f)
        print(f"rows: {len(rows)}  vocab: {len(vocab)}  -> {vocab_pkl}", flush=True)
        return

    if args.mode == "chunk":
        with open(vocab_pkl, "rb") as f:
            vocab = pickle.load(f)
        if args.rows:
            idxs = [int(x) for x in args.rows.split(",")]
            sl = [rows[i] for i in idxs]
        else:
            idxs = list(range(args.start, args.end or len(rows)))
            sl = rows[args.start:args.end or len(rows)]
        # gazetteers must come from the FULL cast of each play in the
        # slice, not just the rows that happen to fall inside it
        plays = {r[tcp_key] for r in sl}
        gaz_rows = [r for r in rows if r[tcp_key] in plays]
        pipe = Pipeline(vocab, build_gazetteers(gaz_rows, tcp_key),
                        use_ner=not args.no_ner)
        if args.rows:
            # redo chunks sort after chunk_NNNNN files, so on merge they
            # override the original results for these row indices
            out_path = args.scratch / f"chunk_redo_{idxs[0]:05d}.jsonl"
        else:
            out_path = args.scratch / f"chunk_{args.start:05d}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for i, r in zip(idxs, sl):
                masked, counts = pipe.process_row(r, tcp_key)
                f.write(json.dumps(
                    {"i": i, "text": masked, "counts": dict(counts)}) + "\n")
        print(f"chunk {out_path.name}: {len(sl)} rows done", flush=True)
        return

    if args.mode == "merge":
        results: dict[int, tuple[str, Counter]] = {}
        for p in sorted(args.scratch.glob("chunk_*.jsonl")):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    results[d["i"]] = (d["text"], Counter(d["counts"]))
        missing = [i for i in range(len(rows)) if i not in results]
        if missing:
            sys.exit(f"missing {len(missing)} rows, e.g. {missing[:10]}")
        out_rows = [finalize_row(rows[i], *results[i]) for i in range(len(rows))]
        write_outputs(out_rows, rows, fieldnames_in, n_crowd, tcp_key, args.output)
        return

    # ---- mode "all": everything in one process ----
    print(f"{len(rows)} rows ({n_crowd} __crowd__ dropped)", flush=True)
    print("building corpus vocabulary ...", flush=True)
    vocab = build_corpus_vocab(rows)
    pipe = Pipeline(vocab, build_gazetteers(rows, tcp_key),
                    use_ner=not args.no_ner)
    out_rows = []
    for i, r in enumerate(rows):
        masked, counts = pipe.process_row(r, tcp_key)
        out_rows.append(finalize_row(r, masked, counts))
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(rows)}", flush=True)
    write_outputs(out_rows, rows, fieldnames_in, n_crowd, tcp_key, args.output)


if __name__ == "__main__":
    main()
