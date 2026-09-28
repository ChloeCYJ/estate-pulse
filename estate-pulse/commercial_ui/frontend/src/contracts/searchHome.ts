export type SearchStatus = "idle" | "loading" | "success" | "no_results" | "error";

export type NavigationItem = {
  id: string;
  label: string;
  active: boolean;
};

export type RecentAnalysisCard = {
  analysis_id: string;
  complex_name: string;
  area_label: string;
  reference_price_label: string;
  analyzed_at_label: string;
  location_label: string;
};

export type SearchResultItem = {
  result_id: string;
  result_type: "registered_complex" | "address_candidate";
  title: string;
  subtitle: string;
  meta: string;
};

export type DisplayError = {
  code: string;
  message: string;
};

export type PendingListingOption = {
  listing_id: number | null;
  label: string;
};

export type PendingAreaOption = {
  area_bucket: number;
  label: string;
  listing_count: number;
  sale_transaction_count: number;
  listing_options: PendingListingOption[];
};

export type PendingAnalysis = {
  complex_id: number;
  complex_name: string;
  finance_profile_label: string;
  auto_submit: boolean;
  selected_area_bucket: number;
  area_options: PendingAreaOption[];
};

export type SearchHomeViewModel = {
  service_title: string;
  service_description: string[];
  search_query: string;
  search_status: SearchStatus;
  navigation: NavigationItem[];
  empty_state: boolean;
  display_error: DisplayError | null;
  recent_analyses: RecentAnalysisCard[];
  search_results: SearchResultItem[];
  pending_analysis: PendingAnalysis | null;
};

export type SearchHomeEnvelope = {
  page: "search-home";
  view_model: SearchHomeViewModel;
  frontend_state: Record<string, unknown>;
  meta: {
    generated_at: string;
    locale: string;
  };
};
