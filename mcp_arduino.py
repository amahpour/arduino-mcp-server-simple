from fastmcp import FastMCP
import serial.tools.list_ports
import asyncio
import subprocess
import os
import re

mcp = FastMCP(name="ArduinoMCPMinimal")

@mcp.tool()
def list_ports() -> list[dict]:
    """Return USB/serial ports."""
    return [
        {"device": p.device, "description": p.description, "hwid": p.hwid}
        for p in serial.tools.list_ports.comports()
    ]

@mcp.tool()
def ping() -> str:
    """Simple ping for testing."""
    return "pong"

# --- Additional tools ---
FQBN_RE = re.compile(r'^[\w]+:[\w]+:[\w]+$')
PORT_RE = re.compile(r'^(COM\d+|/dev/(tty|cu)[\w\d.-]+)$')

PORT_FQBN_CACHE = {}

def cache_ports_and_fqbns():
    """Populate PORT_FQBN_CACHE with port->fqbn mapping and print summary."""
    import json
    global PORT_FQBN_CACHE
    result = subprocess.run([
        "arduino-cli", "board", "list", "--format", "json"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARN] Failed to run arduino-cli board list: {result.stderr}")
        return
    boards = json.loads(result.stdout)
    print("\n[INFO] Arduino board detection summary:")
    for portinfo in boards.get("detected_ports", []):
        port = portinfo.get("port", {}).get("address")
        found = False
        for match in portinfo.get("matching_boards", []):
            fqbn = match.get("fqbn")
            if fqbn:
                PORT_FQBN_CACHE[port] = fqbn
                print(f"  Port: {port}  FQBN: {fqbn}")
                found = True
        if not found:
            print(f"  Port: {port}  [WARN] No FQBN detected. Board may be unrecognized or missing package.")
    print("[INFO] End of board detection summary.\n")

def detect_fqbn(port: str) -> str:
    """Detect the FQBN for a given port using cache or arduino-cli board list."""
    import json
    if port in PORT_FQBN_CACHE:
        return PORT_FQBN_CACHE[port]
    # Fallback to live detection
    result = subprocess.run([
        "arduino-cli", "board", "list", "--format", "json"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to run arduino-cli board list: {result.stderr}")
    boards = json.loads(result.stdout)
    print("DEBUG: arduino-cli board list output:", json.dumps(boards, indent=2))
    for portinfo in boards.get("detected_ports", []):
        if portinfo.get("port", {}).get("address") == port:
            for match in portinfo.get("matching_boards", []):
                fqbn = match.get("fqbn")
                if fqbn:
                    PORT_FQBN_CACHE[port] = fqbn
                    return fqbn
    raise ValueError(
        f"Could not auto-detect FQBN for port {port}.\n"
        f"arduino-cli output: {json.dumps(boards, indent=2)}\n"
        "Please specify fqbn explicitly."
    )

async def _run_cli(*args):
    """Run arduino-cli with the given arguments and return output.
    Always sets the working directory to the workspace root for agentic workflows.
    Uses the WORKSPACE environment variable if set, otherwise defaults to the parent directory of this file.
    """
    import pathlib
    workspace = os.environ.get("WORKSPACE")
    if not workspace:
        # Default to the parent directory of this file
        workspace = str(pathlib.Path(__file__).parent.resolve())
    proc = await asyncio.create_subprocess_exec(
        "arduino-cli", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"arduino-cli {' '.join(args)} failed:\n{stderr.decode()}")
    return stdout.decode()

@mcp.tool()
async def compile(sketch: str, fqbn: str = None, port: str = None):
    """arduino-cli compile. If fqbn is not provided, auto-detect it using port."""
    if fqbn is None:
        if port is None:
            raise ValueError("Either fqbn or port must be provided for compile.")
        fqbn = detect_fqbn(port)
    if not FQBN_RE.match(fqbn):
        raise ValueError(f"Invalid FQBN: {fqbn}")
    if not os.path.exists(sketch):
        raise ValueError(f"Sketch {sketch} does not exist.")
    return await _run_cli("compile", "--fqbn", fqbn, sketch)

@mcp.tool()
async def upload(sketch: str, port: str, fqbn: str = None):
    """arduino-cli upload. If fqbn is not provided, auto-detect it using port."""
    if fqbn is None:
        fqbn = detect_fqbn(port)
    if not FQBN_RE.match(fqbn):
        raise ValueError(f"Invalid FQBN: {fqbn}")
    if not os.path.exists(sketch):
        raise ValueError(f"Sketch {sketch} does not exist.")
    if not PORT_RE.match(port):
        raise ValueError(f"Invalid port: {port}")
    return await _run_cli("upload", "-p", port, "--fqbn", fqbn, sketch)

@mcp.tool()
async def serial_send(port: str, baud: int, message: str, timeout: float = 2):
    """Write a line, read one response."""
    if not PORT_RE.match(port):
        raise ValueError(f"Invalid port: {port}")
    import serial
    loop = asyncio.get_event_loop()
    def _io():
        with serial.Serial(port, baud, timeout=timeout) as ser:
            ser.write((message + "\n").encode())
            ser.flush()
            return ser.readline().decode(errors="replace").strip()
    return await loop.run_in_executor(None, _io)

if __name__ == "__main__":
    cache_ports_and_fqbns()
    mcp.run() 