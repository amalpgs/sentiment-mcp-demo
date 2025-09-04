import os
import sys
import json
from textblob import TextBlob
from prometheus_client import start_http_server, Counter

POS = Counter("tool_sentiment_positive_total", "Tool positive")
NEG = Counter("tool_sentiment_negative_total", "Tool negative")
NEU = Counter("tool_sentiment_neutral_total", "Tool neutral")

PIPE_DIR = os.getenv("PIPE_DIR", "/mcp-pipes")
IN_PIPE = os.path.join(PIPE_DIR, "stdin")
OUT_PIPE = os.path.join(PIPE_DIR, "stdout")

def analyze(text):
    blob = TextBlob(text)
    p = blob.sentiment.polarity
    sentiment = "positive" if p>0.1 else "negative" if p<-0.1 else "neutral"
    return {"sentiment": sentiment, "polarity": p}

def stdio_loop():
    while True:
        with open(IN_PIPE, "r") as fifo_in:
            req = json.loads(fifo_in.readline())
        res = analyze(req.get("params", {}).get("text", ""))
        if res["sentiment"] == "positive": POS.inc()
        elif res["sentiment"] == "negative": NEG.inc()
        else: NEU.inc()
        resp = {"jsonrpc": "2.0", "id": req.get("id"), "result": res}
        with open(OUT_PIPE, "w") as fifo_out:
            fifo_out.write(json.dumps(resp) + "\n")

def main():
    start_http_server(8001)
    stdio_loop()

if __name__ == "__main__":
    main()
