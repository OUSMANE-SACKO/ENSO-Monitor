"""Point d'entrée de l'ETL.

Usage :
    python -m etl.run --version "<version NOAA>"                              # télécharge (ONI_URL)
    python -m etl.run --version "<version NOAA>" --file data/oni.ascii.txt    # fichier local

Extract (télécharger) -> Transform (etl.transform) -> Load (etl.load)
"""
import argparse
import logging
import sys
from pathlib import Path

import httpx

from app.config import settings
from app.db import SessionLocal
from etl.load import load_oni
from etl.transform import parse_oni

log = logging.getLogger("etl")


def extract(url: str | None, file: Path | None) -> str:
    if file:
        log.info("Lecture du fichier local %s", file)
        return file.read_text(encoding="utf-8")
    log.info("Téléchargement %s", url)
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import de l'indice NOAA ONI")
    parser.add_argument("--file", type=Path, help="fichier oni.ascii.txt local")
    parser.add_argument("--url", default=settings.oni_url, help="URL NOAA (par défaut ONI_URL)")
    parser.add_argument("--version", required=True,
                        help="version NOAA de la série, telle qu'indiquée sur la page ONI le jour "
                             "de l'extraction (obligatoire : traçabilité)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    text = extract(args.url, args.file)
    result = parse_oni(text)

    for row in result.rejected.itertuples(index=False):
        log.warning("Ligne rejetée %s %s : %s", row.SEAS, row.YR, row.reason)

    with SessionLocal() as session:
        run = load_oni(
            session,
            result.clean,
            raw_text=text,
            # Même avec --file, la source reste l'URL NOAA d'où le fichier a été téléchargé.
            source_url=args.url,
            source_version=args.version,
            rows_read=result.rows_read,
            rows_rejected=len(result.rejected),
        )

    log.info(
        "Import #%s terminé : %s lues, %s insérées, %s mises à jour, %s rejetées",
        run.id, run.rows_read, run.rows_inserted, run.rows_updated, run.rows_rejected,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
