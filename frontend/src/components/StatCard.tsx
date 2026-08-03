type StatCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm ring-1 ring-transparent transition hover:border-orange-100 hover:ring-orange-100">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-[#24303F]">{value}</p>
      <p className="mt-2 border-l-2 border-[#EE6C2F] pl-3 text-sm text-slate-600">{detail}</p>
    </article>
  );
}
