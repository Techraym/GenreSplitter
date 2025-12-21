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
}

CORE_GENRES = {"Acid Jazz", "Alternative Rock", "Ambient", "Black Metal", "Blues", "Children", "Christmas", "Classic Rock", "Classical", "Country", "Dance-Pop", "Death Metal", "Disco", "Doom Metal", "Drum & Bass", "Dub", "Electronic", "Electropop", "Folk", "Funk", "Garage Rock", "Grunge", "Hard Rock", "Hardcore Punk", "Heavy Metal", "Hip-Hop", "House", "Indie Rock", "Jazz", "Latin", "Metal", "Metalcore", "Nederpop", "New Wave", "Nu Metal", "Other", "Pop", "Pop-Punk", "Pop-Rock", "Post-Grunge", "Post-Punk", "Post-Rock", "Progressive Rock", "Punk-Rock", "R&B", "Rap", "Reggae", "Rock", "Ska", "Ska-Punk", "Soul", "Soundtrack", "Spoken", "Synthpop", "Techno", "Thrash Metal", "Trance", "Trap", "Unknown", "World"}



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
    g = (g or "").strip()
    if not g:
        return "Unknown"
    candidates = genre_candidates(g)
    if not candidates:
        return "Unknown"

    christmas_variants = ["christmas","xmas","noel","noël","kerst","kerstmis","navidad","weihnachten","natale","frozen christmas"]
    for cand in candidates:
        if any(v in cand for v in christmas_variants):
            return "Christmas"

    for cand in candidates:
        low = cand.lower()
        spaced, compact = _norm_match(low)
        for orig_kw, kw_sp, kw_cp in _GENRE_KEYS_NORM:
            if orig_kw in low or kw_sp in spaced or kw_cp in compact:
                return GENRE_SIMPLIFY[orig_kw]
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

