export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageCitation {
  citation_index: number;
  document_id: string;
  document_name: string;
  chunk_id: string;
  chunk_index: number;
  similarity_score: number;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  sequence_number: number;
  grounded: boolean | null;
  retrieval_query: string | null;
  created_at: string;
  citations: MessageCitation[];
}

export interface ConversationDetail extends ConversationSummary {
  messages: ConversationMessage[];
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateConversationRequest { title?: string | null; }
export interface UpdateConversationRequest { title: string; }

export interface CreateMessageRequest {
  content: string;
  top_k?: number;
  document_ids?: string[] | null;
}
