import type { CommercialAuthViewModel } from "./auth";

export type DashboardPageStatus = "ready" | "loading" | "error";
export type AnalysisSource = "live" | "saved";
export type AnalysisSection = "decision" | "financing" | "risks";

export type DashboardDisplayError = {
  code: string;
  message: string;
};

export type DashboardMetric = {
  label: string;
  value: number | null;
  formatted: string;
};

export type PageNotice = {
  level: "info" | "warning" | "error";
  code: string;
  message: string;
};

export type AnalysisDashboardViewModel = {
  page_status: DashboardPageStatus;
  display_error: DashboardDisplayError | null;
  active_section: AnalysisSection;
  analysis_source: AnalysisSource;
  page_notice: PageNotice | null;
  property: {
    analysis_id: string;
    complex_name: string;
    area_label: string;
    reference_price_label: string;
  };
  decision: {
    decision_status: "affordable" | "shortfall" | "error";
    decision_title: string;
    decision_description: string;
  };
  financing: {
    required_cash: DashboardMetric;
    cash_shortfall: DashboardMetric;
    expected_loan: DashboardMetric;
    monthly_payment: DashboardMetric;
  };
  risks: {
    items: unknown[];
  };
};

export type AnalysisDashboardEnvelope = {
  page: "analysis-dashboard";
  view_model: AnalysisDashboardViewModel;
  auth: CommercialAuthViewModel;
  frontend_state: Record<string, unknown>;
  meta: {
    generated_at: string;
    locale: string;
  };
};
