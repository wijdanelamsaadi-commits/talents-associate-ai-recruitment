import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const baseProps = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  strokeWidth: 2.2,
  viewBox: "0 0 24 24",
};

export function FileCVIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M7 3h7l5 5v13H7z" />
      <path d="M14 3v5h5" />
      <path d="M9 15c0-1.2.8-2 2-2" />
      <path d="M13 13l1.4 4 1.6-4" />
      <path d="M11 17c-1.2 0-2-.8-2-2" />
    </svg>
  );
}

export function LinkedinIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M7 10v7" />
      <path d="M7 7.2v.1" />
      <path d="M11 17v-4.2a2.8 2.8 0 0 1 5.6 0V17" />
      <rect x="3.5" y="3.5" width="17" height="17" rx="3" />
    </svg>
  );
}

export function UsersIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
      <path d="M2.8 20a6.2 6.2 0 0 1 12.4 0" />
      <path d="M17 11.5a2.6 2.6 0 1 0-1.5-4.7" />
      <path d="M17.4 14.2A5.2 5.2 0 0 1 21.2 20" />
    </svg>
  );
}

export function BriefcaseIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M9 6V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1" />
      <rect x="3" y="6" width="18" height="14" rx="2" />
      <path d="M3 11h18" />
      <path d="M9 11v2" />
      <path d="M15 11v2" />
    </svg>
  );
}

export function TargetIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="12" cy="12" r="1" />
    </svg>
  );
}

export function StarIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6-5.4-2.9-5.4 2.9 1-6-4.4-4.3 6.1-.9z" />
    </svg>
  );
}

export function UserPlusIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
      <path d="M3 20a6 6 0 0 1 12 0" />
      <path d="M18 8v6" />
      <path d="M15 11h6" />
    </svg>
  );
}

export function ChartIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <path d="M5 20V9h4v11" />
      <path d="M10 20V4h4v16" />
      <path d="M15 20v-7h4v7" />
    </svg>
  );
}

export function MailIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" />
    </svg>
  );
}

export function LockIcon(props: IconProps) {
  return (
    <svg {...baseProps} {...props}>
      <rect x="5" y="10" width="14" height="10" rx="2" />
      <path d="M8 10V8a4 4 0 0 1 8 0v2" />
      <path d="M12 14v2" />
    </svg>
  );
}
