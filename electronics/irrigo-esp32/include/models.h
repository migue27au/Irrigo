#pragma once

#ifndef MODELS_H
#define MODELS_H

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


    void toJSON(JsonObject obj) const {
        obj["sensor_key"] = sensor_key;
        obj["type"] = type;
        obj["op"] = op;
        obj["value"] = value;
        obj["cron"] = cron;
    }

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

    void toJSON(JsonObject obj) const {
        obj["id"] = id;
        JsonArray conditionsArray = obj["conditions"].to<JsonArray>();
        for (int i = 0; i < conditionCount; i++) {
            JsonObject conditionObj = conditionsArray.add<JsonObject>();
            conditions[i].toJSON(conditionObj);
        }
    }

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
    char triggerType[10] = "";

    float intensity = 0;
    int durationSeconds = 0;

    int rulesGroupCount = 0;
    RuleGroup ruleGroups[MAX_RULE_GROUPS];

    void toJSON(JsonObject obj, bool includeRuleGroups = true) const {
        obj["id"] = id;
        obj["trigger_type"] = triggerType;
        obj["intensity"] = intensity;
        obj["duration_seconds"] = durationSeconds;
        
        if(includeRuleGroups){
            JsonArray groupsArray = obj["rule_groups"].to<JsonArray>();
            for (int i = 0; i < rulesGroupCount; i++) {
                JsonObject groupObj = groupsArray.add<JsonObject>();
                ruleGroups[i].toJSON(groupObj);
            }
        }
    }

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        strlcpy(triggerType, obj["trigger_type"] | "", sizeof(triggerType));
        intensity = obj["intensity"].as<float>();
        durationSeconds = obj["duration_seconds"].as<int>();
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

    void toJSON(JsonObject obj, bool includeCommands = true) const {
        obj["id"] = id;
        obj["channel"] = channel;
        obj["enabled"] = enabled;
        obj["intensity"] = intensity;

        if (includeCommands) {
            JsonArray commandsArray = obj["commands"].to<JsonArray>();
            for (int i = 0; i < commandsCount; i++) {
                JsonObject commandObj = commandsArray.add<JsonObject>();
                commands[i].toJSON(commandObj);
            }
        }
    }

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        channel = obj["channel"].as<int>();
        enabled = obj["enabled"].as<bool>();
        intensity = obj["intensity"].as<float>();

        if (!obj["commands"].isNull()) {
            getCommandsFromJSON(obj["commands"].as<JsonArray>());
        } else {
            commandsCount = 0;
        }
    }

    void getCommandsFromJSON(JsonArray jarray) {
        String output;
        serializeJson(jarray, output);
        commandsCount = min((int)jarray.size(), MAX_COMMANDS);
        for (int i = 0; i < commandsCount; i++) {
            commands[i].fromJSON(jarray[i]);
        }
    }

    bool removeCommand(int commandId) {
        int index = -1;
        for (int i = 0; i < commandsCount; i++) {
            if (commands[i].id == commandId) {
                index = i;
                break;
            }
        }

        if (index < 0) {
            return false;
        }

        for (int i = index; i < commandsCount - 1; i++) {
            commands[i] = commands[i + 1];
        }

        commandsCount--;
        return true;
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
        obj["id"] = id;
    }

    void fromJSON(JsonObject obj) {
        id = obj["id"].as<int>();
        strlcpy(key, obj["sensor_key"] | "", sizeof(key));
        strlcpy(unit, obj["unit"] | "", sizeof(unit));
        strlcpy(type, obj["sensor_type"] | "", sizeof(type));
        enabled = obj["enabled"].as<bool>();
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

    void fromJSON(JsonObject obj) {
        strlcpy(sensor_key, obj["sensor_key"] | "", sizeof(sensor_key));
        value = obj["value"].as<float>();
        strlcpy(timestamp, obj["timestamp"] | "", sizeof(timestamp));
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

    void fromJSON(JsonArray array) {
        measureCount = min((int)array.size(), MAX_MEASURES);
        for (int i = 0; i < measureCount; i++) {
            measures[i].fromJSON(array[i].as<JsonObject>());
        }
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

#endif  // MODELS_H