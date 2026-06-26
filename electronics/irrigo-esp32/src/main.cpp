#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <time.h>

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
System me;
MeasureBatch measures;

unsigned long HEARTBEAT_PREVIOUS_MILLIS = 0;

void heartbeat() {
    unsigned long currentMillis = millis();
    if (currentMillis - HEARTBEAT_PREVIOUS_MILLIS >= HEARTBEAT_INTERVAL) {
        HEARTBEAT_PREVIOUS_MILLIS = currentMillis;
        logger.info("Heartbeat");
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
    }
}

String getISO8601Time()
{
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        return "";
    }

    char buffer[40];

    // Fecha + hora hasta segundos
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S", &timeinfo);

    // Milliseconds (ESP32 freeRTOS tick)
    uint32_t ms = millis() % 1000;

    char finalBuffer[60];
    snprintf(finalBuffer, sizeof(finalBuffer), "%s.%03luZ", buffer, ms);

    return String(finalBuffer);
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

    logger.info("Time > Initialing NTP configuration...");
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    logger.ok("Time > NTP configurated");

    logger.info("API Service > Starting...");
    api.begin();
    logger.ok("API Service > Started");
    
    logger.info("API > getCurrentSystem...");
    jsonResponse.clear();
    if (api.getCurrentSystem(jsonResponse)) {
        logger.ok("API > Response OK");
        JsonObject obj = jsonResponse.as<JsonObject>();
        me.system.fromJSON(obj);
        me.system.firmware = FIRMWARE;

        logger.info("API > getCurrentSystem > ID", me.system.id);
        logger.info("API > getCurrentSystem > FIRMWARE", me.system.firmware);
    } else {
        logger.bad("API > Unexpected error");
        logger.bad("API > Cannot connect to server");
    }

    logger.info("API > updateFirmwareVersion...");
    if (api.updateFirmwareVersion()) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error");
    }

    logger.info("SENSORS > Initializing...");
    me.sensors[0].set("temp1", "temperature", "ºC");
    me.sensors[1].set("temp2", "temperature", "ºC");
    me.sensors[1].set("humi1", "humidity", "%");
    me.sensors[1].set("humi2", "humidity", "%");
    me.sensors[1].set("soil1", "soil moisture", "%");
    me.sensors[1].set("soil2", "soil moisture", "%");
    me.sensors[1].set("wind", "wind speed", "m/s");
    me.sensors[1].set("rain", "precipitation", "L/m2");    
    me.sensorCount = 8;

    logger.ok("SENSORS > Initialized");

    logger.info("API > createSensors...");
    if (api.createSensors(me.sensorsToJson())) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error");
    }

    logger.info("API > getActuators...");
    jsonResponse.clear();
    if (api.getActuators(jsonResponse)) {
        logger.ok("API > getActuators Response OK");
        me.actuatorCount = jsonResponse.size();
        logger.info("Actuators > ", String(me.actuatorCount)); 
        JsonArray arr = jsonResponse.as<JsonArray>();
        for (size_t i = 0; i < arr.size(); i++) {
            JsonObject actuatorJSON = arr[i];

            me.actuators[i].fromJSON(actuatorJSON);
            
            logger.info("API > getCommandsOfActuator", me.actuators[i].id);
            JsonDocument actuatorsDoc;
            if (api.getCommandsOfActuator(String(me.actuators[i].id), actuatorsDoc)) {
                logger.ok("API > getCommandsOfActuator Response OK");
                String output;
                serializeJson(actuatorsDoc, output);
                Serial.println(output);
                me.actuators[i].getCommandsFromJSON(actuatorsDoc["commands"].as<JsonArray>());

                for(int j = 0; j < me.actuators[i].commandsCount; j++){
                    if(me.actuators[i].commands[j].trigger_type == COMMAND_TRIGGER_AUTOMATIC){
                        logger.info("API > getRulesOfCommand: ", me.actuators[i].commands[j].id);
                        JsonDocument rulesDoc;
                        if (api.getRulesOfCommand(String(me.actuators[i].commands[j].id), rulesDoc)) {
                            logger.ok("API > getRulesOfCommand Response OK");
                            me.actuators[i].commands[j].getRulesGroupFromJSON(rulesDoc["groups"].as<JsonArray>());
                        } else {
                            logger.bad("API > getRulesOfCommand Unexpected error");
                        }
                    }
                }
            } else {
                logger.bad("API > getCommandsOfActuator Unexpected error");
            }
        }
    } else {
        logger.bad("API > getActuators Unexpected error");
    }
    logger.ok("SETUP finished");
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

    /*TEST INGEST*/
    logger.info("Time > Getting time ISO");
    String time = getISO8601Time();
    if (time.length() > 0){
        logger.info("Time > ISO time obtained: ", time);
        
        for(int i = 0; i < me.sensorCount; i++){
            measures.add(me.sensors[i].key, random(0, 10000)/100.0, time);
        }
    } else {
        logger.info("Time > Error getting time");
    }

    if(measures.measureCount > MAX_MEASURES*0.66){
        jsonResponse.clear();
        jsonResponse["data"] = measures.toJSON();
        measures.clear();
        logger.info("API > ingestMeasures...");
        if (api.ingestMeasures(jsonResponse)) {
            logger.ok("API > Response OK");
        } else {
            logger.bad("API > Unexpected error" );
        }
    }
    
    delay(5000);
}