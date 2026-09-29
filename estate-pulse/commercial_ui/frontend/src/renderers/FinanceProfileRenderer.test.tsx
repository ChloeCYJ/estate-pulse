import { fireEvent } from "@testing-library/dom";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CommercialAuthViewModel, FinanceProfileViewModel } from "../contracts";
import { FinanceProfileRenderer } from "./FinanceProfileRenderer";

const authenticated: CommercialAuthViewModel = {
  status: "authenticated",
  display_name: "회원",
  email: "member@example.com",
  provider: "Google",
  finance_profile_exists: true,
  error: null
};

const viewModel: FinanceProfileViewModel = {
  page_status: "ready",
  form: {
    cash_amount_eok: 2,
    annual_income_eok: 1,
    interest_rate_percent: 4,
    credit_loan_balance_eok: 0.2,
    other_loan_balance_eok: 0,
    home_count: 1,
    owned_real_estate_value_eok: 10,
    owned_real_estate_debt_eok: 3,
    use_manual_ltv: false,
    manual_ltv_rate: null
  },
  summary: { total_assets: 1_200_000_000, total_debt: 320_000_000, net_worth: 880_000_000, home_count: 1 },
  field_errors: {},
  notice: null
};

afterEach(cleanup);

describe("FinanceProfileRenderer", () => {
  it("submits UI units and preserves numeric zero values", () => {
    const onSave = vi.fn();
    const view = render(<FinanceProfileRenderer viewModel={viewModel} auth={authenticated} onSave={onSave} onBack={vi.fn()} onLoginRequested={vi.fn()} onLogoutRequested={vi.fn()} />);

    fireEvent.change(view.getByLabelText("보유 현금 (억원)"), { target: { value: "3.5" } });
    fireEvent.click(view.getByRole("button", { name: "저장" }));

    expect(onSave).toHaveBeenCalledWith({ ...viewModel.form, cash_amount_eok: 3.5 });
    expect(view.getAllByDisplayValue("0").length).toBeGreaterThan(0);
  });

  it("offers login instead of saving for an anonymous user", () => {
    const onLoginRequested = vi.fn();
    const view = render(<FinanceProfileRenderer viewModel={{ ...viewModel, page_status: "auth_required" }} auth={{ ...authenticated, status: "anonymous", display_name: null }} onSave={vi.fn()} onBack={vi.fn()} onLoginRequested={onLoginRequested} onLogoutRequested={vi.fn()} />);

    fireEvent.click(view.getByRole("button", { name: "로그인" }));

    expect(onLoginRequested).toHaveBeenCalledOnce();
    expect(view.getByText("로그인이 필요합니다")).toBeInTheDocument();
  });
});
