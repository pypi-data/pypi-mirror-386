# DM CORE TRACER

DM Core Tracer library is responsible for the following:

- Provides HTTP Request library to service, so that they can invoke HTTP calls.
- Trace every inbound HTTP request, in the context of service
- Trace every outbound HTTP request, in the context of service
- Trace every outbound RabbitMQ message, in the context of service
- Trace every inbound RabbitMQ message, in the context of service
- Trace the calls between functions / methods within the service showing the flow of data
