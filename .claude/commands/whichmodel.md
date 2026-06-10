Analyze what model to use for: "$ARGUMENTS"

IMPORTANT: You MUST call MCP tools using the tool-call interface, NOT via Bash. MCP tools are NOT shell commands.

## Instructions

1. If $ARGUMENTS is empty, ask the user what task they want analyzed.

2. Call the MCP tool `mcp__model-selector__analyze_task` (this is a tool call, NOT a bash command) with these parameters:
   - `prompt`: "$ARGUMENTS"
   - `graphify_path`: "./graphify-out/graph.json" (if graphify-out/ exists in the working directory, otherwise omit)

3. If `recommendation.routing.ai_review.required` is true:
   - Internally rerank only `recommendation.routing.ai_review.candidates`.
   - Follow `recommendation.routing.ai_review.policy`.
   - Pick exactly one candidate model id and effort level.
   - Do not pick a model outside the candidate list.
   - Treat this as the final recommendation.

4. If `recommendation.routing.ai_review.required` is false, use `recommendation.primary`.

5. Present the result as follows:

---

### Model Recommendation

**Complexity**: {complexity} (score: {total_score})
**Task type**: `{routing.task_type}`
**Router**: `{routing.router_mode}`{if ai_review.required: " + AI review"}
**Model**: `{final_model}` | **Effort**: {final_effort}
**Budget alt**: `{budget_alternative.model}` | {budget_alternative.effort_level} effort

**Blast radius**: {files_affected} files across {communities_crossed} communities
Top areas:
- {community_label} ({nodes_affected} nodes)
- ...

**Cost**: {primary cost} | Alt: {alternative cost}
Top model fits:
- `{routing.scored_candidates[0].model}` score {score}, fit {fit}, ${cost_per_1m}/1M
- `{routing.scored_candidates[1].model}` score {score}, fit {fit}, ${cost_per_1m}/1M
- `{routing.scored_candidates[2].model}` score {score}, fit {fit}, ${cost_per_1m}/1M

Reason:
{one short reason from deterministic or AI review}

➜ `/model {recommended_model_id}`

---

## Rules
- NEVER run MCP tools as bash commands
- Do NOT dump raw JSON
- If AI review is required, mention it in one short phrase only
- If blast radius is 0: note recommendation is keyword-only
- If complexity is "critical": warn this is a high-risk cross-system change
