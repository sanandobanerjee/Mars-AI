import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QueryResult } from "@/lib/types";
import CopyButton from "./CopyButton";

function buildGithubUrl(result: QueryResult, filePath: string, startLine: number, endLine: number): string | null {
  const { owner, repo, default_branch } = result.repo_meta;
  if (!owner || !repo) return null;
  return `https://github.com/${owner}/${repo}/blob/${default_branch || "main"}/${filePath}#L${startLine}-L${endLine}`;
}

function formatCitationsAsText(result: QueryResult): string {
  return result.citations
    .map((c) => `${c.qualified_name} — ${c.file_path}:${c.start_line}`)
    .join("\n");
}

export default function AnswerPanel({ result }: { result: QueryResult }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="border border-text/10 bg-panel rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="font-display text-xl font-semibold text-mars">
            Answer
          </div>
          <CopyButton text={result.answer} />
        </div>
        <div
          className={[
            "font-body text-text/90 leading-relaxed text-base space-y-3",
            "[&_ul]:list-disc [&_ul]:pl-5",
            "[&_ol]:list-decimal [&_ol]:pl-5",
            "[&_strong]:text-mars [&_strong]:font-semibold",
            "[&_code]:font-body [&_code]:bg-void [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:tracking-tight",
            "[&_table]:w-full [&_table]:border-collapse",
            "[&_th]:border-b [&_th]:border-text/10 [&_th]:p-2 [&_th]:text-left [&_th]:text-xs [&_th]:uppercase [&_th]:text-text/50",
            "[&_td]:border-b [&_td]:border-text/10 [&_td]:p-2 [&_td]:text-sm",
          ].join(" ")}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.answer}
          </ReactMarkdown>
        </div>
      </div>

      <div className="border border-text/10 bg-panel rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="font-display text-xl font-semibold text-mars">
            Citations
            <span className="font-body text-sm text-text/40 ml-3">{result.citations.length}</span>
          </div>
          <CopyButton text={formatCitationsAsText(result)} />
        </div>
        <div className="space-y-3">
          {result.citations.map((c, i) => {
            const url = buildGithubUrl(result, c.file_path, c.start_line, c.end_line);
            return (
              <div key={i} className="flex items-baseline justify-between gap-4">
                <span className="font-body text-mars-bright text-sm">{c.qualified_name}</span>
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-body text-text/40 text-xs whitespace-nowrap hover:text-mars hover:underline transition-colors"
                  >
                    {c.file_path}:{c.start_line}
                  </a>
                ) : (
                  <span className="font-body text-text/40 text-xs whitespace-nowrap">
                    {c.file_path}:{c.start_line}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}