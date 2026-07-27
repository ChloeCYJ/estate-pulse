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
  search_results: []
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
    view.getByRole("button", { name: "분석 시작" }).click();

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
          title: "서울숲트리마제",
          subtitle: "서울 성동구 왕십리로 83",
          meta: "등록된 단지"
        }
      ]
    });

    expect(view.getAllByRole("heading", { level: 2, name: "검색 결과" })).toHaveLength(1);
  });

  it("limits the recent analysis cards to three items", () => {
    const view = renderSearchHome({
      recent_analyses: [
        createRecentAnalysis("1", "서울숲1"),
        createRecentAnalysis("2", "서울숲2"),
        createRecentAnalysis("3", "서울숲3"),
        createRecentAnalysis("4", "서울숲4")
      ]
    });

    expect(view.getByRole("button", { name: "서울숲1 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.getByRole("button", { name: "서울숲2 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.getByRole("button", { name: "서울숲3 최근 분석 다시 보기" })).toBeInTheDocument();
    expect(view.queryByRole("button", { name: "서울숲4 최근 분석 다시 보기" })).not.toBeInTheDocument();
  });
});

function renderSearchHome(
  overrides: Partial<SearchHomeViewModel> = {},
  handlers?: {
    onSearchSubmitted?: (query: string) => void;
    onRecentAnalysisSelected?: (analysisId: string) => void;
    onNavigationSelected?: (target: string) => void;
  }
) {
  return render(
    <SearchHomeRenderer
      viewModel={{ ...baseViewModel, ...overrides }}
      onSearchSubmitted={handlers?.onSearchSubmitted ?? vi.fn()}
      onRecentAnalysisSelected={handlers?.onRecentAnalysisSelected ?? vi.fn()}
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
