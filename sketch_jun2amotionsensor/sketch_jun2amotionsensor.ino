#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "NEERAJ";
const char* password = "12345678";

#define PIR_PIN D2

ESP8266WebServer server(80);

void handleRoot() {
  String html = "<h1>ESP8266 PIR Sensor</h1>";
  html += "<p>Visit /motion to get PIR status.</p>";
  server.send(200, "text/html", html);
}

void handleMotion() {
  int motion = digitalRead(PIR_PIN);

  if (motion == HIGH) {
    server.send(200, "text/plain", "1");
  } else {
    server.send(200, "text/plain", "0");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIR_PIN, INPUT);

  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/motion", handleMotion);

  server.begin();

  Serial.println("Web server started.");
  Serial.println("Waiting for PIR sensor warm-up...");
  delay(30000);  // PIR warm-up
  Serial.println("PIR ready.");
}

void loop() {
  server.handleClient();

  static int lastState = LOW;
  int currentState = digitalRead(PIR_PIN);

  if (currentState != lastState) {
    if (currentState == HIGH) {
      Serial.println("Motion Detected!");
    } else {
      Serial.println("Area Clear");
    }

    lastState = currentState;
  }
}