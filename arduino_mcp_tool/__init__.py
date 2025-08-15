"""
Arduino MCP Server

A Model Context Protocol (MCP) server that enables AI agents to interact with Arduino boards.
Provides tools for listing ports, compiling sketches, uploading code, and serial communication.

This server acts as a bridge between AI agents and Arduino CLI, allowing automated
Arduino development workflows through the MCP protocol.
"""

from fastmcp import FastMCP
import serial.tools.list_ports
import asyncio
import subprocess
import os
import re

# Initialize the MCP server with a descriptive name
mcp = FastMCP(name="ArduinoMCP")


@mcp.tool()
def list_ports() -> list[dict]:
    """
    List all available USB/serial ports on the system.

    Returns:
        list[dict]: List of dictionaries containing port information.
            Each dict has keys: 'device', 'description', 'hwid'

    Example:
        Returns ports like:
        [
            {"device": "/dev/cu.usbmodem1234", "description": "Arduino UNO", "hwid": "USB VID:PID=2341:0043"},
            {"device": "/dev/cu.Bluetooth-Incoming-Port", "description": "n/a", "hwid": "n/a"}
        ]
    """
    return [
        {"device": p.device, "description": p.description, "hwid": p.hwid}
        for p in serial.tools.list_ports.comports()
    ]


@mcp.tool()
def ping() -> str:
    """
    Simple health check to verify the MCP server is running.

    Returns:
        str: Always returns "pong" to confirm server is responsive

    This is useful for testing connectivity and server status.
    """
    return "pong"


