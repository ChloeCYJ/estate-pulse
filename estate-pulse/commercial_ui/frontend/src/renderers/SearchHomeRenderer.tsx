import { useEffect, useRef, useState, type RefObject } from "react";

import type {
  NavigationItem,
  PendingAnalysis,
  PendingAreaOption,
  SearchHomeViewModel,
  SearchResultItem
} from "../contracts";
import { AppShellFrame } from "../components/AppShellFrame";
import { RecentAnalysisCard } from "../components/RecentAnalysisCard";
import { SearchInput } from "../components/SearchInput";
import { StatePanel } from "../components/StatePanel";

type SearchHomeRendererProps = {
  viewModel: SearchHomeViewModel;
  onSearchSubmitted: (query: string) => void;
  onRecentAnalysisSelected: (analysisId: string) => void;
  onSearchResultSelected: (
    resultType: "registered_complex" | "address_candidate",
    resultId: string
  ) => void;
  onAnalysisRequested: (payload: {
    complex_id: number;
    area_bucket: number;
    listing_id: number | null;
  }) => void;
  onNavigationSelected: (target: string) => void;
};

export function SearchHomeRenderer({
  viewModel,
  onSearchSubmitted,
  onRecentAnalysisSelected,
  onSearchResultSelected,
  onAnalysisRequested,
  onNavigationSelected
}: SearchHomeRendererProps) {
  const [query, setQuery] = useState(viewModel.search_query);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedAreaBucket, setSelectedAreaBucket] = useState<number | null>(
    viewModel.pending_analysis?.selected_area_bucket ?? null
  );
  const [selectedListingId, setSelectedListingId] = useState<number | null>(null);
  const autoSubmitKeyRef = useRef<string | null>(null);
  const pendingAnalysisPanelRef = useRef<HTMLElement | null>(null);
  const lastScrolledPendingAnalysisIdRef = useRef<number | null>(null);
  const pendingAnalysisId = viewModel.pending_analysis?.complex_id ?? null;
  const heroTitle = viewModel.service_description[0] ?? viewModel.service_title;
  const heroDescription = viewModel.service_description[1] ?? "";
  const recentCards = viewModel.recent_analyses.slice(0, 3);
  const shouldRenderResults = viewModel.search_status !== "idle";
  const selectedAreaOption = resolveSelectedAreaOption(viewModel.pending_analysis, selectedAreaBucket);

  useEffect(() => {
    setQuery(viewModel.search_query);
  }, [viewModel.search_query]);

  useEffect(() => {
    setSelectedAreaBucket(viewModel.pending_analysis?.selected_area_bucket ?? null);
    setSelectedListingId(viewModel.pending_analysis?.area_options[0]?.listing_options[0]?.listing_id ?? null);
  }, [viewModel.pending_analysis]);

  useEffect(() => {
    if (!selectedAreaOption) {
      setSelectedListingId(null);
      return;
    }
    if (!selectedAreaOption.listing_options.some((option) => option.listing_id === selectedListingId)) {
      setSelectedListingId(selectedAreaOption.listing_options[0]?.listing_id ?? null);
    }
  }, [selectedAreaOption, selectedListingId]);

  useEffect(() => {
    if (pendingAnalysisId === null) {
      lastScrolledPendingAnalysisIdRef.current = null;
      return;
    }
    if (lastScrolledPendingAnalysisIdRef.current === pendingAnalysisId) {
      return;
    }

    lastScrolledPendingAnalysisIdRef.current = pendingAnalysisId;
    pendingAnalysisPanelRef.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }, [pendingAnalysisId]);

  useEffect(() => {
    if (!viewModel.pending_analysis?.auto_submit || !selectedAreaOption) {
      autoSubmitKeyRef.current = null;
      return;
    }

    const requestKey = [
      viewModel.pending_analysis.complex_id,
      selectedAreaOption.area_bucket,
      selectedListingId ?? "transaction"
    ].join(":");
    if (autoSubmitKeyRef.current === requestKey) {
      return;
    }

    autoSubmitKeyRef.current = requestKey;
    onAnalysisRequested({
      complex_id: viewModel.pending_analysis.complex_id,
      area_bucket: selectedAreaOption.area_bucket,
      listing_id: selectedListingId
    });
  }, [onAnalysisRequested, selectedAreaOption, selectedListingId, viewModel.pending_analysis]);

  return (
    <AppShellFrame>
      <div className="ep-page">
        <header className="ep-header">
          <div className="ep-header__inner">
            <span className="ep-wordmark">{viewModel.service_title}</span>
            <button
              type="button"
              className="ep-nav-toggle"
              aria-expanded={isMobileMenuOpen}
              aria-controls="search-home-navigation"
              onClick={() => setIsMobileMenuOpen((current) => !current)}
            >
              메뉴
            </button>
            <nav
              id="search-home-navigation"
              className={`ep-topnav${isMobileMenuOpen ? " is-open" : ""}`}
              aria-label="사용자 메뉴"
            >
              {viewModel.navigation.map((item) => (
                <NavigationButton
                  key={item.id}
                  item={item}
                  onSelect={() => {
                    setIsMobileMenuOpen(false);
                    onNavigationSelected(item.id);
                  }}
                />
              ))}
            </nav>
          </div>
        </header>

        <main className="ep-layout">
          <section className="ep-hero" aria-labelledby="search-home-title">
            <div className="ep-hero__content">
              <h1 id="search-home-title">{heroTitle}</h1>
              <p className="ep-hero__description">{heroDescription}</p>
            </div>
            <div className="ep-hero__search">
              <SearchInput
                value={query}
                onChange={setQuery}
                onSubmit={() => onSearchSubmitted(query)}
                disabled={viewModel.search_status === "loading"}
              />
            </div>
          </section>

          {shouldRenderResults ? (
            <section className="ep-results-section" aria-label="검색 결과">
              <SearchResultsPanel
                viewModel={viewModel}
                searchQuery={viewModel.search_query || query}
                onSearchResultSelected={onSearchResultSelected}
              />
            </section>
          ) : null}

          {viewModel.pending_analysis ? (
            <PendingAnalysisPanel
              panelRef={pendingAnalysisPanelRef}
              pendingAnalysis={viewModel.pending_analysis}
              searchStatus={viewModel.search_status}
              selectedAreaBucket={selectedAreaBucket}
              selectedListingId={selectedListingId}
              onAreaBucketChange={setSelectedAreaBucket}
              onListingIdChange={setSelectedListingId}
              onSubmit={() => {
                if (!selectedAreaOption) {
                  return;
                }
                onAnalysisRequested({
                  complex_id: viewModel.pending_analysis!.complex_id,
                  area_bucket: selectedAreaOption.area_bucket,
                  listing_id: selectedListingId
                });
              }}
            />
          ) : null}

          <section className="ep-recent-section" aria-labelledby="recent-analyses-title">
            <div className="ep-section-head">
              <h2 id="recent-analyses-title">최근 분석</h2>
              <button
                type="button"
                className="ep-section-link"
                onClick={() => onNavigationSelected("saved_analyses")}
              >
                전체 보기 <span>→</span>
              </button>
            </div>
            {recentCards.length > 0 ? (
              <div className="ep-recent-grid">
                {recentCards.map((item) => (
                  <RecentAnalysisCard
                    key={item.analysis_id}
                    item={item}
                    onSelect={onRecentAnalysisSelected}
                  />
                ))}
              </div>
            ) : (
              <StatePanel
                title="저장된 최근 분석이 없습니다"
                description="기존 분석을 저장하면 여기에서 빠르게 다시 확인할 수 있습니다."
              />
            )}
          </section>
        </main>
      </div>
    </AppShellFrame>
  );
}

