import type { AnalysisSection } from "../../contracts";

type AnalysisSectionNavProps = {
  activeSection: AnalysisSection;
  onSelect: (section: AnalysisSection) => void;
};

const sections: Array<{ id: AnalysisSection; label: string }> = [
  { id: "decision", label: "종합 분석" },
  { id: "financing", label: "자금 계획" },
  { id: "risks", label: "리스크" }
];

export function AnalysisSectionNav({ activeSection, onSelect }: AnalysisSectionNavProps) {
  return (
    <nav className="ep-analysis-nav" aria-label="분석 섹션">
      {sections.map((section) => (
        <button
          key={section.id}
          type="button"
          className={`ep-analysis-nav__item${activeSection === section.id ? " is-active" : ""}`}
          aria-current={activeSection === section.id ? "page" : undefined}
          onClick={() => onSelect(section.id)}
        >
          {section.label}
        </button>
      ))}
    </nav>
  );
}
