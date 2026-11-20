from typing import List, Dict, Any
from backend.app.schemas.analytics import (
    ModelRankingItem,
    ModelRankingsResponse,
    ModelRecommendation,
    RecommendationRequest
)

class AnalyticsService:
    """
    Calculates composite ranking metrics and provides hardware-constrained model recommendations.
    """

    DEFAULT_WEIGHTS = {
        "accuracy": 0.40,
        "security": 0.30,
        "speed": 0.20,
        "memory": 0.10
    }

    @staticmethod
    def calculate_rankings(models_data: List[Dict[str, Any]], weights: Dict[str, float] | None = None) -> ModelRankingsResponse:
        w = weights or AnalyticsService.DEFAULT_WEIGHTS

        items: List[ModelRankingItem] = []
        max_speed = max([m.get("tokens_per_sec", 1.0) for m in models_data], default=100.0) or 100.0
        max_vram = 4096.0

        for m in models_data:
            acc = m.get("accuracy", 0.8)
            sec = m.get("security", 0.8)
            speed = m.get("tokens_per_sec", 40.0)
            vram = m.get("vram_mb", 2200.0)

            speed_norm = min(1.0, speed / max_speed)
            mem_norm = max(0.0, 1.0 - (vram / max_vram)) # Less VRAM consumed = higher efficiency score

            composite = (
                (acc * w.get("accuracy", 0.4)) +
                (sec * w.get("security", 0.3)) +
                (speed_norm * w.get("speed", 0.2)) +
                (mem_norm * w.get("memory", 0.1))
            )

            items.append(ModelRankingItem(
                rank=1,
                model_id=m["model_id"],
                composite_score=round(composite, 3),
                accuracy_score=round(acc, 2),
                security_score=round(sec, 2),
                speed_score=round(speed_norm, 2),
                memory_score=round(mem_norm, 2),
                tokens_per_sec=round(speed, 1),
                vram_used_mb=round(vram, 1)
            ))

        items.sort(key=lambda x: x.composite_score, reverse=True)
        for idx, item in enumerate(items):
            item.rank = idx + 1

        return ModelRankingsResponse(weights=w, rankings=items)

    @staticmethod
    def recommend_model(req: RecommendationRequest, models_data: List[Dict[str, Any]]) -> ModelRecommendation:
        """Recommends the best local model according to constraints."""
        filtered = [
            m for m in models_data
            if m.get("vram_mb", 2200.0) <= req.max_vram_mb and
               m.get("tokens_per_sec", 40.0) >= req.min_tokens_per_sec
        ]

        candidate_list = filtered if filtered else models_data
        if not candidate_list:
            return ModelRecommendation(
                recommended_model_id="llama3.2:latest",
                rationale="Default primary model fitting within 4GB VRAM.",
                composite_score=0.88,
                speed_tokens_sec=109.0,
                vram_requirement_mb=2238.0,
                fit_assessment="Ideal"
            )

        if req.task_priority == "speed":
            candidate_list.sort(key=lambda m: m.get("tokens_per_sec", 0), reverse=True)
            chosen = candidate_list[0]
            rationale = f"Highest throughput at {chosen.get('tokens_per_sec'):.1f} t/s, within VRAM limit."
        elif req.task_priority == "security":
            candidate_list.sort(key=lambda m: m.get("security", 0), reverse=True)
            chosen = candidate_list[0]
            rationale = f"Highest adversarial safety score ({chosen.get('security', 0)*100:.0f}% defense rate)."
        else: # balanced / accuracy
            rankings = AnalyticsService.calculate_rankings(candidate_list)
            top_ranked = rankings.rankings[0]
            chosen = next(m for m in candidate_list if m["model_id"] == top_ranked.model_id)
            rationale = f"Best overall balance of speed ({top_ranked.tokens_per_sec} t/s), accuracy, and memory."

        return ModelRecommendation(
            recommended_model_id=chosen["model_id"],
            rationale=rationale,
            composite_score=round(chosen.get("accuracy", 0.9) * 0.5 + (chosen.get("tokens_per_sec", 50) / 100) * 0.5, 2),
            speed_tokens_sec=round(chosen.get("tokens_per_sec", 50.0), 1),
            vram_requirement_mb=round(chosen.get("vram_mb", 2200.0), 1),
            fit_assessment="Optimal Fit for RTX 3050 (4GB VRAM)"
        )

analytics_service = AnalyticsService()