def detect_fqbn(port: str) -> str:
    """
    Automatically detect the FQBN (Fully Qualified Board Name) for a given port.

    Uses arduino-cli to query connected boards and find the matching FQBN
    for the specified port. This enables automatic board detection without
    requiring manual FQBN specification.

    Args:
        port (str): The serial port address (e.g., "/dev/cu.usbmodem1234")

    Returns:
        str: The FQBN for the board on the specified port

    Raises:
        RuntimeError: If arduino-cli command fails
        ValueError: If no board is detected on the specified port

    Example:
        detect_fqbn("/dev/cu.usbmodem1234") -> "arduino:avr:uno"
    """
    import json

    # Run arduino-cli to get board information in JSON format
    result = subprocess.run(
        ["arduino-cli", "board", "list", "--format", "json"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to run arduino-cli board list: {result.stderr}")

    # Parse the JSON response from arduino-cli
    boards = json.loads(result.stdout)

    # Search through detected ports to find a match
    for portinfo in boards.get("detected_ports", []):
        if portinfo.get("port", {}).get("address") == port:
            # Check all matching boards for this port
            for match in portinfo.get("matching_boards", []):
                fqbn = match.get("fqbn")
                if fqbn:
                    return fqbn

    # If no board found, raise an error
    raise ValueError(f"Could not auto-detect FQBN for port {port}")


async def _run_cli(*args):
    """
    Execute arduino-cli commands asynchronously.

    This is a helper function that runs arduino-cli with the specified arguments
    and returns the output. It handles working directory management and error
    reporting for all arduino-cli operations.

    Args:
        *args: Command line arguments to pass to arduino-cli

    Returns:
        str: The stdout output from the arduino-cli command

    Raises:
        RuntimeError: If the arduino-cli command fails (non-zero exit code)

    Note:
        Uses the WORKSPACE environment variable if set, otherwise uses current
        working directory. This ensures consistent behavior in different contexts.
    """
    # Determine working directory - prefer WORKSPACE env var, fallback to current dir
    workspace = os.environ.get("WORKSPACE", os.getcwd())

    # Create and run the subprocess
    proc = await asyncio.create_subprocess_exec(
        "arduino-cli",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workspace,  # Set working directory for the command
    )

    # Wait for completion and capture output
    stdout, stderr = await proc.communicate()

    # Check for errors
    if proc.returncode != 0:
        raise RuntimeError(f"arduino-cli {' '.join(args)} failed:\n{stderr.decode()}")

    return stdout.decode()


@mcp.tool()
async def compile(sketch: str, fqbn: str = None, port: str = None):
    """
    Compile an Arduino sketch using arduino-cli.

    Compiles the specified sketch for the target board. If FQBN is not provided,
    it will be automatically detected using the port. This enables seamless
    compilation without requiring manual board specification.

    Args:
        sketch (str): Path to the sketch directory (e.g., "sketches/echo_serial")
        fqbn (str, optional): Fully Qualified Board Name (e.g., "arduino:avr:uno")
        port (str, optional): Serial port for auto-detecting FQBN (e.g., "/dev/cu.usbmodem1234")

    Returns:
        str: Compilation output from arduino-cli

    Raises:
        ValueError: If neither fqbn nor port is provided, or if sketch doesn't exist
        RuntimeError: If compilation fails

    Example:
        await compile("sketches/echo_serial", port="/dev/cu.usbmodem1234")
    """
    # Auto-detect FQBN if not provided
    if fqbn is None:
        if port is None:
            raise ValueError("Either fqbn or port must be provided for compile.")
        fqbn = detect_fqbn(port)

    # Validate that the sketch exists
    if not os.path.exists(sketch):
        raise ValueError(f"Sketch {sketch} does not exist.")

    # Run the compilation
    return await _run_cli("compile", "--fqbn", fqbn, sketch)


@mcp.tool()
async def upload(sketch: str, port: str, fqbn: str = None):
    """
    Upload a compiled Arduino sketch to a board.

    Uploads the specified sketch to the Arduino board connected to the given port.
    If FQBN is not provided, it will be automatically detected. This function
    handles the entire upload process including board detection and error handling.

    Args:
        sketch (str): Path to the sketch directory (e.g., "sketches/echo_serial")
        port (str): Serial port where the board is connected (e.g., "/dev/cu.usbmodem1234")
        fqbn (str, optional): Fully Qualified Board Name (e.g., "arduino:avr:uno")

    Returns:
        str: Upload output from arduino-cli

    Raises:
        ValueError: If sketch doesn't exist
        RuntimeError: If upload fails

    Example:
        await upload("sketches/echo_serial", "/dev/cu.usbmodem1234")
    """
    # Auto-detect FQBN if not provided
    if fqbn is None:
        fqbn = detect_fqbn(port)

    # Validate that the sketch exists
    if not os.path.exists(sketch):
        raise ValueError(f"Sketch {sketch} does not exist.")

    # Run the upload command
    return await _run_cli("upload", "-p", port, "--fqbn", fqbn, sketch)


@mcp.tool()
async def serial_send(port: str, baud: int, message: str, timeout: float = 2):
    """
    Send a message over serial and read the response.

    Opens a serial connection to the specified port, sends the message,
    and reads back the response. This enables bidirectional communication
    with Arduino sketches that implement serial protocols.

    Args:
        port (str): Serial port to connect to (e.g., "/dev/cu.usbmodem1234")
        baud (int): Baud rate for serial communication (e.g., 9600, 115200)
        message (str): Message to send over serial
        timeout (float, optional): Timeout in seconds for reading response. Defaults to 2.

    Returns:
        str: The response received from the serial port

    Raises:
        RuntimeError: If serial communication fails

    Example:
        await serial_send("/dev/cu.usbmodem1234", 115200, "Hello Arduino!")
    """
    import serial

    # Get the current event loop for running blocking I/O
    loop = asyncio.get_event_loop()

    def _io():
        """
        Internal function to handle blocking serial I/O operations.

        This function runs in a thread pool to avoid blocking the event loop
        during serial communication operations.
        """
        # Open serial connection with specified parameters
        with serial.Serial(port, baud, timeout=timeout) as ser:
            # Send message with newline and flush to ensure transmission
            ser.write((message + "\n").encode())
            ser.flush()

            # Read response and decode, handling encoding errors gracefully
            return ser.readline().decode(errors="replace").strip()

    # Run the blocking I/O operation in a thread pool
    return await loop.run_in_executor(None, _io)


@mcp.tool()
async def serial_write(port: str, baud: int, message: str):
    """
    Send a message over serial without reading a response.

    Opens a serial connection to the specified port, sends the message,
    and immediately closes the connection. This is useful for sending
    commands or data to Arduino sketches that don't need to respond.

    Args:
        port (str): Serial port to connect to (e.g., "/dev/cu.usbmodem1234")
        baud (int): Baud rate for serial communication (e.g., 9600, 115200)
        message (str): Message to send over serial

    Returns:
        str: Confirmation message indicating successful transmission

    Raises:
        RuntimeError: If serial communication fails

    Example:
        await serial_write("/dev/cu.usbmodem1234", 115200, "LED_ON")
    """
    import serial

    # Get the current event loop for running blocking I/O
    loop = asyncio.get_event_loop()

    def _io():
        """
        Internal function to handle blocking serial write operations.

        This function runs in a thread pool to avoid blocking the event loop
        during serial communication operations.
        """
        # Open serial connection with specified parameters
        with serial.Serial(port, baud, timeout=1) as ser:
            # Send message with newline and flush to ensure transmission
            ser.write((message + "\n").encode())
            ser.flush()
            return f"Message sent successfully to {port}"

    # Run the blocking I/O operation in a thread pool
    return await loop.run_in_executor(None, _io)


@mcp.tool()
async def serial_read(port: str, baud: int, timeout: float = 2):
    """
    Read a message from serial without sending anything.

    Opens a serial connection to the specified port and waits to read
    incoming data. This is useful for monitoring serial output from
    Arduino sketches or reading sensor data.

    Args:
        port (str): Serial port to connect to (e.g., "/dev/cu.usbmodem1234")
        baud (int): Baud rate for serial communication (e.g., 9600, 115200)
        timeout (float, optional): Timeout in seconds for reading. Defaults to 2.

    Returns:
        str: The data received from the serial port, or empty string if timeout

    Raises:
        RuntimeError: If serial communication fails

    Example:
        await serial_read("/dev/cu.usbmodem1234", 115200, timeout=5)
    """
    import serial

    # Get the current event loop for running blocking I/O
    loop = asyncio.get_event_loop()

    def _io():
        """
        Internal function to handle blocking serial read operations.

        This function runs in a thread pool to avoid blocking the event loop
        during serial communication operations.
        """
        # Open serial connection with specified parameters
        with serial.Serial(port, baud, timeout=timeout) as ser:
            # Read response and decode, handling encoding errors gracefully
            data = ser.readline().decode(errors="replace").strip()
            return data if data else ""

    # Run the blocking I/O operation in a thread pool
    return await loop.run_in_executor(None, _io)


def main() -> None:
    """Entry point for console script."""
    mcp.run()


if __name__ == "__main__":
    # Start the MCP server when run directly
    main()
