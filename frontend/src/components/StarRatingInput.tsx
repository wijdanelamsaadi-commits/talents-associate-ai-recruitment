import { StarRating } from "../components/StarRating";

type StarRatingInputProps = {
  label: string;
  value: number;
  onChange: (value: number) => void;
};

export function StarRatingInput({ label, value, onChange }: StarRatingInputProps) {
  return (
    <div>
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <div className="mt-2">
        <StarRating value={value} onChange={onChange} size="lg" />
      </div>
    </div>
  );
}
