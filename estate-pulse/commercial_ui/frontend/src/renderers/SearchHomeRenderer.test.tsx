import { fireEvent } from "@testing-library/dom";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { SearchHomeViewModel } from "../contracts";
import { SearchHomeRenderer } from "./SearchHomeRenderer";

const baseViewModel: SearchHomeViewModel = {
  service_title: "Estate Plus",
  service_description: [
    "서울 아파트를 숫자로 판단하세요",
    "거래가와 자금 조건을 함께 반영해 바로 검토할 단지를 빠르게 좁혀드립니다."
  ],
  search_query: "",
  search_status: "idle",
  navigation: [
    { id: "search", label: "단지 검색", active: true },
    { id: "comparison", label: "단지 비교", active: false },
    { id: "saved_analyses", label: "저장한 분석", active: false }
  ],
  empty_state: true,
  display_error: null,
  recent_analyses: [],
  search_results: [],
  pending_analysis: null
};

afterEach(() => {
  cleanup();
});

describe("SearchHomeRenderer", () => {
  it("renders the idle state with a single headline and wordmark", () => {
    const view = renderSearchHome();

    expect(view.getAllByText("Estate Plus")).toHaveLength(1);
    expect(view.getAllByRole("heading", { level: 1, name: "서울 아파트를 숫자로 판단하세요" })).toHaveLength(1);
    expect(view.getByPlaceholderText("단지명이나 주소를 입력하세요")).toBeInTheDocument();
    expect(view.queryByText("검색을 시작해 주세요")).not.toBeInTheDocument();
    expect(view.queryByRole("heading", { level: 2, name: "검색 결과" })).not.toBeInTheDocument();
    expect(view.getAllByRole("heading", { level: 2, name: "최근 분석" })).toHaveLength(1);
    expect(view.getByRole("button", { name: "전체 보기 →" })).toBeInTheDocument();
  });

  it("renders recent analysis cards when data is present", () => {
    const view = renderSearchHome({
      recent_analyses: [
        {
          analysis_id: "11",
          complex_name: "마포래미안푸르지오",
          area_label: "84.9m²",
          reference_price_label: "12.3억",
          analyzed_at_label: "2026-07-26 09:30",
          location_label: "서울 마포구 아현동"
        }
      ]
    });

    expect(view.getByRole("button", { name: "마포래미안푸르지오 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.getByText("12.3억")).toBeInTheDocument();
    expect(view.getByText("2026.07.26")).toBeInTheDocument();
    expect(view.getByText("분석 다시 보기")).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    const view = renderSearchHome({
      search_status: "loading"
    });

    expect(view.getByTestId("loading-state")).toBeInTheDocument();
  });

  it("emits search result selection for registered complexes", () => {
    const onSearchResultSelected = vi.fn();
    const view = renderSearchHome(
      {
        search_query: "공덕",
        search_status: "success",
        search_results: [
          {
            result_id: "complex:7",
            result_type: "registered_complex",
            title: "Test Complex",
            subtitle: "Seoul",
            meta: "registered"
          }
        ]
      },
      { onSearchResultSelected }
    );

    fireEvent.click(view.getByRole("button", { name: "Test Complex 분석 대상 선택" }));

    expect(onSearchResultSelected).toHaveBeenCalledWith("registered_complex", "complex:7");
  });

  it("renders the pending analysis picker and emits analysis payload", () => {
    const onAnalysisRequested = vi.fn();
    const view = renderSearchHome(
      {
        search_query: "test",
        search_status: "success",
        pending_analysis: {
          complex_id: 7,
          complex_name: "Test Complex",
          finance_profile_label: "Latest profile",
          auto_submit: false,
          selected_area_bucket: 84.9,
          area_options: [
            {
              area_bucket: 84.9,
              label: "84.9m²",
              listing_count: 1,
              sale_transaction_count: 3,
              listing_options: [
                { listing_id: null, label: "최근 거래 기준" },
                { listing_id: 11, label: "#11 | 9.0억" }
              ]
            }
          ]
        }
      },
      { onAnalysisRequested }
    );

    expect(view.getByText("Test Complex")).toBeInTheDocument();
    fireEvent.click(view.getAllByRole("button", { name: "분석 시작" })[0]);

    expect(onAnalysisRequested).toHaveBeenCalledWith({
      complex_id: 7,
      area_bucket: 84.9,
      listing_id: null
    });
  });

  it("scrolls the pending analysis picker into view when a target is selected", () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView
    });
    const view = renderSearchHome({
      search_query: "행당동",
      search_status: "success"
    });
    const pendingViewModel = {
      ...baseViewModel,
      search_query: "행당동",
      search_status: "success" as const,
      pending_analysis: {
        complex_id: 7,
        complex_name: "행당 한진타운",
        finance_profile_label: "최근 자금 프로필 #10",
        auto_submit: false,
        selected_area_bucket: 60,
        area_options: [
          {
            area_bucket: 60,
            label: "60.0m²",
            listing_count: 0,
            sale_transaction_count: 33,
            listing_options: [{ listing_id: null, label: "최근 거래 기준" }]
          }
        ]
      }
    };

    view.rerender(
      <SearchHomeRenderer
        viewModel={pendingViewModel}
        onSearchSubmitted={vi.fn()}
        onRecentAnalysisSelected={vi.fn()}
        onSearchResultSelected={vi.fn()}
        onAnalysisRequested={vi.fn()}
        onNavigationSelected={vi.fn()}
      />
    );

    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });

    view.rerender(
      <SearchHomeRenderer
        viewModel={pendingViewModel}
        onSearchSubmitted={vi.fn()}
        onRecentAnalysisSelected={vi.fn()}
        onSearchResultSelected={vi.fn()}
        onAnalysisRequested={vi.fn()}
        onNavigationSelected={vi.fn()}
      />
    );

    expect(scrollIntoView).toHaveBeenCalledOnce();
    delete (HTMLElement.prototype as Partial<HTMLElement>).scrollIntoView;
  });

  it("renders the no-results state", () => {
    const view = renderSearchHome({
      search_query: "없는단지",
      search_status: "no_results"
    });

    expect(view.getByText("검색 결과가 없습니다")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    const view = renderSearchHome({
      search_query: "오류단지",
      search_status: "error",
      display_error: {
        code: "search_failed",
        message: "검색 중 오류가 발생했습니다."
      }
    });

    expect(view.getByText("검색에 실패했습니다")).toBeInTheDocument();
    expect(view.getByText("검색 중 오류가 발생했습니다.")).toBeInTheDocument();
  });

  it("emits the search trigger with the current query", () => {
    const onSearchSubmitted = vi.fn();
    const view = renderSearchHome({}, { onSearchSubmitted });
    const input = view.getByPlaceholderText("단지명이나 주소를 입력하세요");

    fireEvent.change(input, { target: { value: "성수" } });
    view.getByRole("button", { name: "검색" }).click();

    expect(onSearchSubmitted).toHaveBeenCalledWith("성수");
  });

  it("emits recent analysis selection events", () => {
    const onRecentAnalysisSelected = vi.fn();
    const view = renderSearchHome(
      {
        recent_analyses: [
          {
            analysis_id: "11",
            complex_name: "마포래미안푸르지오",
            area_label: "84.9m²",
            reference_price_label: "12.3억",
            analyzed_at_label: "2026-07-26 09:30",
            location_label: "서울 마포구 아현동"
          }
        ]
      },
      { onRecentAnalysisSelected }
    );

    view.getByRole("button", { name: "마포래미안푸르지오 최근 분석 다시 보기" }).click();

    expect(onRecentAnalysisSelected).toHaveBeenCalledWith("11");
  });

  it("keeps top navigation keyboard accessible", () => {
    const onNavigationSelected = vi.fn();
    const view = renderSearchHome({}, { onNavigationSelected });

    view.getByRole("button", { name: "단지 비교" }).click();

    expect(onNavigationSelected).toHaveBeenCalledWith("comparison");
  });

  it("routes the recent section action to saved analyses", () => {
    const onNavigationSelected = vi.fn();
    const view = renderSearchHome({}, { onNavigationSelected });

    view.getByRole("button", { name: "전체 보기 →" }).click();

    expect(onNavigationSelected).toHaveBeenCalledWith("saved_analyses");
  });

  it("renders the search result heading once when results exist", () => {
    const view = renderSearchHome({
      search_query: "성수",
      search_status: "success",
      search_results: [
        {
          result_id: "complex:1",
          result_type: "registered_complex",
          title: "서울숲센트럴파크",
          subtitle: "서울 성동구 왕십리로 83",
          meta: "등록 단지"
        }
      ]
    });

    expect(view.getAllByRole("heading", { level: 2, name: "검색 결과" })).toHaveLength(1);
  });

  it("limits the recent analysis cards to three items", () => {
    const view = renderSearchHome({
      recent_analyses: [
        createRecentAnalysis("1", "서울숲 1차"),
        createRecentAnalysis("2", "서울숲 2차"),
        createRecentAnalysis("3", "서울숲 3차"),
        createRecentAnalysis("4", "서울숲 4차")
      ]
    });

    expect(view.getByRole("button", { name: "서울숲 1차 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.getByRole("button", { name: "서울숲 2차 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.getByRole("button", { name: "서울숲 3차 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.queryByRole("button", { name: "서울숲 4차 최근 분석 다시 보기" })).not.toBeInTheDocument();
  });
});

function renderSearchHome(
  overrides: Partial<SearchHomeViewModel> = {},
  handlers?: {
    onSearchSubmitted?: (query: string) => void;
    onRecentAnalysisSelected?: (analysisId: string) => void;
    onSearchResultSelected?: (resultType: "registered_complex" | "address_candidate", resultId: string) => void;
    onAnalysisRequested?: (payload: {
      complex_id: number;
      area_bucket: number;
      listing_id: number | null;
    }) => void;
    onNavigationSelected?: (target: string) => void;
  }
) {
  return render(
    <SearchHomeRenderer
      viewModel={{ ...baseViewModel, ...overrides }}
      onSearchSubmitted={handlers?.onSearchSubmitted ?? vi.fn()}
      onRecentAnalysisSelected={handlers?.onRecentAnalysisSelected ?? vi.fn()}
      onSearchResultSelected={handlers?.onSearchResultSelected ?? vi.fn()}
      onAnalysisRequested={handlers?.onAnalysisRequested ?? vi.fn()}
      onNavigationSelected={handlers?.onNavigationSelected ?? vi.fn()}
    />
  );
}

function createRecentAnalysis(analysisId: string, complexName: string) {
  return {
    analysis_id: analysisId,
    complex_name: complexName,
    area_label: "84.9m²",
    reference_price_label: "12.3억",
    analyzed_at_label: "2026-07-26 09:30",
    location_label: "서울 마포구 아현동"
  };
}
