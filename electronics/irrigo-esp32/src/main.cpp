#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
// TODO TODO TODO SD library
// TODO TODO TODO RTC library
#include <time.h>

#include "Logger.h"
#include "secrets.h"
#include "ApiService.h" 
#include "models.h"

static char FIRMWARE[] = "IrrigoESP32/0.1";

#define PIN_ACTUATOR_0 26
#define PIN_ACTUATOR_1 27
#define PIN_ACTUATOR_2 14
#define PIN_ACTUATOR_3 12
#define PIN_STATUS_LED 2

const int ACTUATOR_PINS[MAX_ACTUATORS] = {
    PIN_ACTUATOR_0,
    PIN_ACTUATOR_1,
    PIN_ACTUATOR_2,
    PIN_ACTUATOR_3
};

//TODO TODO TODO get this config from SD

#define MAX_PENDING_EXECUTED_COMMANDS 20

#define WIFI_MAX_CONNECTION_ATTEMPS 20
#define HEARTBEAT_INTERVAL 500 // ms

#define TASK_MEASURE_MS (15 * 1000UL)
#define TASK_CHECK_COMMANDS_MS (30 * 1000UL)
#define TASK_INGEST_MS (60 * 1000UL)
#define TASK_UPDATE_ACTUATORS_MS (60 * 1000UL)
#define TASK_UPDATE_RTC_MS (300 * 1000UL)

unsigned long LAST_MILLIS_MEASURE = 0;
unsigned long LAST_MILLIS_CHECKCOMMAND = 0;
unsigned long LAST_MILLIS_INGEST = 0;
unsigned long LAST_MILLIS_UPDATEACTUATORS = 0;
unsigned long LAST_MILLIS_UPDATERTC = 0;
unsigned long HEARTBEAT_PREVIOUS_MILLIS = 0;

bool CONNETED_TO_WIFI = false;
Logger logger;
ApiService api(SERVER_HOST, SERVER_PORT, API_KEY, FIRMWARE, false);
JsonDocument jsonResponse;
System me;
MeasureBatch measures;
QueueHandle_t actuatorQueue = NULL;
QueueHandle_t completedCommandQueue = NULL;

struct tm currentDateTime;
struct PendingExecutedCommand {
    int commandId;
    char executedAt[32] = "";
};

struct CompletedCommandEvent {
    int commandId;
};

PendingExecutedCommand pendingExecutedCommands[MAX_PENDING_EXECUTED_COMMANDS];
int pendingExecutedCommandCount = 0;

bool saveCommandToSD(int commandId, const String &executedAt);
bool getCommandToSD();
bool processPendingCommandExecutions();
bool persistPendingExecutedCommandIds();
bool checkCommands();
bool getTimeFromRTC(String &isoTime, struct tm &dt);

struct ActuatorTaskCommand {
    int actuatorChannel;
    int commandId;
    int durationSeconds;
    float intensity;
    bool manual = false;
};

struct ActuatorState {
    bool active = false;
    TickType_t endTick = 0;
    int commandId = -1;
    bool manual = false;
};

void heartbeat(unsigned long currentMillis) {
    if (currentMillis - HEARTBEAT_PREVIOUS_MILLIS >= HEARTBEAT_INTERVAL) {
        HEARTBEAT_PREVIOUS_MILLIS = currentMillis;
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
        logger.info("Heartbeat");
        Serial.println();
    }
    
}

