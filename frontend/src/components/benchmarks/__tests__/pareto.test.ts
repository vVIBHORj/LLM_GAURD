/**
 * Frontend Unit & Scenario Verification for Pareto Benchmarking (Task 2.3 Phase 2B)
 * Directly tests the shared production utilities in paretoUtils.ts.
 */
import type { BenchmarkReport } from '../../../types/index.ts';
import type { ParetoChartPoint } from '../ParetoChart.tsx';
import {
  isValidChartPoint,
  filterValidChartPoints,
  calculateChartBounds,
  transformReportToChartPoints,
  sortParetoFrontier,
  formatMetricNumber,
  formatAccuracyPercent,
} from '../paretoUtils.ts';

function assert(condition: boolean, message?: string): asserts condition {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertEqual<T>(actual: T, expected: T, message?: string) {
  if (actual !== expected) {
    throw new Error(message || `Expected ${expected}, but got ${actual}`);
  }
}

console.log('--- Running Pareto Benchmarking Production Utility Tests ---');

// Test 1: Zero, null, undefined, negative, and non-finite metric validation
{
  // Valid zero measurements
  assertEqual(isValidChartPoint({ tokens_per_sec: 0.0, accuracy_rate: 0.0 }), true, 'Zero throughput and zero accuracy must be valid');
  assertEqual(isValidChartPoint({ tokens_per_sec: 45.2, accuracy_rate: 0.0 }), true, 'Zero accuracy must be retained');
  assertEqual(isValidChartPoint({ tokens_per_sec: 0.0, accuracy_rate: 0.95 }), true, 'Zero throughput must be retained');

  // Missing metrics
  assertEqual(isValidChartPoint({ tokens_per_sec: null, accuracy_rate: 0.9 }), false, 'Null throughput must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: 45.2, accuracy_rate: null }), false, 'Null accuracy must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: undefined, accuracy_rate: 0.9 }), false, 'Undefined throughput must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: 45.2, accuracy_rate: undefined }), false, 'Undefined accuracy must be rejected');

  // Negative values
  assertEqual(isValidChartPoint({ tokens_per_sec: -10.0, accuracy_rate: 0.9 }), false, 'Negative throughput must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: 50.0, accuracy_rate: -0.1 }), false, 'Negative accuracy must be rejected');

  // Non-finite values
  assertEqual(isValidChartPoint({ tokens_per_sec: NaN, accuracy_rate: 0.9 }), false, 'NaN throughput must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: 50.0, accuracy_rate: NaN }), false, 'NaN accuracy must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: Infinity, accuracy_rate: 0.9 }), false, 'Infinity throughput must be rejected');
  assertEqual(isValidChartPoint({ tokens_per_sec: 50.0, accuracy_rate: 1.5 }), false, 'Accuracy > 1.0 must be rejected');

  // Direct filterValidChartPoints array test
  const rawPoints: ParetoChartPoint[] = [
    { model_id: 'm-valid', tokens_per_sec: 10.0, accuracy_rate: 0.8, is_pareto: false, status: 'BENCHMARKED' },
    { model_id: 'm-zero', tokens_per_sec: 0.0, accuracy_rate: 0.0, is_pareto: false, status: 'BENCHMARKED' },
    { model_id: 'm-neg', tokens_per_sec: -5.0, accuracy_rate: 0.8, is_pareto: false, status: 'BENCHMARKED' },
  ];
  const filtered = filterValidChartPoints(rawPoints);
  assertEqual(filtered.length, 2, 'Negative point must be filtered out, valid and zero points retained');

  console.log('✓ Test 1: Zero, missing, negative, and non-finite metric validation passed');
}

// Test 2: Metric Formatting (Null is 'N/A', Never Fabricated Zero)
{
  assertEqual(formatMetricNumber(null, 't/s', 1), 'N/A');
  assertEqual(formatMetricNumber(undefined, 'MB', 0), 'N/A');
  assertEqual(formatMetricNumber(NaN, 'ms', 1), 'N/A');
  assertEqual(formatMetricNumber(0.0, 't/s', 1), '0.0 t/s', 'Genuine measured zero throughput formats as 0.0 t/s');
  assertEqual(formatMetricNumber(0.0, 'MB', 0), '0 MB', 'Genuine measured zero VRAM formats as 0 MB');
  assertEqual(formatAccuracyPercent(null), 'N/A');
  assertEqual(formatAccuracyPercent(0.0), '0.0%', 'Genuine 0 accuracy formats as 0.0%');
  assertEqual(formatAccuracyPercent(0.9234), '92.3%');
  console.log('✓ Test 2: Formatting preserves N/A for missing metrics and formats measured zero correctly');
}

