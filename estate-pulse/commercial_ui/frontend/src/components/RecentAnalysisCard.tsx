import type { RecentAnalysisCard as RecentAnalysisCardModel } from "../contracts";
import { formatAnalysisDateLabel } from "../formatters/analysisDate";

type RecentAnalysisCardProps = {
  item: RecentAnalysisCardModel;
  onSelect: (analysisId: string) => void;
};

export function RecentAnalysisCard({ item, onSelect }: RecentAnalysisCardProps) {
  const formattedDate = formatAnalysisDateLabel(item.analyzed_at_label || "");

  return (
    <button
      type="button"
      className="ep-card ep-recent-card"
      onClick={() => onSelect(item.analysis_id)}
      aria-label={`${item.complex_name} 최근 분석 다시 보기`}
    >
      <div className="ep-recent-card__head">
        <span className="ep-badge">최근 분석</span>
      </div>
      <strong className="ep-recent-card__title">{item.complex_name || "-"}</strong>
      <p className="ep-recent-card__meta">{item.location_label || "-"}</p>
      <p className="ep-recent-card__price">{item.reference_price_label || "-"}</p>
      <div className="ep-recent-card__details">
        <span>{item.area_label || "-"}</span>
        <span>{formattedDate}</span>
      </div>
      <div className="ep-recent-card__footer">
        <span className="ep-recent-card__cta">분석 다시 보기</span>
      </div>
    </button>
  );
}
