import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QueryResult } from "@/lib/types";

export default function AnswerPanel({ result }: { result: QueryResult }) {
  return (
    <div className="space-y-4">
      <div className="bg-surface border border-text-dim/20 rounded-lg p-5">
        <div className="text-text-dim text-xs uppercase tracking-wide mb-2 font-mono">
          Answer
        </div>
        <div className="text-text leading-relaxed space-y-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:text-rust [&_strong]:font-semibold [&_code]:font-mono [&_code]:bg-bg [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-signal [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-text-dim/20 [&_th]:p-2 [&_th]:text-left [&_th]:font-mono [&_th]:text-xs [&_th]:uppercase [&_th]:text-text-dim [&_td]:border [&_td]:border-text-dim/20 [&_td]:p-2 [&_td]:text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.answer}
          </ReactMarkdown>
        </div>
      </div>

      <div className="bg-surface border border-text-dim/20 rounded-lg p-5">
        <div className="text-text-dim text-xs uppercase tracking-wide mb-3 font-mono">
          Citations ({result.citations.length})
        </div>
        <div className="space-y-1.5 font-mono text-sm">
          {result.citations.map((c, i) => (
            <div key={i} className="text-text-dim">
              <span className="text-rust">{c.qualified_name}</span>{" "}
              <span>
                {c.file_path}:{c.start_line}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}