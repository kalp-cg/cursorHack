import type { Metadata } from "next";
import { Fraunces, Manrope, Noto_Sans_Gujarati, Noto_Serif_Devanagari } from "next/font/google";
import "./globals.css";
import DisclaimerBar from "@/components/DisclaimerBar";
import TopBar from "@/components/TopBar";
import { AppProvider } from "@/lib/app-context";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope",
  display: "swap",
});

const notoDevanagari = Noto_Serif_Devanagari({
  subsets: ["devanagari", "latin"],
  variable: "--font-noto-devanagari",
  display: "swap",
  weight: ["400", "600"],
});

const notoGujarati = Noto_Sans_Gujarati({
  subsets: ["gujarati", "latin"],
  variable: "--font-noto-gujarati",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "VedyaAI — Classical Formulation Discriminator",
  description:
    "AI-assisted Ayurvedic formulation decision support. Rank formulations with classical citations and safety gates.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${fraunces.variable} ${manrope.variable} ${notoDevanagari.variable} ${notoGujarati.variable}`}
    >
      <body
        className="locale-en"
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          ["--font-display" as string]: "var(--font-fraunces), Georgia, serif",
          ["--font-ui" as string]: "var(--font-manrope), system-ui, sans-serif",
          ["--font-devanagari" as string]: "var(--font-noto-devanagari), serif",
          ["--font-gujarati" as string]: "var(--font-noto-gujarati), sans-serif",
        }}
      >
        <AppProvider>
          <TopBar />
          <main style={{ flex: 1 }}>{children}</main>
          <DisclaimerBar />
        </AppProvider>
      </body>
    </html>
  );
}
