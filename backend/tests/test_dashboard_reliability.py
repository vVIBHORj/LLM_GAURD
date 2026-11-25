import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
from backend.app.main import create_app

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

def test_dashboard_endpoint_serves_html(client):
    """Verify that GET /dashboard serves dashboard.html successfully with HTTP 200."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LocalLLM Guard" in response.text
    assert "apiCall" in response.text
    assert "escapeHtml" in response.text

def test_dashboard_xss_prevention_and_api_helpers():
    """
    Spawns headless Chromium to execute the client-side JavaScript of dashboard.html
    and directly verify XSS neutralization, apiCall response parsing, error handling,
    and single-scope evaluation polling lifecycle.
    """
    html_path = Path("backend/app/static/dashboard.html").resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        page.goto(html_path)
        page.wait_for_timeout(1000)

        assert not page_errors, f"Unexpected page errors on load: {page_errors}"

        # 1. Test XSS neutralization with escapeHtml
        xss_payloads = [
            ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
            ("<img src=x onerror=alert(1)>", "&lt;img src=x onerror=alert(1)&gt;"),
            ("\"><svg onload=alert(1)>", "&quot;&gt;&lt;svg onload=alert(1)&gt;"),
            ("Normal & safe 'text'", "Normal &amp; safe &#39;text&#39;"),
            (None, ""),
            (12345, "12345")
        ]

        for payload, expected in xss_payloads:
            result = page.evaluate("(val) => escapeHtml(val)", payload)
            assert result == expected, f"escapeHtml failed for {payload}: expected {expected}, got {result}"

        # 2. Verify model response injection rendering safely in container
        mock_report = {
            "model_id": "malicious-model<script>alert('xss')</script>",
            "engine_used": "direct",
            "defense_rate": 0.5,
            "defended_attacks": 1,
            "total_attacks": 2,
            "risk_level": "HIGH",
            "generated_at": "2026-11-24T12:00:00Z",
            "attack_details": [
                {
                    "category": "INJECTION",
                    "attack_vector": "Prompt Override",
                    "defended": False,
                    "prompt": "Say <img src=x onerror=alert('prompt')>",
                    "model_response": "<img src=x onerror=alert('response')><script>window.__xss_flag = true;</script>",
                    "thinking_preview": "<think>Dangerous <svg onload=alert('think')></think>",
                    "reason": "Executed payload with <script>alert('reason')</script>"
                }
            ]
        }

        page.evaluate("(rep) => renderSecurityReport(rep)", mock_report)
        xss_triggered = page.evaluate("() => Boolean(window.__xss_flag)")
        assert not xss_triggered, "XSS was executed during renderSecurityReport!"

        # Check DOM text content contains rendered strings rather than raw tags
        container_html = page.inner_html("#security-results-container")
        assert "<script>" not in container_html, "Raw <script> tag leaked into innerHTML!"
        assert "&lt;script&gt;" in container_html or "alert(&#39;xss&#39;)" in container_html

        # 3. Test renderEvaluationResults XSS neutralization
        mock_results = [
            {
                "prompt_text": "Test <script>window.__eval_xss = true;</script>",
                "raw_output": "Output <img src=x onerror='window.__eval_xss = true;'>",
                "passed": False,
                "latency_ms": 120.5,
                "completion_tokens": 15
            }
        ]
        page.evaluate("(res) => renderEvaluationResults(res)", mock_results)
        eval_xss_triggered = page.evaluate("() => Boolean(window.__eval_xss)")
        assert not eval_xss_triggered, "XSS was executed during renderEvaluationResults!"

        # 4. Test apiCall function behavior against mock responses
        api_test_results = page.evaluate("""
            async () => {
                const results = {};

                // Mock fetch function
                const originalFetch = window.fetch;

                // 4A: Successful response with .data wrapper
                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({ success: true, data: { id: "run-123", status: "QUEUED" } })
                });
                const resA = await apiCall('/test-success');
                results.successWrapper = (resA && resA.id === 'run-123' && resA.status === 'QUEUED');

                // 4B: Successful response without wrapper
                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ([{ id: "mod-1" }])
                });
                const resB = await apiCall('/test-array');
                results.arraySuccess = Array.isArray(resB) && resB.length === 1;

                // 4C: HTTP 404 with string detail
                window.fetch = async () => ({
                    ok: false,
                    status: 404,
                    statusText: "Not Found",
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({ detail: "Model 'missing' is not registered." })
                });
                try {
                    await apiCall('/test-404');
                    results.err404 = false;
                } catch (e) {
                    results.err404 = e.message.includes("Model 'missing' is not registered.");
                }

                // 4D: HTTP 422 with validation array detail
                window.fetch = async () => ({
                    ok: false,
                    status: 422,
                    statusText: "Unprocessable Entity",
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({
                        detail: [
                            { loc: ["body", "model_id"], msg: "Field required" },
                            { loc: ["body", "dataset_id"], msg: "Field required" }
                        ]
                    })
                });
                try {
                    await apiCall('/test-422');
                    results.err422 = false;
                } catch (e) {
                    results.err422 = e.message.includes("model_id: Field required") && e.message.includes("dataset_id: Field required");
                }

                // 4E: HTTP 500 with non-JSON response
                window.fetch = async () => ({
                    ok: false,
                    status: 500,
                    statusText: "Internal Server Error",
                    headers: new Headers({ 'content-type': 'text/plain' }),
                    text: async () => "Internal server crash"
                });
                try {
                    await apiCall('/test-500');
                    results.err500 = false;
                } catch (e) {
                    results.err500 = e.message.includes("HTTP 500");
                }

                // 4F: Network failure (fetch throws)
                window.fetch = async () => {
                    throw new Error("Failed to fetch");
                };
                try {
                    await apiCall('/test-net-err');
                    results.netErr = false;
                } catch (e) {
                    results.netErr = e.message.includes("Network failure");
                }

                // Restore fetch
                window.fetch = originalFetch;
                return results;
            }
        """)

        assert api_test_results["successWrapper"] is True, "apiCall failed to unpack success data wrapper"
        assert api_test_results["arraySuccess"] is True, "apiCall failed on array response"
        assert api_test_results["err404"] is True, "apiCall failed to extract 404 detail message"
        assert api_test_results["err422"] is True, "apiCall failed to format 422 validation array detail"
        assert api_test_results["err500"] is True, "apiCall failed on HTTP 500 text response"
        assert api_test_results["netErr"] is True, "apiCall failed on network failure"

        # 5. Test evaluation workflow lifecycle
        lifecycle_results = page.evaluate("""
            async () => {
                const results = {};
                const originalFetch = window.fetch;

                // 5A: Submission error (404) does not start polling, shows error badge, unlocks buttons
                window.fetch = async () => ({
                    ok: false,
                    status: 404,
                    statusText: "Not Found",
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({ detail: "Dataset not found." })
                });

                // Ensure dataset exists in activeDatasets
                activeDatasets = [{ id: "ds-1", name: "Promptfoo Rigorous Security Suite" }];
                const modelSelect = document.getElementById('model-select');
                if (modelSelect) modelSelect.value = "llama3.2:latest";

                await runRigorousEval('Promptfoo Rigorous Security Suite');
                const badgeText = document.getElementById('eval-run-badge').textContent;
                const secBtnDisabled = document.getElementById('btn-run-sec-suite').disabled;

                results.submissionErrorCaught = (badgeText === 'SUBMISSION FAILED');
                results.buttonReEnabled = (secBtnDisabled === false);
                results.noRunIdStored = (currentEvaluationState.runId === null);
                results.noTimeoutActive = (currentEvaluationState.timeoutHandle === null);

                // 5B: Missing run ID in 200 response
                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({ success: true, data: { status: "QUEUED" } }) // missing id
                });
                await runRigorousEval('Promptfoo Rigorous Security Suite');
                results.missingRunIdHandled = (document.getElementById('eval-run-badge').textContent === 'INVALID RESPONSE');

                // 5C: Successful submission and completion polling
                let pollCount = 0;
                window.fetch = async (url) => {
                    const u = String(url);
                    if (u.includes('/api/v1/evaluations') && !u.includes('/evaluations/')) {
                        return {
                            ok: true,
                            status: 202,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: { id: "run-xyz", status: "QUEUED" } })
                        };
                    } else if (u.includes('/evaluations/run-xyz/results')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: [{ prompt_text: "test", passed: true, latency_ms: 50, completion_tokens: 10 }] })
                        };
                    } else if (u.includes('/evaluations/run-xyz')) {
                        pollCount++;
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({
                                success: true,
                                data: {
                                    id: "run-xyz",
                                    status: pollCount >= 2 ? "COMPLETED" : "RUNNING",
                                    total_duration_seconds: 4.2,
                                    tokens_per_second_avg: 55.4,
                                    accuracy_rate: 1.0
                                }
                            })
                        };
                    }
                    return { ok: false, status: 404, headers: new Headers() };
                };

                await runRigorousEval('Promptfoo Rigorous Security Suite');
                results.activeRunIdSet = (currentEvaluationState.runId === "run-xyz");

                // Wait 4.5 seconds for recursive polling to hit COMPLETED
                await new Promise(r => setTimeout(r, 4500));

                results.pollCompleted = (document.getElementById('eval-run-badge').textContent === 'COMPLETED');
                results.stateResetAfterCompletion = (currentEvaluationState.runId === null && currentEvaluationState.timeoutHandle === null);
                results.ledgerRendered = document.getElementById('eval-results-container').innerHTML.includes('Test Execution Ledger');

                window.fetch = originalFetch;
                return results;
            }
        """)

        assert lifecycle_results["submissionErrorCaught"] is True, "Submission error was not caught"
        assert lifecycle_results["buttonReEnabled"] is True, "Run button remained locked after failure"
        assert lifecycle_results["noRunIdStored"] is True, "Run ID was erroneously set on failure"
        assert lifecycle_results["noTimeoutActive"] is True, "Timeout was scheduled on failure"
        assert lifecycle_results["missingRunIdHandled"] is True, "Missing run ID in 200 response was not handled"
        assert lifecycle_results["activeRunIdSet"] is True, "Active run ID was not set on valid submission"
        assert lifecycle_results["pollCompleted"] is True, "Polling did not terminate with COMPLETED badge"
        assert lifecycle_results["stateResetAfterCompletion"] is True, "Evaluation state was not reset after completion"
        assert lifecycle_results["ledgerRendered"] is True, "Assertion ledger was not rendered on completion"

        # 6. Phase 2B: Test dynamic model dropdown population
        model_dropdown_results = page.evaluate("""
            async () => {
                const results = {};
                const originalFetch = window.fetch;

                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({
                        success: true,
                        data: [
                            { id: "phi3:mini", name: "phi3:mini", parameter_size: "3.8B", quantization: "Q4", disk_size_bytes: 2200000000 },
                            { id: "gemma2:2b", name: "gemma2:2b", parameter_size: "2B", quantization: "Q4", disk_size_bytes: 1600000000 }
                        ]
                    })
                });

                await loadModels();
                const sel = document.getElementById('model-select');
                const options = Array.from(sel.options).map(o => ({ value: o.value, text: o.text }));

                results.optionCount = options.length;
                results.firstValue = options[0]?.value;
                results.firstText = options[0]?.text;
                results.secondValue = options[1]?.value;

                window.fetch = originalFetch;
                return results;
            }
        """)

        assert model_dropdown_results["optionCount"] == 2, f"Expected 2 options in model-select, got {model_dropdown_results['optionCount']}"
        assert model_dropdown_results["firstValue"] == "phi3:mini"
        assert "phi3:mini (3.8B)" in model_dropdown_results["firstText"]
        assert model_dropdown_results["secondValue"] == "gemma2:2b"

        # 7. Phase 2B: Test bounded transient polling retry recovery
        retry_recovery_results = page.evaluate("""
            async () => {
                const results = {};
                const originalFetch = window.fetch;
                let pollAttempts = 0;

                // Configure runRigorousEval with temporary mock
                window.fetch = async (url) => {
                    const u = String(url);
                    if (u.includes('/api/v1/evaluations') && !u.includes('/evaluations/')) {
                        return {
                            ok: true,
                            status: 202,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: { id: "run-retry-test", status: "QUEUED" } })
                        };
                    } else if (u.includes('/evaluations/run-retry-test/results')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: [] })
                        };
                    } else if (u.includes('/evaluations/run-retry-test')) {
                        pollAttempts++;
                        if (pollAttempts === 1) {
                            // First poll: simulate network drop / transient failure
                            throw new Error("Temporary network glitch");
                        }
                        // Subsequent polls succeed and complete
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({
                                success: true,
                                data: { id: "run-retry-test", status: "COMPLETED", total_duration_seconds: 2.0 }
                            })
                        };
                    }
                    return { ok: false, status: 404, headers: new Headers() };
                };

                activeDatasets = [{ id: "ds-1", name: "Promptfoo Rigorous Security Suite" }];
                await runRigorousEval('Promptfoo Rigorous Security Suite');

                // Wait 4 seconds for transient retry to fire and recover
                await new Promise(r => setTimeout(r, 4000));

                results.recoveredFromBlip = (document.getElementById('eval-run-badge').textContent === 'COMPLETED');
                results.consecutiveErrorsReset = (currentEvaluationState.consecutiveErrors === 0);

                window.fetch = originalFetch;
                return results;
            }
        """)

        assert retry_recovery_results["recoveredFromBlip"] is True, "Polling failed to recover from transient network error"
        assert retry_recovery_results["consecutiveErrorsReset"] is True, "consecutiveErrors was not reset after recovery"

        # 8. Phase 2B: Test visibility-aware telemetry polling through actual visibilitychange event
        visibility_results = page.evaluate("""
            () => {
                const results = {};
                results.timerActiveOnInit = (telemetryTimer !== null);

                // Dispatch real visibilitychange event with hidden = true
                Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
                document.dispatchEvent(new Event('visibilitychange'));
                results.timerStoppedWhenHidden = (telemetryTimer === null);

                // Dispatch real visibilitychange event with hidden = false
                Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
                document.dispatchEvent(new Event('visibilitychange'));
                results.timerResumedWhenVisible = (telemetryTimer !== null);

                return results;
            }
        """)

        assert visibility_results["timerActiveOnInit"] is True
        assert visibility_results["timerStoppedWhenHidden"] is True
        assert visibility_results["timerResumedWhenVisible"] is True

        # 9. Phase 2B Corrective: Telemetry connected, stale, disconnected, and recovery states
        telemetry_lifecycle_results = page.evaluate("""
            async () => {
                const results = {};
                const originalFetch = window.fetch;

                // 9A: Successful response -> CONNECTED / LIVE
                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({
                        success: true,
                        data: {
                            cpu: { usage_percent: 15.5 },
                            ram: { used_percent: 50.0, free_mb: 8192, total_mb: 16384 },
                            gpu: { vram_usage_percent: 25.0, allocated_mb: 1024 },
                            hardware_safety_status: 'SAFE'
                        }
                    })
                });

                await updateTelemetry();
                const liveBadge = document.getElementById('telemetry-conn-text')?.textContent;
                const safetyLive = document.getElementById('safety-pill')?.textContent;
                results.liveBadge = (liveBadge === 'LIVE');
                results.safetyLive = safetyLive.includes('READY');

                // 9B: Network failure within 15s window -> STALE
                window.fetch = async () => { throw new Error("Connection timed out"); };
                await updateTelemetry();
                const staleBadge = document.getElementById('telemetry-conn-text')?.textContent;
                const safetyStale = document.getElementById('safety-pill')?.textContent;
                results.staleBadge = staleBadge.includes('STALE');
                results.safetyStale = safetyStale.includes('STALE');

                // Verify gauge values were NOT wiped to zero on failure
                const cpuStill15 = document.getElementById('cpu-pct')?.textContent;
                results.gaugePreserved = (cpuStill15 === '15.5%');

                // 9C: Outdated failure (> 15s elapsed) -> DISCONNECTED
                lastTelemetrySuccessTime = Date.now() - 20000; // 20s ago
                await updateTelemetry();
                const discBadge = document.getElementById('telemetry-conn-text')?.textContent;
                const safetyOffline = document.getElementById('safety-pill')?.textContent;
                results.discBadge = (discBadge === 'DISCONNECTED');
                results.safetyOffline = safetyOffline.includes('OFFLINE');

                // 9D: Recovery after failure -> restores CONNECTED / LIVE
                window.fetch = async () => ({
                    ok: true,
                    status: 200,
                    headers: new Headers({ 'content-type': 'application/json' }),
                    json: async () => ({
                        success: true,
                        data: {
                            cpu: { usage_percent: 18.2 },
                            ram: { used_percent: 52.0, free_mb: 7800, total_mb: 16384 },
                            gpu: { vram_usage_percent: 30.0, allocated_mb: 1200 },
                            hardware_safety_status: 'SAFE'
                        }
                    })
                });
                await updateTelemetry();
                const recoveredBadge = document.getElementById('telemetry-conn-text')?.textContent;
                results.recovered = (recoveredBadge === 'LIVE');

                window.fetch = originalFetch;
                return results;
            }
        """)

        assert telemetry_lifecycle_results["liveBadge"] is True, "Telemetry did not show LIVE on success"
        assert telemetry_lifecycle_results["safetyLive"] is True, "Safety badge did not show READY on success"
        assert telemetry_lifecycle_results["staleBadge"] is True, "Telemetry did not show STALE on recent failure"
        assert telemetry_lifecycle_results["safetyStale"] is True, "Safety badge did not show STALE on recent failure"
        assert telemetry_lifecycle_results["gaugePreserved"] is True, "Telemetry gauges were erroneously wiped to zero"
        assert telemetry_lifecycle_results["discBadge"] is True, "Telemetry did not show DISCONNECTED on prolonged failure"
        assert telemetry_lifecycle_results["safetyOffline"] is True, "Safety badge did not show OFFLINE on prolonged failure"
        assert telemetry_lifecycle_results["recovered"] is True, "Telemetry failed to recover to LIVE after failure"

        # 10. Phase 2B Corrective: Zero Synthetic Pareto Data & Clean Empty State
        pareto_integrity_results = page.evaluate("""
            async () => {
                const results = {};
                const originalFetch = window.fetch;

                // 10A: Empty benchmark reports from backend
                window.fetch = async (url) => {
                    const u = String(url);
                    if (u.includes('/api/v1/analytics/rankings')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: { rankings: [] } })
                        };
                    } else if (u.includes('/api/v1/benchmarks')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: [] })
                        };
                    }
                    return { ok: false, status: 404, headers: new Headers() };
                };

                await loadRankings();
                const paretoHtml = document.getElementById('pareto-cards')?.innerHTML;
                const peakSpeedText = document.getElementById('overview-peak-speed')?.textContent;
                const peakModelText = document.getElementById('overview-peak-model')?.textContent;

                results.showsEmptyState = paretoHtml.includes('No Empirical Benchmark Reports Compiled');
                results.noSyntheticSpeed = !peakSpeedText.includes('109.3');
                results.speedDashed = peakSpeedText.includes('—');
                results.noSyntheticLlama = !peakModelText.includes('Llama 3.2 (3B)');

                // 10B: Real benchmark reports returned from /api/v1/benchmarks using exact ParetoPoint schema
                window.fetch = async (url) => {
                    const u = String(url);
                    if (u.includes('/api/v1/analytics/rankings')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: { rankings: [] } })
                        };
                    } else if (u.includes('/api/v1/benchmarks')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({
                                success: true,
                                data: [
                                    {
                                        id: "rep-real-1",
                                        title: "Empirical Qwen vs Llama Run",
                                        results: [
                                            {
                                                model_id: "qwen2.5:3b",
                                                run_id: "run-real-1",
                                                status: "BENCHMARKED",
                                                speed_tokens_sec: 48.2,
                                                accuracy_score: 0.91,
                                                peak_vram_mb: 2450.0,
                                                gpu_name: "RTX 3050"
                                            }
                                        ],
                                        pareto_frontier: [
                                            {
                                                model_id: "qwen2.5:3b",
                                                run_id: "run-real-1",
                                                tokens_per_sec: 48.2,
                                                accuracy_rate: 0.91,
                                                peak_vram_mb: 2450.0,
                                                is_pareto_optimal: true
                                            }
                                        ]
                                    }
                                ]
                            })
                        };
                    }
                    return { ok: false, status: 404, headers: new Headers() };
                };

                await loadRankings();
                const realParetoHtml = document.getElementById('pareto-cards')?.innerHTML;
                const realPeakSpeed = document.getElementById('overview-peak-speed')?.textContent;
                const realPeakModel = document.getElementById('overview-peak-model')?.textContent;
                const realPeakStatus = document.getElementById('overview-peak-status')?.textContent;

                results.rendersRealParetoCard = realParetoHtml.includes('qwen2.5:3b') && realParetoHtml.includes('48.2 t/s') && realParetoHtml.includes('91%');
                results.noNaNInRealCard = !realParetoHtml.includes('NaN') && !realParetoHtml.includes('undefined');
                results.realPeakSpeedUpdated = realPeakSpeed.includes('48.2');
                results.realPeakModelUpdated = (realPeakModel === 'qwen2.5:3b');
                results.realHardwareProvenance = (realPeakStatus === 'RTX 3050');

                // 10C: Null, missing, and non-finite metrics on ParetoPoint render 'N/A' and never '0' or 'NaN'
                window.fetch = async (url) => {
                    const u = String(url);
                    if (u.includes('/api/v1/analytics/rankings')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({ success: true, data: { rankings: [] } })
                        };
                    } else if (u.includes('/api/v1/benchmarks')) {
                        return {
                            ok: true,
                            status: 200,
                            headers: new Headers({ 'content-type': 'application/json' }),
                            json: async () => ({
                                success: true,
                                data: [
                                    {
                                        id: "rep-invalid-metrics",
                                        title: "Partial Metrics Report",
                                        results: [
                                            {
                                                model_id: "test-null-model",
                                                run_id: "run-null-1",
                                                status: "BENCHMARKED",
                                                speed_tokens_sec: null,
                                                accuracy_score: null
                                            }
                                        ],
                                        pareto_frontier: [
                                            {
                                                model_id: "test-null-model",
                                                run_id: "run-null-1",
                                                tokens_per_sec: null,
                                                accuracy_rate: null,
                                                peak_vram_mb: 1024.0,
                                                is_pareto_optimal: true
                                            },
                                            {
                                                model_id: "test-missing-model",
                                                run_id: "run-missing-1",
                                                is_pareto_optimal: true
                                            },
                                            {
                                                model_id: "test-nonfinite-model",
                                                run_id: "run-nonfinite-1",
                                                tokens_per_sec: "not-a-number",
                                                accuracy_rate: 0,
                                                peak_vram_mb: 1024.0,
                                                is_pareto_optimal: true
                                            }
                                        ]
                                    }
                                ]
                            })
                        };
                    }
                    return { ok: false, status: 404, headers: new Headers() };
                };

                await loadRankings();
                const invalidParetoHtml = document.getElementById('pareto-cards')?.innerHTML;
                results.invalidMetricsNoNaN = !invalidParetoHtml.includes('NaN') && !invalidParetoHtml.includes('undefined');
                results.invalidMetricsShowNA = (invalidParetoHtml.match(/N\\/A/g) || []).length === 5;
                results.genuineZeroAccuracyPreserved = invalidParetoHtml.includes('0%');

                window.fetch = originalFetch;
                return results;
            }
        """)

        assert pareto_integrity_results["showsEmptyState"] is True, "Pareto section did not show empty state when no benchmarks exist"
        assert pareto_integrity_results["noSyntheticSpeed"] is True, "Synthetic speed (109.3) was still present"
        assert pareto_integrity_results["speedDashed"] is True, "Peak speed was not set to unmeasured dash"
        assert pareto_integrity_results["noSyntheticLlama"] is True, "Synthetic 'Llama 3.2 (3B)' card was still present"
        assert pareto_integrity_results["rendersRealParetoCard"] is True, "Real Pareto card was not rendered from /api/v1/benchmarks"
        assert pareto_integrity_results["noNaNInRealCard"] is True, "Real Pareto card rendered NaN or undefined"
        assert pareto_integrity_results["realPeakSpeedUpdated"] is True, "Peak speed did not update from real benchmark"
        assert pareto_integrity_results["realPeakModelUpdated"] is True, "Peak model did not update to real benchmark model"
        assert pareto_integrity_results["realHardwareProvenance"] is True, "Hardware provenance GPU name was not preserved"
        assert pareto_integrity_results["invalidMetricsNoNaN"] is True, "Null/missing/non-finite Pareto metrics rendered NaN or undefined"
        assert pareto_integrity_results["invalidMetricsShowNA"] is True, "Null/missing/non-finite Pareto metrics did not render expected N/A count"
        assert pareto_integrity_results["genuineZeroAccuracyPreserved"] is True, "Genuine 0 accuracy was not preserved as 0%"

        browser.close()
