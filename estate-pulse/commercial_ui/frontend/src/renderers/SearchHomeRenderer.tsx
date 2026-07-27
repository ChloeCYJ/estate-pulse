import { useEffect, useState } from "react";

import type { NavigationItem, SearchHomeViewModel, SearchResultItem } from "../contracts";
import { AppShellFrame } from "../components/AppShellFrame";
import { RecentAnalysisCard } from "../components/RecentAnalysisCard";
import { SearchInput } from "../components/SearchInput";
import { StatePanel } from "../components/StatePanel";

type SearchHomeRendererProps = {
  viewModel: SearchHomeViewModel;
  onSearchSubmitted: (query: string) => void;
  onRecentAnalysisSelected: (analysisId: string) => void;
  onNavigationSelected: (target: string) => void;
};

export function SearchHomeRenderer({
  viewModel,
  onSearchSubmitted,
  onRecentAnalysisSelected,
  onNavigationSelected
}: SearchHomeRendererProps) {
  const [query, setQuery] = useState(viewModel.search_query);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const heroTitle = viewModel.service_description[0] ?? viewModel.service_title;
  const heroDescription = viewModel.service_description[1] ?? "";
  const recentCards = viewModel.recent_analyses.slice(0, 3);
  const shouldRenderResults = viewModel.search_status !== "idle";

  useEffect(() => {
    setQuery(viewModel.search_query);
  }, [viewModel.search_query]);

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
              <SearchResultsPanel viewModel={viewModel} searchQuery={viewModel.search_query || query} />
            </section>
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
  searchQuery
}: {
  viewModel: SearchHomeViewModel;
  searchQuery: string;
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
        <StatePanel
          title="검색에 실패했습니다"
          description={viewModel.display_error.message}
          tone="danger"
        />
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
        <StatePanel
          title="검색 결과가 없습니다"
          description="단지명 또는 주소를 다시 확인해 주세요."
        />
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
          <SearchResultCard key={item.result_id} item={item} />
        ))}
      </div>
    </>
  );
}

function SearchResultCard({ item }: { item: SearchResultItem }) {
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
    </article>
  );
}
