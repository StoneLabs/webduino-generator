inline void respond(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)
{
	server.httpSuccess();
	if (type != WebServer::ConnectionType::HEAD)
	{
		pinMode(LED_BUILTIN, OUTPUT);
		digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
		server.print("OK!");
	}
}