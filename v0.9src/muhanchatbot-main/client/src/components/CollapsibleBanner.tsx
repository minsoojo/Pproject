import { useCollapsible } from '@/contexts/CollapsibleContext';
import { useEffect } from 'react';

interface CollapsibleBannerProps {
  title: string;
  subtitle?: string;
  badgeText?: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function CollapsibleBanner({
  title,
  subtitle,
  badgeText,
  defaultExpanded = true,
  children,
  className = '',
}: CollapsibleBannerProps) {
  // Always set isActive to true to keep the banner expanded
  const isActive = true;
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @font-face {
        font-family: 'Presentation';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-5Medium.woff2') format('woff2');
        font-weight: 500;
        font-display: swap;
      }
      @font-face {
        font-family: 'Presentation';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2404@1.0/Freesentation-7Bold.woff2') format('woff2');
        font-weight: 700;
        font-display: swap;
      }
      .banner-title {
        font-family: 'Presentation', sans-serif;
        font-weight: 700;
      }
      .banner-subtitle {
        font-family: 'Presentation', sans-serif;
        font-weight: 500;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div className={`bg-white dark:bg-slate-900 border border-primary/20 dark:border-slate-700 rounded-3xl p-6 shadow-md dark:shadow-none flex flex-col ${className}`}>
      <div className="flex flex-col items-center text-center">
        <div className="w-full">
          {subtitle && <p className="banner-subtitle text-sm text-primary/70 dark:text-primary/60 font-semibold">{subtitle}</p>}
          <h3 className="banner-title text-2xl font-bold text-primary dark:text-white">{title}</h3>
        </div>
        {badgeText && (
          <span className="bg-primary/10 text-primary dark:bg-primary/20 dark:text-white text-xs font-medium px-2.5 py-0.5 rounded-full">
            {badgeText}
          </span>
        )}
      </div>
      
      <div className={`transition-all duration-300 overflow-hidden ${isActive ? 'mt-4 opacity-100' : 'h-0 opacity-0 mt-0'}`}>
        {children}
      </div>
    </div>
  );
}
