"""
fix_corrupted_candidate_names.py — One-time script to clean all corrupted candidate names.

Run:
    .\\venv\\Scripts\\python scripts\\fix_corrupted_candidate_names.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.entities import Candidate, CVFile, ExtractedCVData
from app.services.cv_name_cleaner import is_invalid_candidate_name, sanitize_or_fallback_name


def main():
    db = SessionLocal()
    try:
        candidates = db.execute(select(Candidate)).scalars().all()

        print("=" * 70)
        print("  FIX CORRUPTED CANDIDATE NAMES — DATABASE CLEANUP SCRIPT")
        print("=" * 70)
        print(f"Total candidates: {len(candidates)}\n")

        fixed = []
        kept = []
        manual = []

        for candidate in candidates:
            fn = candidate.first_name or ""
            ln = candidate.last_name or ""

            if not is_invalid_candidate_name(fn, ln):
                kept.append(candidate)
                continue

            # Gather context for recovery
            raw_text = None
            filename = None
            email = candidate.email

            # Get CV raw text + filename
            cv_file = db.execute(
                select(CVFile).where(CVFile.candidate_id == candidate.id).limit(1)
            ).scalars().first()
            if cv_file:
                filename = cv_file.original_filename
                extracted = db.execute(
                    select(ExtractedCVData).where(ExtractedCVData.cv_file_id == cv_file.id).limit(1)
                ).scalars().first()
                if extracted:
                    raw_text = extracted.raw_text

            new_fn, new_ln = sanitize_or_fallback_name(
                first_name=fn,
                last_name=ln,
                raw_text=raw_text,
                email=email,
                filename=filename,
            )

            if new_fn == "Prénom" and new_ln == "Candidat":
                manual.append((candidate, fn, ln))
                continue

            fixed.append((candidate.id, fn, ln, new_fn, new_ln))
            candidate.first_name = new_fn
            candidate.last_name = new_ln

        db.commit()

        # Report
        print(f"{'ID':10} | {'BEFORE (CORRUPTED)':40} | {'AFTER (FIXED)':30} | STATUS")
        print("-" * 100)
        for cid, old_fn, old_ln, new_fn, new_ln in fixed:
            old = f"{old_fn} {old_ln}".strip()[:38]
            new = f"{new_fn} {new_ln}".strip()[:28]
            print(f"{str(cid)[:8]:10} | {old:40} | {new:30} | FIXED")

        for candidate, old_fn, old_ln in manual:
            old = f"{old_fn} {old_ln}".strip()[:38]
            print(f"{str(candidate.id)[:8]:10} | {old:40} | {'(needs manual review)':30} | MANUAL")

        print("-" * 100)
        print(f"\nFixed automatically : {len(fixed)}")
        print(f"Needs manual review : {len(manual)}")
        print(f"Already valid       : {len(kept)}")
        print(f"Total processed     : {len(candidates)}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
