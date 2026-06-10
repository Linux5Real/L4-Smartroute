Open the Model Selector settings UI.

IMPORTANT: You MUST use the Bash tool to run shell commands. Do NOT use MCP tools for this.

## Instructions

1. Run the following bash command to start the settings server in the background:

```bash
pkill -f "model-selector-setup" 2>/dev/null; model-selector-setup &
sleep 1
echo "READY"
```

2. Then tell the user exactly this (copy verbatim, keep the formatting):

---

**Model Selector Settings** is running at:

**http://localhost:6639**

Open that link in your browser to configure:
- Which models are available
- Optimization mode (Quality / Balanced / Performance / Token Saver)
- Graphify path and budget settings

**After saving**, changes to the optimization mode take effect immediately.
Changes to the **model list** require a **Claude Code restart** to apply.

To stop the settings server, run: `pkill -f model-selector-setup`

---

3. Do NOT open the URL yourself. Just show the message above.
