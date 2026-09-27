"""Trust-but-verify layer: every LLM suggestion is checked against the real
graph before it is even shown to the user. This is what keeps the AI feature
from ever corrupting the schedule."""
from ..engine.graph import Graph


def validate_suggestions(raw_suggestions: list, new_task_id: str,
                          existing_task_ids: set, graph: Graph) -> list:
    valid = []
    for s in raw_suggestions:
        pred_id = s.get("predecessor_id")
        confidence = s.get("confidence", 0)
        reason = s.get("reason", "")

        if not pred_id or pred_id == new_task_id:
            continue
        if pred_id not in existing_task_ids:
            continue
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            confidence = 0.5

        would_cycle, _ = graph.would_create_cycle(pred_id, new_task_id)
        if would_cycle:
            continue  # never surface a suggestion that would break the DAG

        valid.append({
            "predecessor_id": pred_id,
            "successor_id": new_task_id,
            "reason": str(reason)[:200],
            "confidence": float(confidence),
        })

    valid.sort(key=lambda x: x["confidence"], reverse=True)
    return valid