void actuatorTask(void *param) {
    ActuatorTaskCommand taskCommand;
    ActuatorState states[MAX_ACTUATORS];

    while (true) {
        TickType_t now = xTaskGetTickCount();
        TickType_t nextWake = portMAX_DELAY;

        for (int i = 0; i < MAX_ACTUATORS; i++) {
            if (states[i].active) {
                if (states[i].endTick <= now) {
                    digitalWrite(ACTUATOR_PINS[i], LOW);
                    states[i].active = false;
                    logger.ok("ACTUATOR TASK > Command finished on actuator ", String(i));

                    if (states[i].commandId != -1) {
                        CompletedCommandEvent event;
                        event.commandId = states[i].commandId;
                        if (completedCommandQueue != NULL) {
                            xQueueSend(completedCommandQueue, &event, pdMS_TO_TICKS(10));
                        }
                    }

                    states[i].commandId = -1;
                    states[i].manual = false;
                } else {
                    TickType_t remaining = states[i].endTick - now;
                    if (remaining < nextWake) {
                        nextWake = remaining;
                    }
                }
            }
        }

        TickType_t receiveTimeout = nextWake == portMAX_DELAY ? portMAX_DELAY : nextWake;
        if (receiveTimeout == 0) {
            receiveTimeout = 1;
        }

        if (xQueueReceive(actuatorQueue, &taskCommand, receiveTimeout) == pdTRUE) {
            if (taskCommand.actuatorChannel < 0 || taskCommand.actuatorChannel >= MAX_ACTUATORS) {
                logger.bad("ACTUATOR TASK > Invalid actuator channel", String(taskCommand.actuatorChannel));
                continue;
            }

            logger.info("ACTUATOR TASK > Executing command", String(taskCommand.commandId));
            digitalWrite(ACTUATOR_PINS[taskCommand.actuatorChannel], HIGH);
            states[taskCommand.actuatorChannel].active = true;
            states[taskCommand.actuatorChannel].commandId = taskCommand.commandId;
            states[taskCommand.actuatorChannel].manual = taskCommand.manual;

            TickType_t durationSecondsTicks = taskCommand.durationSeconds / portTICK_PERIOD_MS;
            if (durationSecondsTicks == 0) {
                durationSecondsTicks = 1;
            }
            states[taskCommand.actuatorChannel].endTick = xTaskGetTickCount() + durationSecondsTicks;
            logger.info("ACTUATOR TASK > Actuator ", String(taskCommand.actuatorChannel));
            logger.info("ACTUATOR TASK > durationSeconds ms", String(taskCommand.durationSeconds));
        }
    }
}

bool connectWiFi() {
    if (WiFi.status() == WL_CONNECTED){

        return true;
    }

    logger.info("WiFi > Connecting...");
    logger.info("WiFi > SSID", WIFI_SSID);
    logger.info("WiFi > PASS", WIFI_PASSWORD);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;

    while (WiFi.status() != WL_CONNECTED && attempts < WIFI_MAX_CONNECTION_ATTEMPS) {
        delay(500);
        Serial.print(WiFi.status());
        attempts++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        logger.ok("WiFi > Connected");
        logger.info("WiFi > IP", WiFi.localIP());
        logger.info("WiFi > Attempts", attempts);
        CONNETED_TO_WIFI = true;
        return true;
    } else {
        logger.bad("WiFi > Connection FAILED");
        logger.info("WiFi > Attempts", attempts);
        CONNETED_TO_WIFI = false;
        return false;
    }
}

void initPins(){
    logger.info("PINS > Initializing...");
    for (int i = 0; i < MAX_ACTUATORS; i++) {
        pinMode(ACTUATOR_PINS[i], OUTPUT);
        digitalWrite(ACTUATOR_PINS[i], LOW);
    }
    pinMode(PIN_STATUS_LED, OUTPUT);
    logger.ok("PINS > Initialized");
}

bool executeCommand(int actuatorChannel, const Command &command, bool manualCommand = false){
    logger.info("COMMAND > Queueing command", command.id);
    logger.info("COMMAND > Intensity", String(command.intensity));
    logger.info("COMMAND > durationSeconds", String(command.durationSeconds));
    logger.info("COMMAND > Trigger type", String(command.triggerType));

    if (actuatorQueue == NULL) {
        logger.bad("COMMAND > Queue not initialized");
        return false;
    }

    if (actuatorChannel < 0 || actuatorChannel >= MAX_ACTUATORS) {
        logger.bad("COMMAND > Invalid actuator channel", String(actuatorChannel));
        return false;
    }

    ActuatorTaskCommand taskCommand;
    taskCommand.actuatorChannel = actuatorChannel;
    taskCommand.commandId = command.id;
    taskCommand.durationSeconds = command.durationSeconds;
    taskCommand.intensity = command.intensity;
    taskCommand.manual = manualCommand;

    if (xQueueSend(actuatorQueue, &taskCommand, pdMS_TO_TICKS(100)) != pdTRUE) {
        logger.bad("COMMAND > Command queue full");
        return false;
    }

    logger.ok("COMMAND > Command queued", String(command.id));
    return true;
}

