import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "vietnamese"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: { default: "Legal AI", template: "%s | Legal AI" },
  description: "Không gian làm việc tra cứu tài liệu pháp lý có dẫn nguồn.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body className={inter.variable}>{children}</body>
    </html>
  );
}
