#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// ── WiFi credentials ─────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ── Render Django backend ────────────────────────────────────────
const char* DJANGO_BASE_URL = "https://scan2serve.online";

// Use the same value as ESP32_SECRET_TOKEN in Render environment variables
const char* ESP32_SECRET_TOKEN = "your_secret_token_here"//"scan2serve-esp32-secret-123";

// Table ID for this ESP32
const int TABLE_ID = 1;

// ── Pin definitions ──────────────────────────────────────────────
const int IR_PIN             = 32;
const int SERVICE_BUTTON_PIN = 33;
const int ORDER_BUTTON_PIN   = 27;
const int BUZZER_PIN         = 25;

// ── State ────────────────────────────────────────────────────────
bool tableOccupied     = false;
bool lastTableOccupied = false;

int serviceButtonState     = HIGH;
int lastServiceButtonState = HIGH;

int orderButtonState     = HIGH;
int lastOrderButtonState = HIGH;

// Polling state
unsigned long lastOrderPollTime = 0;
const unsigned long ORDER_POLL_INTERVAL = 5000; // 5 seconds

int lastSeenOrderId = 0;
bool orderPollInitialized = false;

// ── Forward declarations ─────────────────────────────────────────
void sendTableStatus(bool occupied);
void checkForNewOrders();
void triggerBuzzer(int frequency, int durationMs);
int extractIntValue(String body, String key, int defaultValue);
bool extractBoolValue(String body, String key, bool defaultValue);

// ─────────────────────────────────────────────────────────────────

void setup() {
  pinMode(IR_PIN, INPUT);
  pinMode(SERVICE_BUTTON_PIN, INPUT_PULLUP);
  pinMode(ORDER_BUTTON_PIN, INPUT_PULLUP);

  Serial.begin(115200);
  Serial.println("Scan2Serve ESP32 Kitchen/Table IoT Starting...");

  ledcAttach(BUZZER_PIN, 2000, 8);
  ledcWriteTone(BUZZER_PIN, 0);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi connected. ESP32 IP: ");
  Serial.println(WiFi.localIP());

  Serial.println("ESP32 will now poll Render backend for new orders.");
}

// ─────────────────────────────────────────────────────────────────

void loop() {
  // ── IR sensor → table occupancy ────────────────────────────────
  int irValue = digitalRead(IR_PIN);
  tableOccupied = (irValue == LOW); // LOW = object detected

  if (tableOccupied != lastTableOccupied) {
    Serial.printf("Table Status: %s\n", tableOccupied ? "OCCUPIED" : "AVAILABLE");
    sendTableStatus(tableOccupied);
    lastTableOccupied = tableOccupied;
  }

  // ── Service button ─────────────────────────────────────────────
  serviceButtonState = digitalRead(SERVICE_BUTTON_PIN);

  if (lastServiceButtonState == HIGH && serviceButtonState == LOW) {
    Serial.println("Customer Service Requested!");
    triggerBuzzer(1500, 1000);
  }

  lastServiceButtonState = serviceButtonState;

  // ── Manual kitchen buzzer test button ──────────────────────────
  orderButtonState = digitalRead(ORDER_BUTTON_PIN);

  if (lastOrderButtonState == HIGH && orderButtonState == LOW) {
    Serial.println("Manual kitchen buzzer test triggered.");
    triggerBuzzer(2500, 2000);
  }

  lastOrderButtonState = orderButtonState;

  // ── Check Render backend for new orders every 5 seconds ────────
  if (millis() - lastOrderPollTime >= ORDER_POLL_INTERVAL) {
    lastOrderPollTime = millis();
    checkForNewOrders();
  }

  delay(50);
}

// ─────────────────────────────────────────────────────────────────
// Send table occupancy status to Django
// POST /tables/<TABLE_ID>/ir-status/
// ─────────────────────────────────────────────────────────────────

