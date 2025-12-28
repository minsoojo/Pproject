import { Badge } from "@/components/ui/badge";

export interface QuickSuggestionsProps {
  suggestions: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

export function QuickSuggestions({ suggestions, onSuggestionClick }: QuickSuggestionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {suggestions.map((suggestion, idx) => (
        <Badge
          key={idx}
          variant="outline"
          className="cursor-pointer rounded-full px-4 py-2 text-sm hover-elevate active-elevate-2"
          onClick={() => {
            onSuggestionClick?.(suggestion);
            console.log(`Suggestion clicked: ${suggestion}`);
          }}
          data-testid={`suggestion-${idx}`}
        >
          {suggestion}
        </Badge>
      ))}
    </div>
  );
}
