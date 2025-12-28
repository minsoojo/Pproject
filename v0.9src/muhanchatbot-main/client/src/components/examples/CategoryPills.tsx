import { CategoryPills } from "../CategoryPills";

export default function CategoryPillsExample() {
  const categories = [
    { id: "scholarship", label: "장학금" },
    { id: "schedule", label: "학사일정" },
    { id: "course", label: "수강신청" },
    { id: "seasonal", label: "계절학기" },
    { id: "leave", label: "휴학" },
    { id: "return", label: "복학" },
    { id: "tuition", label: "등록금" },
  ];

  return (
    <div className="border-b border-border py-3">
      <CategoryPills
        categories={categories}
        onCategorySelect={(id) => console.log("Selected:", id)}
      />
    </div>
  );
}
