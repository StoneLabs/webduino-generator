#pragma once

// Responde with string from PROGMEM. Read till \0
inline void staticResponder(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete, const unsigned char* response, const char* mime)
{
  server.httpSuccess(mime);

  if (type != WebServer::ConnectionType::HEAD)
  {
    server.printP(response);
  }
}

// Responde with data from PROGMEM
inline void staticResponder(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete, const unsigned char* response, size_t response_size, const char* mime)
{
  server.httpSuccess(mime);

  /* if we're handling a GET or POST, we can output our data here.
     For a HEAD request, we just stop after outputting headers. */
  if (type != WebServer::ConnectionType::HEAD)
  {
    /* this is a special form of print that outputs from PROGMEM */
    server.writeP(response, response_size);
  }
}

// MIME TYPES
{%- for mime, hash in mimeData.items() %}
static const char m_{{hash}}_s[] = "{{mime}}";
{%- endfor %}

// STATIC PAGES
{%- for file, data in fileData.items() %}
{%- if data.file_type == 0 %}
static const unsigned char f_{{data.file_hash}}_s[] PROGMEM = "{{data.file_content}}";
inline void f_{{data.file_hash}} (WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete) { staticResponder(server, type, url_tail, tail_complete, f_{{data.file_hash}}_s, m_{{data.mime_hash}}_s); }
{%- endif %}
{%- endfor %}

// BINARY PAGES
{%- for file, data in fileData.items() %}
{%- if data.file_type == 1 %}
static const unsigned char f_{{data.file_hash}}_s[] PROGMEM = {{data.file_content}};
inline void f_{{data.file_hash}} (WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete) { staticResponder(server, type, url_tail, tail_complete, f_{{data.file_hash}}_s, sizeof(f_{{data.file_hash}}_s), m_{{data.mime_hash}}_s); }
{%- endif %}
{%- endfor %}

// DYNAMIC PAGES
{%- for file, data in fileData.items() %}
{%- if data.file_type == 2 %}
namespace f_{{data.file_hash}} 
{
  {{data.file_content}}
}
{% endif %}
{%- endfor %}
