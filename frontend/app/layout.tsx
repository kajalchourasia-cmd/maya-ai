import type { Metadata } from "next";
import "./globals.css";
import "./purple-theme.css";
import { ThemeToggle } from "./maya/theme-toggle";

export const metadata: Metadata = {
  title: "Maya AI — Your maternal companion",
  description: "A controlled fictional local demo of Nestline journey, safety, planning, and evidence-validation boundaries.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-IN" data-maya-theme="light">
      <body className="antialiased">{children}<ThemeToggle /></body>
    </html>
  );
}
