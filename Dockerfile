FROM python:3.9
WORKDIR /app
RUN apt-get update && apt-get install -y procps
COPY agent.py .
CMD ["python", "agent.py"]

