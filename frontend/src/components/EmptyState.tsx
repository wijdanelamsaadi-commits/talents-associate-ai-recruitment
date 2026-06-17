type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white px-6 py-10 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-[#1D6EEA]/10 text-lg font-bold text-[#1D6EEA]">
        +
      </div>
      <h2 className="mt-4 text-lg font-semibold text-[#0B1F3A]">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">{description}</p>
      {actionLabel ? (
        <button
          className="mt-5 rounded-lg bg-[#1D6EEA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#165AC0]"
          onClick={onAction}
          type="button"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
