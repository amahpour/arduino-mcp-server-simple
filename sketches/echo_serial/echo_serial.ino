/*
 * Echo Serial Example for MCP Server Validation
 * 
 * This sketch demonstrates a simple serial echo server that:
 * - Receives serial input from the MCP server
 * - Echoes it back with a unique prefix for identification
 * - Provides a reliable way to test serial communication
 * 
 * Purpose: This sketch serves as a test case for the Arduino MCP server,
 * allowing AI agents to verify that serial communication is working
 * correctly between the MCP server and Arduino board.
 */

void setup() {
  // Initialize serial communication at 115200 baud rate
  // This matches the baud rate expected by the MCP server
  Serial.begin(115200);
  
  // Wait for serial port to connect (required for some boards)
  // This ensures the serial connection is established before proceeding
  while (!Serial) { 
    ; // Wait for serial port to connect
  }
  
  // Send ready message to indicate the sketch is running
  // This helps verify that the upload was successful
  Serial.println("[ECHO_SERIAL] Ready");
}

void loop() {
  // Check if there's data available to read from serial
  if (Serial.available()) {
    // Read the incoming string until newline character
    // This reads the complete message sent by the MCP server
    String input = Serial.readStringUntil('\n');
    
    // Remove any whitespace from the beginning and end
    // This cleans up the input and handles any extra characters
    input.trim();
    
    // Only process non-empty messages
    if (input.length() > 0) {
      // Print the received message with a prefix for identification
      // The prefix "[ECHO_SERIAL] Received: " helps distinguish this output
      // from other serial messages and confirms the message was received
      Serial.print("[ECHO_SERIAL] Received: ");
      Serial.println(input);
    }
  }
} 