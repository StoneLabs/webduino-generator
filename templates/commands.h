#pragma once

inline void staticResponder(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete, const unsigned char* response, const char* mime)
{
  server.httpSuccess(mime);

  /* if we're handling a GET or POST, we can output our data here.
     For a HEAD request, we just stop after outputting headers. */
  if (type != WebServer::ConnectionType::HEAD)
  {
    /* this is a special form of print that outputs from PROGMEM */
    server.printP(response);
  }
}

__COMMANDS_DEF_MIMES__

__COMMANDS_DEF_STATIC__

__COMMANDS_DEF_DYNAMIC__