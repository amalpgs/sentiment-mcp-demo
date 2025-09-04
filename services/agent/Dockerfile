FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent.py .
ENV MCP_TRANSPORT=stdio
CMD ["python", "agent.py"]