void sendTableStatus(bool occupied) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected. Skipping table status update.");
    return;
  }

  WiFiClientSecure client;
  client.setInsecure(); 
  // For final production, use a real root certificate instead of setInsecure().

  HTTPClient http;

  String url = String(DJANGO_BASE_URL) + "/tables/" + String(TABLE_ID) + "/ir-status/";

  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-ESP32-Token", ESP32_SECRET_TOKEN);

  String payload = occupied ? "{\"occupied\": true}" : "{\"occupied\": false}";

  Serial.print("[HTTP] Sending table status to: ");
  Serial.println(url);
  Serial.print("[HTTP] Payload: ");
  Serial.println(payload);

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("[HTTP] Table status response code: %d\n", httpCode);
    Serial.println(response);
  } else {
    Serial.printf("[HTTP] Table status failed: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
}

// ─────────────────────────────────────────────────────────────────
// ESP32 polls Django for new orders
// GET /orders/iot/new-orders/?last_id=<lastSeenOrderId>
// ─────────────────────────────────────────────────────────────────

void checkForNewOrders() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected. Skipping order check.");
    return;
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;

  String url = String(DJANGO_BASE_URL) + "/orders/iot/new-orders/?last_id=" + String(lastSeenOrderId);

  http.begin(client, url);
  http.addHeader("X-ESP32-Token", ESP32_SECRET_TOKEN);

  Serial.print("[HTTP] Checking new orders: ");
  Serial.println(url);

  int httpCode = http.GET();

  if (httpCode == 200) {
    String body = http.getString();

    Serial.println("[HTTP] New order API response:");
    Serial.println(body);

    bool newOrders = extractBoolValue(body, "new_orders", false);
    int latestOrderId = extractIntValue(body, "latest_order_id", lastSeenOrderId);
    int count = extractIntValue(body, "count", 0);

    // First successful poll only initializes the last seeno rder.
    // This prevents buzzer triggering for old orders after ESP32 restarts.
    if (!orderPollInitialized) {
      lastSeenOrderId = latestOrderId;
      orderPollInitialized = true;

      Serial.print("[IoT] Initial sync complete. Last seen order ID: ");
      Serial.println(lastSeenOrderId);

      http.end();
      return;
    }

    if (newOrders && latestOrderId > lastSeenOrderId) {
      Serial.printf("[IoT] %d new order(s) found. Latest order ID: %d\n", count, latestOrderId);

      triggerBuzzer(2500, 2000);

      lastSeenOrderId = latestOrderId;
    } else {
      Serial.println("[IoT] No new orders.");
      lastSeenOrderId = latestOrderId;
    }

  } else if (httpCode > 0) {
    String body = http.getString();
    Serial.printf("[HTTP] Order check failed. Code: %d\n", httpCode);
    Serial.println(body);
  } else {
    Serial.printf("[HTTP] Order check request failed: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
}

// ─────────────────────────────────────────────────────────────────
// Simple JSON integer extractor
// Example: extractIntValue(body, "latest_order_id", 0)
// ─────────────────────────────────────────────────────────────────

int extractIntValue(String body, String key, int defaultValue) {
  String searchKey = "\"" + key + "\"";
  int keyIndex = body.indexOf(searchKey);

  if (keyIndex == -1) {
    return defaultValue;
  }

  int colonIndex = body.indexOf(":", keyIndex);

  if (colonIndex == -1) {
    return defaultValue;
  }

  int startIndex = colonIndex + 1;

  while (
    startIndex < body.length() &&
    (body[startIndex] == ' ' || body[startIndex] == '\n' || body[startIndex] == '\r' || body[startIndex] == '\t')
  ) {
    startIndex++;
  }

  int endIndex = startIndex;

  while (endIndex < body.length() && isDigit(body[endIndex])) {
    endIndex++;
  }

  if (endIndex == startIndex) {
    return defaultValue;
  }

  return body.substring(startIndex, endIndex).toInt();
}

// ─────────────────────────────────────────────────────────────────
// Simple JSON boolean extractor
// Example: extractBoolValue(body, "new_orders", false)
// ─────────────────────────────────────────────────────────────────

bool extractBoolValue(String body, String key, bool defaultValue) {
  String searchKey = "\"" + key + "\"";
  int keyIndex = body.indexOf(searchKey);

  if (keyIndex == -1) {
    return defaultValue;
  }

  int colonIndex = body.indexOf(":", keyIndex);

  if (colonIndex == -1) {
    return defaultValue;
  }

  int startIndex = colonIndex + 1;

  while (
    startIndex < body.length() &&
    (body[startIndex] == ' ' || body[startIndex] == '\n' || body[startIndex] == '\r' || body[startIndex] == '\t')
  ) {
    startIndex++;
  }

  if (body.substring(startIndex, startIndex + 4) == "true") {
    return true;
  }

  if (body.substring(startIndex, startIndex + 5) == "false") {
    return false;
  }

  return defaultValue;
}

// ─────────────────────────────────────────────────────────────────
// Buzzer function
// ─────────────────────────────────────────────────────────────────

void triggerBuzzer(int frequency, int durationMs) {
  ledcWriteTone(BUZZER_PIN, frequency);
  delay(durationMs);
  ledcWriteTone(BUZZER_PIN, 0);
}