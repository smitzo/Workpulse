import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WorkPulse",
  description: "Modern attendance, timesheet, project, and work analytics platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
