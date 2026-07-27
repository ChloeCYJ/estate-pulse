export function formatAnalysisDateLabel(value: string): string {
  const normalized = value.trim();
  if (!normalized) {
    return "-";
  }

  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) {
    return normalized;
  }

  const [, year, month, day] = match;
  return `${year}.${month}.${day}`;
}
