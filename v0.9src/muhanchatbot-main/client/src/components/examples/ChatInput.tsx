import { ChatInput } from "../ChatInput";

export default function ChatInputExample() {
  return (
    <div className="fixed bottom-0 left-0 right-0">
      <ChatInput
        onSendMessage={(msg) => console.log("Message sent:", msg)}
        placeholder="궁금한 내용을 입력하세요..."
      />
    </div>
  );
}
