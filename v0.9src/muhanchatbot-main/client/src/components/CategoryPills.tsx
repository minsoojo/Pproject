import { Badge } from "@/components/ui/badge";
import { useState } from "react";

export interface Category {
  id: string;
  label: string;
}

export interface CategoryPillsProps {
  categories: Category[];
  onCategorySelect?: (categoryId: string) => void;
}

export function CategoryPills({ categories, onCategorySelect }: CategoryPillsProps) {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const handleClick = (categoryId: string) => {
    const newActive = activeCategory === categoryId ? null : categoryId;
    setActiveCategory(newActive);
    onCategorySelect?.(categoryId);
    console.log(`Category selected: ${categoryId}`);
  };

  return (
    <div className="flex items-center justify-center gap-2 overflow-x-auto pb-2 px-4 md:px-8 scrollbar-hide">
      {categories.map((category) => (
        <Badge
          key={category.id}
          variant="secondary"
          className={`cursor-pointer flex-shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
            activeCategory === category.id
              ? "toggle-elevate toggle-elevated"
              : ""
          }`}
          onClick={() => handleClick(category.id)}
          data-testid={`category-${category.id}`}
        >
          {category.label}
        </Badge>
      ))}
    </div>
  );
}
