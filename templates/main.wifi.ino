#include <SPI.h>
#include <WiFiNINA.h>

// HotHix for WebServer on Nano 33 IoT
#define va_start(v,l) __builtin_va_start(v,l)
#define va_end(v) __builtin_va_end(v)
#define WEBDUINO_FAIL_MESSAGE "<h1>400 Bad Request</h1>"

#include "WebServer.h"

#include "commands.h"

WebServer webserver("", __PORT__);

void setup()
{
    Serial.begin(115200);
    WiFi.begin(__SSID__, __PASS__);
    if ( WiFi.status() != WL_CONNECTED) 
    {
        Serial.println("Couldn't get a wifi connection");
        while(true);
    }
    else
        Serial.println(WiFi.localIP());

__COMMANDS_ADD__

    webserver.begin();
}

void loop()
{
    webserver.processConnection();
}
