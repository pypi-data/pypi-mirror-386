# Phase 5.0 Streaming DAG Runtime - Visual Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 5.0 VIABILITY CHECK - STREAMING DAG RUNTIME                 │
│  Status: ✅ APPROVED (with modifications)                          │
│  Confidence: 85% | Risk: MEDIUM | Timeline: 3-4 weeks              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Current State (v0.8.0)

```
Current Test Baseline: ✅ 123 tests passing

├── orchestration/ (Phase 3.0) ─────────────── 30 tests
│   ├── test_circuit_breaker.py ─────────────── 5
│   ├── test_coordinator.py ─────────────────── 7
│   ├── test_registry.py ────────────────────── 5
│   ├── test_router.py ──────────────────────── 7
│   └── test_runtime.py ─────────────────────── 6
│
├── core pipeline tests ────────────────────── 93 tests
│   ├── test_api_exports.py ─────────────────── 19
│   ├── test_pipeline_builder.py ────────────── 33
│   ├── test_sink_database.py ───────────────── 18
│   ├── test_sink_database_simple.py ────────── 6
│   ├── test_typed_overrides_integration.py ─── 8
│   └── ... (others) ────────────────────────── 9

CRITICAL: All 123 must pass after Phase 5.0!
```

---

## 🎯 Proposed Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Phase 5.0 DAG Runtime                     │
└──────────────────────────────────────────────────────────────┘

                          ┌─────────────┐
                          │   Sources   │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
              │  Provider  │ │ Replay │ │ Synthetic│
              │   Source   │ │ Source │ │  Source  │
              └─────┬──────┘ └───┬────┘ └────┬─────┘
                    │            │            │
                    └────────────┼────────────┘
                                 │
                          ┌──────▼──────┐
                          │   Router/   │
                          │ Partitioner │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
              │  Dedupe   │ │ Window │ │ Transform│
              │ Operator  │ │  Agg   │ │ Operator │
              └─────┬──────┘ └───┬────┘ └────┬─────┘
                    │            │            │
                    └────────────┼────────────┘
                                 │
                          ┌──────▼──────┐
                          │   Batcher   │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
              │   Store   │ │ Kafka  │ │   File   │
              │   Sink    │ │  Sink  │ │   Sink   │
              └───────────┘ └────────┘ └──────────┘

┌──────────────────────────────────────────────────────────────┐
│  Backpressure Feedback Loop (from market_data_store v0.9.0)  │
│  ◄─────────────────────────────────────────────────────────  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 New Package Structure

```
src/market_data_pipeline/
│
├── dag/ (NEW) ──────────────────────────────────────── Phase 5.0
│   ├── __init__.py
│   ├── nodes.py          ← Protocol definitions
│   ├── edges.py          ← Channels + backpressure
│   ├── graph.py          ← DAG validation
│   ├── runtime.py        ← Execution engine (needs completion)
│   ├── metrics.py        ← Prometheus instrumentation
│   ├── windowing.py      ← Tumbling/sliding windows
│   └── partitions.py     ← Keyed partitioning
│
├── adapters/ (NEW) ───────────────────────────────────
│   ├── provider_source.py   ← Wraps MarketDataProvider
│   ├── sink_adapter.py      ← Wraps WriteCoordinator
│   └── serialization.py     ← JSON/msgpack (optional)
│
├── contrib/operators/ (NEW) ──────────────────────────
│   ├── dedupe.py            ← Deduplication operator
│   ├── throttle.py          ← Rate limiting operator
│   ├── router.py            ← Fan-out operator
│   └── ohlc_resample.py     ← Bar resampling (stub)
│
├── orchestration/ (EXISTING - Phase 3.0) ─────────────
│   ├── runtime.py           ⚠️ OVERLAP with DAGRuntimeAPI
│   ├── settings.py          ⚠️ Add DagRuntimeSettings?
│   ├── circuit_breaker.py   ✅ Reuse as-is
│   ├── coordinator.py       ✅ Reuse as-is
│   ├── registry.py          ✅ Reuse as-is
│   └── router.py            ✅ Can become DAG node
│
└── examples/ (NEW) ────────────────────────────────────
    ├── dag_realtime_bars.py    ⚠️ Needs external deps
    ├── dag_quotes_to_store.py  ⚠️ Needs external deps
    └── dag_with_backpressure.py ⚠️ Needs external deps
```

---

## ⚠️ Critical Decision Points

