import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type JourneyStep = {
  number: string;
  title: string;
  text: string;
  icon: ReactNode;
};

type Client = {
  name: string;
  slug: string;
};

const UserIcon = (
  <svg fill="none" height="30" viewBox="0 0 24 24" width="30" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8" />
    <path d="M4.5 20a7.5 7.5 0 0 1 15 0" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
  </svg>
);

const DocumentIcon = (
  <svg fill="none" height="30" viewBox="0 0 24 24" width="30" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.8" />
    <path d="M14 3v5h5M9 13h6M9 16.5h4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
  </svg>
);

const BellIcon = (
  <svg fill="none" height="30" viewBox="0 0 24 24" width="30" xmlns="http://www.w3.org/2000/svg">
    <path d="M6 9a6 6 0 0 1 12 0c0 4 1.2 5.5 2 6.5H4c.8-1 2-2.5 2-6.5Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.8" />
    <path d="M10 19a2 2 0 0 0 4 0" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
  </svg>
);

const journeySteps: JourneyStep[] = [
  {
    number: "01",
    title: "Créez votre compte",
    text: "Inscrivez-vous et complétez votre profil candidat en quelques minutes.",
    icon: UserIcon,
  },
  {
    number: "02",
    title: "Postulez aux offres",
    text: "Parcourez les opportunités disponibles et envoyez vos candidatures facilement.",
    icon: DocumentIcon,
  },
  {
    number: "03",
    title: "Suivez vos candidatures",
    text: "Consultez l'évolution de vos candidatures et recevez les notifications importantes.",
    icon: BellIcon,
  },
];

const clients: Client[] = [
  { name: "Bank Of Africa", slug: "bank-of-africa" },
  { name: "Crédit du Maroc", slug: "credit-du-maroc" },
  { name: "Orange", slug: "orange" },
  { name: "ONCF", slug: "oncf" },
  { name: "RATP Dev", slug: "ratp-dev" },
  { name: "Auto Nejma", slug: "auto-nejma" },
  { name: "Teka", slug: "teka" },
  { name: "Toyota", slug: "toyota" },
  { name: "Société Générale", slug: "societe-generale" },
  { name: "CAT Assurance", slug: "cat-assurance" },
  { name: "Wafa Assurance", slug: "wafa-assurance" },
  { name: "Allianz", slug: "allianz" },
  { name: "AXA", slug: "axa" },
  { name: "RMA", slug: "rma" },
  { name: "Aïnsi Maroc Group", slug: "ainsi-maroc-group" },
  { name: "Gestine Services", slug: "gestine-services" },
  { name: "VCR Sodalmu", slug: "vcr-sodalmu" },
  { name: "Bel", slug: "bel" },
  { name: "Oliveri", slug: "oliveri" },
  { name: "Ecomab", slug: "ecomab" },
  { name: "Hakam Frères", slug: "hakam-freres" },
  { name: "Auto Hall", slug: "auto-hall" },
  { name: "AGMA", slug: "agma" },
];

function ClientLogo({ client }: { client: Client }) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="flex h-28 items-center justify-center rounded-[16px] border border-slate-100 bg-white px-5 shadow-md shadow-slate-900/5">
      {failed ? (
        <span className="text-center text-sm font-bold text-[#061A33]">{client.name}</span>
      ) : (
        <img
          alt={client.name}
          className="max-h-14 max-w-full object-contain"
          loading="lazy"
          onError={() => setFailed(true)}
          src={`/images/clients/${client.slug}.png`}
        />
      )}
    </div>
  );
}

