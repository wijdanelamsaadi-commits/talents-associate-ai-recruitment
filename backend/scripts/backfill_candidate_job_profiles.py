"""Backfill idempotent des profils métier candidats depuis les CV déjà analysés.

Usage prévu après validation métier :
    python backend/scripts/backfill_candidate_job_profiles.py --dry-run
    python backend/scripts/backfill_candidate_job_profiles.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Candidate, ExtractedCVData
from app.services.job_profile_service import classify_candidate_profile, enrich_parsed_data_with_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill des profils métier candidats.")
    parser.add_argument("--apply", action="store_true", help="Enregistre les profils identifiés.")
    parser.add_argument("--dry-run", action="store_true", help="Affiche uniquement le volume concerné.")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        print("Utilisez --dry-run ou --apply.")
        return 2

    updated = 0
    inspected = 0
    with SessionLocal() as db:
        statement = (
            select(ExtractedCVData)
            .where(ExtractedCVData.ai_output.is_not(None))
            .order_by(ExtractedCVData.updated_at.desc())
        )
        seen_candidates = set()
        for extracted_data in db.scalars(statement).all():
            if extracted_data.candidate_id in seen_candidates:
                continue
            seen_candidates.add(extracted_data.candidate_id)
            candidate = db.get(Candidate, extracted_data.candidate_id)
            if candidate is None:
                continue
            inspected += 1
            parsed_data = dict(extracted_data.ai_output or {})
            classification = classify_candidate_profile(parsed_data, extracted_data.raw_text)
            if not classification.title or candidate.identified_job_profile == classification.title:
                continue
            updated += 1
            if args.apply:
                enrich_parsed_data_with_profile(parsed_data, extracted_data.raw_text)
                extracted_data.ai_output = parsed_data
                candidate.identified_job_profile = classification.title
                candidate.job_profile_confidence = classification.confidence
                candidate.job_profile_matched_terms = classification.matched_terms

        if args.apply:
            db.commit()

    mode = "simulation" if args.dry_run else "application"
    print(f"Backfill profils métier ({mode}) : {updated} candidat(s) à mettre à jour sur {inspected} inspecté(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
