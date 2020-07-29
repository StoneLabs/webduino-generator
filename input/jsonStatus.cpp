// no-cost stream operator as described at 
// http://sundial.org/arduino/?page_id=119
template<class T>
inline Print &operator <<(Print &obj, T arg)
{ obj.print(arg); return obj; }

inline void respond(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)
{
  if (type == WebServer::POST)
  {
    server.httpFail();
    return;
  }

  //server.httpSuccess(false, "application/json");
  server.httpSuccess("application/json");
  
  if (type == WebServer::HEAD)
    return;

  int i;    
  server << "[ ";
  for (i = 0; i <= 9; ++i)
  {
    // ignore the pins we use to talk to the Ethernet chip
    int val = digitalRead(i);
    server << "{ \"pin\":\"d" << i << "\", \"value\":" << val << "}, ";
  }

  for (i = 0; i <= 5; ++i)
  {
    int val = analogRead(i);
    server << "{ \"pin\":\"a" << i << "\", \"value\":" << val << "} ";
    if (i != 5)
      server << ", ";
  }
  
  server << " ]";
}