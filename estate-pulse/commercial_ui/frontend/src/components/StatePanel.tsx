import type { ReactNode } from "react";

type StatePanelProps = {
  title: string;
  description: string;
  tone?: "default" | "danger";
  children?: ReactNode;
};

export function StatePanel({ title, description, tone = "default", children }: StatePanelProps) {
  return (
    <section className={`ep-card ep-state-panel ep-state-panel--${tone}`} aria-live="polite">
      <h3>{title}</h3>
      <p>{description}</p>
      {children}
    </section>
  );
}
