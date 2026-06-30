type ListSearchProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label?: string;
};

export function ListSearch({ value, onChange, placeholder, label = "Recherche" }: ListSearchProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <label className="block">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <input
          className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-[#1D6EEA] focus:ring-2 focus:ring-[#1D6EEA]/20"
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          type="search"
          value={value}
        />
      </label>
    </section>
  );
}
