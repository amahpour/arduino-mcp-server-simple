// Echo Serial Example for MCP Server Validation
// Receives serial input and echoes it back with a unique prefix

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }
  Serial.println("[ECHO_SERIAL] Ready");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      Serial.print("[ECHO_SERIAL] Received: ");
      Serial.println(input);
    }
  }
} 