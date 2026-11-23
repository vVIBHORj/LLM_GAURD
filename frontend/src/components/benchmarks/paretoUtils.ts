import type { BenchmarkReport } from '../../types/index.ts';
import type { ParetoChartPoint } from './ParetoChart.tsx';

/**
 * Validates and filters points for chart plotting.
 * Requires finite, non-negative numbers. Zero throughput (0.0) and zero accuracy (0.0)
 * are retained as genuine measurements. Null, undefined, negative, or non-finite values are rejected.
 */
export function isValidChartPoint(p: { tokens_per_sec?: number | null; accuracy_rate?: number | null }): boolean {
  if (p.tokens_per_sec == null || p.accuracy_rate == null) {
    return false;
  }
  if (!Number.isFinite(p.tokens_per_sec) || !Number.isFinite(p.accuracy_rate)) {
    return false;
  }
  if (p.tokens_per_sec < 0 || p.accuracy_rate < 0 || p.accuracy_rate > 1.0) {
    return false;
  }
  return true;
}

/**
 * Filters array of points keeping only valid plottable points.
 */
export function filterValidChartPoints(points: ParetoChartPoint[]): ParetoChartPoint[] {
  return points.filter(isValidChartPoint);
}

/**
 * Transforms a BenchmarkReport into plottable ParetoChartPoint items.
 * Uses backend-determined Pareto frontier membership without recalculation.
 */
export function transformReportToChartPoints(
  report: BenchmarkReport,
  paretoModelIds?: Set<string>
): ParetoChartPoint[] {
  const pIds =
    paretoModelIds ||
    new Set(
      (report.pareto_frontier || [])
        .filter((p) => p.is_pareto_optimal)
        .map((p) => p.model_id)
    );

  return (report.results || [])
    .filter(
      (r) =>
        r.status === 'BENCHMARKED' &&
        isValidChartPoint({ tokens_per_sec: r.speed_tokens_sec, accuracy_rate: r.accuracy_score })
    )
    .map((r) => ({
      model_id: r.model_id,
      run_id: r.run_id,
      tokens_per_sec: r.speed_tokens_sec!,
      accuracy_rate: r.accuracy_score!,
      peak_vram_mb: r.peak_vram_mb,
      peak_ollama_vram_mb: r.peak_ollama_vram_mb,
      gpu_name: r.gpu_name,
      gpu_source: r.gpu_source,
      is_pareto: pIds.has(r.model_id),
      status: r.status,
    }));
}

/**
 * Sorts pareto-optimal frontier points in strictly ascending throughput order for line rendering.
 */
export function sortParetoFrontier(points: ParetoChartPoint[]): ParetoChartPoint[] {
  return points
    .filter((p) => p.is_pareto && isValidChartPoint(p))
    .sort((a, b) => a.tokens_per_sec - b.tokens_per_sec);
}

/**
 * Computes dynamic chart coordinate bounds from valid empirical points.
 * Handles single points, identical points, and zero bounds safely without division by zero.
 */
export function calculateChartBounds(points: ParetoChartPoint[]) {
  const valid = filterValidChartPoints(points);

  if (valid.length === 0) {
    return { isEmpty: true, minX: 0, maxX: 10, minY: 0.0, maxY: 1.0, spanX: 10, spanY: 1.0 };
  }

  const speeds = valid.map((p) => p.tokens_per_sec);
  const rawMinX = Math.min(...speeds);
  const rawMaxX = Math.max(...speeds);

  // Dynamic X bounds with safety margins and fallback for identical/single values
  const minX = Math.max(0, Math.floor(rawMinX * 0.85));
  const maxX =
    rawMinX === rawMaxX
      ? Math.max(10, Math.ceil(rawMaxX * 1.3 || 10))
      : Math.max(minX + 10, Math.ceil(rawMaxX * 1.15));

  // Dynamic Y bounds (accuracy 0.0 - 1.0)
  const accs = valid.map((p) => p.accuracy_rate);
  const rawMinAcc = Math.min(...accs);
  const maxY = 1.0;
  // Dynamic lower zoom floor (0.0 up to 0.7 depending on minimum measured accuracy)
  const minY = Math.max(0, Math.min(0.7, Math.floor((rawMinAcc - 0.05) * 10) / 10));

  const spanX = maxX - minX || 1;
  const spanY = maxY - minY || 0.1;

  return { isEmpty: false, minX, maxX, minY, maxY, spanX, spanY };
}

/**
 * Formats a metric value with unit, or returns 'N/A' if null/undefined.
 * Never converts null to zero.
 */
export function formatMetricNumber(
  val: number | null | undefined,
  unit: string = '',
  decimals: number = 1
): string {
  if (val == null || !Number.isFinite(val)) {
    return 'N/A';
  }
  const formatted = decimals === 0 ? val.toFixed(0) : val.toFixed(decimals);
  return unit ? `${formatted} ${unit}` : formatted;
}

/**
 * Formats a 0.0-1.0 normalized accuracy score into percentage string, or 'N/A' if null.
 */
export function formatAccuracyPercent(val: number | null | undefined): string {
  if (val == null || !Number.isFinite(val)) {
    return 'N/A';
  }
  return `${(val * 100).toFixed(1)}%`;
}
