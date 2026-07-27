export function formatKoreanCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  const absValue = Math.abs(value);
  if (absValue >= 100_000_000) {
    const eok = Math.round((value / 100_000_000) * 10) / 10;
    return `${eok}억`;
  }
  return new Intl.NumberFormat("ko-KR").format(value);
}
