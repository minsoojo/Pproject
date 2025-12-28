import { QuickSuggestions } from "../QuickSuggestions";

export default function QuickSuggestionsExample() {
  const suggestions = [
    "일정",
    "방법",
    "우선순위",
    "유의사항",
  ];

  return (
    <div className="p-4 max-w-2xl">
      <QuickSuggestions
        suggestions={suggestions}
        onSuggestionClick={(s) => console.log("Clicked:", s)}
      />
    </div>
  );
}