bool createSensors(){
    logger.info("SENSORS > Initializing...");
    logger.info("SENSORS > Defining...");
    me.sensors[0].set("temp1", "temperature", "ºC");
    me.sensors[1].set("temp2", "temperature", "ºC");
    me.sensors[2].set("humi1", "humidity", "%");
    me.sensors[3].set("humi2", "humidity", "%");
    me.sensors[4].set("soil1", "soil moisture", "%");
    me.sensors[5].set("soil2", "soil moisture", "%");
    me.sensors[6].set("wind", "wind speed", "m/s");
    me.sensors[7].set("rain", "precipitation", "L/m2");    
    me.sensorCount = 8;
    logger.info("SENSORS > Defined");
    
    logger.info("API > createSensors...");
    if(!CONNETED_TO_WIFI){
        logger.warn("WIFI > Not connected");
        return false;
    }
    if (api.createSensors(me.sensorsToJson())) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error");
        logger.bad("API > Cannot connect to server"); //TODO TODO TODO
    }

    logger.ok("SENSORS > Initialized");
    return true;
}

bool saveSensorsToSD(){
    logger.info("SENSORS > Saving to SD...");
    JsonDocument sensorsDoc = me.sensorsToJson();
    String output;
    serializeJson(sensorsDoc, output);
    logger.info("SENSORS > JSON", output);

    // TODO TODO TODO

    logger.ok("SENSORS > Saved to SD");
    return true;
}

bool getSensorsFromSD(){
    logger.info("SENSORS > Getting from SD...");
    // TODO TODO TODO
    logger.ok("SENSORS > Got from SD");
    return true;
}

bool persistPendingExecutedCommandIds(){
    // TODO TODO TODO implement SD persistence when SD card is connected
    logger.warn("COMMANDS > SD persistence disabled, skipping save");
    return false;
}

bool saveCommandToSD(int commandId, const String &executedAt){
    // TODO TODO TODO Enable SD save when SD card is connected
    logger.warn("COMMANDS > saveCommandToSD skipped, SPIFFS not available");
    return false;
}

bool getCommandToSD(){
    // TODO TODO TODO Enable SD load when SD card is connected
    pendingExecutedCommandCount = 0;
    logger.warn("COMMANDS > getCommandToSD skipped, SPIFFS not available");
    return false;
}

bool processPendingCommandExecutions(){
    if (!getCommandToSD()) {
        return false;
    }

    bool changed = false;
    int index = 0;
    while (index < pendingExecutedCommandCount) {
        int commandId = pendingExecutedCommands[index].commandId;
        String executedAt = pendingExecutedCommands[index].executedAt;
        JsonDocument response;
        if (api.commandExecuted(String(commandId), executedAt, response)) {
            logger.ok("COMMANDS > Pending command executed", String(commandId));
            for (int j = index; j < pendingExecutedCommandCount - 1; j++) {
                pendingExecutedCommands[j] = pendingExecutedCommands[j + 1];
            }
            pendingExecutedCommandCount--;
            changed = true;
        } else {
            logger.warn("COMMANDS > Pending command still pending", String(commandId));
            index++;
        }
    }

    if (changed) {
        if (pendingExecutedCommandCount == 0) {
            // TODO TODO TODO remove pending command marker when SD is available
            logger.ok("COMMANDS > Pending commands cleared from SD");
        } else {
            persistPendingExecutedCommandIds();
        }
    }

    return pendingExecutedCommandCount == 0;
}

