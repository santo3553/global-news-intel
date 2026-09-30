import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Global News Intelligence",
  description: "Interactive real-time global event intelligence and spatial clustering console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
