import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mèo Hồng | Trợ lý chọn quà",
  description: "Trợ lý giúp bạn chọn quà hợp với người nhận.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
