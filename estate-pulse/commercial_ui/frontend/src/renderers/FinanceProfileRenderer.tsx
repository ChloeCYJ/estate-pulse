import { useEffect, useState, type FormEvent } from "react";

import type { CommercialAuthViewModel, FinanceProfileForm, FinanceProfileViewModel } from "../contracts";
import { AccountActions } from "../components/AccountActions";
import { AppShellFrame } from "../components/AppShellFrame";
import { StatePanel } from "../components/StatePanel";
import { formatKoreanCurrency } from "../formatters/koreanCurrency";

type FinanceProfileRendererProps = {
  viewModel: FinanceProfileViewModel;
  auth: CommercialAuthViewModel;
  onSave: (payload: FinanceProfileForm) => void;
  onBack: () => void;
  onLoginRequested: () => void;
  onLogoutRequested: () => void;
};

export function FinanceProfileRenderer({
  viewModel,
  auth,
  onSave,
  onBack,
  onLoginRequested,
  onLogoutRequested
}: FinanceProfileRendererProps) {
  const [form, setForm] = useState<FinanceProfileForm>(viewModel.form);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setForm(viewModel.form);
    setIsSubmitting(viewModel.page_status === "saving");
  }, [viewModel.form, viewModel.page_status]);

  const updateNumber = (field: keyof FinanceProfileForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value === "" ? 0 : Number(value) }));
  };
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (auth.status !== "authenticated") {
      onLoginRequested();
      return;
    }
    setIsSubmitting(true);
    onSave(form);
  };

  return (
    <AppShellFrame>
      <div className="ep-page">
        <header className="ep-header">
          <div className="ep-header__inner">
            <span className="ep-wordmark">Estate Plus</span>
            <AccountActions auth={auth} onLoginRequested={onLoginRequested} onLogoutRequested={onLogoutRequested} onFinanceProfileRequested={() => undefined} />
          </div>
        </header>
        <main className="ep-layout ep-finance-layout">
          <div className="ep-section-head">
            <div><p className="ep-meta">내 정보</p><h1>개인 자산</h1></div>
            <button type="button" className="ep-button ep-button--ghost" onClick={onBack}>돌아가기</button>
          </div>

          {viewModel.notice ? <section className={`ep-card ep-finance-notice ep-finance-notice--${viewModel.notice.level}`}>{viewModel.notice.message}</section> : null}

          {viewModel.page_status === "auth_required" ? (
            <StatePanel title="로그인이 필요합니다" description="로그인 후 개인 자산을 등록하고 분석에 사용할 수 있습니다." />
          ) : (
            <>
              <section className="ep-finance-summary" aria-label="자산 요약">
                <SummaryCard label="총자산" value={formatKoreanCurrency(viewModel.summary.total_assets)} />
                <SummaryCard label="총부채" value={formatKoreanCurrency(viewModel.summary.total_debt)} />
                <SummaryCard label="순자산" value={formatKoreanCurrency(viewModel.summary.net_worth)} />
                <SummaryCard label="보유주택" value={`${viewModel.summary.home_count}채`} />
              </section>
              <form className="ep-card ep-finance-form" onSubmit={submit}>
                <h2>{viewModel.page_status === "empty" ? "개인 자산 등록" : "개인 자산 수정"}</h2>
                <div className="ep-finance-grid">
                  <NumberField label="보유 현금 (억원)" field="cash_amount_eok" value={form.cash_amount_eok} error={viewModel.field_errors.cash_amount_eok} onChange={updateNumber} />
                  <NumberField label="연소득 (억원)" field="annual_income_eok" value={form.annual_income_eok} error={viewModel.field_errors.annual_income_eok} onChange={updateNumber} />
                  <NumberField label="연 이자율 (%)" field="interest_rate_percent" value={form.interest_rate_percent} error={viewModel.field_errors.interest_rate_percent} onChange={updateNumber} />
                  <NumberField label="보유 주택 수" field="home_count" value={form.home_count} error={viewModel.field_errors.home_count} step={1} onChange={updateNumber} />
                  <NumberField label="보유 부동산 시가 (억원)" field="owned_real_estate_value_eok" value={form.owned_real_estate_value_eok} error={viewModel.field_errors.owned_real_estate_value_eok} onChange={updateNumber} />
                  <NumberField label="보유 부동산 대출 (억원)" field="owned_real_estate_debt_eok" value={form.owned_real_estate_debt_eok} error={viewModel.field_errors.owned_real_estate_debt_eok} onChange={updateNumber} />
                  <NumberField label="신용대출 잔액 (억원)" field="credit_loan_balance_eok" value={form.credit_loan_balance_eok} error={viewModel.field_errors.credit_loan_balance_eok} onChange={updateNumber} />
                  <NumberField label="기타 대출 잔액 (억원)" field="other_loan_balance_eok" value={form.other_loan_balance_eok} error={viewModel.field_errors.other_loan_balance_eok} onChange={updateNumber} />
                </div>
                <label className="ep-finance-checkbox">
                  <input type="checkbox" checked={form.use_manual_ltv} onChange={(event) => setForm((current) => ({ ...current, use_manual_ltv: event.target.checked, manual_ltv_rate: event.target.checked ? current.manual_ltv_rate ?? 0 : null }))} />
                  수동 LTV 사용
                </label>
                {form.use_manual_ltv ? <NumberField label="수동 LTV (0~1)" field="manual_ltv_rate" value={form.manual_ltv_rate ?? 0} error={viewModel.field_errors.manual_ltv_rate} step={0.05} onChange={updateNumber} /> : null}
                <div className="ep-finance-actions">
                  <button type="submit" className="ep-button ep-button--primary" disabled={isSubmitting}>{isSubmitting ? "저장 중…" : "저장"}</button>
                </div>
              </form>
            </>
          )}
        </main>
      </div>
    </AppShellFrame>
  );
}

function NumberField({ label, field, value, error, step = 0.1, onChange }: { label: string; field: keyof FinanceProfileForm; value: number; error?: string; step?: number; onChange: (field: keyof FinanceProfileForm, value: string) => void }) {
  return (
    <label className="ep-finance-field">
      <span>{label}</span>
      <input type="number" min="0" step={step} value={value} onChange={(event) => onChange(field, event.target.value)} aria-invalid={Boolean(error)} />
      {error ? <small className="ep-finance-field__error">{error}</small> : null}
    </label>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return <article className="ep-card ep-finance-summary__card"><span>{label}</span><strong>{value}</strong></article>;
}
