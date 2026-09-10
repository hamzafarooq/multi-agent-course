import * as React from "react";
import { cn } from "@/lib/cn";

const fieldBase = cn(
  "w-full rounded-md border border-border bg-surface text-[14px] text-fg",
  "placeholder:text-fg-subtle",
  "transition-[border-color,box-shadow] duration-150",
  "hover:border-border-strong",
  "focus-visible:outline-none focus-visible:border-fg-subtle focus-visible:ring-4 focus-visible:ring-fg/[0.06]",
  "disabled:opacity-50"
);

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input ref={ref} className={cn(fieldBase, "h-10 px-3", className)} {...props} />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(fieldBase, "px-3 py-2.5 leading-relaxed resize-y min-h-[90px]", className)}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export const Label = React.forwardRef<
  HTMLLabelElement,
  React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    className={cn("text-[13px] font-medium text-fg tracking-tight", className)}
    {...props}
  />
));
Label.displayName = "Label";

export function FieldHint({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-[12px] text-fg-subtle mt-1.5 leading-relaxed", className)}>{children}</p>;
}

/* A row of mutually exclusive choices, the way a settings page picks a region or a framework. */
export function Segmented<T extends string>({
  value,
  onChange,
  options,
  ariaLabel,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string; hint?: string }[];
  ariaLabel: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className="inline-flex w-full rounded-md border border-border bg-surface-2 p-0.5"
    >
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(opt.value)}
            className={cn(
              "flex-1 h-9 px-3 rounded-[5px] text-[13px] font-medium tracking-tight",
              "transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fg/20",
              selected
                ? "bg-surface text-fg shadow-[var(--shadow-elev-1)]"
                : "text-fg-muted hover:text-fg"
            )}
          >
            <span className="font-mono">{opt.label}</span>
            {opt.hint && <span className="hidden md:inline text-fg-subtle font-sans"> · {opt.hint}</span>}
          </button>
        );
      })}
    </div>
  );
}
