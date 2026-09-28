import { createRoot, type Root } from "react-dom/client";
import type { FrontendRenderer } from "@streamlit/component-v2-lib";

import { AnalysisDashboardErrorBoundary, AnalysisDashboardRenderer } from "./renderers/AnalysisDashboardRenderer";
import { SearchHomeRenderer } from "./renderers/SearchHomeRenderer";
import type { CommercialUIEnvelope, CommercialUIState } from "./contracts";
import "./design-system/global.css";

type RootContainer = Element | DocumentFragment;

const roots = new WeakMap<RootContainer, Root>();

const renderer: FrontendRenderer<CommercialUIState, CommercialUIEnvelope> = (component) => {
  const root = getOrCreateRoot(component.parentElement);
  const envelope = component.data;

  if (envelope.page === "search-home") {
    root.render(
      <SearchHomeRenderer
        viewModel={envelope.view_model}
        onSearchSubmitted={(query) => {
          const trimmed = query.trim();
          if (!trimmed) {
            return;
          }
          component.setTriggerValue("search_submitted", { query: trimmed });
        }}
        onRecentAnalysisSelected={(analysisId) => {
          component.setTriggerValue("recent_analysis_selected", { analysis_id: analysisId });
        }}
        onSearchResultSelected={(resultType, resultId) => {
          component.setTriggerValue("search_result_selected", {
            result_type: resultType,
            result_id: resultId
          });
        }}
        onAnalysisRequested={(payload) => {
          component.setTriggerValue("analysis_requested", payload);
        }}
        onNavigationSelected={(target) => {
          component.setTriggerValue("navigation_selected", { target });
        }}
      />
    );
  }

  if (envelope.page === "analysis-dashboard") {
    root.render(
      <AnalysisDashboardErrorBoundary
        onRetryRequested={() => {
          component.setTriggerValue("retry_requested", {});
        }}
        onBackToSearchRequested={() => {
          component.setTriggerValue("back_to_search_requested", {});
        }}
      >
        <AnalysisDashboardRenderer
          viewModel={envelope.view_model}
          onSaveRequested={() => {
            component.setTriggerValue("save_requested", {});
          }}
          onComparisonRequested={() => {
            component.setTriggerValue("comparison_requested", {});
          }}
          onBackToSearchRequested={() => {
            component.setTriggerValue("back_to_search_requested", {});
          }}
          onRetryRequested={() => {
            component.setTriggerValue("retry_requested", {});
          }}
        />
      </AnalysisDashboardErrorBoundary>
    );
  }

  return () => {
    const activeRoot = roots.get(component.parentElement);
    if (activeRoot) {
      activeRoot.unmount();
      roots.delete(component.parentElement);
    }
  };
};

export default renderer;

function getOrCreateRoot(parentElement: HTMLElement | ShadowRoot): Root {
  const container: RootContainer = parentElement;
  const existingRoot = roots.get(container);
  if (existingRoot) {
    return existingRoot;
  }
  const root = createRoot(container);
  roots.set(container, root);
  return root;
}
