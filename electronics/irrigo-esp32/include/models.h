#pragma once

#include <Arduino.h>

#define MAX_ACTUATORS 4
#define MAX_SENSORS 8
#define MAX_RULE_GROUPS 8
#define MAX_CONDITIONS 8

// ======================================================
//                    SYSTEM INFO
// ======================================================
struct SystemInfo {
    int id;

    const char* alias;
    const char* description;
    const char* firmware;
};

// ======================================================
//                      ACTUATOR
// ======================================================
struct Actuator {
    int id;
    int channel;

    const char* name;
    const char* description;

    bool is_on;
    float intensity; // 0 - 255 PWM

    unsigned long last_changed_at;
    int last_changed_by;
};

// ======================================================
//                        SENSOR
// ======================================================
struct Sensor {
    int id;

    const char* sensor_key;
    const char* name;
    const char* unit;
    const char* sensor_type;

    bool enabled;
};

// ======================================================
//                     RULE CONDITION
// ======================================================
struct RuleCondition {
    int id;

    const char* type;   // "sensor" | "time"
    const char* op;     // > < >= <= == !=

    float value;
    const char* cron;

    int sensor_id;
};

// ======================================================
//                       RULE GROUP
// ======================================================
struct RuleGroup {
    int id;

    const char* name;
    const char* description;

    bool enabled;

    RuleCondition conditions[MAX_CONDITIONS];
    int conditionCount;
};

// ======================================================
//             FULL IRRIGATION SYSTEM MODEL
// ======================================================
struct IrrigationSystem {
    SystemInfo system;

    Actuator actuators[MAX_ACTUATORS];
    int actuatorCount;

    Sensor sensors[MAX_SENSORS];
    int sensorCount;

    RuleGroup ruleGroups[MAX_RULE_GROUPS];
    int ruleGroupCount;
};