// Test 3: Pareto Frontier Ascending Throughput Ordering
{
  const outOfOrderFrontier: ParetoChartPoint[] = [
    { model_id: 'fast-model', tokens_per_sec: 110.0, accuracy_rate: 0.88, is_pareto: true, status: 'BENCHMARKED' },
    { model_id: 'mid-model', tokens_per_sec: 45.0, accuracy_rate: 0.92, is_pareto: true, status: 'BENCHMARKED' },
    { model_id: 'slow-model', tokens_per_sec: 15.0, accuracy_rate: 0.96, is_pareto: true, status: 'BENCHMARKED' },
    { model_id: 'dominated-model', tokens_per_sec: 30.0, accuracy_rate: 0.80, is_pareto: false, status: 'BENCHMARKED' },
  ];

  const sorted = sortParetoFrontier(outOfOrderFrontier);
  assertEqual(sorted.length, 3, 'Only pareto-optimal points included in frontier line');
  assertEqual(sorted[0].model_id, 'slow-model');
  assertEqual(sorted[1].model_id, 'mid-model');
  assertEqual(sorted[2].model_id, 'fast-model');
  assert(sorted[0].tokens_per_sec < sorted[1].tokens_per_sec);
  assert(sorted[1].tokens_per_sec < sorted[2].tokens_per_sec);
  console.log('✓ Test 3: Pareto frontier line points are strictly sorted by ascending throughput order');
}

// Test 4: Single Model Benchmark & Identical Bounds (No Division by Zero)
{
  const singlePoint: ParetoChartPoint[] = [
    { model_id: 'llama3.2:latest', tokens_per_sec: 80.0, accuracy_rate: 0.92, is_pareto: true, status: 'BENCHMARKED' },
  ];

  const singleBounds = calculateChartBounds(singlePoint);
  assertEqual(singleBounds.isEmpty, false);
  assert(singleBounds.spanX > 0, 'spanX must be positive');
  assert(singleBounds.spanY > 0, 'spanY must be positive');
  assert(singleBounds.maxX > singleBounds.minX);

  const identicalPoints: ParetoChartPoint[] = [
    { model_id: 'm1', tokens_per_sec: 0.0, accuracy_rate: 0.0, is_pareto: true, status: 'BENCHMARKED' },
    { model_id: 'm2', tokens_per_sec: 0.0, accuracy_rate: 0.0, is_pareto: true, status: 'BENCHMARKED' },
  ];

  const zeroBounds = calculateChartBounds(identicalPoints);
  assertEqual(zeroBounds.isEmpty, false);
  assertEqual(zeroBounds.minX, 0);
  assert(zeroBounds.maxX > 0, 'maxX must expand beyond 0 to allow plotting zero throughput');
  assert(zeroBounds.spanX > 0);
  assert(zeroBounds.spanY > 0);
  console.log('✓ Test 4: Single points and zero measurements compute valid non-zero coordinate spans');
}

// Test 5: Report Transformation from Production BenchmarkReport
{
  const report: BenchmarkReport = {
    id: 'report-prod-1',
    title: 'Controlled Production Benchmark',
    dataset_id: 'dataset-eval-1',
    model_ids: ['model-a', 'model-b', 'model-c', 'model-d'],
    generated_at: new Date().toISOString(),
    results: [
      {
        model_id: 'model-a',
        run_id: 'run-a',
        status: 'BENCHMARKED',
        accuracy_score: 0.94,
        speed_tokens_sec: 55.0,
        avg_latency_ms: 140.0,
        peak_vram_mb: 2400.0,
        gpu_name: 'NVIDIA RTX 3050 Laptop GPU',
        gpu_source: 'nvidia-smi',
      },
      {
        model_id: 'model-b',
        run_id: 'run-b',
        status: 'BENCHMARKED',
        accuracy_score: 0.0, // genuine zero accuracy
        speed_tokens_sec: 0.0, // genuine zero speed
        avg_latency_ms: 500.0,
        peak_vram_mb: 1800.0,
      },
      {
        model_id: 'model-c',
        run_id: null,
        status: 'UNBENCHMARKED',
        accuracy_score: null,
        speed_tokens_sec: null,
      },
      {
        model_id: 'model-d',
        run_id: 'run-d',
        status: 'INELIGIBLE',
        accuracy_score: null,
        speed_tokens_sec: null,
      },
    ],
    pareto_frontier: [
      {
        model_id: 'model-a',
        tokens_per_sec: 55.0,
        accuracy_rate: 0.94,
        peak_vram_mb: 2400.0,
        is_pareto_optimal: true,
      },
    ],
  };

  const chartPoints = transformReportToChartPoints(report);
  assertEqual(chartPoints.length, 2, 'Both model-a and genuine zero model-b enter chart points');
  assertEqual(chartPoints[0].model_id, 'model-a');
  assertEqual(chartPoints[0].is_pareto, true);
  assertEqual(chartPoints[1].model_id, 'model-b');
  assertEqual(chartPoints[1].is_pareto, false);
  assertEqual(chartPoints[1].tokens_per_sec, 0.0);
  assertEqual(chartPoints[1].accuracy_rate, 0.0);

  console.log('✓ Test 5: Production report transformation properly maps points and preserves genuine zeroes');
}

console.log('--- ALL FRONTEND PARETO UTILITY TESTS PASSED ---');
