import type { Metadata } from "next";
import { DocumentsWorkspace } from "@/components/documents/documents-workspace";

export const metadata: Metadata = { title: "Tài liệu" };

export default async function DocumentsPage({ searchParams }: { searchParams: Promise<{ deleted?: string }> }) {
  const { deleted } = await searchParams;
  return <DocumentsWorkspace initialFeedback={deleted === "1" ? "Đã xóa tài liệu." : undefined} />;
}
