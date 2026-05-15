"""Propagation graph builder for Phase 2 supply-chain tracing."""
from typing import Any, Dict, List


class PropagationGraphBuilder:
    """Convert trace journey steps into nodes and edges for UI/API responses."""

    def build(self, journey: List[Dict[str, Any]]) -> Dict[str, Any]:
        nodes = []
        edges = []
        for index, step in enumerate(journey):
            node_id = f"n{index}"
            nodes.append({
                "id": node_id,
                "channel": step.get("channel"),
                "hash": step.get("hash") or step.get("payload_hash"),
                "timestamp": step.get("timestamp"),
                "trust_score": step.get("trust_score"),
                "decision": step.get("decision"),
            })
            if index > 0:
                edges.append({"from": f"n{index - 1}", "to": node_id, "transform": step.get("transform")})
        return {"nodes": nodes, "edges": edges}
