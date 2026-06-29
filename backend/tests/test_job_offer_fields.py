from app.schemas.job import JobLanguage, JobOfferCreate


def test_job_offer_schema_accepts_new_fields():
    job = JobOfferCreate(
        title="Développeur",
        description="Poste full stack",
        sector="Informatique",
        soft_skills=["Communication", "Autonomie"],
        languages=[
            JobLanguage(language="Français", level="Courant"),
            JobLanguage(language="Anglais", level="Intermédiaire"),
        ],
        contract_type="CDI",
        education_level="Bac+5",
        required_experience_years=3,
    )

    assert job.sector == "Informatique"
    assert job.soft_skills == ["Communication", "Autonomie"]
    assert len(job.languages) == 2
    assert job.languages[0].language == "Français"
