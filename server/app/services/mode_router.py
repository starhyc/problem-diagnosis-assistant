from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List


class DiagnosisMode(str, Enum):
    DIRECT = "direct"
    PLAN_EXECUTE = "plan_execute"
    REACT = "react"
    HIERARCHICAL = "hierarchical"


LEGACY_MODE_MAP: Dict[str, str] = {
    "prd_minimal": DiagnosisMode.DIRECT.value,
    "prd_standard": DiagnosisMode.PLAN_EXECUTE.value,
    "prd_deep": DiagnosisMode.REACT.value,
    "prd_swarm": DiagnosisMode.HIERARCHICAL.value,
}


def normalize_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    normalized = mode.strip().lower()
    return LEGACY_MODE_MAP.get(normalized, normalized)


@dataclass
class TaskFeatures:
    step_complexity: int
    cross_domain_count: int
    uncertainty: int


class ModeRouter:
    """Rule-based mode router by task feature matrix."""

    def recommend_mode(self, features: TaskFeatures) -> Dict[str, Any]:
        score = (
            features.step_complexity * 0.4
            + features.cross_domain_count * 0.35
            + features.uncertainty * 0.25
        )

        reasons: List[str] = []
        if features.step_complexity >= 8:
            reasons.append("步骤复杂度高")
        elif features.step_complexity >= 5:
            reasons.append("步骤复杂度中等")

        if features.cross_domain_count >= 3:
            reasons.append("涉及多领域协同")
        elif features.cross_domain_count >= 2:
            reasons.append("存在跨域分析需求")

        if features.uncertainty >= 7:
            reasons.append("问题不确定性较高")
        elif features.uncertainty >= 4:
            reasons.append("存在一定不确定性")

        if score >= 7.5:
            mode = DiagnosisMode.HIERARCHICAL
        elif score >= 6.0:
            mode = DiagnosisMode.REACT
        elif score >= 3.5:
            mode = DiagnosisMode.PLAN_EXECUTE
        else:
            mode = DiagnosisMode.DIRECT

        if not reasons:
            reasons.append("任务特征整体简单")

        return {
            "mode": mode.value,
            "score": round(score, 2),
            "features": {
                "step_complexity": features.step_complexity,
                "cross_domain_count": features.cross_domain_count,
                "uncertainty": features.uncertainty,
            },
            "reasons": reasons,
        }


mode_router = ModeRouter()
