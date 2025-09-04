import os
import time
import boto3
import json
from prometheus_client import start_http_server, Counter

PROCESSED = Counter("sentiment_processed_total", "Total processed files")
POS = Counter("sentiment_positive_total", "Positive")
NEG = Counter("sentiment_negative_total", "Negative")
NEU = Counter("sentiment_neutral_total", "Neutral")

PIPE_DIR = os.getenv("PIPE_DIR", "/mcp-pipes")
IN_PIPE = os.path.join(PIPE_DIR, "stdin")
OUT_PIPE = os.path.join(PIPE_DIR, "stdout")

def send_via_fifo(req_json):
    with open(IN_PIPE, "w") as fifo:
        fifo.write(json.dumps(req_json) + "\n")

def recv_via_fifo():
    with open(OUT_PIPE, "r") as fifo:
        return json.loads(fifo.readline())

def handle_text(text):
    req = {"jsonrpc": "2.0", "id": "1", "method": "analyze", "params": {"text": text}}
    send_via_fifo(req)
    res = recv_via_fifo()
    sentiment = res.get("result", {}).get("sentiment", "neutral")
    PROCESSED.inc()
    (POS if sentiment=="positive" else NEG if sentiment=="negative" else NEU).inc()
    print("Sentiment:", sentiment)

def main():
    start_http_server(8000)
    bucket = boto3.client("s3")
    while True:
        # Poll logic omitted
        text = "demo text"
        handle_text(text)
        time.sleep(5)

if __name__ == "__main__":
    main()
