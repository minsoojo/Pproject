import { useState, KeyboardEvent, useEffect, useRef } from "react";
import { Send, ExternalLink } from "lucide-react";
import { useLocation } from "wouter";
import { CollapsibleBanner } from "./CollapsibleBanner";
import * as Popover from "@radix-ui/react-popover";
import { Command } from "cmdk";
import logoImage from '../../public/images/muhani nukki.png';
import gachonLogo from '../../public/images/mudangee.png';
import TimeGreeting from "./TimeGreeting";

export interface Category {
  id: string;
  label: string;
}

export interface WelcomeScreenProps {
  categories: Category[];
  onSearch?: (query: string) => void;
  onCategorySelect?: (categoryId: string) => void;
}

export function WelcomeScreen({ categories, onSearch, onCategorySelect }: WelcomeScreenProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<{id: string, label: string}[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const [activeMealTab, setActiveMealTab] = useState('vision');

  // 인기 검색어 목록
  const popularSearches = [
    { id: 'pop1', label: '도서관 열람실 현황' },
    { id: 'pop2', label: '강의실 배정 조회' },
    { id: 'pop3', label:  '장학금 신청'},
  ];

  // 검색창에 포커스가 갈 때 인기 검색어 표시
  const handleFocus = () => {
    if (!open) {
      setOpen(true);
      setSuggestions(popularSearches);
    }
  };

  // 검색어에 따른 추천 검색어 업데이트
  const updateSuggestions = (searchQuery = query) => {
    if (searchQuery.trim().length > 0) {
      // 실제로는 여기서 API를 호출하거나 더 정교한 추천 로직을 구현할 수 있습니다.
      const filtered = popularSearches.filter(item => 
        item.label.toLowerCase().includes(searchQuery.toLowerCase())
      );
      
      // 검색어가 포함된 추천 검색어가 없으면 기본 추천어 표시
      if (filtered.length === 0) {
        setSuggestions([
          { id: 'sug1', label: `${searchQuery} 검색하기` },
          { id: 'sug2', label: `${searchQuery} 정보` },
          { id: 'sug3', label: `${searchQuery} 조회` },
        ]);
      } else {
        setSuggestions(filtered);
      }
    } else {
      // 검색어가 없으면 인기 검색어 표시
      setSuggestions(popularSearches);
    }
  };

  // 검색 실행
  const handleSearch = () => {
    if (query.trim() && onSearch) {
      onSearch(query);
      setOpen(false);
    }
  };

  // 키보드 이벤트 처리
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 카테고리 선택 처리
  const handleCategoryClick = (categoryId: string) => {
    onCategorySelect?.(categoryId);
  };

  // 오늘 날짜 포맷팅
  const getFormattedDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    const dayOfWeek = weekdays[today.getDay()];
    return `${year}년 ${month}월 ${day}일 (${dayOfWeek})`;
  };

  // 폰트 스타일 추가
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @font-face {
        font-family: 'PresentationLight';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-3Light.woff2') format('woff2');
        font-weight: 300;
        font-display: swap;
      }
      @font-face {
        font-family: 'Presentation';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-5Medium.woff2') format('woff2');
        font-weight: 500;
        font-display: swap;
      }
      .search-input {
        font-family: 'PresentationLight', sans-serif;
        font-size: 1.125rem;
      }
      .hashtag {
        font-family: 'Presentation', sans-serif;
        font-size: 1rem;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  // 학식 메뉴 데이터
  const mealTabs = [
    {
      id: "vision",
      label: "비전타워",
      menus: [
        { item: "된장찌개" },
        { item: "제육볶음" },
        { item: "시금치나물" },
        { item: "김치" },
        { item: "깍두기" },
        { item: "흑미밥" },
      ],
    },
    {
      id: "graduate",
      label: "교육대학원",
      menus: [
        { item: "우동장국" },
        { item: "치킨까스" },
        { item: "단무지" },
        { item: "오이무침" },
        { item: "콩나물무침" },
        { item: "공기밥" },
      ],
    },
    {
      id: "dorm",
      label: "기숙사",
      menus: [
        { item: "김치찌개" },
        { item: "돈까스" },
        { item: "오이양파무침" },
        { item: "콩나물무침" },
        { item: "계란후라이" },
        { item: "보리밥" },
      ],
    },
  ];

  const activeMeal = mealTabs.find(tab => tab.id === activeMealTab);
  const [location] = useLocation();

  // Add/remove class to prevent scrolling when component mounts/unmounts
  useEffect(() => {
    if (location === '/') {
      // Add classes to both html and body for maximum compatibility
      document.documentElement.classList.add('welcome-screen-active');
      document.body.classList.add('welcome-screen-active');
      
      // Store original styles to restore later
      const originalStyles = {
        html: {
          overflow: document.documentElement.style.overflow,
          position: document.documentElement.style.position,
          height: document.documentElement.style.height,
          width: document.documentElement.style.width,
          top: document.documentElement.style.top,
          left: document.documentElement.style.left,
          right: document.documentElement.style.right,
          bottom: document.documentElement.style.bottom
        },
        body: {
          overflow: document.body.style.overflow,
          position: document.body.style.position,
          height: document.body.style.height,
          width: document.body.style.width,
          top: document.body.style.top,
          left: document.body.style.left,
          right: document.body.style.right,
          bottom: document.body.style.bottom
        }
      };

      // Apply styles directly to ensure they take effect
      Object.assign(document.documentElement.style, {
        overflow: 'hidden',
        position: 'fixed',
        height: '100%',
        width: '100%',
        top: '0',
        left: '0',
        right: '0',
        bottom: '0'
      });

      Object.assign(document.body.style, {
        overflow: 'hidden',
        position: 'fixed',
        height: '100%',
        width: '100%',
        top: '0',
        left: '0',
        right: '0',
        bottom: '0'
      });
      
      // Prevent all possible scroll events
      const preventDefault = (e: Event) => {
        if (e.target && (e.target as HTMLElement).tagName === 'INPUT') return;
        e.preventDefault();
        e.stopPropagation();
        return false;
      };
      
      // Add all possible scroll-related event listeners
      const events = [
        'touchmove', 'touchstart', 'touchend', 'touchcancel',
        'wheel', 'mousewheel', 'DOMMouseScroll', 'MozMousePixelScroll',
        'scroll', 'keydown'
      ];
      
      events.forEach(event => {
        document.addEventListener(event, preventDefault, { passive: false, capture: true });
        window.addEventListener(event, preventDefault, { passive: false, capture: true });
      });
      
      // Cleanup function
      return () => {
        // Restore original styles
        Object.assign(document.documentElement.style, originalStyles.html);
        Object.assign(document.body.style, originalStyles.body);
        
        // Remove all event listeners
        events.forEach(event => {
          document.removeEventListener(event, preventDefault, { capture: true } as any);
          window.removeEventListener(event, preventDefault, { capture: true } as any);
        });
        
        // Remove classes
        document.documentElement.classList.remove('welcome-screen-active');
        document.body.classList.remove('welcome-screen-active');
      };
    }
  }, [location]);

  return (
    <div className="relative min-h-screen px-4 py-8">
      {/* 왼쪽 배너 */}
      <div className="hidden xl:flex flex-col gap-6 w-[380px] fixed left-8 top-32">
        <CollapsibleBanner
          title=""
          subtitle={getFormattedDate()}
          defaultExpanded={false}
          className="shadow-none"
        >
          <div className="px-4 pt-2 pb-4 -mt-2">
            <TimeGreeting />
          </div>
        </CollapsibleBanner>
      </div>
      
      {/* 메인 콘텐츠 */}
      <div className="container mx-auto flex flex-col items-center justify-center min-h-[calc(100vh-100px)]">
        <div className="w-full max-w-4xl mx-auto text-center">
          {/* 로고 */}
          <div className="flex justify-center mb-6">
            <img
              src={logoImage}
              alt="AI 도우미"
              className="h-auto w-48 md:w-56 max-h-64 object-contain"
              style={{ minHeight: '200px' }}
              data-testid="logo-mascot"
            />
          </div>

          {/* 검색창 */}
          <div className="w-full max-w-4xl mx-auto mb-5">
            <div 
              className="p-[1.5px] rounded-full"
              style={{
                background: "linear-gradient(90deg, #2F5093, #6AB7EC, #92C157, #EAA93D)",
                boxShadow: "0 8px 25px rgba(0, 0, 0, 0.08)",
              }}
            >
              <div className="relative w-full">
                <Popover.Root 
                  open={open} 
                  onOpenChange={(isOpen) => {
                    // Only close the popover if there's no query and we're not just focusing the input
                    if (!isOpen && !inputRef.current?.contains(document.activeElement)) {
                      setOpen(false);
                    } else if (isOpen) {
                      setOpen(true);
                    }
                  }}
                >
                  <Popover.Anchor asChild>
                    <div className="relative w-full">
                      <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => {
                          const value = e.target.value;
                          setQuery(value);
                          setOpen(true);
                          updateSuggestions(value);
                        }}
                        onKeyDown={handleKeyDown}
                        onFocus={() => {
                          setOpen(true);
                          updateSuggestions(query);
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpen(true);
                        }}
                        placeholder="무엇이든 물어보세요"
                        className="w-full h-12 pl-4 pr-12 rounded-full bg-white dark:bg-slate-800 border-none outline-none text-base placeholder-gray-400 dark:placeholder-gray-500 search-input dark:text-white"
                      />
                      <button
                        onClick={handleSearch}
                        disabled={!query.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full text-gray-500 hover:text-primary dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
                        aria-label="검색"
                      >
                        <Send className="h-5 w-5" />
                      </button>
                    </div>
                  </Popover.Anchor>
                  <Popover.Portal>
                    <Popover.Content
                      className="w-[var(--radix-popover-trigger-width)] mt-1 bg-white dark:bg-slate-800 rounded-lg shadow-xl overflow-hidden border border-gray-100 dark:border-slate-700 z-50"
                      align="start"
                      sideOffset={5}
                      onOpenAutoFocus={(e) => e.preventDefault()}
                      onPointerDownOutside={(e) => {
                        // Don't close if clicking on the input or its container
                        if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
                          setOpen(false);
                        }
                      }}
                    >
                      <Command className="w-full bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
                        <Command.Input
                          value={query}
                          onValueChange={(value) => {
                            setQuery(value);
                            updateSuggestions(value);
                          }}
                          className="hidden"
                        />
                        <Command.List className="w-full max-h-[300px] overflow-y-auto">
                          {suggestions.length > 0 ? (
                            suggestions.map((suggestion) => (
                              <Command.Item
                                key={suggestion.id}
                                value={suggestion.label}
                                onSelect={() => {
                                  setQuery(suggestion.label);
                                  setOpen(false);
                                  if (onSearch) onSearch(suggestion.label);
                                }}
                                className="px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-slate-700 cursor-pointer flex items-center w-full text-left"
                              >
                                <span>{suggestion.label}</span>
                              </Command.Item>
                            ))
                          ) : query.length > 0 ? (
                            <div className="px-4 py-2 text-sm text-gray-500 dark:text-gray-400">
                              검색어와 일치하는 결과가 없습니다.
                            </div>
                          ) : null}
                        </Command.List>
                      </Command>
                    </Popover.Content>
                  </Popover.Portal>
                </Popover.Root>
              </div>
            </div>

            {/* 카테고리 버튼들 */}
            <div className="flex flex-wrap justify-center gap-3 mt-6">
              {categories.map((category) => (
                <button
                  key={category.id}
                  className="hashtag rounded-full bg-white/40 backdrop-blur-md px-5 py-2 text-sm shadow-sm border border-[#E4E4E7] hover:bg-white/60 hover:shadow-md transition-all duration-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-700"
                  onClick={() => handleCategoryClick(category.id)}
                  data-testid={`welcome-category-${category.id}`}
                >
                  {category.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 우측 배너 (데스크톱 전용) */}
      <div className="hidden 2.5xl:flex flex-col gap-6 w-[380px] fixed right-8 top-32">
        {/* 오늘의 학식 배너 */}
        <CollapsibleBanner
          title="오늘의 학식"
          subtitle={getFormattedDate()}
          defaultExpanded={false}
          className="shadow-none"
        >
          <div className="flex gap-2 mb-4">
            {mealTabs.map((tab) => (
              <button
                key={tab.id}
                className={`flex-1 rounded-2xl border px-3 py-2 text-sm font-medium transition-colors ${
                  activeMealTab === tab.id
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-gray-100 border-gray-200 text-gray-700 hover:bg-gray-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700'
                }`}
                onClick={() => setActiveMealTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {activeMeal?.menus.map((menu, index) => (
              <div 
                key={index} 
                className="px-3 py-2 bg-gray-50 dark:bg-slate-800 rounded-lg text-gray-800 dark:text-gray-200 text-sm whitespace-nowrap"
              >
                {menu.item}
              </div>
            ))}
          </div>
        </CollapsibleBanner>

        {/* 학사 일정 배너 */}
        <CollapsibleBanner
          title="오늘의 학사일정"
          subtitle={getFormattedDate()}
          defaultExpanded={false}
          className="shadow-none"
        >
          <div className="space-y-2">
            {[
              "2024학년도 2학기 수강신청",
              "캡스톤 디자인 발표회",
              "학부 연구생 모집 설명회",
            ].map((event, index) => (
              <div
                key={index}
                className="p-3 rounded-lg bg-muted/50 dark:bg-slate-800 border border-muted-foreground/20 dark:border-slate-700"
              >
                <p className="text-sm font-medium text-foreground dark:text-white">
                  {event}
                </p>
              </div>
            ))}
          </div>
        </CollapsibleBanner>
      </div>

      {/* 무당이 로고 - 버튼과 분리된 별도의 컨테이너 - 모바일에서는 숨김 */}
      <a 
        href="https://www.gachon.ac.kr/kor/index.do" 
        target="_blank" 
        rel="noopener noreferrer"
        className="fixed left-12 bottom-7 z-20 h-28 w-28 transition-transform hover:scale-105 hidden md:block"
      >
        <img 
          src={gachonLogo} 
          alt="Gachon University" 
          className="h-full w-full object-contain"
        />
      </a>
      
      {/* 가천대학교 버튼 - 모바일에서는 숨김 */}
      <div className="fixed left-20 bottom-8 z-10 hidden md:block">
        <a 
          href="https://www.gachon.ac.kr/kor/index.do" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-3 bg-white dark:bg-slate-800 pl-16 pr-6 py-2.5 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 border border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-600"
        >
          <span className="text-2xl font-bold text-gray-800 dark:text-gray-200">
            가천대학교
          </span>
          <ExternalLink className="h-5 w-5 text-gray-400 hover:text-blue-500 transition-colors" />
        </a>
      </div>
    </div>
  );
}
