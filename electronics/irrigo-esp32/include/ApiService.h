#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32HTTP.h>

#define ENDPOINT_IRRIGATION_ME "/irrigation-systems/me"
#define ENDPOINT_IRRIGATION_ME_FIRMWARE "/irrigation-systems/me/firmware"

class ApiService {
public:

    ApiService(const char* host, uint16_t port, const String& apiKey, const String& firmware, bool logger = false);

    void begin();

    bool getCurrentSystem(JsonDocument& response);
    bool updateFirmwareVersion();

private:

    HTTP http;

    String apiKey;
    String firmware;

    char* host;
    uint16_t port;
    bool logger;

    
    // Añade automáticamente: X-API-Key, Content-Type, Accept, User-Agent    
    void addDefaultHeaders(
        HTTPRequest& request
    );

    // Helpers
    HTTPRequest buildGetRequest(const String& endpoint);
    HTTPRequest buildPostRequest(const String& endpoint, const String& payload);
    bool parseJsonResponse(HTTPResponse& response, JsonDocument& document);
};