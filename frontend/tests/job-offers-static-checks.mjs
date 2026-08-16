import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const jobOffersPage = readFileSync(resolve(root, "src/pages/JobOffersPage.tsx"), "utf8");
const matchingPage = readFileSync(resolve(root, "src/pages/MatchingPage.tsx"), "utf8");
const referencesService = readFileSync(resolve(root, "src/services/references.ts"), "utf8");

const checks = {
  "Poste utilise une liste explicite": jobOffersPage.includes("<select") && jobOffersPage.includes("Sélectionnez un poste"),
  "Poste propose Autre": jobOffersPage.includes('<option value={OTHER_OPTION_VALUE}>Autre</option>'),
  "Autre affiche le champ Précisez le poste": jobOffersPage.includes('placeholder="Précisez le poste"'),
  "Autre est obligatoire": jobOffersPage.includes('placeholder="Précisez le poste"') && jobOffersPage.includes("required"),
  "Le mot Autre n'est pas envoyé comme titre": jobOffersPage.includes('setFormState((current) => ({ ...current, [field]: isCustom ? "" : value }))'),
  "Offres recharge les postes depuis la référence backend": jobOffersPage.includes("getJobReferenceTitles()"),
  "Matching utilise la même référence backend": matchingPage.includes("getJobReferenceTitles()"),
  "Service référence utilise /api/references/job-titles": referencesService.includes('"/api/references/job-titles"'),
  "Aucune limite de 80 postes": !jobOffersPage.includes(".slice(0, 80)") && !matchingPage.includes(".slice(0, 80)") && !referencesService.includes(".slice(0, 80)"),
  "buildShareUrl ajoute job_id": jobOffersPage.includes('url.searchParams.set("job_id", job.id)'),
  "LinkedIn encode buildShareUrl": jobOffersPage.includes("https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(buildShareUrl(sharingJob))}"),
};

let failed = false;
for (const [label, passed] of Object.entries(checks)) {
  console.log(`${passed ? "[OK]" : "[ERREUR]"} ${label}`);
  failed ||= !passed;
}

if (failed) {
  process.exit(1);
}
