import { SourceLink } from "../SourceLink";

export default function SourceLinkExample() {
  return (
    <div className="p-4 bg-card border border-card-border rounded-2xl max-w-md space-y-2">
      <SourceLink title="2025학년도 수강신청 공지 바로가기" url="#" />
      <SourceLink title="학사안내(수강신청) PDF 열기" url="#" />
      <SourceLink title="종합정보시스템 수강신청 페이지" url="#" />
    </div>
  );
}
