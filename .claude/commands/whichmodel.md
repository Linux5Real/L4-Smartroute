Analyze what model to use for: "$ARGUMENTS"

IMPORTANT: You MUST call MCP tools using the tool-call interface, NOT via Bash. MCP tools are NOT shell commands.

## Instructions

1. If $ARGUMENTS is empty, ask the user what task they want analyzed.

2. Call the MCP tool `mcp__model-selector__analyze_task` (this is a tool call, NOT a bash command) with these parameters:
   - `prompt`: "$ARGUMENTS"
   - `graphify_path`: "./graphify-out/graph.json" (if graphify-out/ exists in the working directory, otherwise omit)

3. Parse the JSON result and present it as follows:

---

### Model Recommendation

**Complexity**: {complexity} (score: {total_score})
**Model**: `{primary.model}` | **Effort**: {primary.effort_level}
**Budget alt**: `{budget_alternative.model}` | {budget_alternative.effort_level} effort

**Blast radius**: {files_affected} files across {communities_crossed} communities
Top areas:
- {community_label} ({nodes_affected} nodes)
- ...

**Cost**: {primary cost} | Alt: {alternative cost}

➜ `/model {recommended_model_id}`

---

## Rules
- NEVER run MCP tools as bash commands
- Do NOT dump raw JSON
- If blast radius is 0: note recommendation is keyword-only
- If complexity is "critical": warn this is a high-risk cross-system change
