import type { CommercialAuthViewModel } from "../contracts";

type AccountActionsProps = {
  auth: CommercialAuthViewModel;
  onLoginRequested: () => void;
  onLogoutRequested: () => void;
  onFinanceProfileRequested: () => void;
};

export function AccountActions({
  auth,
  onLoginRequested,
  onLogoutRequested,
  onFinanceProfileRequested
}: AccountActionsProps) {
  if (auth.status === "authenticated") {
    return (
      <div className="ep-account-actions" aria-label="계정 메뉴">
        <span className="ep-account-actions__identity">
          {auth.display_name || auth.email || "회원"}
          {auth.provider ? <small>{auth.provider}</small> : null}
        </span>
        <button type="button" className="ep-account-button" onClick={onFinanceProfileRequested}>개인 자산</button>
        <button type="button" className="ep-account-button" onClick={onLogoutRequested}>로그아웃</button>
      </div>
    );
  }

  return (
    <div className="ep-account-actions" aria-label="계정 메뉴">
      {auth.status === "error" && auth.error ? <span className="ep-account-actions__error">{auth.error.message}</span> : null}
      <button type="button" className="ep-account-button ep-account-button--primary" onClick={onLoginRequested}>로그인</button>
    </div>
  );
}
