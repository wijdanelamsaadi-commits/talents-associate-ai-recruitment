type StarRatingProps = {
  value: number;
  onChange?: (value: number) => void;
  size?: "sm" | "lg";
  readOnly?: boolean;
};

export function StarRating({ value, onChange, size = "sm", readOnly = false }: StarRatingProps) {
  const starSize = size === "lg" ? "text-2xl" : "text-lg";

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => {
        const isActive = star <= value;
        if (readOnly || !onChange) {
          return (
            <span key={star} className={isActive ? "text-[#E8590C]" : "text-slate-300"} aria-hidden="true">
              ★
            </span>
          );
        }
        return (
          <button
            key={star}
            type="button"
            className={`${starSize} transition ${isActive ? "text-[#E8590C]" : "text-slate-300 hover:text-[#F97316]"}`}
            onClick={() => onChange(star)}
            aria-label={`${star} étoile${star > 1 ? "s" : ""}`}
          >
            ★
          </button>
        );
      })}
    </div>
  );
}