bool saveActuatorsToSD(){
    logger.info("ACTUATORS > Saving to SD...");
    JsonDocument actuatorsDoc;
    JsonArray arr = actuatorsDoc.to<JsonArray>();
    for(int i = 0; i < me.actuatorCount; i++){
        JsonObject actuatorJSON = arr.add<JsonObject>();
        me.actuators[i].toJSON(actuatorJSON);
    }
    String output;
    serializeJson(actuatorsDoc, output);
    logger.info("ACTUATORS > JSON", output);

    // TODO TODO TODO

    logger.ok("ACTUATORS > Saved to SD");
    return true;
}

bool getMeasureValue(const char* sensorKey, float &value) {
    // Stubbed sensor read: return a random float value for any sensor key.
    // Replace this with the actual sensor driver read once hardware is available.
    value = random(0, 10000) / 100.0;
    return true;
}

int timeStringToMinutes(const char* hhmm) {
    if (strlen(hhmm) != 5 || hhmm[2] != ':') {
        return -1;
    }

    int hours = (hhmm[0] - '0') * 10 + (hhmm[1] - '0');
    int minutes = (hhmm[3] - '0') * 10 + (hhmm[4] - '0');
    if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
        return -1;
    }

    return hours * 60 + minutes;
}

bool compareTime(const char* op, const char* hhmm) {
    if (currentDateTime.tm_hour < 0 || currentDateTime.tm_hour > 23 || currentDateTime.tm_min < 0 || currentDateTime.tm_min > 59) {
        logger.warn("RULES > currentDateTime invalid");
        return false;
    }

    int currentMinutes = currentDateTime.tm_hour * 60 + currentDateTime.tm_min;
    int conditionMinutes = timeStringToMinutes(hhmm);
    if (conditionMinutes < 0) {
        return false;
    }

    bool result = false;
    if (strcmp(op, "==") == 0) {
        result = currentMinutes == conditionMinutes;
    }
    if (strcmp(op, "!=") == 0) {
        result = currentMinutes != conditionMinutes;
    }
    if (strcmp(op, ">") == 0) {
        result = currentMinutes > conditionMinutes;
    }
    if (strcmp(op, "<") == 0) {
        result = currentMinutes < conditionMinutes;
    }
    if (strcmp(op, ">=") == 0) {
        result = currentMinutes >= conditionMinutes;
    }
    if (strcmp(op, "<=") == 0) {
        result = currentMinutes <= conditionMinutes;
    }

    logger.info("RULES > compareTime", String(op) + " " + String(hhmm) + " => " + String(result));
    if (result) {
        logger.ok("RULES > Time condition passed", String(hhmm));
    } else {
        logger.warn("RULES > Time condition failed", String(hhmm));
    }
    return result;
}

bool evaluateCondition(const RuleCondition &condition) {
    logger.info("RULES > Evaluating condition", String(condition.type));
    if (strcmp(condition.type, "time") == 0) {
        logger.info("RULES > Time condition", String(condition.op) + " " + String(condition.cron));
        return compareTime(condition.op, condition.cron);
    } else if (strcmp(condition.type, "sensor") == 0) {
        if(strcmp(condition.sensor_key, "") == 0){
            logger.warn("RULES > Sensor key is empty");
            return false;
        }
        float sensorValue;
        if (!getMeasureValue(condition.sensor_key, sensorValue)) {
            logger.warn("RULES > Sensor value not found", String(condition.sensor_key));
            return false;
        }
        logger.info("RULES > Sensor condition", String(condition.sensor_key));
        logger.info("RULES > Sensor value", String(sensorValue));

        bool result = false;
        if (strcmp(condition.op, "==") == 0) {
            result = sensorValue == condition.value;
        }
        if (strcmp(condition.op, "!=") == 0) {
            result = sensorValue != condition.value;
        }
        if (strcmp(condition.op, ">") == 0) {
            result = sensorValue > condition.value;
        }
        if (strcmp(condition.op, "<") == 0) {
            result = sensorValue < condition.value;
        }
        if (strcmp(condition.op, ">=") == 0) {
            result = sensorValue >= condition.value;
        }
        if (strcmp(condition.op, "<=") == 0) {
            result = sensorValue <= condition.value;
        }

        if (result) {
            logger.ok("RULES > Sensor condition passed", String(condition.sensor_key));
        } else {
            logger.warn("RULES > Sensor condition failed", String(condition.sensor_key));
        }
        return result;
    } else {
        logger.warn("RULES > Unsupported condition type", String(condition.type));
        return false;
    }

}

