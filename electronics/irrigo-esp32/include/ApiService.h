#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32HTTP.h>

#define ENDPOINT_IRRIGATION_ME "/irrigation-systems/me"
#define ENDPOINT_IRRIGATION_ME_FIRMWARE "/irrigation-systems/me/firmware"
#define ENDPOINT_SENSORS_CREATE "/sensors/create"
#define ENDPOINT_SENSORS_INGEST "/sensors/ingest"
#define ENDPOINT_ACTUATORS_GET "/actuators/get"
#define ENDPOINT_COMMANDS_GET "/actuators/{actuator_id}/commands"
#define ENDPOINT_RULES "/rules/{command_id}/get"

#define COMMAND_TRIGGER_MANUAL "manual"
#define COMMAND_TRIGGER_AUTOMATIC "automatic"

class ApiService {
public:

    ApiService(const char* host, uint16_t port, const char* apiKey, const char* firmware, bool logger = false);

    void begin();

    bool getCurrentSystem(JsonDocument& payload);
    bool updateFirmwareVersion();
    bool createSensors(JsonDocument doc);
    bool ingestMeasures(JsonDocument doc);
    bool getActuators(JsonDocument& payload);
    bool getCommandsOfActuator(String actuator_id, JsonDocument& payload);
    bool getRulesOfCommand(String command_id, JsonDocument& payload);

private:
    
    HTTP http;
    char* apiKey;
    char* firmware;

    char* host;
    uint16_t port;
    bool logger;

    void addDefaultHeaders(HTTPRequest& request);   // Añade automáticamente: X-API-Key, Content-Type, Accept, User-Agent    

    // Helpers
    HTTPRequest buildGetRequest(const String& endpoint);
    HTTPRequest buildPostRequest(const String& endpoint, const String& payload);
    bool parseJsonResponse(HTTPResponse& response, JsonDocument& document);
};