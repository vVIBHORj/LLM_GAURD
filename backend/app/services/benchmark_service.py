from typing import List, Dict, Any
from backend.app.schemas.benchmark import ParetoPoint, ModelBenchmarkScore

class BenchmarkService:
    """
    Computes comparative multi-model benchmark statistics and Pareto frontiers.
    """

    @staticmethod
    def calculate_pareto_frontier(points: List[Dict[str, Any]]) -> List[ParetoPoint]:
        """
        Identifies non-dominated models in (Tokens/sec, Accuracy Rate) space.
        A model is Pareto-optimal if no other model has BOTH strictly higher speed AND higher accuracy.
        """
        pareto_points: List[ParetoPoint] = []
        for i, p1 in enumerate(points):
            dominated = False
            for j, p2 in enumerate(points):
                if i != j:
                    if (p2["tokens_per_sec"] >= p1["tokens_per_sec"] and
                        p2["accuracy_rate"] >= p1["accuracy_rate"] and
                        (p2["tokens_per_sec"] > p1["tokens_per_sec"] or p2["accuracy_rate"] > p1["accuracy_rate"])):
                        dominated = True
                        break

            pareto_points.append(ParetoPoint(
                model_id=p1["model_id"],
                tokens_per_sec=round(p1["tokens_per_sec"], 1),
                accuracy_rate=round(p1["accuracy_rate"], 2),
                peak_vram_mb=round(p1.get("peak_vram_mb", 0.0), 1),
                is_pareto_optimal=not dominated
            ))

        return pareto_points

benchmark_service = BenchmarkService()
