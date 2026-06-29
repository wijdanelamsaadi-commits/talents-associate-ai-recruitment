export const JOB_POSITIONS = [
  "Directeur Général",
  "Directeur",
  "Chef de Projet",
  "Chef d'Équipe",
  "Coordinateur",
  "Consultant",
  "Ingénieur",
  "Architecte",
  "Analyste",
  "Développeur",
  "Administrateur",
  "Technicien",
  "Comptable",
  "Contrôleur de Gestion",
  "Auditeur",
  "Fiscaliste",
  "Trésorier",
  "Juriste",
  "Acheteur",
  "Commercial",
  "Business Developer",
  "Responsable Commercial",
  "Chargé de Clientèle",
  "Recruteur",
  "Chargé RH",
  "HR Business Partner",
  "Gestionnaire Paie",
  "Formateur",
  "Assistant",
  "Assistant de Direction",
  "Office Manager",
  "Secrétaire",
  "Chargé Marketing",
  "Chef de Produit",
  "Community Manager",
  "Graphiste",
  "Data Analyst",
  "Data Scientist",
  "Product Owner",
  "Product Manager",
  "DevOps",
  "Administrateur Réseau",
  "Administrateur Système",
  "Chef de Production",
  "Responsable Production",
  "Responsable Qualité",
  "Responsable HSE",
  "Logisticien",
  "Magasinier",
  "Gestionnaire de Stock",
  "Chauffeur",
  "Conducteur de Travaux",
  "Chef de Chantier",
  "Dessinateur",
  "Médecin",
  "Infirmier",
  "Pharmacien",
  "Réceptionniste",
  "Serveur",
  "Cuisinier",
  "Vendeur",
  "Caissier",
  "Agent de Sécurité",
  "Agent Administratif",
  "Opérateur",
  "Ouvrier Qualifié",
  "Stagiaire",
] as const;

export const LANGUAGE_OPTIONS = ["Arabe", "Français", "Anglais", "Espagnol", "Allemand"] as const;

export const LANGUAGE_LEVELS = ["Débutant", "Intermédiaire", "Avancé", "Courant", "Natif"] as const;

export type JobLanguage = {
  language: string;
  level: string;
};

export const EXPERIENCE_LEVEL_TO_YEARS: Record<string, number> = {
  "0–1 an": 0,
  "2–5 ans": 3,
  "5–10 ans": 7,
  "10 ans et plus": 10,
};

export function yearsToExperienceLevel(years: number | null | undefined): string {
  if (years === null || years === undefined) {
    return "";
  }
  if (years <= 1) {
    return "0–1 an";
  }
  if (years <= 5) {
    return "2–5 ans";
  }
  if (years <= 10) {
    return "5–10 ans";
  }
  return "10 ans et plus";
}
