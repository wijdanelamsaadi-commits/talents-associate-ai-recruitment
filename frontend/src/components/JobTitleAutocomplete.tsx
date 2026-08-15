import { ChangeEvent, FocusEvent, useId, useMemo, useRef, useState } from "react";

type JobTitleAutocompleteProps = {
  label?: string;
  options: readonly string[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
};

const MAX_VISIBLE_OPTIONS = 80;

export function JobTitleAutocomplete({
  label,
  options,
  value,
  onChange,
  placeholder = "Rechercher un poste",
  required = false,
  disabled = false,
}: JobTitleAutocompleteProps) {
  const listId = useId();
  const blurTimeoutRef = useRef<number | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const filteredOptions = useMemo(() => {
    const normalizedValue = value.trim().toLowerCase();
    const matchingOptions = normalizedValue
      ? options.filter((option) => option.toLowerCase().includes(normalizedValue))
      : options;
    return matchingOptions.slice(0, MAX_VISIBLE_OPTIONS);
  }, [options, value]);

  const openList = () => {
    if (!disabled && options.length > 0) {
      setIsOpen(true);
    }
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
    openList();
  };

  const handleBlur = (_event: FocusEvent<HTMLInputElement>) => {
    blurTimeoutRef.current = window.setTimeout(() => setIsOpen(false), 120);
  };

  const selectOption = (option: string) => {
    if (blurTimeoutRef.current !== null) {
      window.clearTimeout(blurTimeoutRef.current);
    }
    onChange(option);
    setIsOpen(false);
  };

  return (
    <label className="relative block">
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <input
        aria-autocomplete="list"
        aria-controls={listId}
        aria-expanded={isOpen}
        autoComplete="off"
        className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#EE6C2F] focus:ring-2 focus:ring-[#EE6C2F]/20 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
        disabled={disabled}
        onBlur={handleBlur}
        onChange={handleChange}
        onFocus={openList}
        placeholder={placeholder}
        required={required}
        role="combobox"
        value={value}
      />
      {isOpen ? (
        <div
          className="absolute z-[60] mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 text-sm shadow-xl"
          id={listId}
          role="listbox"
        >
          {filteredOptions.length > 0 ? (
            filteredOptions.map((option) => (
              <button
                className="block w-full px-3 py-2 text-left text-slate-700 hover:bg-orange-50 hover:text-[#EE6C2F]"
                key={option}
                onMouseDown={(event) => {
                  event.preventDefault();
                  selectOption(option);
                }}
                role="option"
                type="button"
              >
                {option}
              </button>
            ))
          ) : (
            <div className="px-3 py-2 text-slate-500">Aucun poste trouve</div>
          )}
        </div>
      ) : null}
    </label>
  );
}
