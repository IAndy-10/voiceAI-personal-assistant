import { type Language, LANGUAGES } from "../types/conversation";

interface Props {
  value: Language;
  onChange: (language: Language) => void;
  disabled: boolean;
}

export function LanguagePicker({ value, onChange, disabled }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Conversation language"
      className="inline-flex rounded-lg border border-zinc-300 p-0.5 dark:border-zinc-700"
    >
      {LANGUAGES.map(({ code, label }) => (
        <button
          key={code}
          type="button"
          role="radio"
          aria-checked={value === code}
          disabled={disabled}
          onClick={() => onChange(code)}
          className={`rounded-md px-3 py-1 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
            value === code
              ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
              : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
