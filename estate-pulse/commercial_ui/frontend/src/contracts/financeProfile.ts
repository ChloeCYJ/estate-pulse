import type { CommercialAuthViewModel } from "./auth";

export type FinanceProfileForm = {
  cash_amount_eok: number;
  annual_income_eok: number;
  interest_rate_percent: number;
  credit_loan_balance_eok: number;
  other_loan_balance_eok: number;
  home_count: number;
  owned_real_estate_value_eok: number;
  owned_real_estate_debt_eok: number;
  use_manual_ltv: boolean;
  manual_ltv_rate: number | null;
};

export type FinanceProfileViewModel = {
  page_status: "empty" | "ready" | "saving" | "validation_error" | "storage_error" | "auth_required";
  form: FinanceProfileForm;
  summary: {
    total_assets: number;
    total_debt: number;
    net_worth: number;
    home_count: number;
  };
  field_errors: Record<string, string>;
  notice: { level: "info" | "warning" | "error"; code: string; message: string } | null;
};

export type FinanceProfileEnvelope = {
  page: "finance-profile";
  view_model: FinanceProfileViewModel;
  auth: CommercialAuthViewModel;
  frontend_state: Record<string, unknown>;
  meta: { generated_at: string; locale: string };
};
