import { ErrorMessage } from "../ErrorMessage";

export default function ErrorMessageExample() {
  return (
    <div className="p-4">
      <ErrorMessage
        message="입력하신 문장을 정확히 이해하기 어려워요. 혹시 오타가 있거나 키보드가 잘못 눌린 건 아닐까요? 찾고 계신 내용을 조금 더 정확히 적어주시면 빠르게 도와드릴게요!"
        suggestions={["#장학금", "#학사일정", "#수강신청", "#계절학기"]}
        onSuggestionClick={(s) => console.log("Clicked:", s)}
      />
    </div>
  );
}
