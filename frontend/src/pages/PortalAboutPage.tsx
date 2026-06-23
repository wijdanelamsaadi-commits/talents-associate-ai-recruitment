import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type ValueCard = {
  title: string;
  text: string;
  icon: ReactNode;
};

const TargetIcon = (
  <svg fill="none" height="34" viewBox="0 0 24 24" width="34" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
    <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="1.8" />
    <circle cx="12" cy="12" r="1.6" fill="currentColor" />
    <path d="M12 3V1M21 12h2M12 21v2M3 12H1" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
  </svg>
);

const HandshakeIcon = (
  <svg fill="none" height="34" viewBox="0 0 24 24" width="34" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M3 8.5 7 6l3.2 2.4a2 2 0 0 0 2.4 0L16 6l5 2.5M3 8.5V15l3 2.5M21 8.5V15l-3 2.5"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
    <path
      d="m9 12 2.2 2.2a1.5 1.5 0 0 0 2.1 0L18 9.5M11 17l1.6 1.6a1.4 1.4 0 0 0 2 0M14 16l1.4 1.4a1.4 1.4 0 0 0 2 0"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

const ShieldIcon = (
  <svg fill="none" height="34" viewBox="0 0 24 24" width="34" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M12 3 5 6v5.5c0 4.3 3 7.4 7 9.5 4-2.1 7-5.2 7-9.5V6l-7-3Z"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
    <rect height="5" rx="1" stroke="currentColor" strokeWidth="1.8" width="6.5" x="8.75" y="11" />
    <path d="M10 11v-1.3a2 2 0 0 1 4 0V11" stroke="currentColor" strokeWidth="1.8" />
  </svg>
);

const SupportIcon = (
  <svg fill="none" height="34" viewBox="0 0 24 24" width="34" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 13v-1a8 8 0 0 1 16 0v1" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    <rect height="6" rx="1.6" stroke="currentColor" strokeWidth="1.8" width="3.5" x="3" y="12.5" />
    <rect height="6" rx="1.6" stroke="currentColor" strokeWidth="1.8" width="3.5" x="17.5" y="12.5" />
    <path d="M20 18.5a3 3 0 0 1-3 3h-3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
  </svg>
);

const valueCards: ValueCard[] = [
  {
    title: "Notre mission",
    text: "Faciliter la rencontre entre les talents et les entreprises grâce à une plateforme simple, efficace et humaine.",
    icon: TargetIcon,
  },
  {
    title: "Notre engagement",
    text: "Nous nous engageons à offrir une expérience transparente, sécurisée et équitable à tous les candidats.",
    icon: HandshakeIcon,
  },
  {
    title: "Vos données, notre priorité",
    text: "La sécurité et la confidentialité de vos données sont garanties. Nous ne partageons jamais vos informations sans votre accord.",
    icon: ShieldIcon,
  },
  {
    title: "Accompagnement",
    text: "Notre équipe RH est là pour vous accompagner à chaque étape de votre parcours professionnel.",
    icon: SupportIcon,
  },
];

export function PortalAboutPage() {
  return (
    <main className="bg-white">
      {/* SECTION 1 — Titre + intro */}
      <section className="mx-auto max-w-[1360px] px-6 pb-4 pt-16 text-center lg:px-12 lg:pt-20">
        <h1 className="text-4xl font-extrabold leading-tight text-[#061A33] sm:text-5xl lg:text-[52px]">
          À propos de Talents Associate
        </h1>
        <span className="mx-auto mt-6 block h-1 w-20 rounded-full bg-[#ff3d00]" />
        <p className="mx-auto mt-7 max-w-3xl text-lg leading-8 text-slate-600">
          Talents Associate est une plateforme de recrutement intelligente qui met en relation les talents avec les
          bonnes opportunités. Notre mission est de simplifier le recrutement tout en offrant une expérience fluide et
          humaine aux candidats.
        </p>
      </section>

      {/* SECTION 2 — 4 cartes valeurs */}
      <section className="mx-auto max-w-[1360px] px-6 py-12 lg:px-12 lg:py-16">
        <div className="grid gap-7 sm:grid-cols-2 lg:grid-cols-4">
          {valueCards.map((card) => (
            <article
              className="group flex flex-col items-center rounded-[20px] border border-slate-100 bg-white px-7 py-9 text-center shadow-lg shadow-slate-900/5 transition duration-300 hover:-translate-y-1.5 hover:shadow-xl hover:shadow-orange-500/10"
              key={card.title}
            >
              <span className="flex h-[88px] w-[88px] items-center justify-center rounded-full bg-[#ff3d00]/10 text-[#ff3d00] transition duration-300 group-hover:bg-[#ff3d00]/15">
                {card.icon}
              </span>
              <h2 className="mt-6 text-lg font-extrabold text-[#061A33]">{card.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{card.text}</p>
            </article>
          ))}
        </div>
      </section>

      {/* SECTION 3 — CTA */}
      <section className="mx-auto max-w-[1360px] px-6 pb-20 lg:px-12">
        <div className="grid items-center gap-8 overflow-hidden rounded-[24px] bg-[#FFF7F2] px-7 py-9 md:grid-cols-[auto_1fr_auto] md:px-12 md:py-10">
          <div className="flex justify-center md:justify-start">
            <img
              alt="Candidate travaillant sur son ordinateur"
              className="h-32 w-32 rounded-2xl object-cover md:h-36 md:w-36"
              src="/portal-hero-woman.png"
            />
          </div>

          <div className="text-center md:text-left">
            <h2 className="text-2xl font-extrabold leading-snug text-[#061A33] sm:text-[28px]">
              Prêt à trouver l'opportunité qui vous correspond ?
            </h2>
            <p className="mt-3 max-w-xl text-base leading-7 text-slate-600">
              Découvrez des offres adaptées à vos compétences et faites le prochain pas dans votre carrière.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row md:flex-col lg:flex-row">
            <Link
              className="inline-flex min-h-[52px] items-center justify-center gap-2 rounded-lg bg-[#ff3d00] px-7 text-sm font-bold text-white shadow-lg shadow-orange-500/20 transition hover:bg-[#e63600]"
              to="/portal/jobs"
            >
              Voir les offres
              <span aria-hidden="true">→</span>
            </Link>
            <Link
              className="inline-flex min-h-[52px] items-center justify-center gap-2 rounded-lg border border-[#ff3d00] bg-white px-7 text-sm font-bold text-[#ff3d00] transition hover:bg-[#ff3d00]/5"
              to="/portal/profile"
            >
              <span aria-hidden="true">⌑</span>
              Compléter mon profil
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