bool evaluateRuleGroup(const RuleGroup &group) {
    logger.info("RULES > Evaluating rule group", String(group.conditionCount));
    for (int c = 0; c < group.conditionCount; c++) {
        if (!evaluateCondition(group.conditions[c])) {
            logger.warn("RULES > Rule group failed at condition", String(c));
            return false;
        }
    }
    logger.ok("RULES > Rule group passed", String(group.conditionCount));
    return true;
}

bool checkCommands(){
    logger.info("CHECK COMMANDS > Starting evaluation");
    bool actuatorsChanged = false;

    for (int i = 0; i < me.actuatorCount; i++) {
        logger.info("CHECK COMMANDS > Scanning actuator", String(me.actuators[i].id));
        for (int j = 0; j < me.actuators[i].commandsCount; j++) {
            Command &command = me.actuators[i].commands[j];

            if (strcmp(command.triggerType, COMMAND_TRIGGER_MANUAL) == 0) {
                int commandId = command.id;
                if (executeCommand(me.actuators[i].channel, command, true)) {
                    if (me.actuators[i].removeCommand(commandId)) {
                        logger.ok("ACTUATORS > Manual command removed from local stack", String(commandId));
                        actuatorsChanged = true;
                        j--;
                    } else {
                        logger.warn("ACTUATORS > Failed to remove manual command from stack", String(commandId));
                    }
                }
                continue;
            }

            if (strcmp(command.triggerType, COMMAND_TRIGGER_AUTOMATIC) == 0) {
                bool groupMatched = false;
                for (int g = 0; g < command.rulesGroupCount; g++) {
                    if (evaluateRuleGroup(command.ruleGroups[g])) {
                        groupMatched = true;
                        break;
                    }
                }

                if (groupMatched) {
                    logger.info("ACTUATORS > Automatic command conditions met", String(command.id));
                    if (!executeCommand(me.actuators[i].channel, command, false)) {
                        logger.warn("ACTUATORS > Failed to queue automatic command", String(command.id));
                    }
                }
            }
        }
    }

    if (actuatorsChanged) {
        logger.ok("CHECK COMMANDS > Actuator commands changed");
    } else {
        logger.info("CHECK COMMANDS > No actuator changes detected");
    }
    return actuatorsChanged;
}

