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
    char sensor_key[12] = "";

    char type[8] = "";   // sensor | time
    char op[4] = "";   // < > == != >= <=

    float value = 0;
    char cron[8] = "";   // 16:30

    int sensor_id = 0;

    void fromJSON(JsonObject obj) {
        strlcpy(sensor_key, obj["sensor_key"] | "", sizeof(sensor_key));
        strlcpy(type, obj["type"] | "", sizeof(type));
        strlcpy(op, obj["op"] | "", sizeof(op));
        value = obj["value"].as<float>();
        strlcpy(cron, obj["cron"] | "", sizeof(cron));

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
        if(!conditionsArray.isNull()){
            for (JsonObject conditionObj : conditionsArray) {
                if (conditionCount >= MAX_CONDITIONS)
                    break;
    
                conditions[conditionCount].fromJSON(conditionObj);
                conditionCount++;
            }
        }
    }
};

// ======================================================
//                       COMMAND
// ======================================================
class Command {
public:
    int id = 0;
    char trigger_type[10] = "";

    float intensity = 0;
    int duration = 0;

    int rulesGroupCount = 0;
    RuleGroup ruleGroups[MAX_RULE_GROUPS];

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        strlcpy(trigger_type, obj["trigger_type"] | "", sizeof(trigger_type));
        intensity = obj["intensity"].as<float>();
        duration = obj["duration"].as<int>();
    }

    void getRulesGroupFromJSON(JsonArray jarray){
        rulesGroupCount = min((int)jarray.size(), MAX_RULE_GROUPS);

        for (int i = 0; i < rulesGroupCount; i++) {
            ruleGroups[i].fromJSON(jarray[i]);
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
        commandsCount = min((int)jarray.size(), MAX_COMMANDS);
        for (int i = 0; i < commandsCount; i++) {
            commands[i].fromJSON(jarray[i]);
        }
    }
};


// ======================================================
//                         SENSOR
// ======================================================
class Sensor {
public:
    int id = 0;
    
    char key[12] = "";
    char unit[8] = "";
    char type[16] = "";

    bool enabled = true;

    void toJSON(JsonObject obj) const {
        obj["sensor_key"] = key;
        obj["unit"] = unit;
        obj["sensor_type"] = type;
        obj["enabled"] = enabled;
    }

    void set(String key, String unit, String type, bool enabled = true){
        strlcpy(this->key, key.c_str(), sizeof(this->key));
        strlcpy(this->unit, unit.c_str(), sizeof(this->unit));
        strlcpy(this->type, type.c_str(), sizeof(this->type));
        this->enabled = enabled;
    }
};

// ======================================================
//                     MEASURE
// ======================================================
class Measure {
public:
    char sensor_key[12] = "";
    float value;
    char timestamp[32] = "";

    void toJSON(JsonObject obj) const {
        obj["sensor_key"] = sensor_key;
        obj["value"] = value;
        obj["timestamp"] = timestamp;
    }

    void set(String sensor_key, float value, String timestamp){
        strlcpy(this->sensor_key, sensor_key.c_str(), sizeof(this->sensor_key));
        strlcpy(this->timestamp, timestamp.c_str(), sizeof(this->timestamp));
        this->value = value;
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

    bool add(String sensor_key, float value, String timestamp) {
        if (measureCount >= MAX_MEASURES)
            return false;
        measures[measureCount++].set(sensor_key, value, timestamp);

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