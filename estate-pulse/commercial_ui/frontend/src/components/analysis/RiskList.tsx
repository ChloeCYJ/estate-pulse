type RiskListProps = {
  items: unknown[];
};

export function RiskList({ items }: RiskListProps) {
  if (items.length === 0) {
    return (
      <div className="ep-card ep-analysis-panel">
        <h3>리스크</h3>
        <p className="ep-analysis-empty">현재 표시할 리스크가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="ep-analysis-risk-list">
      {items.map((item, index) => {
        const normalized = normalizeRisk(item, index);
        return (
          <article key={normalized.key} className="ep-card ep-analysis-risk-card">
            <div className="ep-analysis-risk-card__head">
              <span className={`ep-badge ep-badge--risk-${normalized.severity}`}>{normalized.severityLabel}</span>
              <strong>{normalized.title}</strong>
            </div>
            {normalized.description ? <p>{normalized.description}</p> : null}
          </article>
        );
      })}
    </div>
  );
}

function normalizeRisk(item: unknown, index: number) {
  if (typeof item === "string") {
    return {
      key: `risk-${index}`,
      title: item,
      description: "",
      severity: "info",
      severityLabel: "안내"
    } as const;
  }

  if (item && typeof item === "object") {
    const raw = item as Record<string, unknown>;
    const severity = toSeverity(raw.severity);
    return {
      key: String(raw.code ?? raw.title ?? `risk-${index}`),
      title: String(raw.title ?? raw.code ?? `리스크 ${index + 1}`),
      description: String(raw.description ?? raw.evidence ?? ""),
      severity,
      severityLabel: severityLabel(severity)
    } as const;
  }

  return {
    key: `risk-${index}`,
    title: `리스크 ${index + 1}`,
    description: "",
    severity: "info",
    severityLabel: "안내"
  } as const;
}

function toSeverity(value: unknown): "high" | "medium" | "low" | "info" {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "high") {
    return "high";
  }
  if (normalized === "medium") {
    return "medium";
  }
  if (normalized === "low") {
    return "low";
  }
  return "info";
}

function severityLabel(value: "high" | "medium" | "low" | "info") {
  if (value === "high") {
    return "주의";
  }
  if (value === "medium") {
    return "확인";
  }
  if (value === "low") {
    return "참고";
  }
  return "안내";
}
