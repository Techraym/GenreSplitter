import re
from typing import Optional, Dict, Tuple

# Utilities
FILENAME_RE = re.compile(r"^\s*(?P<artist>[^-]+?)\s*-\s*(?P<title>.+?)\s*\.mp3\s*$", re.IGNORECASE)

# Closed-system genre folding (Discogs + Last.fm oriented; outputs a closed set incl. selected subgenres).
GENRE_SIMPLIFY: Dict[str, str] = {
    "alternative rock": "Alternative Rock",
    "progressive rock": "Progressive Rock",
    "stage and screen": "Soundtrack",
    "stage & screen": "Soundtrack",
    "drum and bass": "Drum & Bass",
    "hardcore punk": "Hardcore Punk",
    "classic rock": "Classic Rock",
    "thrash metal": "Thrash Metal",
    "black metal": "Black Metal",
    "death metal": "Death Metal",
    "drum & bass": "Drum & Bass",
    "funk / soul": "Soul",
    "gangsta rap": "Rap",
    "garage rock": "Garage Rock",
    "heavy metal": "Heavy Metal",
    "post-grunge": "Post-Grunge",
    "smooth jazz": "Jazz",
    "spoken word": "Spoken",
    "children's": "Children",
    "deep house": "House",
    "doom metal": "Doom Metal",
    "electronic": "Electronic",
    "electropop": "Electropop",
    "indie folk": "Folk",
    "indie rock": "Indie Rock",
    "soundtrack": "Soundtrack",
    "tech house": "House",
    "acid jazz": "Acid Jazz",
    "classical": "Classical",
    "dance pop": "Dance-Pop",
    "dance-pop": "Dance-Pop",
    "dutch pop": "Nederpop",
    "eurodance": "Electronic",
    "hard rock": "Hard Rock",
    "hardstyle": "Electronic",
    "metalcore": "Metalcore",
    "non-music": "Spoken",
    "orchestra": "Classical",
    "post punk": "Post-Punk",
    "post-punk": "Post-Punk",
    "post-rock": "Post-Rock",
    "prog rock": "Progressive Rock",
    "punk rock": "Punk-Rock",
    "punk-rock": "Punk-Rock",
    "synth pop": "Synthpop",
    "synth-pop": "Synthpop",
    "alt rock": "Alternative Rock",
    "hollands": "Nederpop",
    "nederpop": "Nederpop",
    "new wave": "New Wave",
    "nu metal": "Nu Metal",
    "pop punk": "Pop-Punk",
    "pop rock": "Pop-Rock",
    "pop-punk": "Pop-Punk",
    "pop-rock": "Pop-Rock",
    "schlager": "Pop",
    "ska punk": "Ska-Punk",
    "ska-punk": "Ska-Punk",
    "symphony": "Classical",
    "synthpop": "Synthpop",
    "teen pop": "Pop",
    "ambient": "Ambient",
    "country": "Country",
    "dubstep": "Electronic",
    "hip hop": "Hip-Hop",
    "hip-hop": "Hip-Hop",
    "grunge": "Grunge",
    "hiphop": "Hip-Hop",
    "reggae": "Reggae",
    "techno": "Techno",
    "trance": "Trance",
    "blues": "Blues",
    "disco": "Disco",
    "house": "House",
    "k-pop": "Pop",
    "latin": "Latin",
    "metal": "Metal",
    "opera": "Classical",
    "score": "Soundtrack",
    "world": "World",
    "folk": "Folk",
    "funk": "Funk",
    "jazz": "Jazz",
    "kpop": "Pop",
    "rock": "Rock",
    "soul": "Soul",
    "trap": "Trap",
    "dnb": "Drum & Bass",
    "dub": "Dub",
    "edm": "Electronic",
    "pop": "Pop",
    "r&b": "R&B",
    "rap": "Rap",
    "rnb": "R&B",
    "ska": "Ska",

    # --- Dutch "piratenmuziek" / "geheime zender" culture ---
    # Keep these explicit aliases narrow; broader classification is handled by is_piratenmuziek().
    "piratenmuziek": "Piratenmuziek",
    "piraten hits": "Piratenmuziek",
    "piratenhits": "Piratenmuziek",
    "piratenzender": "Piratenmuziek",
    "piraten zender": "Piratenmuziek",
    "geheime zender": "Piratenmuziek",
}

CORE_GENRES = {"Acid Jazz", "Alternative Rock", "Ambient", "Black Metal", "Blues", "Children", "Christmas", "Classic Rock", "Classical", "Country", "Dance-Pop", "Death Metal", "Disco", "Doom Metal", "Drum & Bass", "Dub", "Electronic", "Electropop", "Folk", "Funk", "Garage Rock", "Grunge", "Hard Rock", "Hardcore Punk", "Heavy Metal", "Hip-Hop", "House", "Indie Rock", "Jazz", "Latin", "Metal", "Metalcore", "Nederpop", "New Wave", "Nu Metal", "Other", "Piratenmuziek", "Pop", "Pop-Punk", "Pop-Rock", "Post-Grunge", "Post-Punk", "Post-Rock", "Progressive Rock", "Punk-Rock", "R&B", "Rap", "Reggae", "Rock", "Ska", "Ska-Punk", "Soul", "Soundtrack", "Spoken", "Synthpop", "Techno", "Thrash Metal", "Trance", "Trap", "Unknown", "World"}


