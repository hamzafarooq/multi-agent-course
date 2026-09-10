import { useState } from "react";
import { motion } from "motion/react";
import { Check, Copy, ExternalLink, PartyPopper, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Credentials } from "@/lib/types";
import { cn } from "@/lib/cn";

interface DoneHeroProps {
  appUrl: string;
  credentials?: Credentials | null;
  projectName?: string | null;
}

export function DoneHero({ appUrl, credentials, projectName }: DoneHeroProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
      className="h-full flex items-center"
    >
      <Card className="w-full p-10" elevated>
        <div className="flex flex-col items-start">
          <Badge tone="accent" className="mb-5">
            <PartyPopper className="w-3 h-3" />
            Ready to demo
          </Badge>
          <h2 className="text-[48px] leading-[1.05] font-semibold tracking-[-0.04em] text-fg">
            Your product is live.
          </h2>
          <p className="mt-4 text-[15.5px] leading-relaxed text-fg-muted max-w-[560px]">
            Both servers are up, QA passed, and the demo user below is already seeded
            {projectName ? ` for ${projectName}` : ""}. Open the app and walk the core loop.
          </p>

          <UrlRow url={appUrl} />

          {credentials && <CredentialsBlock credentials={credentials} />}

          <div className="mt-9 flex items-center gap-3">
            <Button
              size="lg"
              onClick={() => window.open(appUrl, "_blank", "noopener")}
            >
              <Sparkles className="w-4 h-4" />
              Open the app
              <ExternalLink className="w-4 h-4" />
            </Button>
            <p className="text-[12.5px] text-fg-subtle">
              Opens in a new tab. Sign in with the demo login above.
            </p>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function UrlRow({ url }: { url: string }) {
  return (
    <div className="mt-8 w-full max-w-[560px]">
      <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-4 h-12">
        <div className="flex items-center gap-2 text-[12px] text-fg-subtle">
          <span className="inline-flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-success" />
            <span className="font-mono">live</span>
          </span>
          <span className="text-border-strong">·</span>
        </div>
        <code className="flex-1 font-mono text-[14px] text-fg truncate">{url}</code>
        <CopyButton text={url} />
      </div>
    </div>
  );
}

function CredentialsBlock({ credentials }: { credentials: Credentials }) {
  return (
    <div className="mt-5 w-full max-w-[560px]">
      <div className="text-[11px] font-mono text-fg-subtle uppercase tracking-widest mb-2">
        Demo login
      </div>
      <Card className="p-4 bg-surface-2">
        <CredRow label="email" value={credentials.email} />
        <div className="h-px bg-border my-3" />
        <CredRow label="password" value={credentials.password} />
      </Card>
    </div>
  );
}

function CredRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 font-mono text-[12px] text-fg-subtle uppercase tracking-wide">
        {label}
      </span>
      <code className="flex-1 font-mono text-[13.5px] text-fg truncate">{value}</code>
      <CopyButton text={value} />
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1400);
        } catch {
          /* ignore */
        }
      }}
      className={cn(
        "inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md",
        "text-[11.5px] font-medium text-fg-muted hover:text-fg",
        "border border-border hover:border-border-strong hover:bg-surface-3",
        "transition-colors"
      )}
    >
      {copied ? <Check className="w-3 h-3 text-success" strokeWidth={2.5} /> : <Copy className="w-3 h-3" />}
      {copied ? "copied" : "copy"}
    </button>
  );
}
