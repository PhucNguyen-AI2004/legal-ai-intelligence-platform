import type { Metadata } from "next";
import { DocumentDetailWorkspace } from "@/components/documents/document-detail-workspace";

export const metadata: Metadata = { title: "Chi tiết tài liệu" };

export default async function DocumentDetailPage({ params }: { params: Promise<{ documentId: string }> }) {
  const { documentId } = await params;
  return <DocumentDetailWorkspace documentId={documentId} />;
}
