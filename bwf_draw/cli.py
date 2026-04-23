from __future__ import annotations

import sys
from pathlib import Path

import click

from .browser import launch
from .fetcher import CloudflareChallengeError, fetch_event_pdf
from .merger import merge
from .paths import OUTPUT_ROOT
from .url import parse

SETUP_LANDING = "https://bwfworldtour.bwfbadminton.com/calendar/"


@click.group()
def cli() -> None:
    """Download BWF tournament bracket PDFs (5 events) and merge into one file.

    Use `bwf-draw setup` once first to prime the dedicated Chrome profile
    against Cloudflare, then `bwf-draw download <url>` for each tournament.
    """


@cli.command()
def setup() -> None:
    """Open the dedicated Chrome profile so you can clear Cloudflare manually once."""
    click.echo("Opening Chrome with the dedicated profile.")
    click.echo(f"  Profile dir: {Path('profile').resolve()}")
    click.echo("Browse the BWF site briefly (a click or two), then close the window.")
    with launch(headless=False) as (_, context):
        page = context.new_page()
        page.goto(SETUP_LANDING, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
    click.echo("Setup complete. Cookies saved to profile/.")


@cli.command()
@click.argument("url")
def download(url: str) -> None:
    """Download 5-event PDFs for the tournament at URL and merge them."""
    try:
        parsed = parse(url)
    except ValueError as e:
        raise click.ClickException(str(e)) from e

    out_dir = OUTPUT_ROOT / parsed.slug
    click.echo(f"Tournament: {parsed.slug} (id={parsed.tournament_id})")
    click.echo(f"Output dir: {out_dir}")

    pdfs: list[Path] = []
    with launch(headless=False) as (_, context):
        for ev, ev_url in parsed.event_urls:
            click.echo(f"  [{ev.upper()}] {ev_url}")
            try:
                pdf = fetch_event_pdf(context, ev, ev_url, out_dir)
            except CloudflareChallengeError as e:
                raise click.ClickException(str(e)) from e
            click.echo(f"      saved -> {pdf} ({pdf.stat().st_size} bytes)")
            pdfs.append(pdf)

    combined = OUTPUT_ROOT / f"{parsed.slug}_combined.pdf"
    merge(pdfs, combined)
    click.echo(f"\nCombined PDF: {combined}")


_KNOWN_SUBCOMMANDS = {"setup", "download", "--help", "-h"}


def main() -> None:
    """Entry point. Allow `bwf-draw <url>` as shorthand for `bwf-draw download <url>`."""
    argv = sys.argv[1:]
    if argv and argv[0] not in _KNOWN_SUBCOMMANDS and argv[0].startswith("http"):
        sys.argv = [sys.argv[0], "download", *argv]
    cli(prog_name="bwf-draw")


if __name__ == "__main__":
    main()
