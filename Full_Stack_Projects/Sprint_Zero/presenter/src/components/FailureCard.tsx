import { motion } from "motion/react";
import { AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface FailureCardProps {
  state: string;
  message: string;
  recovery: string;
}

export function FailureCard({ state, message, recovery }: FailureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="h-full flex items-center"
    >
      <Card className="w-full p-8 border-danger/30">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-md bg-danger/10 border border-danger/30 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-danger" strokeWidth={1.75} />
          </div>
          <div className="min-w-0">
            <Badge tone="danger" className="mb-3">
              {state}
            </Badge>
            <h3 className="text-[20px] font-semibold tracking-tight text-fg">
              The run stopped here.
            </h3>
            <p className="mt-2 text-[14px] leading-relaxed text-fg-muted">{message}</p>

            <div className="mt-6 rounded-md border border-border bg-surface-2 p-4">
              <div className="text-[11px] font-mono text-fg-subtle uppercase tracking-widest mb-2">
                Recovery
              </div>
              <div className="text-[13.5px] leading-relaxed text-fg-muted whitespace-pre-wrap">
                {recovery}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
