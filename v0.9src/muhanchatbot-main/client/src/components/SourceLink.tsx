import { ExternalLink } from "lucide-react";

export interface SourceLinkProps {
  title: string;
  url: string;
}

export function SourceLink({ title, url }: SourceLinkProps) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-1.5 text-sm hover-elevate active-elevate-2 rounded px-2 py-1 -mx-2"
      data-testid="link-source"
    >
      <span className="text-current/90" aria-hidden="true">🔗</span>
      <span className="underline decoration-current/40 hover:decoration-current/60">
        {title}
      </span>
      <ExternalLink className="h-3 w-3 opacity-60" />
    </a>
  );
}
