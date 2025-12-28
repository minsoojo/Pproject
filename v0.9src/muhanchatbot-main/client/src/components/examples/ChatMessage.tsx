import { ChatMessage } from "../ChatMessage";

export default function ChatMessageExample() {
  return (
    <div className="space-y-4 p-4 max-w-4xl">
      <ChatMessage
        role="user"
        content="2025학년도 1학기 수강신청 일정이 언제야?"
        timestamp="오후 2:30"
      />
      
      <ChatMessage
        role="assistant"
        content={`수강신청 일정은 다음과 같습니다.
학사안내 및 학교 공지 기준으로 정리해드릴게요.

• 장바구니 기간: 02월 10일 ~ 02월 14일
• 본수강신청: 02월 17일 10:00 ~
• 수강정정: 02월 24일 ~ 02월 28일
• 폐강확정 및 인원조정: 03월 02일

필요하시면 방법, 우선순위, 팁도 알려드릴게요!`}
        sources={[
          { title: "2025학년도 수강신청 공지 바로가기", url: "#" },
          { title: "학사안내(수강신청) PDF 열기", url: "#" },
          { title: "종합정보시스템 수강신청 페이지", url: "#" }
        ]}
        timestamp="오후 2:30"
      />
    </div>
  );
}
