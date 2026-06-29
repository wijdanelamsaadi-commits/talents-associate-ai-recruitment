export const PIPELINE_STAGE_OPTIONS = [
  { value: "preselectionne", label: "Présélectionné" },
  { value: "non_selectionne", label: "Non sélectionné" },
  { value: "entretien_cabinet", label: "Entretien cabinet" },
  { value: "entretien_client", label: "Entretien client" },
  { value: "profil_valide", label: "Profil validé" },
  { value: "refus_candidat", label: "Refus candidat" },
] as const;

export const EVALUATION_DECISION_OPTIONS = [
  { value: "preselectionne", label: "Présélectionné" },
  { value: "non_selectionne", label: "Non sélectionné" },
  { value: "profil_valide", label: "Profil validé" },
  { value: "refus_candidat", label: "Refus candidat" },
] as const;

export const INTERVIEW_TYPE_OPTIONS = [
  { value: "entretien_cabinet", label: "Entretien cabinet" },
  { value: "entretien_client", label: "Entretien client" },
] as const;

export function pipelineStageLabel(stage: string) {
  return PIPELINE_STAGE_OPTIONS.find((option) => option.value === stage)?.label ?? stage;
}
