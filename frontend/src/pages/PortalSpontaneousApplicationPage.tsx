import { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

const opportunities = [
  "Sélectionnez le poste visé",
  "Responsable Ressources Humaines",
  "Talent Acquisition Specialist",
  "Consultant RH",
  "Chargé de recrutement",
  "Candidature spontanée",
];

export function PortalSpontaneousApplicationPage() {
  const navigate = useNavigate();

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    navigate("/portal/jobs");
  };

  return (
    <main className="bg-white">
      {/* Hero simple */}
      <section className="mx-auto max-w-[1360px] px-6 pb-2 pt-16 text-center lg:px-12 lg:pt-20">
        <span className="inline-flex rounded-full bg-[#EE6C2F]/10 px-4 py-2 text-sm font-semibold text-[#EE6C2F]">
          Nous recrutons
        </span>
        <h1 className="mt-5 text-4xl font-extrabold leading-tight text-[#24303F] sm:text-5xl lg:text-[52px]">
          Candidature spontanée
        </h1>
        <span className="mx-auto mt-6 block h-1 w-20 rounded-full bg-[#EE6C2F]" />
        <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-slate-600">
          Vous ne trouvez pas l'offre idéale ? Déposez votre candidature spontanée et saisissez de nouvelles
          opportunités adaptées à votre profil.
        </p>
      </section>

      {/* Formulaire de candidature */}
      <section className="relative z-20 mx-auto mt-8 max-w-[1180px] px-6 pb-20">
        <form
          className="rounded-[1.75rem] border border-slate-100 bg-white p-6 shadow-2xl shadow-slate-900/10 sm:p-8 lg:p-10"
          onSubmit={handleSubmit}
        >
          <div className="mb-7">
            <span className="inline-flex rounded-full bg-[#EE6C2F]/10 px-4 py-2 text-sm font-semibold text-[#EE6C2F]">
              Nous recrutons
            </span>
            <h2 className="mt-4 text-3xl font-extrabold text-[#24303F]">Formulaire de recrutement</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Nous recherchons des talents qualifiés avec des opportunités professionnelles en CDI, CDD, intérim ou freelance.
              Déposez votre candidature et saisissez de nouvelles opportunités adaptées à votre profil.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#24303F]">Opportunité *</span>
              <select className="mt-2 h-12 w-full rounded-lg border border-slate-200 bg-white px-4 text-sm text-slate-600 outline-none transition focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10">
                {opportunities.map((opportunity) => (
                  <option key={opportunity}>{opportunity}</option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Nom *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="Votre nom" required />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Prénom *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="Votre prénom" required />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Email *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="exemple@email.com" required type="email" />
            </label>

            <label className="block">
              <span className="text-sm font-bold text-[#24303F]">Téléphone *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="06 12 34 56 78" required />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#24303F]">Ville *</span>
              <input className="mt-2 h-12 w-full rounded-lg border border-slate-200 px-4 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="Votre ville" required />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#24303F]">Message de candidature</span>
              <textarea className="mt-2 min-h-28 w-full rounded-lg border border-slate-200 px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-[#EE6C2F] focus:ring-4 focus:ring-[#EE6C2F]/10" placeholder="Présentez-vous et expliquez vos motivations..." />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-bold text-[#24303F]">CV *</span>
              <span className="mt-2 flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[#EE6C2F] bg-[#EE6C2F]/[0.03] px-6 py-7 text-center transition hover:bg-[#EE6C2F]/[0.06]">
                <span className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#EE6C2F] text-xl font-bold text-white">⇧</span>
                <span className="mt-4 text-sm font-bold text-[#24303F]">Glissez-déposez votre CV ou cliquez pour parcourir</span>
                <span className="mt-2 text-sm text-slate-500">PDF, DOC, DOCX (max 10MB)</span>
                <input accept=".pdf,.doc,.docx" className="sr-only" required type="file" />
              </span>
            </label>
          </div>

          <button
            className="mt-6 flex h-12 w-full items-center justify-center rounded-lg bg-[#EE6C2F] text-sm font-bold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#D9551B]"
            type="submit"
          >
            Envoyer ma candidature
          </button>
          <p className="mt-4 text-center text-sm text-slate-500">Vos données sont sécurisées et confidentielles</p>
        </form>
      </section>
    </main>
  );
}