function ReferencesCarousel() {
  const [perView, setPerView] = useState(5);
  const [page, setPage] = useState(0);

  useEffect(() => {
    const computePerView = () => {
      const width = window.innerWidth;
      if (width < 640) return 2;
      if (width < 1024) return 3;
      return 5;
    };
    const handleResize = () => setPerView(computePerView());
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const pageCount = Math.max(1, Math.ceil(clients.length / perView));

  useEffect(() => {
    if (page > pageCount - 1) setPage(0);
  }, [page, pageCount]);

  useEffect(() => {
    if (pageCount <= 1) return;
    const timer = window.setInterval(() => {
      setPage((current) => (current + 1) % pageCount);
    }, 3000);
    return () => window.clearInterval(timer);
  }, [pageCount]);

  const pages = Array.from({ length: pageCount }, (_, pageIndex) =>
    clients.slice(pageIndex * perView, pageIndex * perView + perView),
  );

  return (
    <div>
      <div className="overflow-hidden">
        <div
          className="flex transition-transform duration-700 ease-in-out"
          style={{ transform: `translateX(-${page * 100}%)` }}
        >
          {pages.map((group, groupIndex) => (
            <div
              className="grid w-full shrink-0 grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5"
              key={groupIndex}
            >
              {group.map((client) => (
                <ClientLogo client={client} key={client.slug} />
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10 flex items-center justify-center gap-2.5">
        {Array.from({ length: pageCount }, (_, dotIndex) => (
          <button
            aria-label={`Aller au groupe ${dotIndex + 1}`}
            className={`h-2.5 rounded-full transition-all duration-300 ${
              dotIndex === page ? "w-7 bg-[#ff5a1f]" : "w-2.5 bg-slate-300 hover:bg-slate-400"
            }`}
            key={dotIndex}
            onClick={() => setPage(dotIndex)}
            type="button"
          />
        ))}
      </div>
    </div>
  );
}

export function PortalHomePage() {
  return (
    <main className="bg-white">
      {/* SECTION 1 — Hero premium (image + overlay uniquement) */}
      <section
        className="relative min-h-[70vh] overflow-hidden bg-[#061A33] bg-cover bg-center lg:min-h-[80vh]"
        style={{ backgroundImage: "url('/images/portal-hero-corporate.jpg')" }}
      >
        <div className="absolute inset-0" style={{ backgroundColor: "rgba(6, 26, 51, 0.65)" }} />
      </section>

      {/* SECTION 2 — Qui sommes-nous */}
      <section className="mx-auto max-w-[1360px] px-6 py-16 lg:px-12 lg:py-24">
        <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16">
          <div
            aria-label="Entretien professionnel chez Talents Associate"
            className="min-h-[280px] w-full rounded-[1.5rem] bg-slate-100 bg-cover bg-center shadow-2xl shadow-slate-900/15 lg:min-h-[360px]"
            role="img"
            style={{ backgroundImage: "url('/images/portal-about-interview.jpg')" }}
          />
          <div>
            <h2 className="text-3xl font-extrabold text-[#061A33] sm:text-4xl">Qui sommes-nous ?</h2>
            <span className="mt-5 block h-1 w-20 rounded-full bg-[#ff5a1f]" />
            <p className="mt-7 text-lg leading-8 text-slate-600">
              Talents Associate accompagne les candidats dans leur parcours professionnel en facilitant l'accès à des
              opportunités adaptées à leurs compétences, leurs ambitions et leur profil.
            </p>
          </div>
        </div>
      </section>

      {/* SECTION 3 — Votre parcours candidat */}
      <section className="bg-[#f7f9fc]">
        <div className="mx-auto max-w-[1360px] px-6 py-16 lg:px-12 lg:py-24">
          <div className="text-center">
            <span className="mx-auto block h-1 w-12 rounded-full bg-[#ff5a1f]" />
            <h2 className="mt-6 text-3xl font-extrabold text-[#061A33] sm:text-4xl lg:text-[44px]">
              Votre parcours candidat
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-600">
              Une expérience simple et efficace pour vous accompagner à chaque étape de votre recherche d'emploi.
            </p>
          </div>

          <div className="mt-14 grid gap-8 md:grid-cols-3">
            {journeySteps.map((step) => (
              <article
                className="flex flex-col items-center rounded-[20px] bg-white px-8 py-10 text-center shadow-lg shadow-slate-900/5 transition duration-300 hover:-translate-y-1.5 hover:shadow-xl hover:shadow-orange-500/10"
                key={step.number}
              >
                <span className="flex h-20 w-20 items-center justify-center rounded-full bg-[#ff5a1f]/10 text-[#ff5a1f]">
                  {step.icon}
                </span>
                <span className="mt-6 text-sm font-extrabold tracking-wider text-[#ff5a1f]">{step.number}</span>
                <h3 className="mt-2 text-xl font-extrabold text-[#061A33]">{step.title}</h3>
                <span className="mt-4 block h-0.5 w-10 bg-[#ff5a1f]/40" />
                <p className="mt-5 text-sm leading-7 text-slate-600">{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 4 — Nos références */}
      <section className="bg-white">
        <div className="mx-auto max-w-[1360px] px-6 py-16 lg:px-12 lg:py-24">
          <div className="text-center">
            <span className="mx-auto block h-1 w-12 rounded-full bg-[#ff5a1f]" />
            <h2 className="mt-6 text-3xl font-extrabold text-[#061A33] sm:text-4xl lg:text-[44px]">Nos références</h2>
            <p className="mx-auto mt-5 max-w-2xl text-lg leading-8 text-slate-600">
              Ils nous font confiance pour les accompagner dans leurs recrutements et leur développement.
            </p>
          </div>

          <div className="mt-14">
            <ReferencesCarousel />
          </div>
        </div>
      </section>
    </main>
  );
}
