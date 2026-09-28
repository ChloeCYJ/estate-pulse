import { Component, useEffect, useState, type ErrorInfo, type ReactNode } from "react";

import type { AnalysisDashboardViewModel, AnalysisSection } from "../contracts";
import { AppShellFrame } from "../components/AppShellFrame";
import { StatePanel } from "../components/StatePanel";
import { AnalysisSectionNav } from "../components/analysis/AnalysisSectionNav";
import { DecisionHero } from "../components/analysis/DecisionHero";
import { RiskList } from "../components/analysis/RiskList";

type AnalysisDashboardRendererProps = {
  viewModel: AnalysisDashboardViewModel;
  onSaveRequested: () => void;
  onComparisonRequested: () => void;
  onBackToSearchRequested: () => void;
  onRetryRequested: () => void;
};

type AnalysisDashboardErrorBoundaryProps = {
  children: ReactNode;
  onRetryRequested: () => void;
  onBackToSearchRequested: () => void;
};

type AnalysisDashboardErrorBoundaryState = {
  hasError: boolean;
};

export function AnalysisDashboardRenderer({
  viewModel,
  onSaveRequested,
  onComparisonRequested,
  onBackToSearchRequested,
  onRetryRequested
}: AnalysisDashboardRendererProps) {
  const [activeSection, setActiveSection] = useState<AnalysisSection>(viewModel.active_section);

  useEffect(() => {
    setActiveSection(viewModel.active_section);
  }, [viewModel.active_section]);

  return (
    <AppShellFrame>
      <div className="ep-page">
        <header className="ep-header">
          <div className="ep-header__inner">
            <span className="ep-wordmark">Estate Plus</span>
            <button type="button" className="ep-section-link" onClick={onBackToSearchRequested}>
              단지 검색으로 돌아가기
            </button>
          </div>
        </header>

        <main className="ep-layout ep-analysis-layout">
          <section className="ep-card ep-analysis-header" aria-labelledby="analysis-property-title">
            <div>
              <p className="ep-meta">분석 #{viewModel.property.analysis_id || "-"}</p>
              <h1 id="analysis-property-title">{viewModel.property.complex_name}</h1>
              <div className="ep-analysis-header__meta">
                <span>{viewModel.property.area_label}</span>
                <span>{viewModel.property.reference_price_label}</span>
              </div>
            </div>
            <div className="ep-analysis-actions">
              <button
                type="button"
                className="ep-button ep-button--ghost"
                onClick={onSaveRequested}
                disabled={viewModel.analysis_source === "saved"}
              >
                저장
              </button>
              <button type="button" className="ep-button ep-button--secondary" onClick={onComparisonRequested}>
                비교로 이동
              </button>
            </div>
          </section>

          {viewModel.page_notice ? (
            <section className={`ep-card ep-analysis-notice ep-analysis-notice--${viewModel.page_notice.level}`}>
              <strong>{viewModel.page_notice.message}</strong>
            </section>
          ) : null}

          {viewModel.page_status === "error" && viewModel.display_error ? (
            <section className="ep-analysis-error">
              <StatePanel
                title="분석 결과를 표시할 수 없습니다"
                description={viewModel.display_error.message}
                tone="danger"
              />
              <div className="ep-analysis-error__actions">
                <button type="button" className="ep-button ep-button--secondary" onClick={onRetryRequested}>
                  다시 시도
                </button>
                <button type="button" className="ep-button ep-button--ghost" onClick={onBackToSearchRequested}>
                  단지 검색으로 돌아가기
                </button>
              </div>
            </section>
          ) : (
            <>
              <DecisionHero viewModel={viewModel} />
              <AnalysisSectionNav activeSection={activeSection} onSelect={setActiveSection} />
              <AnalysisSectionContent activeSection={activeSection} viewModel={viewModel} />
            </>
          )}
        </main>
      </div>
    </AppShellFrame>
  );
}

export class AnalysisDashboardErrorBoundary extends Component<
  AnalysisDashboardErrorBoundaryProps,
  AnalysisDashboardErrorBoundaryState
> {
  public state: AnalysisDashboardErrorBoundaryState = {
    hasError: false
  };

  public static getDerivedStateFromError(): AnalysisDashboardErrorBoundaryState {
    return { hasError: true };
  }

  public componentDidCatch(_error: Error, _errorInfo: ErrorInfo): void {
    void _error;
    void _errorInfo;
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="ep-card ep-analysis-error-boundary">
          <h2>분석 화면을 불러오지 못했습니다.</h2>
          <div className="ep-analysis-error__actions">
            <button
              type="button"
              className="ep-button ep-button--secondary"
              onClick={() => {
                this.setState({ hasError: false });
                this.props.onRetryRequested();
              }}
            >
              다시 시도
            </button>
            <button
              type="button"
              className="ep-button ep-button--ghost"
              onClick={this.props.onBackToSearchRequested}
            >
              단지 검색으로 돌아가기
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function AnalysisSectionContent({
  activeSection,
  viewModel
}: {
  activeSection: AnalysisSection;
  viewModel: AnalysisDashboardViewModel;
}) {
  if (activeSection === "financing") {
    return (
      <section className="ep-card ep-analysis-panel" aria-labelledby="analysis-financing-title">
        <h3 id="analysis-financing-title">자금 계획</h3>
        <dl className="ep-analysis-definition-list">
          {Object.values(viewModel.financing).map((metric) => (
            <div key={metric.label} className="ep-analysis-definition-list__row">
              <dt>{metric.label}</dt>
              <dd>{metric.formatted}</dd>
            </div>
          ))}
        </dl>
      </section>
    );
  }

  if (activeSection === "risks") {
    return <RiskList items={viewModel.risks.items} />;
  }

  return (
    <section className="ep-card ep-analysis-panel" aria-labelledby="analysis-overview-title">
      <h3 id="analysis-overview-title">종합 분석</h3>
      <p>{viewModel.decision.decision_description}</p>
    </section>
  );
}
