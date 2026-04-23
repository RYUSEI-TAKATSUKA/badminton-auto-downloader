from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

EVENTS: tuple[str, ...] = ("ms", "ws", "md", "wd", "xd")

_TOURNAMENT_PATH_RE = re.compile(
    r"^/tournament/(?P<tid>\d+)/(?P<slug>[^/]+)(?:/.*)?$"
)


@dataclass(frozen=True)
class TournamentURLs:
    tournament_id: str
    slug: str
    event_urls: list[tuple[str, str]]


def parse(url: str) -> TournamentURLs:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http") or not parsed.netloc.endswith(
        "bwfbadminton.com"
    ):
        raise ValueError(
            f"Not a BWF tournament URL: {url!r} (expected host *.bwfbadminton.com)"
        )

    m = _TOURNAMENT_PATH_RE.match(parsed.path)
    if not m:
        raise ValueError(
            f"URL does not match /tournament/<id>/<slug>/... pattern: {url!r}"
        )
    tid = m.group("tid")
    slug = m.group("slug")

    base_path = f"/tournament/{tid}/{slug}/draws/full-draw"
    event_urls: list[tuple[str, str]] = []
    for ev in EVENTS:
        new_path = f"{base_path}/{ev}"
        event_urls.append(
            (
                ev,
                urlunparse(
                    (parsed.scheme, parsed.netloc, new_path, "", "", "")
                ),
            )
        )

    return TournamentURLs(tournament_id=tid, slug=slug, event_urls=event_urls)
