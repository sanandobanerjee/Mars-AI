import type { Metadata } from "next";
import { Chakra_Petch, Sora } from "next/font/google";
import "./globals.css";

const chakraPetch = Chakra_Petch({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-display",
});
const sora = Sora({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Mars — Multi-hop Agent Retrieval and Scoring",
  description: "A codebase-aware coding agent for exploring unfamiliar Python repositories through multi-hop, call-graph-aware reasoning.",
  keywords: ["RAG", "LangGraph", "code agent", "AST", "call graph", "AI"],
  openGraph: {
    title: "Mars — Multi-hop Agent Retrieval and Scoring",
    description: "Explore any Python codebase through multi-hop, call-graph-aware AI reasoning.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${chakraPetch.variable} ${sora.variable}`}
      >
        {children}
      </body>
    </html>
  );
}