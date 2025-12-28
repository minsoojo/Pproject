export interface Context {
  title?: string;
  url?: string;
  meta_id?: string;
  chunk_id?: number;
}

export interface ChatMessageData  {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  contexts?: Context[];   // 🔥 그대로 사용
}
