# MCP Example Basic

## Agentic Arduino Workflow

This project supports fully agentic workflows for Arduino development and upload using MCP tools.

### Sketch Path Conventions
- **Always specify the sketch path as the folder containing the `.ino` file**, not the `.ino` file itself.
- The path should be **relative to the workspace root** (e.g., `sketches/echo_serial`).

### Working Directory Handling
- All Arduino CLI commands are run with the working directory set to the workspace root.
- The agent uses the `WORKSPACE` environment variable if set, or defaults to the directory containing the agent script.
- This ensures that relative paths work reliably for both human and agent workflows.

### Environment Variables
- `WORKSPACE`: (optional) Set this to the absolute path of your project root to control where subprocesses run.

### Example Usage
```
# Upload a sketch (from workspace root)
arduino-cli upload -p <port> --fqbn <fqbn> sketches/echo_serial
```

### Troubleshooting
- If you see `No such file or directory`, ensure you are passing the sketch **folder** and that your working directory is the project root.
- For agentic workflows, the agent will handle working directory and path resolution automatically. 