function NavigationButton({
  item,
  onSelect
}: {
  item: NavigationItem;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className={`ep-topnav__item${item.active ? " is-active" : ""}`}
      aria-current={item.active ? "page" : undefined}
      onClick={onSelect}
    >
      {item.label}
    </button>
  );
}

function SearchResultsPanel({
  viewModel,
  searchQuery,
  onSearchResultSelected
}: {
  viewModel: SearchHomeViewModel;
  searchQuery: string;
  onSearchResultSelected: (
    resultType: "registered_complex" | "address_candidate",
    resultId: string
  ) => void;
}) {
  const normalizedQuery = searchQuery.trim();

  if (viewModel.search_status === "loading") {
    return (
      <>
        <div className="ep-section-head">
          <h2>검색 결과</h2>
          {normalizedQuery ? <span className="ep-meta">검색어: {normalizedQuery}</span> : null}
        </div>
        <div className="ep-results-list" data-testid="loading-state">
          <div className="ep-skeleton-card" />
          <div className="ep-skeleton-card" />
          <div className="ep-skeleton-card" />
        </div>
      </>
    );
  }

  if (viewModel.search_status === "error" && viewModel.display_error) {
    return (
      <>
        <div className="ep-section-head">
          <h2>검색 결과</h2>
          {normalizedQuery ? <span className="ep-meta">검색어: {normalizedQuery}</span> : null}
        </div>
        <StatePanel title="검색에 실패했습니다" description={viewModel.display_error.message} tone="danger" />
      </>
    );
  }

  if (viewModel.search_status === "no_results") {
    return (
      <>
        <div className="ep-section-head">
          <h2>검색 결과</h2>
          {normalizedQuery ? <span className="ep-meta">검색어: {normalizedQuery}</span> : null}
        </div>
        <StatePanel title="검색 결과가 없습니다" description="단지명이나 주소를 다시 확인해 주세요" />
      </>
    );
  }

  return (
    <>
      <div className="ep-section-head">
        <h2>검색 결과</h2>
        {normalizedQuery ? <span className="ep-meta">검색어: {normalizedQuery}</span> : null}
      </div>
      <div className="ep-results-list">
        {viewModel.search_results.map((item) => (
          <SearchResultCard
            key={item.result_id}
            item={item}
            onSelect={item.result_type === "registered_complex" ? onSearchResultSelected : null}
          />
        ))}
      </div>
    </>
  );
}

