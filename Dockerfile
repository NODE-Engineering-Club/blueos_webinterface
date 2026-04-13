FROM python:3.11-slim

WORKDIR /app
COPY . .
EXPOSE 8080

# BlueOS Extension Metadata
LABEL version="1.0.0"
LABEL description="Real-time boat GPS tracker via MAVLink2REST"
LABEL permissions='{"HostConfig": {"NetworkMode": "host"}}'
LABEL authors='[{"name": "Your Name"}]'

CMD ["python", "main.py"]
