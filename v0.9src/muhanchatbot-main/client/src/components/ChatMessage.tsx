import { SourceLink } from "./SourceLink";
import mascotImage from '../../public/images/muhani nukki.png';
import { useCallback } from "react";

// Add the font face style
document.head.insertAdjacentHTML('beforeend', `
  <style>
    @font-face {
      font-family: 'Presentation';
      src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-7Bold.woff2') format('woff2');
      font-weight: 700;
      font-display: swap;
    }
  </style>
`);

export interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;

  // 기존
  sources?: Array<{ title: string; url: string }>;

  // ✅ 추가 (RAG에서 내려오는 contexts 그대로 받기)
  contexts?: Array<{
    title?: string;
    url?: string;
    meta_id?: string;
    chunk_id?: number;
  }>;

  timestamp?: string;

}

// Component for rendering category buttons
const CategoryButton = ({ category, onClick }: { category: string; onClick: (category: string) => void }) => {
  // Map of category names to emoji icons
  const categoryIcons: Record<string, string> = {
    '캠퍼스맵': '🗺️',
    '학사일정': '📆',
    '수강신청': '💻',
    '교내연락처': '☎️',
    '등록금': '💰',
    '편의시설': '🏪',
    '도서관': '📚',
  };

  return (
    <button
      onClick={() => onClick(category)}
      className="flex-shrink-0 flex flex-col items-center justify-center w-20 h-20 rounded-xl bg-white dark:bg-slate-700 shadow-md hover:shadow-lg transition-shadow duration-200 p-1.5 m-0.5"
    >
      <span className="text-2xl mb-1">{categoryIcons[category] || '🔘'}</span>
      <span className="text-xs font-medium text-center break-words leading-tight">{category}</span>
    </button>
  );
};

export function ChatMessage({ role, content, sources, contexts, timestamp, onCategorySelect }: ChatMessageProps & { onCategorySelect?: (category: string) => void }) {
  const isUser = role === "user";

  // Function to handle category button click
  const handleCategoryClick = useCallback((category: string) => {
    // Remove # if present
    const cleanCategory = category.startsWith('#') ? category.slice(1) : category;
    console.log(`Category selected: ${cleanCategory}`);
    
    // Call the onCategorySelect prop if it exists
    if (onCategorySelect) {
      // Map the Korean category name back to its ID
      const categoryMap: Record<string, string> = {
        '캠퍼스맵': 'campus_map',
        '학사일정': 'schedule',
        '수강신청': 'course',
        '교내연락처': 'contacts',
        '등록금': 'tuition',
        '편의시설': 'facilities',
        '도서관': 'library'
      };
      
      const categoryId = categoryMap[cleanCategory] || cleanCategory;
      onCategorySelect(categoryId);
    }
  }, [onCategorySelect]);

  // Function to render content with hashtags as buttons
  const renderContent = (text: string) => {
    // Check if the message is the welcome message with hashtags
    if (text.includes('안녕하세요! 가천대학교 AI 도우미입니다.')) {
      const parts = text.split('\n\n');
      const welcomeText = parts[0];
      const hashtagLines = parts.slice(1, -1);
      const questionText = parts[parts.length - 1];
      
      // Extract categories from hashtags
      const categories = hashtagLines
        .flatMap(line => line.split(' '))
        .filter(tag => tag.startsWith('#'))
        .map(tag => tag.substring(1));

      return (
        <div className="space-y-4">
          <p className="text-lg leading-relaxed whitespace-pre-wrap font-['Presentation']">{welcomeText}</p>
          
          {/* Render category grid */}
          <div className="flex flex-wrap justify-center gap-1 w-full">
            {categories.map((category, index) => (
              <CategoryButton 
                key={index} 
                category={category} 
                onClick={handleCategoryClick} 
              />
            ))}
          </div>
          
          <p className="text-lg leading-relaxed whitespace-pre-wrap font-['Presentation'] mt-4">{questionText}</p>
        </div>
      );
    }
    
    // For regular messages, just return the content as is
    return <p className="text-lg leading-relaxed whitespace-pre-wrap font-['Presentation']">{text}</p>;
  };

  return (
    <div
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} mb-4`}
      data-testid={`message-${role}`}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          <img 
            src={mascotImage} 
            alt="마스코트" 
            className="h-12 w-12 object-contain"
          />
        </div>
      )}

      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[85%] md:max-w-3xl`}>
        {isUser ? (
          <div className="bg-[#E0E0E0] dark:bg-[#202A44] text-[#516295] dark:text-white rounded-3xl px-5 py-3">
            {renderContent(content)}
            {sources && sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-current/10 space-y-1">
                {sources.map((source, idx) => (
                  <SourceLink key={idx} title={source.title} url={source.url} />
                ))}
              </div>
            )}
            {contexts && contexts.length > 0 && (
              <div className="mt-3 pt-3 border-t border-current/10">
                <div className="text-sm font-semibold mb-1">📚 참고 문서</div>
                <div className="space-y-1">
                  {contexts.map((ctx, idx) => (
                    ctx.url ? (
                      <SourceLink
                        key={`ctx-${idx}`}
                        title={ctx.title ?? ctx.meta_id ?? "문서"}
                        url={ctx.url}
                      />
                    ) : (
                      <div key={`ctx-${idx}`} className="text-sm opacity-80">
                        ▸ {ctx.title ?? ctx.meta_id ?? "문서"}
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}  
          </div>
        ) : (
          <div 
            className="p-[1.5px] rounded-3xl w-full"
            style={{
              background: "linear-gradient(90deg, #2F5093, #6AB7EC, #92C157, #EAA93D)",
              boxShadow: "0 8px 25px rgba(0, 0, 0, 0.08)",
            }}
          >
            <div className="bg-white dark:bg-slate-800 rounded-[22px] px-5 py-4 text-[#516295] dark:text-white">
              {renderContent(content)}
              {sources && sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-current/10 space-y-1">
                  {sources.map((source, idx) => (
                    <SourceLink key={idx} title={source.title} url={source.url} />
                  ))}
                </div>
              )}
              {contexts && contexts.length > 0 && (
                <div className="mt-3 pt-3 border-t border-current/10">
                  <div className="text-sm font-semibold mb-1">참고 링크</div>
                  <div className="space-y-1">
                    {contexts.map((ctx, idx) => (
                      ctx.url ? (
                        <SourceLink
                          key={`ctx-${idx}`}
                          title={ctx.title ?? ctx.meta_id ?? "참고 자료"}
                          url={ctx.url}
                        />
                      ) : (
                        <div key={`ctx-${idx}`} className="text-sm opacity-80">
                          • {ctx.title ?? ctx.meta_id ?? "참고 자료"}
                        </div>
                      )
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {timestamp && (
        <span className="text-xs text-muted-foreground mt-1 px-1">
          {timestamp}
        </span>
      )}
    </div>
  );
}
