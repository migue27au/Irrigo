#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>

#define MAX_COMMANDS 8
#define MAX_ACTUATORS 4
#define MAX_SENSORS 8
#define MAX_RULE_GROUPS 4
#define MAX_CONDITIONS 8
#define MAX_MEASURES 32


// ======================================================
//                        SYSTEM INFO
// ======================================================
class SystemInfo {
public:
    int id = 0;

    String firmware;


    void toJSON(JsonObject obj) const {
        obj["id"] = id;
        obj["firmware"] = firmware;
    }

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
    }
};

// ======================================================
//                     RULE CONDITION
// ======================================================
class RuleCondition {
public:
    String sensor_key = "";

    String type;   // sensor | time
    String op;     // > < >= <= == !=

    float value = 0;
    String cron;

    int sensor_id = 0;

    void fromJSON(JsonObject obj) {
        sensor_key = obj["sensor_key"].as<String>();
        type = obj["type"].as<String>();
        op = obj["op"].as<String>();
        value = obj["value"].as<float>();
        cron = obj["cron"].as<String>();
    }
};

// ======================================================
// RULE GROUP
// ======================================================
class RuleGroup {
public:
    int id = 0;

    RuleCondition conditions[MAX_CONDITIONS];
    int conditionCount = 0;

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();

        conditionCount = 0;

        JsonArray conditionsArray = obj["conditions"].as<JsonArray>();

        for (JsonObject conditionObj : conditionsArray) {
            if (conditionCount >= MAX_CONDITIONS)
                break;

            conditions[conditionCount].fromJSON(conditionObj);
            conditionCount++;
        }
    }
};

// ======================================================
//                       COMMAND
// ======================================================
class Command {
public:
    int id = 0;
    String trigger_type = "";

    float intensity = 0;
    int duration = 0;

    int rulesGroupCount = 0;
    RuleGroup ruleGroups[MAX_RULE_GROUPS];

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        trigger_type = obj["trigger_type"].as<String>();
        intensity = obj["intensity"].as<int>();
        duration = obj["duration"].as<int>();
    }

    void getRulesGroupFromJSON(JsonArray jarray){
        rulesGroupCount = jarray.size();
        int i = 0;
        for (JsonObject rulesGroupJson : jarray) {
            ruleGroups[i++].fromJSON(rulesGroupJson);
        }
    }
};

// ======================================================
//                       ACTUATOR
// ======================================================
class Actuator {
public:
    int id = 0;
    int channel = 0;

    bool enabled = false;
    float intensity = 0;

    int commandsCount = 0;
    Command commands[MAX_COMMANDS];

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        channel = obj["channel"].as<int>();
        enabled = obj["enabled"].as<bool>();
        intensity = obj["intensity"].as<float>();
    }

    void getCommandsFromJSON(JsonArray jarray) {
        String output;
        serializeJson(jarray, output);
        Serial.println(output);
        commandsCount = jarray.size();  
        int i = 0;
        for (JsonObject commandJson : jarray) {
            commands[i++].fromJSON(commandJson);
        }
    }
};


// ======================================================
//                         SENSOR
// ======================================================
class Sensor {
public:
    int id = 0;
    String key;
    String unit;
    String type;

    bool enabled = true;
    String created_at;

    void toJSON(JsonObject obj) const {
        obj["sensor_key"] = key;
        obj["unit"] = unit;
        obj["sensor_type"] = type;
        obj["enabled"] = enabled;
    }
};

// ======================================================
//                     MEASURE
// ======================================================
class Measure {
public:
    String sensor_key;
    float value;
    String timestamp;

    void toJSON(JsonObject obj) const {
        obj["sensor_key"] = sensor_key;
        obj["value"] = value;
        obj["timestamp"] = timestamp;
    }
};

class MeasureBatch {
public:
    Measure measures[MAX_MEASURES];
    int measureCount = 0;

    bool add(const Measure& measure) {
        if (measureCount >= MAX_MEASURES)
            return false;

        measures[measureCount++] = measure;
        return true;
    }

    bool add(const String& sensor_key, float value, String timestamp) {
        if (measureCount >= MAX_MEASURES)
            return false;

        measures[measureCount].sensor_key = sensor_key;
        measures[measureCount].value = value;
        measures[measureCount].timestamp = timestamp;

        measureCount++;

        return true;
    }

    bool pop(Measure& measure) {
        if (measureCount == 0)
            return false;

        measure = measures[measureCount - 1];
        measureCount--;

        return true;
    }

    void clear() {
        measureCount = 0;
    }

    JsonDocument toJSON() const {
        JsonDocument doc;
        JsonArray array = doc.to<JsonArray>();

        for (int i = 0; i < measureCount; i++) {
            JsonObject obj = array.add<JsonObject>();
            measures[i].toJSON(obj);
        }

        return doc;
    }
};

// ======================================================
// IRRIGATION SYSTEM
// ======================================================
class System {
public:
    SystemInfo system;

    Actuator actuators[MAX_ACTUATORS];
    int actuatorCount = 0;

    Sensor sensors[MAX_SENSORS];
    int sensorCount = 0;

    JsonDocument sensorsToJson() const {
        JsonDocument doc;
        JsonArray array = doc["sensors"].to<JsonArray>();

        for (int i = 0; i < sensorCount; i++) {
            JsonObject obj = array.add<JsonObject>();
            sensors[i].toJSON(obj);
        }

        return doc;
    }
};