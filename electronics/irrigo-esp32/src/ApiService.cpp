#include "ApiService.h"

ApiService::ApiService(const char* host, uint16_t port, const String& apiKey, const String& firmware, bool logger){
    this->host = (char*)host;
    this->port = port;
    this->apiKey = apiKey;
    this->firmware = firmware;
    this->logger = logger;
}

void ApiService::begin(){
    http.setValues(host, port, logger);
    http.begin();
}


//============================================================
//                      PRIVATE METHODS
//============================================================

void ApiService::addDefaultHeaders(HTTPRequest& request){
    request.setHeader("X-API-Key", apiKey);
    request.setHeader("Content-Type", "application/json");
    request.setHeader("Accept", "application/json");
    request.setHeader("User-Agent", firmware);
}

HTTPRequest ApiService::buildGetRequest(const String& endpoint){
    HTTPRequest request(HTTP_GET, endpoint);
    addDefaultHeaders(request);
    return request;
}

HTTPRequest ApiService::buildPostRequest(const String& endpoint, const String& payload){
    HTTPRequest request(HTTP_POST, endpoint, payload);
    addDefaultHeaders(request);

    return request;
}

bool ApiService::parseJsonResponse(HTTPResponse& response, JsonDocument& document){
    if(response.getResponseCode() != HTTP_RESPONSE_OK)
        return false;

    DeserializationError error = deserializeJson(document, response.getPayload());

    return !error;
}

//============================================================
//                      API ENDPOINTS
//============================================================

bool ApiService::getCurrentSystem(JsonDocument& payload){
    HTTPRequest httpRequest = buildGetRequest(ENDPOINT_IRRIGATION_ME);
    HTTPResponse httpResponse = http.sendRequest(httpRequest);

    return parseJsonResponse(httpResponse, payload);
}

bool ApiService::updateFirmwareVersion() {
    JsonDocument doc;
    doc["firmware_version"] = this->firmware;
    String payload;
    serializeJson(doc, payload);

    HTTPRequest request = buildPostRequest(ENDPOINT_IRRIGATION_ME_FIRMWARE, payload);
    HTTPResponse response = http.sendRequest(request);

    return response.getResponseCode() == HTTP_RESPONSE_OK;
}