bool apiUpdateActuators(){
    logger.info("ACTUATORS > Updating...");
    if(!CONNETED_TO_WIFI){
        logger.warn("WIFI > Not connected");
        return false;
    }
    logger.info("API > getActuators...");
    JsonDocument actuatorsDoc;
    if (api.getActuators(actuatorsDoc)) {
        logger.ok("API > getActuators Response OK");
        me.actuatorCount = actuatorsDoc.size();
        logger.info("ACTUATORS > Number", String(me.actuatorCount)); 
        JsonArray arr = actuatorsDoc.as<JsonArray>();
        bool actuatorsChanged = false;

        for (size_t i = 0; i < arr.size(); i++) {
            JsonObject actuatorJSON = arr[i];

            me.actuators[i].fromJSON(actuatorJSON);
            logger.info("ACTUATORS > Getting commands...");
            if(!CONNETED_TO_WIFI){
                logger.warn("WIFI > Not connected");
                return false;
            }
            logger.info("API > getCommandsOfActuator", me.actuators[i].id);
            JsonDocument commandsDoc;
            if (api.getCommandsOfActuator(String(me.actuators[i].id), commandsDoc)) {
                logger.ok("API > getCommandsOfActuator Response OK");
                String output;
                serializeJson(commandsDoc, output);
                me.actuators[i].getCommandsFromJSON(commandsDoc["commands"].as<JsonArray>());
                for(int j = 0; j < me.actuators[i].commandsCount; j++){
                    if(strcmp(me.actuators[i].commands[j].triggerType, COMMAND_TRIGGER_AUTOMATIC) == 0){
                        logger.info("ACTUATORS > Automatic command recieved. Getting rules...");
                        if(!CONNETED_TO_WIFI){
                            logger.warn("WIFI > Not connected");
                            return false;
                        }
                        logger.info("API > getRulesOfCommand", me.actuators[i].commands[j].id);
                        JsonDocument rulesDoc;
                        if (api.getRulesOfCommand(String(me.actuators[i].commands[j].id), rulesDoc)) {
                            logger.ok("API > getRulesOfCommand Response OK");
                            me.actuators[i].commands[j].getRulesGroupFromJSON(rulesDoc["groups"].as<JsonArray>());
                            logger.ok("ACTUATORS > Command rules updated");
                        } else {
                            logger.bad("API > getRulesOfCommand Unexpected error");
                            logger.bad("API > Cannot connect to server"); //TODO TODO TODO
                            return false;
                        }
                    } else if(strcmp(me.actuators[i].commands[j].triggerType, COMMAND_TRIGGER_MANUAL) == 0){
                        // Manual commands are handled in checkCommands()
                    } else {
                        logger.bad("ACTUATORS > Command trigger type unknown", me.actuators[i].commands[j].triggerType);
                    }
                }
            } else {
                logger.bad("API > getCommandsOfActuator Unexpected error");
                logger.bad("API > Cannot connect to server"); //TODO TODO TODO
                return false;
            }
        }

        if (actuatorsChanged) {
            if (!saveActuatorsToSD()) {
                logger.warn("ACTUATORS > Failed to persist actuators after manual command removal");
            }
        }

    } else {
        logger.bad("API > getActuators Unexpected error");
        logger.bad("API > Cannot connect to server"); //TODO TODO TODO
        return false;
    }
    logger.info("ACTUATORS > Updated...");
    return true;
}

bool getActuatorsFromSD(){
    logger.info("ACTUATORS > Getting from SD...");
    // TODO TODO TODO
    logger.ok("ACTUATORS > Got from SD");
    return true;
}

bool measureSensors(){
    //TODO TODO TODO
    logger.info("MEASURES > Measuring sensors...");
    String time = "";
    struct tm executedDateTime;
    if (!getTimeFromRTC(time, executedDateTime)) {
        logger.warn("MEASURES > Failed to read RTC time, using fallback timestamp");
        return false;
    }

    for (int i = 0; i < me.sensorCount; i++){
        float sensorValue;
        getMeasureValue(me.sensors[i].key, sensorValue);
        measures.add(me.sensors[i].key, sensorValue, time);
    }
    logger.ok("MEASURES > Measured sensors");
    return true;
}

bool apiIngestMeasures(){
    logger.info("MEASURES > Ingesting...");
    if(!CONNETED_TO_WIFI){
        logger.warn("WIFI > Not connected");
        return false;
    }
    logger.info("API > ingestMeasures...");
    JsonDocument measuresDoc;    
    measuresDoc["data"] = measures.toJSON();
    measures.clear();
    logger.info("API > ingestMeasures...");
    if (api.ingestMeasures(measuresDoc)) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error" );
        logger.bad("API > Cannot connect to server"); //TODO TODO TODO
        return false;
    }
    logger.ok("MEASURES > Ingested");
    return true;
}

bool saveMeasuresToSD(){
    logger.info("MEASURES > Saving to SD...");
    JsonDocument measuresDoc;
    measuresDoc["data"] = measures.toJSON();
    String output;
    serializeJson(measuresDoc, output);
    logger.info("MEASURES > JSON", output);

    // TODO TODO TODO

    logger.ok("MEASURES > Saved to SD");
    return true;
}