```
┌─────────────────────────────────────────────────────────────┐
│  DECISION 1: Runtime API Strategy                    🔴 BLOCKER │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Current:  orchestration.PipelineRuntime (Phase 3.0)        │
│  Proposed: dag.DagRuntime + orchestration.DAGRuntimeAPI     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Option A: MERGE (Recommended)                         │  │
│  │   ✓ Clean unified API                                 │  │
│  │   ✓ No user confusion                                 │  │
│  │   ✗ More initial work                                 │  │
│  │                                                         │  │
│  │   orchestration.PipelineRuntime                        │  │
│  │       ├── .run_pipeline()     ← existing              │  │
│  │       └── .run_dag()          ← new                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Option B: Keep Separate (Not Recommended)             │  │
│  │   ✓ Faster to implement                               │  │
│  │   ✗ Two APIs doing similar things                     │  │
│  │   ✗ User confusion                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ACTION: Choose Option A before starting                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DECISION 2: External Dependencies               🟡 IMPORTANT │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Required by examples:                                        │
│    • market_data_core      (not in repo)                     │
│    • market_data_store     (needs v0.9.0 - unreleased)       │
│    • market_data_ibkr      (not in repo)                     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Strategy: Conditional Imports (Recommended)            │  │
│  │                                                         │  │
│  │   try:                                                  │  │
│  │       from market_data_core import Provider            │  │
│  │       HAS_CORE = True                                   │  │
│  │   except ImportError:                                   │  │
│  │       HAS_CORE = False                                  │  │
│  │       Provider = None  # Stub                          │  │
│  │                                                         │  │
│  │   @pytest.mark.skipif(not HAS_CORE, ...)               │  │
│  │   def test_integration(): ...                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ACTION: Implement graceful degradation                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Implementation Roadmap

```
┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.1 - Foundation               Week 1 | 15-20 hours │
├──────────────────────────────────────────────────────────────┤
│  ✓ Add dependencies (mmh3)                                    │
│  ✓ Create dag/ package                                        │
│  ✓ Implement core runtime (replace mock)                      │
│  ✓ Graph validation                                           │
│  ✓ Channel backpressure                                       │
│  📊 +15-20 tests                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.2 - Windowing                Week 2 | 10-15 hours │
├──────────────────────────────────────────────────────────────┤
│  ✓ Tumbling window operator                                   │
│  ✓ Event-time watermarks                                      │
│  ✓ Hash partitioning                                          │
│  ✓ Keyed state                                                │
│  📊 +10-15 tests                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.3 - Operators                Week 2 | 8-10 hours  │
├──────────────────────────────────────────────────────────────┤
│  ✓ Dedupe operator                                            │
│  ✓ Throttle operator                                          │
│  ✓ Router operator (fan-out)                                  │
│  ✓ OHLC resample (stub)                                       │
│  📊 +8-12 tests                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.4 - Adapters                Week 3 | 12-15 hours  │
├──────────────────────────────────────────────────────────────┤
│  ✓ Provider source adapter (conditional)                      │
│  ✓ Sink adapter (conditional)                                 │
│  ✓ Graceful fallback for missing deps                         │
│  📊 +5-8 tests (may skip if deps unavailable)                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.5 - API Integration         Week 3 | 8-10 hours  │
├──────────────────────────────────────────────────────────────┤
│  ✓ Merge runtime APIs (resolve Decision 1)                    │
│  ✓ Unified settings                                           │
│  ✓ Documentation                                              │
│  📊 +5 tests                                                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.6 - Examples                Week 4 | 5-8 hours   │
├──────────────────────────────────────────────────────────────┤
│  ✓ Simple DAG example (no external deps)                      │
│  ✓ Windowed aggregation example                              │
│  ✓ Full example (conditional on deps)                         │
│  📊 +3 tests                                                  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Phase 5.0.7 - Backpressure            Week 4 | 8-10 hours  │
├──────────────────────────────────────────────────────────────┤
│  ✓ Coordinator metrics polling                                │
│  ✓ Adaptive throttling                                        │
│  ✓ KEDA/HPA autoscaling metrics                               │
│  📊 +5 tests                                                  │
└──────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
TOTAL: 66-88 hours | +51-68 tests | 3-4 weeks
═══════════════════════════════════════════════════════════════
```

---

## ✅ Success Metrics

```
┌─────────────────────────────────────────────────────────────┐
│  MUST HAVE (Phase 5.0 Blocker)                              │
├─────────────────────────────────────────────────────────────┤
│  ☐ All 123 existing tests pass         ◄── CRITICAL        │
│  ☐ Core DAG executes simple graphs                          │
│  ☐ Graph validation works (cycle detection)                 │
│  ☐ Channel backpressure works                               │
│  ☐ 40+ new tests passing                                    │
│  ☐ No external dependencies for core                        │
│  ☐ Documentation complete                                   │
│  ☐ Zero linter/type errors                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  SHOULD HAVE (Phase 5.0 Complete)                           │
├─────────────────────────────────────────────────────────────┤
│  ☐ Windowing operators work                                 │
│  ☐ 4+ contrib operators implemented                         │
│  ☐ 60+ new tests passing                                    │
│  ☐ 1+ runnable example (standalone)                         │
│  ☐ Performance benchmarks                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  NICE TO HAVE (Phase 5.1+)                                  │
├─────────────────────────────────────────────────────────────┤
│  ☐ Integration with market_data_store v0.9.0                │
│  ☐ Backpressure feedback loop working                       │
│  ☐ 3+ integration examples                                  │
│  ☐ KEDA autoscaling demo                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Risk Heatmap