# --- Piratenmuziek classification ---
# This classification is intended to align with "geheime zender" / pirate radio programming in NL:
# largely Nederlandstalig levenslied/volks, (Duitse) schlager and related compilations ("piratenhits").

PIRATEN_STRONG_KEYWORDS = {
    "piratenmuziek",
    "piratenhits",
    "piraten hits",
    "piraat",
    "piraten",
    "piratenzender",
    "geheime zender",
    "piratenmedley",
    "piraten medley",
}

PIRATEN_CONTEXT_KEYWORDS = {
    "nederlandstalig",
    "hollands",
    "volksmuziek",
    "levenslied",
    "smartlap",
    "schlager",
    "duitse schlager",
    "feest",
    "party",
    "polka",
}

# A pragmatic "seed" artist set based on common pirate-hit compilations and pirate charts.
PIRATEN_SEED_ARTISTS = {
    "jannes",
    "frans bauer",
    "henk wijngaard",
    "marianne weber",
    "stef ekkel",
    "koos alberts",
    "rene riva",
    "grad damen",
    "thomas berge",
    "dries roelvink",
    "monique smit",
    "rene schuurmans",
    "helemaal hollands",
    "albert west",
    "mooi wark",
    "frank van etten",
    "django wagner",
    "mart hoogkamer",
}

def _norm_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[\u2019\u2018\u201c\u201d]", "'", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def piratenmuziek_score(artist: str, title: str, raw_genre: Optional[str] = None) -> int:
    """Return a score indicating likelihood of NL 'piratenmuziek' (geheime zender style)."""
    a = _norm_text(artist)
    t = _norm_text(title)
    g = _norm_text(raw_genre or "")
    text = f"{a} {t} {g}".strip()

    score = 0

    # Strong direct indicators
    if any(kw in text for kw in PIRATEN_STRONG_KEYWORDS):
        score += 6

    # Seed artist list (high precision)
    for sa in PIRATEN_SEED_ARTISTS:
        if sa and sa in a:
            score += 6
            break

    # Contextual indicators
    if any(kw in text for kw in PIRATEN_CONTEXT_KEYWORDS):
        score += 2

    # Small bump if it's explicitly labeled as (Duitse) schlager + NL context
    if ("schlager" in text or "volks" in text) and ("nederland" in text or "hollands" in text):
        score += 1

    return score

def is_piratenmuziek(artist: str, title: str, raw_genre: Optional[str] = None, threshold: int = 6) -> bool:
    return piratenmuziek_score(artist, title, raw_genre) >= int(threshold)



def _norm_match(s: str) -> tuple[str, str]:
    s = (s or "").lower().strip()
    s = re.sub(r"[\-_/]+", " ", s)
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s, s.replace(" ", "")

_GENRE_KEYS_NORM: list[tuple[str, str, str]] = []
for _kw in GENRE_SIMPLIFY.keys():
    _sp, _cp = _norm_match(_kw)
    _GENRE_KEYS_NORM.append((_kw, _sp, _cp))

def genre_candidates(raw: str) -> list[str]:
    """Split on commas/;/| and slashes; add hyphen variants and hyphen parts."""
    if not raw:
        return []
    s = raw.strip().lower()
    parts = re.split(r"\s*[,;/|]\s*|\s+/\s+", s)

    out: list[str] = []
    seen = set()

    def add(x: str) -> None:
        x = re.sub(r"\s+", " ", (x or "").strip())
        if not x:
            return
        if x not in seen:
            seen.add(x)
            out.append(x)

    for p in parts:
        if not p:
            continue
        add(p)
        if "-" in p:
            add(p.replace("-", " "))
            for sub in [t.strip() for t in p.split("-")]:
                add(sub)
    return out

