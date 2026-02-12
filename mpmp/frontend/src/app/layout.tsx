import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MPMP — Medical Practice Management",
  description: "HIPAA-compliant practice management for functional medicine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
