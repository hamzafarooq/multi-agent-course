export function Logo({ className }: { className?: string }) {
  return (
    <div className={"flex items-center gap-2.5 " + (className ?? "")}>
      <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden>
        <rect width="32" height="32" rx="7" fill="#171717" />
        <circle cx="16" cy="16" r="7.5" stroke="#ffffff" strokeWidth="1.75" />
        <circle cx="16" cy="16" r="2.5" fill="#ffffff" />
      </svg>
      <div className="flex items-baseline gap-2">
        <span className="text-[14.5px] font-semibold tracking-tight text-fg">Sprint Zero</span>
        <span className="text-[12px] text-fg-subtle">Presenter</span>
      </div>
    </div>
  );
}
