from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobOffer
from app.schemas import JobOfferCreate, JobOfferUpdate


def create_job_offer(db: Session, job_in: JobOfferCreate) -> JobOffer:
    job_data = job_in.model_dump()
    job = JobOffer(
        **job_data,
        employment_type=_map_contract_to_employment_type(job_data.get("contract_type")),
        requirements=_format_requirements(job_data),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_job_offers(db: Session, skip: int = 0, limit: int = 100) -> list[JobOffer]:
    statement = select(JobOffer).order_by(JobOffer.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def get_job_offer(db: Session, job_id: UUID) -> JobOffer | None:
    return db.get(JobOffer, job_id)


def update_job_offer(db: Session, job: JobOffer, job_in: JobOfferUpdate) -> JobOffer:
    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    if "contract_type" in update_data:
        job.employment_type = _map_contract_to_employment_type(job.contract_type)
    if any(field in update_data for field in ("required_skills", "preferred_skills", "required_experience_years", "education_level")):
        job.requirements = _format_requirements(
            {
                "required_skills": job.required_skills or [],
                "preferred_skills": job.preferred_skills or [],
                "required_experience_years": job.required_experience_years,
                "education_level": job.education_level,
            }
        )

    db.commit()
    db.refresh(job)
    return job


def delete_job_offer(db: Session, job: JobOffer) -> None:
    db.delete(job)
    db.commit()


def _map_contract_to_employment_type(contract_type: str | None) -> str:
    normalized = (contract_type or "").lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "full_time": "full_time",
        "fulltime": "full_time",
        "part_time": "part_time",
        "parttime": "part_time",
        "contract": "contract",
        "internship": "internship",
        "temporary": "temporary",
    }
    return mapping.get(normalized, "full_time")


def _format_requirements(job_data: dict) -> str:
    parts = []
    if job_data.get("required_skills"):
        parts.append("Required skills: " + ", ".join(job_data["required_skills"]))
    if job_data.get("preferred_skills"):
        parts.append("Preferred skills: " + ", ".join(job_data["preferred_skills"]))
    if job_data.get("required_experience_years") is not None:
        parts.append(f"Experience: {job_data['required_experience_years']} years")
    if job_data.get("education_level"):
        parts.append("Education: " + job_data["education_level"])
    return "\n".join(parts) if parts else ""
