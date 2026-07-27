import { createRoot, type Root } from "react-dom/client";
import type { FrontendRenderer } from "@streamlit/component-v2-lib";

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
        onNavigationSelected={(target) => {
          component.setTriggerValue("navigation_selected", { target });
        }}
      />
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
