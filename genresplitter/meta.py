APP_NAME = "GenreSplitter"
APP_VERSION = "2.9.0-hotfix5"
APP_DATE = "21-december-2025"
APP_COPYRIGHT = "Copyright © 2025 R. Snijder. All rights reserved."

APP_RELEASE_NOTES = (
    "GenreSplitter v2.9.0-hotfix5 release: "
    "Python 3.13 compat (vervangt imghdr door Pillow) + "
    "iTunes single-winner selectie (voorkomt meerdere plaatsingen; altijd verplaatsen naar beste match) + "
    "fix voor stop/crash (write_run_report flag altijd geïnitialiseerd) + "
    "cover art normalisatie (converteert WEBP/GIF/unknown naar JPEG/PNG en update bestaande artwork netjes) + "
    "metadata update policies: "
    ""confidence" (alleen overschrijven bij hoge matchscore; anders alleen lege tags vullen) en "
    ""cover_only" (alleen artwork updaten, teksttags ongemoeid). "
    "Incl. multi-format metadata tagging (MP3/ID3v2.4, FLAC, M4A/MP4, WAV/AIFF, OGG/OPUS) en run-rapportage (CSV + JSON). "
    "Zie: https://github.com/Techraym/GenreSplitter"
)
