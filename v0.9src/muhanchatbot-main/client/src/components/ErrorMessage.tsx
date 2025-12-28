import { AlertCircle } from "lucide-react";
import { QuickSuggestions } from "./QuickSuggestions";

export interface ErrorMessageProps {
  message: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
}

export function ErrorMessage({ message, suggestions, onSuggestionClick }: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-8 px-4" data-testid="error-message">
      <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-base text-foreground mb-6 max-w-md leading-relaxed">
        {message}
      </p>
      {suggestions && suggestions.length > 0 && (
        <QuickSuggestions suggestions={suggestions} onSuggestionClick={onSuggestionClick} />
      )}
    </div>
  );
}
