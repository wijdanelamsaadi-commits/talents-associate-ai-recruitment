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


def test_job_offer_schema_accepts_custom_business_values():
    job = JobOfferCreate(
        title="Responsable innovation territoriale",
        description="Poste stratégique",
        sector="Économie sociale et solidaire",
        soft_skills="Orientation client; Pensée stratégique; Curiosité",
        languages=[
            JobLanguage(language="Amazigh", level="Courant"),
        ],
        contract_type="Mission longue durée",
        education_level="MBA spécialisé",
        required_experience_years=6,
        status="open",
    )

    assert job.title == "Responsable innovation territoriale"
    assert job.sector == "Économie sociale et solidaire"
    assert job.contract_type == "Mission longue durée"
    assert job.education_level == "MBA spécialisé"
    assert job.required_experience_years == 6
    assert job.soft_skills == ["Orientation client", "Pensée stratégique", "Curiosité"]
    assert job.languages[0].language == "Amazigh"


def test_job_offer_schema_accepts_custom_title_from_other_option():
    job = JobOfferCreate(
        title="Ingénieur Biomédical",
        description="Mission de coordination biomédicale",
        sector="Santé",
        contract_type="Mission",
        education_level="Bac+5",
        required_skills=["Maintenance biomédicale"],
        status="open",
    )

    assert job.title == "Ingénieur Biomédical"
    assert job.title != "Autre"