function SearchResultCard({
  item,
  onSelect
}: {
  item: SearchResultItem;
  onSelect: ((resultType: "registered_complex" | "address_candidate", resultId: string) => void) | null;
}) {
  return (
    <article className="ep-card ep-result-card">
      <div className="ep-result-card__head">
        <span className={`ep-badge${item.result_type === "registered_complex" ? " ep-badge--primary" : ""}`}>
          {item.result_type === "registered_complex" ? "등록 단지" : "주소 검색"}
        </span>
        <span className="ep-meta">{item.meta}</span>
      </div>
      <strong>{item.title || "-"}</strong>
      <p>{item.subtitle || "-"}</p>
      {onSelect ? (
        <button
          type="button"
          className="ep-result-card__action"
          onClick={() => onSelect(item.result_type, item.result_id)}
        >
          {item.title} 분석 대상 선택
        </button>
      ) : (
        <span className="ep-meta">등록된 단지에서만 바로 분석할 수 있습니다.</span>
      )}
    </article>
  );
}

function PendingAnalysisPanel({
  panelRef,
  pendingAnalysis,
  searchStatus,
  selectedAreaBucket,
  selectedListingId,
  onAreaBucketChange,
  onListingIdChange,
  onSubmit
}: {
  panelRef: RefObject<HTMLElement | null>;
  pendingAnalysis: PendingAnalysis;
  searchStatus: SearchHomeViewModel["search_status"];
  selectedAreaBucket: number | null;
  selectedListingId: number | null;
  onAreaBucketChange: (value: number) => void;
  onListingIdChange: (value: number | null) => void;
  onSubmit: () => void;
}) {
  const selectedAreaOption = resolveSelectedAreaOption(pendingAnalysis, selectedAreaBucket);
  const isLoading = searchStatus === "loading";

  return (
    <section
      ref={panelRef}
      className="ep-card ep-pending-analysis"
      aria-labelledby="pending-analysis-title"
    >
      <div className="ep-pending-analysis__head">
        <div>
          <h2 id="pending-analysis-title">{pendingAnalysis.complex_name}</h2>
          <p className="ep-meta">{pendingAnalysis.finance_profile_label}</p>
        </div>
        {isLoading ? <span className="ep-badge ep-badge--primary">분석 준비 중</span> : null}
      </div>
      <div className="ep-pending-analysis__grid">
        <label className="ep-pending-analysis__field">
          <span>면적</span>
          <select
            value={selectedAreaOption?.area_bucket ?? ""}
            onChange={(event) => onAreaBucketChange(Number(event.target.value))}
            disabled={isLoading}
          >
            {pendingAnalysis.area_options.map((option) => (
              <option key={option.area_bucket} value={option.area_bucket}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="ep-pending-analysis__field">
          <span>가격 기준</span>
          <select
            value={selectedListingId === null ? "transaction" : String(selectedListingId)}
            onChange={(event) => {
              const value = event.target.value;
              onListingIdChange(value === "transaction" ? null : Number(value));
            }}
            disabled={isLoading}
          >
            {(selectedAreaOption?.listing_options ?? []).map((option) => (
              <option
                key={option.listing_id === null ? "transaction" : option.listing_id}
                value={option.listing_id === null ? "transaction" : String(option.listing_id)}
              >
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="ep-pending-analysis__footer">
        <span className="ep-meta">
          거래 {selectedAreaOption?.sale_transaction_count ?? 0}건 · 매물 {selectedAreaOption?.listing_count ?? 0}건
        </span>
        <button type="button" className="ep-button ep-button--primary" disabled={isLoading} onClick={onSubmit}>
          분석 시작
        </button>
      </div>
    </section>
  );
}

function resolveSelectedAreaOption(
  pendingAnalysis: PendingAnalysis | null,
  selectedAreaBucket: number | null
): PendingAreaOption | null {
  if (!pendingAnalysis) {
    return null;
  }
  return (
    pendingAnalysis.area_options.find((option) => option.area_bucket === selectedAreaBucket) ??
    pendingAnalysis.area_options[0] ??
    null
  );
}
