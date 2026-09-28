export type {
  DisplayError,
  NavigationItem,
  PendingAnalysis,
  PendingAreaOption,
  PendingListingOption,
  RecentAnalysisCard,
  SearchHomeEnvelope,
  SearchHomeViewModel,
  SearchResultItem,
  SearchStatus
} from "./searchHome";
export type {
  AnalysisDashboardEnvelope,
  AnalysisDashboardViewModel,
  AnalysisSection,
  AnalysisSource,
  DashboardDisplayError,
  DashboardMetric,
  DashboardPageStatus,
  PageNotice
} from "./analysisDashboard";

import type { AnalysisDashboardEnvelope } from "./analysisDashboard";
import type { SearchHomeEnvelope } from "./searchHome";

export type CommercialUIEnvelope = SearchHomeEnvelope | AnalysisDashboardEnvelope;

export type CommercialUIState = {
  search_submitted: { query: string } | null;
  recent_analysis_selected: { analysis_id: string } | null;
  search_result_selected: { result_type: "registered_complex" | "address_candidate"; result_id: string } | null;
  analysis_requested: { complex_id: number; area_bucket: number; listing_id: number | null } | null;
  navigation_selected: { target: string } | null;
  save_requested: Record<string, never> | null;
  comparison_requested: Record<string, never> | null;
  back_to_search_requested: Record<string, never> | null;
  retry_requested: Record<string, never> | null;
};
