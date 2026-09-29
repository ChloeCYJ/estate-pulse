export type CommercialAuthStatus = "anonymous" | "authenticated" | "error";

export type CommercialAuthViewModel = {
  status: CommercialAuthStatus;
  display_name: string | null;
  email: string | null;
  provider: string | null;
  finance_profile_exists: boolean;
  error: { code: string; message: string } | null;
};

export const anonymousAuthViewModel: CommercialAuthViewModel = {
  status: "anonymous",
  display_name: null,
  email: null,
  provider: null,
  finance_profile_exists: false,
  error: null
};
