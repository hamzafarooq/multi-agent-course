import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { motion } from "motion/react";
import { FileText, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { fetchDoc } from "@/lib/status";

interface DocPreviewProps {
  docFile: string;
  title: string;
  subtitle: string;
  /** bust the cache when the file changes on disk */
  cacheKey?: string;
}

export function DocPreview({ docFile, title, subtitle, cacheKey }: DocPreviewProps) {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchDoc(docFile)
      .then((text) => {
        if (!cancelled) {
          setContent(text);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message ?? "Failed to load");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [docFile, cacheKey]);

  return (
    <motion.div
      key={docFile + (cacheKey ?? "")}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.2, 0.8, 0.2, 1] }}
      className="h-full"
    >
      <Card className="h-full flex flex-col" elevated>
        <CardHeader className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 rounded-md bg-surface-2 border border-border flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4 text-fg" strokeWidth={1.75} />
            </div>
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>
                <code className="font-mono text-[12px]">docs/{docFile}</code> · {subtitle}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto pt-2">
          {loading ? (
            <div className="space-y-3 py-6">
              <div className="h-5 w-2/3 rounded shimmer" />
              <div className="h-4 w-full rounded shimmer" />
              <div className="h-4 w-5/6 rounded shimmer" />
              <div className="h-4 w-4/6 rounded shimmer" />
              <div className="h-4 w-3/4 rounded shimmer" />
            </div>
          ) : error ? (
            <div className="py-10 flex items-start gap-3 text-fg-muted">
              <Loader2 className="w-4 h-4 animate-spin mt-0.5" />
              <div>
                <div className="text-[14px] text-fg">Writing {docFile}</div>
                <div className="text-[12.5px] text-fg-subtle mt-1">{error}</div>
              </div>
            </div>
          ) : (
            <div className="markdown max-w-[780px]">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
