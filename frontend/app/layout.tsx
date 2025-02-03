import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Employee Analytics",
  description: "Employee performance, attendance, and workload analytics dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
