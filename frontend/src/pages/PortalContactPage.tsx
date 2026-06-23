import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type ContactCard = {
  title: string;
  value: string;
  href: string;
  external?: boolean;
  icon: ReactNode;
  iconWrapClass: string;
  iconColorClass: string;
};

const PhoneIcon = (
  <svg fill="none" height="26" viewBox="0 0 24 24" width="26" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M6.5 3.5h2.2l1.3 4-1.8 1.2a12 12 0 0 0 5.1 5.1l1.2-1.8 4 1.3v2.2a2 2 0 0 1-2.2 2A16 16 0 0 1 4.5 5.7a2 2 0 0 1 2-2.2Z"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
  </svg>
);

const WhatsAppIcon = (
  <svg fill="none" height="26" viewBox="0 0 24 24" width="26" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M4 20l1.3-3.9A7.5 7.5 0 1 1 8 19l-4 1Z"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
    <path
      d="M9.2 8.6c.2-.5.4-.5.7-.5h.5c.2 0 .4 0 .6.5l.6 1.4c0 .2 0 .3-.1.5l-.5.6c-.1.1-.2.3 0 .6.3.5.7 1 1.2 1.3.5.4 1 .5 1.2.6.2 0 .4 0 .5-.1l.6-.7c.2-.2.3-.2.5-.1l1.4.6c.2.1.4.2.4.3 0 .4-.1 1.1-.5 1.4-.4.3-1.2.7-1.9.5-1.3-.3-2.6-.9-3.8-2.2-1-1.1-1.6-2.3-1.8-3 -.1-.6.1-1.2.6-1.9Z"
      fill="currentColor"
    />
  </svg>
);

const MailIcon = (
  <svg fill="none" height="26" viewBox="0 0 24 24" width="26" xmlns="http://www.w3.org/2000/svg">
    <rect height="13" rx="2" stroke="currentColor" strokeWidth="1.8" width="18" x="3" y="5.5" />
    <path d="m4 7 8 6 8-6" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
  </svg>
);

const PinIcon = (
  <svg fill="none" height="26" viewBox="0 0 24 24" width="26" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M12 21s7-5.3 7-11a7 7 0 1 0-14 0c0 5.7 7 11 7 11Z"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeWidth="1.8"
    />
    <circle cx="12" cy="10" fill="currentColor" r="2.4" />
  </svg>
);

const ClockIcon = (
  <svg fill="none" height="30" viewBox="0 0 24 24" width="30" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
    <path d="M12 7.5V12l3 2" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
  </svg>
);

const MAPS_URL =
  "https://www.google.com/maps/search/?api=1&query=" +
  encodeURIComponent("Avenue Lalla Yacout Résidence Galis App 17 Casablanca");

const contactCards: ContactCard[] = [
  {
    title: "Téléphone",
    value: "+212 (0) 6 88 12 88 13",
    href: "tel:+212688128813",
    icon: PhoneIcon,
    iconWrapClass: "bg-[#ff3d00]/10",
    iconColorClass: "text-[#ff3d00]",
  },
  {
    title: "WhatsApp",
    value: "+212 (0) 6 88 12 88 13",
    href: "https://wa.me/212688128813",
    external: true,
    icon: WhatsAppIcon,
    iconWrapClass: "bg-[#25D366]/10",
    iconColorClass: "text-[#25D366]",
  },
  {
    title: "Email",
    value: "Contact@talentsag.ma",
    href: "mailto:Contact@talentsag.ma",
    icon: MailIcon,
    iconWrapClass: "bg-[#ff3d00]/10",
    iconColorClass: "text-[#ff3d00]",
  },
  {
    title: "Adresse",
    value: "Avenue Lalla Yacout Résidence Galis App 17 Casablanca",
    href: MAPS_URL,
    external: true,
    icon: PinIcon,
    iconWrapClass: "bg-[#ff3d00]/10",
    iconColorClass: "text-[#ff3d00]",
  },
];

export function PortalContactPage() {
  return (
    <main className="bg-white">
      {/* SECTION 1 — Hero */}
      <section className="mx-auto max-w-[1360px] px-6 pb-4 pt-16 text-center lg:px-12 lg:pt-20">
        <h1 className="text-4xl font-extrabold leading-tight text-[#061A33] sm:text-5xl lg:text-[52px]">
          Contactez-nous
        </h1>
        <span className="mx-auto mt-6 block h-1 w-20 rounded-full bg-[#ff3d00]" />
        <p className="mx-auto mt-7 max-w-2xl text-lg leading-8 text-slate-600">
          Une question, un besoin d'information ou un accompagnement ?
          <br className="hidden sm:block" /> Notre équipe est là pour vous aider.
        </p>
      </section>

      {/* SECTION 2 — Cartes coordonnées */}
      <section className="mx-auto max-w-3xl px-6 py-10 lg:py-12">
        <div className="grid gap-5">
          {contactCards.map((card) => (
            <a
              className="group flex cursor-pointer items-center gap-5 rounded-[20px] border border-slate-100 bg-white px-6 py-5 shadow-lg shadow-slate-900/5 transition duration-300 hover:-translate-y-1 hover:border-[#ff3d00] hover:shadow-xl hover:shadow-orange-500/10 sm:gap-6 sm:px-8 sm:py-6"
              href={card.href}
              key={card.title}
              rel={card.external ? "noreferrer noopener" : undefined}
              target={card.external ? "_blank" : undefined}
            >
              <span
                className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full ${card.iconWrapClass} ${card.iconColorClass}`}
              >
                {card.icon}
              </span>
              <span className="h-12 w-px shrink-0 bg-slate-200" aria-hidden="true" />
              <span className="min-w-0">
                <span className="block text-base font-extrabold text-[#061A33]">{card.title}</span>
                <span className="mt-1 block break-words text-sm text-slate-600 sm:text-base">{card.value}</span>
              </span>
            </a>
          ))}
        </div>
      </section>

      {/* SECTION 3 — Disponibilité */}
      <section className="mx-auto max-w-3xl px-6 pb-20">
        <div className="flex flex-col items-center gap-4 rounded-[20px] bg-[#FFF7F2] px-8 py-10 text-center">
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-[#ff3d00]/10 text-[#ff3d00]">
            {ClockIcon}
          </span>
          <h2 className="text-xl font-extrabold text-[#061A33]">Disponibles pour vous</h2>
          <p className="max-w-md text-sm leading-7 text-slate-600 sm:text-base">
            Nous répondons à vos demandes du lundi au vendredi, de 9h00 à 18h00.
          </p>
          <Link
            className="mt-1 text-sm font-bold text-[#ff3d00] transition hover:text-[#e63600]"
            to="/portal/jobs"
          >
            Découvrir nos offres →
          </Link>
        </div>
      </section>
    </main>
  );
}
