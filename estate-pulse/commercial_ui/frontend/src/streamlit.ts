import type { FrontendRendererArgs } from "@streamlit/component-v2-lib";

import type { CommercialUIEnvelope, CommercialUIState } from "./contracts";

export type CommercialUIRendererArgs = FrontendRendererArgs<
  CommercialUIState,
  CommercialUIEnvelope
>;
