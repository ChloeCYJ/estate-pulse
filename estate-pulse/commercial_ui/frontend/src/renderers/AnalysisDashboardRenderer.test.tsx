import { fireEvent } from "@testing-library/dom";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { AnalysisDashboardViewModel } from "../contracts";
import { AnalysisDashboardErrorBoundary, AnalysisDashboardRenderer } from "./AnalysisDashboardRenderer";

const baseViewModel: AnalysisDashboardViewModel = {
  page_status: "ready",
  display_error: null,
  active_section: "decision",
  analysis_source: "saved",
  page_notice: null,
  property: {
    analysis_id: "41",
    complex_name: "Mapo Heights",
    area_label: "84.9m²",
    reference_price_label: "12.3억"
  },
  decision: {
    decision_status: "affordable",
    decision_title: "매수 가능",
    decision_description: "현재 자금으로 진입 가능합니다."
  },
  financing: {
    required_cash: { label: "총 필요 자금", value: 250000000, formatted: "2.5억" },
    cash_shortfall: { label: "부족 자금", value: 0, formatted: "0원" },
    expected_loan: { label: "예상 대출", value: 540000000, formatted: "5.4억" },
    monthly_payment: { label: "월 상환액", value: null, formatted: "-" }
  },
  risks: {
    items: []
  }
};

afterEach(() => {
  cleanup();
});

describe("AnalysisDashboardRenderer", () => {
  it("renders the property header and financing metrics", () => {
    const view = renderDashboard();

    expect(view.getByRole("heading", { level: 1, name: "Mapo Heights" })).toBeInTheDocument();
    expect(view.getByText("84.9m²")).toBeInTheDocument();
    expect(view.getByText("12.3억")).toBeInTheDocument();
    expect(view.getByText("2.5억")).toBeInTheDocument();
    expect(view.getByText("0원")).toBeInTheDocument();
  });

  it("emits save, comparison, and back triggers", () => {
    const onSaveRequested = vi.fn();
    const onComparisonRequested = vi.fn();
    const onBackToSearchRequested = vi.fn();
    const view = renderDashboard(
      { analysis_source: "live" },
      { onSaveRequested, onComparisonRequested, onBackToSearchRequested }
    );

    fireEvent.click(view.getByRole("button", { name: "저장" }));
    fireEvent.click(view.getByRole("button", { name: "비교로 이동" }));
    fireEvent.click(view.getByRole("button", { name: "단지 검색으로 돌아가기" }));

    expect(onSaveRequested).toHaveBeenCalledTimes(1);
    expect(onComparisonRequested).toHaveBeenCalledTimes(1);
    expect(onBackToSearchRequested).toHaveBeenCalledTimes(1);
  });

  it("shows the error boundary fallback and actions", () => {
    const onRetryRequested = vi.fn();
    const onBackToSearchRequested = vi.fn();
    const BrokenChild = () => {
      throw new Error("boom");
    };

    const view = render(
      <AnalysisDashboardErrorBoundary
        onRetryRequested={onRetryRequested}
        onBackToSearchRequested={onBackToSearchRequested}
      >
        <BrokenChild />
      </AnalysisDashboardErrorBoundary>
    );

    expect(view.getByText("분석 화면을 불러오지 못했습니다.")).toBeInTheDocument();
    fireEvent.click(view.getByRole("button", { name: "다시 시도" }));
    fireEvent.click(view.getByRole("button", { name: "단지 검색으로 돌아가기" }));
    expect(onRetryRequested).toHaveBeenCalledTimes(1);
    expect(onBackToSearchRequested).toHaveBeenCalledTimes(1);
  });
});

function renderDashboard(
  overrides: Partial<AnalysisDashboardViewModel> = {},
  handlers?: {
    onSaveRequested?: () => void;
    onComparisonRequested?: () => void;
    onBackToSearchRequested?: () => void;
    onRetryRequested?: () => void;
  }
) {
  return render(
    <AnalysisDashboardRenderer
      viewModel={{ ...baseViewModel, ...overrides }}
      onSaveRequested={handlers?.onSaveRequested ?? vi.fn()}
      onComparisonRequested={handlers?.onComparisonRequested ?? vi.fn()}
      onBackToSearchRequested={handlers?.onBackToSearchRequested ?? vi.fn()}
      onRetryRequested={handlers?.onRetryRequested ?? vi.fn()}
    />
  );
}