bool getMeasuresFromSD(){
    logger.info("MEASURES > Getting from SD...");
    // TODO TODO TODO
    logger.ok("MEASURES > Got from SD");
    return true;
}

bool measuresInSD(){
    logger.info("MEASURES > Checking if measures in SD...");
    // TODO TODO TODO
    logger.ok("MEASURES > The are not measures in SD");
    return false;
    logger.warn("MEASURES > Measures in SD");
    return true;
}

bool checkMeasuresToIngest(){
    if(measures.measureCount > MAX_MEASURES*0.66){
        logger.info("MEASURES > Measures count", String(measures.measureCount));
        logger.info("MEASURES > Ingesting measures...");
        
        if(apiIngestMeasures()){
            logger.ok("MEASURES > Ingested measures");
            while(measuresInSD()){
                logger.info("MEASURES > Getting measures from SD...");
                if(getMeasuresFromSD()){
                    logger.ok("MEASURES > Got measures from SD");
                    logger.info("MEASURES > Ingesting measures...");
                    if(apiIngestMeasures()){
                        logger.ok("MEASURES > Ingested measures");
                    } else {
                        logger.bad("MEASURES > Error ingesting measures");
                        saveMeasuresToSD();
                    }
                } else {
                    logger.bad("MEASURES > Error getting measures from SD");
                }
            }
        } else {
            logger.bad("MEASURES > Error ingesting measures");
            saveMeasuresToSD();
        }

    }
    return true;
}

bool apiGetSystem(){
    logger.info("SYSTEM > Getting...");
    logger.info("API > getCurrentSystem...");
    JsonDocument systemDoc;
    me.system.firmware = FIRMWARE;
    if(!CONNETED_TO_WIFI){
        logger.warn("WIFI > Not connected");
        return false;
    }
    if (api.getCurrentSystem(systemDoc)) {
        logger.ok("API > Response OK");
        JsonObject obj = systemDoc.as<JsonObject>();
        me.system.fromJSON(obj);
        me.system.firmware = FIRMWARE;

        logger.info("API > getCurrentSystem > ID", me.system.id);
        logger.info("API > getCurrentSystem > FIRMWARE", me.system.firmware);
    } else {
        logger.bad("API > Unexpected error");
        logger.bad("API > Cannot connect to server"); //TODO TODO TODO
    }

    logger.info("API > updateFirmwareVersion...");
    if (api.updateFirmwareVersion()) {
        logger.ok("API > Response OK");
    } else {
        logger.bad("API > Unexpected error");
        logger.bad("API > Cannot connect to server"); //TODO TODO TODO
    }
    logger.ok("SYSTEM > Obtained");
    return true;
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

bool updateRTC(){
    logger.info("TIME > Updating RTC...");
    if(!CONNETED_TO_WIFI){
        logger.warn("WIFI > Not connected");
        return false;
    }
    String time = getISO8601Time();
    if (time.length() > 0){
        logger.ok("TIME > ISO time obtained", time);
        // TODO TODO TODO
    } else {
        logger.info("TIME > Error getting time");
        return false;
    }
    

    logger.ok("TIME > RTC updated");
    return true;
}

bool getTimeFromRTC(String &isoTime, struct tm &dt){
    logger.info("TIME > Getting from RTC...");

    // TODO TODO TODO Read actual RTC hardware here when the RTC module is available.
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        logger.warn("TIME > Failed to get local time for RTC fallback");
        return false;
    }

    isoTime = getISO8601Time();
    dt = timeinfo;
    currentDateTime = timeinfo;

    logger.ok("TIME > Got from RTC", isoTime);
    return true;
}



