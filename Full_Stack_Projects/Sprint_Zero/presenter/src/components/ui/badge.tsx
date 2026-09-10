import * as React from "react";
import { cn } from "@/lib/cn";

type Tone = "neutral" | "accent" | "success" | "warn" | "danger";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-3 text-fg-muted border-border",
  accent: "bg-fg text-bg border-fg",
  success: "bg-success/10 text-success border-success/25",
  warn: "bg-warn/10 text-warn border-warn/25",
  danger: "bg-danger/10 text-danger border-danger/25",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full",
        "text-[11px] font-medium tracking-wide uppercase border",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

export function Dot({ tone = "neutral" }: { tone?: "neutral" | "accent" | "success" | "warn" | "danger" }) {
  const color = {
    neutral: "bg-fg-subtle",
    accent: "bg-fg",
    success: "bg-success",
    warn: "bg-warn",
    danger: "bg-danger",
  }[tone];
  return <span className={cn("inline-block w-1.5 h-1.5 rounded-full", color)} />;
}
