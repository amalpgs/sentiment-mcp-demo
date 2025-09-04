#!/usr/bin/env python3
import argparse
import sys
import json
from textblob import TextBlob
from flask import Flask, request, jsonify
from prometheus_client import start_http_server, Counter

POS = Counter("tool_sentiment_positive_total", "Tool positive count")
NEG = Counter("tool_sentiment_negative_total", "Tool negative count")
NEU = Counter("tool_sentiment_neutral_total", "Tool neutral count")
app = Flask(__name__)

def analyze_text(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return {"sentiment": label, "polarity": polarity}

@app.route("/mcp", methods=["POST"])
def mcp_http():
    req = request.get_json(force=True)
    params = req.get("params", {})
    text = params.get("text", "")
    res = analyze_text(text)
    # update metrics
    if res["sentiment"] == "positive":
        POS.inc()
    elif res["sentiment"] == "negative":
        NEG.inc()
    else:
        NEU.inc()
    return jsonify({"jsonrpc":"2.0","id":req.get("id"), "result": res})

def stdio_loop():
    # Very simple stdio loop: read lines, respond
    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
            text = req.get("params", {}).get("text", "")
            res = analyze_text(text)
            if res["sentiment"] == "positive":
                POS.inc()
            elif res["sentiment"] == "negative":
                NEG.inc()
            else:
                NEU.inc()
            resp = {"jsonrpc":"2.0","id":req.get("id"), "result": res}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc":"2.0","error": {"message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio","http"], default="stdio")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    start_http_server(8001)
    if args.transport == "stdio":
        stdio_loop()
    else:
        app.run(host="0.0.0.0", port=args.port)
