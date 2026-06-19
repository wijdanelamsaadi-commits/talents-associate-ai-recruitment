import { Link } from "react-router-dom";

export function PortalHomePage() {
  return (
    <main>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:py-20">
          <div>
            <p className="text-sm font-semibold uppercase text-[#E8590C]">Opportunités de carrière</p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight text-[#0B1F3A] sm:text-5xl">
              Espace candidat Talents Associate.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
              Depuis le site Talents Associate, créez ou complétez votre profil, déposez votre CV, consultez les offres
              disponibles et suivez l'avancement de vos candidatures.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="rounded-lg bg-[#E8590C] px-5 py-3 text-sm font-semibold text-white hover:bg-[#c94b08]" to="/portal/register">
                Créer un compte
              </Link>
              <Link
                className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
                to="/portal/login"
              >
                Se connecter
              </Link>
              <Link
                className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:border-[#E8590C] hover:text-[#E8590C]"
                to="/portal/jobs"
              >
                Voir les offres
              </Link>
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-6">
            <h2 className="text-lg font-semibold text-[#0B1F3A]">Parcours candidat</h2>
            <div className="mt-5 space-y-4">
              {[
                ["1", "Créer un profil", "Renseignez les informations utiles au recrutement."],
                ["2", "Ajouter votre CV", "Déposez un fichier PDF ou DOCX et gardez-le à jour."],
                ["3", "Postuler et suivre", "Postulez aux offres et suivez l'avancement de vos candidatures."],
              ].map(([step, title, description]) => (
                <div className="flex gap-3" key={step}>
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#E8590C] text-sm font-bold text-white">
                    {step}
                  </span>
                  <div>
                    <p className="font-semibold text-[#0B1F3A]">{title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-4 py-10 sm:px-6 md:grid-cols-3">
        {[
          ["Profil candidat", "Vos informations et votre CV restent disponibles pour les opportunités futures."],
          ["Score de matching", "Votre CV est analysé et comparé aux critères des offres ouvertes."],
          ["Mes candidatures", "Consultez vos candidatures depuis votre espace candidat."],
        ].map(([title, description]) => (
          <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm" key={title}>
            <h3 className="text-base font-semibold text-[#0B1F3A]">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