```
              HIGH PROBABILITY ───────────────►
                │
         HIGH   │  ⚠️ External      🔴 API
       IMPACT   │     Dependencies     Confusion
                │     (Deps N/A)       (Dual APIs)
                │
                │
                │  🟢 Perf Impact   🟡 Incomplete
                │     (Opt-in)         Scaffold
       LOW      │                      (Expected)
                │
                └─────────────────────────────────►
                        LOW PROBABILITY

Legend:
🔴 High Risk - Immediate action required
🟡 Medium Risk - Monitor closely  
🟢 Low Risk - Accept or minimal mitigation
⚠️ Managed - Plan in place
```

---

## 🚦 Go / No-Go Criteria

```
┌─────────────────────────────────────────────────────────────┐
│  PRE-FLIGHT CHECKLIST                                        │
├─────────────────────────────────────────────────────────────┤
│  ☐ Decision 1 resolved (runtime API)          ◄── BLOCKER  │
│  ☐ Decision 2 resolved (dependencies)         ◄── BLOCKER  │
│  ☐ Virtual environment active                               │
│  ☐ All 123 tests pass (baseline)                            │
│  ☐ Git branch created                                       │
│  ☐ Dependencies added to pyproject.toml                     │
│  ☐ Team/stakeholders aligned                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  VIABILITY ASSESSMENT                                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Architecture:        ██████████ 9/10  ✅ Excellent        │
│   Code Quality:        ████████░░ 8/10  ✅ Good             │
│   Documentation:       █████████░ 9/10  ✅ Excellent        │
│   Test Strategy:       ████████░░ 8/10  ✅ Good             │
│   Backward Compat:     ██████████ 10/10 ✅ Perfect          │
│   Dependencies:        █████░░░░░ 5/10  ⚠️ Risky            │
│   Completeness:        ██████░░░░ 6/10  ⚠️ Needs work       │
│                                                               │
│   ─────────────────────────────────────────────────────     │
│   OVERALL VIABILITY:   ████████░░ 8.5/10                     │
│                                                               │
│   Recommendation:      ✅ PROCEED WITH MODIFICATIONS         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Quick Reference

### Files Created for Planning:
- ✅ `PHASE_5_EVALUATION_AND_PLAN.md` - Detailed 11-section analysis
- ✅ `PHASE_5_DECISION_BRIEF.md` - Executive summary
- ✅ `PHASE_5_VISUAL_SUMMARY.md` - This document

### Next Steps:
1. Review decision brief
2. Make Decision 1 (runtime API)
3. Make Decision 2 (dependencies)
4. Create feature branch: `phase-5.0-dag-runtime`
5. Begin Phase 5.0.1 implementation

### Key Commands:
```bash
# Baseline tests
pytest tests/unit/ -q --tb=no

# Create branch
git checkout -b phase-5.0-dag-runtime

# Run tests continuously
pytest tests/unit/ -q --tb=no -x

# Check linting
ruff check src/

# Type checking
mypy src/market_data_pipeline/dag/
```

---

**Prepared**: 2024-10-15  
**Status**: ✅ PLANNING COMPLETE - READY FOR DECISION  
**Version**: 1.0

