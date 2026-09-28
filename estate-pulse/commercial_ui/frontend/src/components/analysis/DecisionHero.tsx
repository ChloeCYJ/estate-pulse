import type { AnalysisDashboardViewModel } from "../../contracts";

type DecisionHeroProps = {
  viewModel: AnalysisDashboardViewModel;
};

const metricOrder: Array<keyof AnalysisDashboardViewModel["financing"]> = [
  "required_cash",
  "expected_loan",
  "cash_shortfall",
  "monthly_payment"
];

export function DecisionHero({ viewModel }: DecisionHeroProps) {
  return (
    <section className="ep-card ep-analysis-hero" aria-labelledby="analysis-decision-title">
      <div className="ep-analysis-hero__copy">
        <span className={`ep-badge ep-badge--status-${viewModel.decision.decision_status}`}>
          {viewModel.analysis_source === "saved" ? "저장 분석" : "신규 분석"}
        </span>
        <h2 id="analysis-decision-title">{viewModel.decision.decision_title}</h2>
        <p>{viewModel.decision.decision_description}</p>
      </div>
      <div className="ep-analysis-metric-grid">
        {metricOrder.map((metricKey) => {
          const metric = viewModel.financing[metricKey];
          return (
            <article key={metricKey} className="ep-analysis-metric-card">
              <span className="ep-meta">{metric.label}</span>
              <strong>{metric.formatted}</strong>
            </article>
          );
        })}
      </div>
    </section>
  );
}
