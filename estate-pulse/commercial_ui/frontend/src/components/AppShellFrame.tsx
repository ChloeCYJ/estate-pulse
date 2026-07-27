import type { ReactNode } from "react";

type AppShellFrameProps = {
  children: ReactNode;
};

export function AppShellFrame({ children }: AppShellFrameProps) {
  return <div className="ep-shell">{children}</div>;
}
