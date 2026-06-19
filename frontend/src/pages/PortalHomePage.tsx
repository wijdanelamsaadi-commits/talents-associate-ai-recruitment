import { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

const opportunities = [
  "Sélectionnez le poste visé",
  "Responsable Ressources Humaines",
  "Talent Acquisition Specialist",
  "Consultant RH",
  "Chargé de recrutement",
  "Candidature spontanée",
];

const heroStats = [
  ["100% sécurisé", "Vos données protégées", "🛡"],
  ["Réponse rapide", "Sous 7 jours ouvrés", "⚡"],
  ["+2,500 talents", "Nous ont déjà rejoints", "♚"],
];

const reasons = [
  ["Analyse IA avancée", "Votre CV est analysé par notre intelligence artificielle pour identifier vos compétences et votre potentiel.", "✣"],
  ["Matching précis", "Recevez des recommandations d'offres qui correspondent le mieux à votre profil et à vos ambitions.", "◎"],
  ["Suivi en temps réel", "Suivez l'avancement de vos candidatures en temps réel depuis votre espace personnel.", "♢"],
  ["Confidentialité garantie", "Vos informations sont protégées et partagées uniquement avec les entreprises concernées.", "◆"],
];

export function PortalHomePage() {
  const navigate = useNavigate();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    navigate("/portal/jobs");
  };

  return (
    <main className="bg-white">
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-white to-[#fff6f1]">
        <div className="mx-auto grid max-w-[1360px] items-center gap-12 px-6 pb-7 pt-10 lg:grid-cols-[0.95fr_1.05fr] lg:px-12 lg:pb-10 lg:pt-14">
          <div className="relative z-10">
            <span className="inline-flex items-center rounded-full bg-[#ff3d00]/10 px-4 py-2 text-sm font-semibold text-[#ff3d00]">
              <span className="mr-2 text-base">★</span>
              Votre carrière, notre mission
            </span>
            <h1 className="mt-6 max-w-[660px] text-4xl font-extrabold leading-[1.08] text-[#061A33] sm:text-5xl lg:text-[50px] xl:text-[56px]">
              Trouvez l'opportunité
              <span className="block text-[#ff3d00]">qui vous correspond</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
              Déposez votre CV, complétez votre profil et suivez vos candidatures depuis votre espace candidat.
            </p>
            <div className="mt-8 flex flex-wrap gap-5">
              <Link
                className="inline-flex min-h-14 items-center justify-center rounded-lg bg-[#ff3d00] px-8 text-sm font-bold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]"
                to="/portal/jobs"
              >
                Voir les offres
              </Link>
              <Link
                className="inline-flex min-h-14 items-center justify-center rounded-lg border border-[#ff3d00] bg-white px-8 text-sm font-bold text-[#ff3d00] transition hover:bg-[#ff3d00]/5"
                to="/portal/profile"
              >
                Déposer mon CV
              </Link>
            </div>

            <div className="mt-10 grid max-w-2xl gap-4 sm:grid-cols-3">
              {heroStats.map(([title, detail, icon], index) => (
                <div className="flex items-center gap-3 sm:border-r sm:border-orange-100 sm:pr-4 last:border-r-0" key={title}>
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#ff3d00]/10 text-lg text-[#ff3d00]">
                    {icon}
                  </span>
                  <span>
                    <span className="block text-sm font-extrabold text-[#061A33]">{title}</span>
                    <span className="mt-1 block text-xs text-slate-500">{detail}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="relative min-h-[360px] lg:min-h-[460px]">
            <div className="absolute right-0 top-12 hidden h-[430px] w-[430px] rounded-full border-r-4 border-[#ff3d00] lg:block" />
            <div className="absolute right-0 top-16 h-80 w-40 rounded-[2rem] bg-[#ff3d00]/15" />
            <div className="absolute -left-4 top-24 hidden grid-cols-6 gap-3 lg:grid">
              {Array.from({ length: 30 }).map((_, index) => (
                <span className="h-1.5 w-1.5 rounded-full bg-[#ff3d00]" key={index} />
              ))}
            </div>
            <div className="absolute bottom-0 right-0 h-28 w-64 rounded-tl-[4rem] bg-[#ff3d00]/15" />
            <img
              alt="Candidate professionnelle travaillant sur ordinateur"
              className="relative z-10 h-[360px] w-full rounded-[1.5rem] object-cover shadow-2xl shadow-slate-900/15 lg:h-[460px]"
              src="/portal-hero-woman.png"
            />
          </div>
        </div>
      </section>

      <section className="relative z-20 mx-auto -mt-2 max-w-[1180px] px-6 pb-8">
        <form
          className="rounded-[1.75rem] border border-slate-100 bg-white p-6 shadow-2xl shadow-slate-900/10 sm:p-8 lg:p-10"
          onSubmit={handleSubmit}
        >
          <div className="mb-7">
            <span className="inline-flex rounded-full bg-[#ff3d00]/10 px-4 py-2 text-sm font-semibold text-[#ff3d00]">
              Nous recrutons
            </span>
            <h2 className="mt-4 text-3xl font-extrabold text-[#061A33]">Formulaire de recrutement</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Nous recherchons des talents qualifiés avec des opportunités professionnelles en CDI, CDD, intérim ou freelance.
              Déposez votre candidature et saisissez de nouvelles opportunités adaptées à votre profil.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#061A33]">Opportunité *</span>
              <select className="mt-2 h-12 w-full rounded-lg border border-slate-200 bg-white px-4 text-sm text-slate-600 outline-none transition focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10">
                {opportunities.map((opportunity) => (
                  <option key={opportunity}>{opportunity}</option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#061A33]">Nom *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="Votre nom" required />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#061A33]">Prénom *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="Votre prénom" required />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#061A33]">Email *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="exemple@email.com" required type="email" />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#061A33]">Téléphone *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="06 12 34 56 78" required />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#061A33]">Ville *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="Votre ville" required />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#061A33]">Message de candidature</span>
              <textarea className="mt-2 min-h-28 w-full rounded-lg border border-slate-200 px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#ff3d00] focus:ring-4 focus:ring-[#ff3d00]/10" placeholder="Présentez-vous et expliquez vos motivations..." />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#061A33]">CV *</span>
              <span className="mt-2 flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[#ff3d00] bg-[#ff3d00]/[0.03] px-6 py-7 text-center transition hover:bg-[#ff3d00]/[0.06]">
                <span className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#ff3d00] text-xl font-bold text-white">⇧</span>
                <span className="mt-4 text-sm font-bold text-[#061A33]">Glissez-déposez votre CV ou cliquez pour parcourir</span>
                <span className="mt-2 text-sm text-slate-500">PDF, DOC, DOCX (max 10MB)</span>
                <input accept=".pdf,.doc,.docx" className="sr-only" required type="file" />
              </span>
            </label>
          </div>

          <button
            className="mt-6 flex h-12 w-full items-center justify-center rounded-lg bg-[#ff3d00] text-sm font-bold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]"
            type="submit"
          >
            Envoyer ma candidature
          </button>
          <p className="mt-4 text-center text-sm text-slate-500">Vos données sont sécurisées et confidentielles</p>
        </form>
      </section>

      <section className="mx-auto max-w-[1360px] px-6 pb-10">
        <div className="rounded-[1.5rem] bg-[#fff6f1] px-8 py-8 shadow-sm">
          <h2 className="text-center text-2xl font-extrabold text-[#061A33]">Pourquoi candidater chez Talents Associate ?</h2>
          <div className="mx-auto mt-3 h-0.5 w-14 bg-[#ff3d00]" />
          <div className="mt-8 grid gap-6 md:grid-cols-4">
            {reasons.map(([title, description, icon], index) => (
              <article className="flex gap-4 md:border-r md:border-orange-200 md:pr-6 last:border-r-0" key={title}>
                <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[#ff3d00]/10 text-2xl text-[#ff3d00]">
                  {icon}
                </span>
                <div>
                  <h3 className="text-sm font-extrabold text-[#061A33]">{title}</h3>
                  <p className="mt-3 text-xs leading-6 text-slate-600">{description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
