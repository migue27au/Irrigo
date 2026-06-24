#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>

#include "Logger.h"
#include "secrets.h"
#include "ApiService.h" 
#include "models.h"

#define FIRMWARE "IrrigoESP32/0.1"

#define PIN_ACTUATOR_1 26
#define PIN_STATUS_LED 2

#define COMMAND_POLL_MS     5000
#define SENSOR_UPLOAD_MS    30000

#define WIFI_MAX_CONNECTION_ATTEMPS 20
#define HEARTBEAT_INTERVAL 500 // ms

Logger logger;
ApiService api(SERVER_HOST, SERVER_PORT, API_KEY, FIRMWARE, true);
JsonDocument jsonResponse; 
IrrigationSystem me;

unsigned long HEARTBEAT_PREVIOUS_MILLIS = 0;

void heartbeat() {
    unsigned long currentMillis = millis();
    if (currentMillis - HEARTBEAT_PREVIOUS_MILLIS >= HEARTBEAT_INTERVAL) {
        HEARTBEAT_PREVIOUS_MILLIS = currentMillis;
        logger.info("Heartbeat");
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
    }
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED)
        return;

    logger.info("WiFi > Connecting...");
    logger.info("WiFi > SSID: ", WIFI_SSID);
    logger.info("WiFi > PASS: ", WIFI_PASSWORD);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;

    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_MAX_CONNECTION_ATTEMPS) {
        delay(500);
        Serial.print(WiFi.status());
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        logger.ok("WiFi > Connected");
        logger.info("WiFi > IP: ", WiFi.localIP());
        logger.info("WiFi > Attempts: ", attempts);
    } 
    else {
        logger.bad("WiFi > Connection FAILED");
        logger.info("WiFi > Attempts: ", attempts);
        logger.warn("WiFi > Restarting ESP32...");

        delay(2000);
        ESP.restart();
    }
}

void initPins(){
    logger.info("Pins > Initializing...");
    pinMode(PIN_ACTUATOR_1, OUTPUT);
    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_ACTUATOR_1, LOW);
    logger.ok("Pins > Initialized");
}

//=========================================================
//                         SETUP
//=========================================================
void setup()
{
    Serial.begin(115200);

    logger.ok("Firmware: ", FIRMWARE);

    initPins();
    connectWiFi();

    logger.info("API Service > Starting...");
    api.begin();
    logger.ok("API Service > Started");

    logger.info("API > getCurrentSystem...");
    jsonResponse.clear();
    if (api.getCurrentSystem(jsonResponse)) {
        logger.ok("API > Response OK");

        me.system.id = jsonResponse["id"];
        me.system.alias = jsonResponse["alias"];
        me.system.firmware = FIRMWARE;

        logger.info("API > getCurrentSystem > ID", me.system.id);
        logger.info("API > getCurrentSystem > Alias", me.system.alias);
        logger.info("API > getCurrentSystem > FIRMWARE", me.system.firmware);
    } else {
        logger.bad("API > Unexpected error");
    }

    logger.info("API > updateFirmwareVersion...");
    if (api.updateFirmwareVersion()) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error");
    }
}


//=========================================================
//                         LOOP
//=========================================================
void loop()
{
    if(WiFi.status() != WL_CONNECTED){
        connectWiFi();
    }

    unsigned long now = millis();

    heartbeat();
}