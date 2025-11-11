import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kagura Memory Cloud",
  description: "Universal AI Memory Platform - Admin Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.Node;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
