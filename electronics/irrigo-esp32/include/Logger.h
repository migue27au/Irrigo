#pragma once
#include <Arduino.h>

class Logger {
public:
  void begin(unsigned long baud = 115200) {
    Serial.begin(baud);
    delay(200);
  }

  // INFO
  void info(const char* msg) {
    printPrefix(F("[i] "));
    Serial.println(msg);
  }

  void info(const __FlashStringHelper* msg) {
    printPrefix(F("[i] "));
    Serial.println(msg);
  }

  void info(const char* msg, const char* value) {
    printPrefix(F("[i] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void info(const char* msg, const String& value) {
    printPrefix(F("[i] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void info(const char* msg, int value) {
    printPrefix(F("[i] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void info(const char* msg, float value) {
    printPrefix(F("[i] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value, 2);
  }

  void info(const char* msg, IPAddress ip) {
    printPrefix(F("[i] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(ip);
  }

  // OK
  void ok(const char* msg) {
    printPrefix(F("[+] "));
    Serial.println(msg);
  }

  void ok(const __FlashStringHelper* msg) {
    printPrefix(F("[+] "));
    Serial.println(msg);
  }

  void ok(const char* msg, const char* value) {
    printPrefix(F("[+] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void ok(const char* msg, const String& value) {
    printPrefix(F("[+] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  // WARN
  void warn(const char* msg) {
    printPrefix(F("[!] "));
    Serial.println(msg);
  }

  void warn(const __FlashStringHelper* msg) {
    printPrefix(F("[!] "));
    Serial.println(msg);
  }

  void warn(const char* msg, const char* value) {
    printPrefix(F("[!] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void warn(const char* msg, int value) {
    printPrefix(F("[!] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  // BAD / ERROR
  void bad(const char* msg) {
    printPrefix(F("[-] "));
    Serial.println(msg);
  }

  void bad(const __FlashStringHelper* msg) {
    printPrefix(F("[-] "));
    Serial.println(msg);
  }

  void bad(const char* msg, const char* value) {
    printPrefix(F("[-] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  void bad(const char* msg, int value) {
    printPrefix(F("[-] "));
    Serial.print(msg);
    Serial.print(F(": "));
    Serial.println(value);
  }

  // RAW
  void raw(const char* msg) {
    Serial.println(msg);
  }

  void raw(const __FlashStringHelper* msg) {
    Serial.println(msg);
  }

private:
  void printPrefix(const __FlashStringHelper* p) {
    Serial.print(p);
  }
};