//=========================================================
//                         SETUP
//=========================================================
void setup()
{
    Serial.begin(115200);

    logger.info("SETUP > starting...");
    logger.ok("FIRWARE", FIRMWARE);

    initPins();
    
    if (!connectWiFi()) {
        logger.bad("SETUP > Error connecting to WiFi");
    }
    

    logger.info("TIME > Initialing NTP configuration...");
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    logger.ok("TIME > NTP configurated");
    
    logger.info("TIME > Starting RTC...");
    //TODO TODO TODO
    logger.ok("TIME > RTC started");

    if(CONNETED_TO_WIFI == true && !updateRTC()) {
        logger.bad("TIME > Error updating RTC.");
    }


    actuatorQueue = xQueueCreate(10, sizeof(ActuatorTaskCommand));
    completedCommandQueue = xQueueCreate(10, sizeof(CompletedCommandEvent));

    if (actuatorQueue == NULL) {
        logger.bad("ACTUATORS > Failed to create queue");
    } else {
        xTaskCreatePinnedToCore(
            actuatorTask,
            "ActuatorTask",
            4096,
            NULL,
            1,
            NULL,
            1);
    }

    logger.info("API > Starting...");
    api.begin();
    logger.ok("API > Started");
    
    apiGetSystem();    

    if(createSensors()) {
        saveSensorsToSD();
    } else {
        logger.warn("SETUP > Error creating sensors. Getting from SD...");
        getSensorsFromSD();
    }

    if (apiUpdateActuators()) {
        saveActuatorsToSD();
    } else {
        getActuatorsFromSD();
        logger.warn("SETUP > Error updating actuators. Getting from SD...");
    }
    
    logger.ok("SETUP > finished");
}


//=========================================================
//                         LOOP
//=========================================================
void loop()
{
    if (WiFi.status() != WL_CONNECTED || !CONNETED_TO_WIFI) {
        CONNETED_TO_WIFI = false;
        connectWiFi();
    }

    unsigned long now = millis();

    if (now - LAST_MILLIS_MEASURE >= TASK_MEASURE_MS) {
        LAST_MILLIS_MEASURE = now;
        logger.info("LOOP > time to measure sensors");
        measureSensors();
    }

    if (now - LAST_MILLIS_CHECKCOMMAND >= TASK_CHECK_COMMANDS_MS) {
        LAST_MILLIS_CHECKCOMMAND = now;
        logger.info("LOOP > time to checkCommands");
        checkCommands();
    }

    if (now - LAST_MILLIS_INGEST >= TASK_INGEST_MS) {
        LAST_MILLIS_INGEST = now;
        logger.info("LOOP > time to ingest measures");
        checkMeasuresToIngest();
    }

    if (now - LAST_MILLIS_UPDATEACTUATORS >= TASK_UPDATE_ACTUATORS_MS) {
        LAST_MILLIS_UPDATEACTUATORS = now;
        logger.info("LOOP > Checking pending command executions");
        processPendingCommandExecutions();
        logger.info("LOOP > time to update actuators");
        if (apiUpdateActuators()) {
            saveActuatorsToSD();
        }
    }

    // Check for completed commands in the queue
    if (completedCommandQueue != NULL) {
        CompletedCommandEvent completedEvent;
        if (xQueueReceive(completedCommandQueue, &completedEvent, 0) == pdTRUE) {
            logger.info("LOOP > Command finished event received", String(completedEvent.commandId));
            String executedAt;
            struct tm executedDateTime;
            if (!getTimeFromRTC(executedAt, executedDateTime)) {
                logger.warn("LOOP > Failed to read RTC time for completed command");
            }
            JsonDocument response;
            if (api.commandExecuted(String(completedEvent.commandId), executedAt, response)) {
                logger.ok("LOOP > commandExecuted notified", String(completedEvent.commandId));
            } else {
                logger.warn("LOOP > commandExecuted failed", String(completedEvent.commandId));
                saveCommandToSD(completedEvent.commandId, executedAt);
            }
        }
    }

    if (now - LAST_MILLIS_UPDATERTC >= TASK_UPDATE_RTC_MS) {
        LAST_MILLIS_UPDATERTC = now;
        logger.info("LOOP > time to update RTC");
        updateRTC();
    }

    heartbeat(now);

    //TODO TODO TODO endpoint para gestionar errores
}