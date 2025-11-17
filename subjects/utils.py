import unicodedata
from typing import Optional, Tuple

from django.conf import settings
from django.utils import timezone


def _normalize_text(value: Optional[str]) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).strip().lower()


def normalize_season_token(token: Optional[str]) -> Optional[str]:
    norm = _normalize_text(token)
    if not norm:
        return None
    mapping = {
        "o": "O",
        "oto": "O",
        "otono": "O",
        "otono1": "O",
        "otonio": "O",
        "otoño": "O",
        "oto": "O",
        "primavera": "P",
        "prim": "P",
        "p": "P",
        "spring": "P",
    }
    if norm in mapping:
        return mapping[norm]
    upper = norm.upper()
    if upper in {"O", "P"}:
        return upper
    return None


def parse_period_string(value: Optional[str]) -> Tuple[Optional[str], Optional[int]]:
    if not value:
        return None, None
    raw = str(value).strip()
    if not raw:
        return None, None
    if "-" in raw:
        season_token, year_token = raw.split("-", 1)
    else:
        season_token, year_token = raw, ""
    season = normalize_season_token(season_token)
    year_token = "".join(ch for ch in year_token if ch.isdigit())
    year = None
    if year_token:
        try:
            year = int(year_token)
        except ValueError:
            year = None
    if year is not None and year < 100:
        year += 2000 if year < 50 else 1900
    return season, year


def get_default_period_from_settings() -> Tuple[str, int]:
    season, year = parse_period_string(getattr(settings, "SUBJECT_DEFAULT_PERIOD", ""))
    if season and year:
        return season, year
    now = timezone.now()
    fallback_season = "O" if now.month <= 6 else "P"
    return fallback_season, now.year