def normalize_genre(g: str) -> str:
    """Normalize arbitrary genre strings to a supported top-level genre.

    Rules (kept intact; extended for new top-level folders):
    - Suffix dominance: the last genre term determines the parent genre (e.g. synthpop -> Pop).
    - Overrides (dominant anywhere in the string):
        - any *metal* -> Metal
        - "hard rock" -> Rock
    - Special cases:
        - "folk pop" -> Pop
        - "pop punk" -> Punk
        - "punk rock" -> Punk
        - "alternative rock" -> Alternative
        - "indie rock" -> Indie
        - "k-pop"/"kpop" -> K-Pop
        - "hip-hop"/"hip hop"/"hiphop" -> Hip-Hop
    - New top-level folders (dominant / token-based):
        - trance -> Trance
        - house -> House
        - edm -> EDM
        - club -> Club
        - hardcore -> Hardcore
    - Return "Other" only as a final fallback when nothing matches.
    """
    if not g:

        # HOTFIX v2.9.3.26 token_fallback:
        # Some APIs return partial/fragmented tags (e.g. "indie", "songwriter"). Treat these as safe fallbacks.
        # Do NOT map country/language fragments like "dutch" to a genre.
        if 'tokens' in locals():
            token_set = set(tokens)
            if "indie" in token_set:
                return "Indie"
            if "folk" in token_set:
                return "Folk"
            if "songwriter" in token_set or "songwriters" in token_set:
                return "Pop"

        return "Other"
    s = str(g).strip().lower()
    if not s:
        return "Other"

    # Normalize separators
    s = s.replace("_", " ").replace("/", " ").replace("-", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()

    # Exact special cases / aliases
    special_cases = {
        "folk pop": "Pop",
        "pop punk": "Punk",
        "punk rock": "Punk",
        "alternative rock": "Alternative",
        "indie rock": "Indie",
        "k pop": "K-Pop",
        "kpop": "K-Pop",
        "hip hop": "Hip-Hop",
        "hiphop": "Hip-Hop",
            "indie pop": "Pop",
        "dutch indie": "Indie",
        "indie folk": "Folk",
        "singer songwriter": "Pop",
        "singer songwriters": "Pop",
        "singer-songwriter": "Pop",
        "singer/songwriter": "Pop",
}
    if s in special_cases:
        return special_cases[s]

    # Dominant overrides
    if "metal" in s:
        return "Metal"
    if "hard rock" in s:
        return "Rock"

    # New top-level electronic folders:
    # - Treat as top-level if present as a token anywhere, or if last token matches.
    tokens = [t for t in s.split(" ") if t]
    token_set = set(tokens)

    if "edm" in token_set:
        return "EDM"
    # 'club' often appears as "club mix"/"club edit"
    if "club" in token_set:
        return "Club"
    # hardcore should win over house/trance if both present (rare but can happen)
    if "hardcore" in token_set:
        return "Hardcore"

    last = tokens[-1] if tokens else s
    if last == "trance" or last.endswith("trance"):
        return "Trance"
    if last == "house" or last.endswith("house"):
        return "House"

    # Suffix dominance for remaining top-level genres
    def _suffix_pick(word: str):
        suffix_map = [
            ("classical", "Classical"),
            ("country", "Country"),
            ("reggae", "Reggae"),
            ("latin", "Latin"),
            ("blues", "Blues"),
            ("jazz", "Jazz"),
            ("folk", "Folk"),
            ("punk", "Punk"),
            ("rock", "Rock"),
            ("dance", "Dance"),
            ("indie", "Indie"),
            ("alternative", "Alternative"),
            ("rap", "Rap"),
            ("pop", "Pop"),
        ]
        for suf, out in suffix_map:
            if word == suf or word.endswith(suf):
                return out
        return None

    picked = _suffix_pick(last)
    if picked:
        return picked

    # GENRE_MAP synonyms (final)
    try:
        if "GENRE_MAP" in globals() and isinstance(GENRE_MAP, dict):
            for top, syns in GENRE_MAP.items():
                try:
                    if s == str(top).strip().lower():
                        return str(top)
                    if isinstance(syns, (set, list, tuple)):
                        for syn in syns:
                            if s == str(syn).strip().lower():
                                return str(top)
                except Exception:
                    continue
    except Exception:
        pass

    return "Other"


def is_christmas_track(artist: str, title: str, genre: Optional[str]) -> bool:
    if genre and normalize_genre(genre) == "Christmas":
        return True
    text = f"{artist} {title}".lower()
    keywords = [
        "christmas","xmas","merry christmas","jingle bells","we wish you",
        "noel","noël","kerst","kerstmis","navidad","weihnachten","natale",
        "white christmas","silent night","santa claus"
    ]
    return any(kw in text for kw in keywords)

def guess_genre_from_keywords(artist: str, title: str) -> Optional[str]:
    text = f"{artist} {title}".lower()
    # Piratenmuziek (geheime zender) heuristic
    if is_piratenmuziek(artist, title, raw_genre=text, threshold=6):
        return "Piratenmuziek"
    for kw in ["christmas","xmas","merry christmas","jingle bells","we wish you","noel","noël","kerst","kerstmis","navidad","weihnachten","natale","white christmas","silent night","santa claus"]:
        if kw in text:
            return "Christmas"
    for kw, gen in GENRE_SIMPLIFY.items():
        if kw in text:
            return gen
    return None

def artist_bucket(artist: str) -> str:
    if not artist:
        return "!-?"
    artist = artist.strip()
    if not artist:
        return "!-?"
    ch = artist[0].upper()
    if ch.isdigit():
        return "0-9"
    if "A" <= ch <= "Z":
        return ch
    return "!-?"


def parse_artist_title(filename: str) -> Optional[Tuple[str, str]]:
    m = FILENAME_RE.match(filename)
    if not m:
        return None
    return m.group("artist").strip(), m.group("title").strip()

