#include <SPI.h>
#include <WiFiNINA.h>

// HotHix for WebServer on Nano 33 IoT
#define va_start(v,l) __builtin_va_start(v,l)
#define va_end(v) __builtin_va_end(v)
#define WEBDUINO_FAIL_MESSAGE "<h1>400 Bad Request</h1>"

#include "WebServer.h"

#include "commands.h"

WebServer webserver("", {{ metaData.port }});

void setup()
{
    Serial.begin(115200);
    WiFi.begin("{{ metaData.ssid }}", "{{ metaData.pass }}");
    if ( WiFi.status() != WL_CONNECTED) 
    {
        Serial.println("Couldn't get a wifi connection");
        while(true);
    }
    else
        Serial.println(WiFi.localIP());

    {% if 'index.html' in fileData %}
    webserver.setDefaultCommand(&f_{{fileData['index.html'].file_hash}});
    {%- endif %}

    {% for file, data in fileData.items() %}
    webserver.addCommand("{{file}}", &f_{{data.file_hash}}{{"::respond" if data.file_type == 2}});
    {%- endfor %}

    webserver.begin();
}

void loop()
{
    webserver.processConnection();
}
