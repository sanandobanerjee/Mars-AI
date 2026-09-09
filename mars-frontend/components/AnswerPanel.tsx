import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { QueryResult } from "@/lib/types";

export default function AnswerPanel({ result }: { result: QueryResult }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <div className="border border-text/10 bg-panel rounded-lg p-6">
        <div className="font-display text-xl font-semibold mb-4 text-mars">
          Answer
        </div>
        <div className="font-body text-text/90 leading-relaxed text-base space-y-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:text-mars [&_strong]:font-semibold [&_code]:font-body [&_code]:bg-void [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:tracking-tight [&_table]:w-full [&_table]:border-collapse [&_th]:border-b [&_th]:border-text/10 [&_th]:p-2 [&_th]:text-left [&_th]:text-xs [&_th]:uppercase [&_th]:text-text/50 [&_td]:border-b [&_td]:border-text/10 [&_td]:p-2 [&_td]:text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {result.answer}
          </ReactMarkdown>
        </div>
      </div>

      <div className="border border-text/10 bg-panel rounded-lg p-6">
        <div className="font-display text-xl font-semibold mb-4 text-mars">
          Citations
          <span className="font-body text-sm text-text/40 ml-3">{result.citations.length}</span>
        </div>
        <div className="space-y-3">
          {result.citations.map((c, i) => (
            <div key={i} className="flex items-baseline justify-between gap-4">
              <span className="font-body text-mars-bright text-sm">{c.qualified_name}</span>
              <span className="font-body text-text/40 text-xs whitespace-nowrap">
                {c.file_path}:{c.start_line}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}