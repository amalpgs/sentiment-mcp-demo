#!/usr/bin/env python3
import os
import time
import json
import boto3
import sys
import requests
from prometheus_client import start_http_server, Counter

# Metrics
PROCESSED = Counter("sentiment_processed_total", "Total processed files")
POS = Counter("sentiment_positive_total", "Positive results")
NEG = Counter("sentiment_negative_total", "Negative results")
NEU = Counter("sentiment_neutral_total", "Neutral results")

# Config via env
S3_BUCKET = os.getenv("S3_BUCKET", "mcp-demo-bucket")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # "http" or "stdio"
MCP_TOOL_URL = os.getenv("MCP_TOOL_URL", "http://mcp-tool.ai-tools.svc.cluster.local")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

processed_prefix = "processed/"

# S3 client
s3 = boto3.client("s3", region_name=AWS_REGION)

def list_text_objects():
    res = s3.list_objects_v2(Bucket=S3_BUCKET)
    for item in res.get("Contents", []):
        key = item["Key"]
        if key.endswith(".txt") and not key.startswith(processed_prefix):
            yield key

def read_s3_object(key):
    resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
    return resp["Body"].read().decode("utf-8")

def mark_processed(key):
    target = processed_prefix + key
    s3.copy_object(Bucket=S3_BUCKET, CopySource={'Bucket': S3_BUCKET, 'Key': key}, Key=target)
    s3.delete_object(Bucket=S3_BUCKET, Key=key)

def call_mcp_http(text):
    payload = {"jsonrpc": "2.0", "id": "1", "method": "analyze", "params": {"text": text}}
    try:
        r = requests.post(f"{MCP_TOOL_URL}/mcp", json=payload, timeout=20)
        return r.json()
    except Exception as e:
        print("HTTP MCP call failed:", e, file=sys.stderr)
        return None

def call_mcp_stdio(text):
    # protocol: write JSON-RPC request line, read response line (very simple)
    # In a real implementation you'd use proper framing (length-prefix/newline) per MCP stdio guidance.
    req = {"jsonrpc":"2.0","id":"1","method":"analyze","params":{"text":text}}
    sys.stdout.flush()
    # send via stdout? For a sidecar pattern, the process would communicate differently.
    # We'll simply write to stdout and read a line from stdin in this demo pattern.
    sys.stdout.write(json.dumps(req) + "\n")
    sys.stdout.flush()
    # read response
    resp_line = sys.stdin.readline()
    if not resp_line:
        return None
    return json.loads(resp_line)

def handle_result(res):
    if not res or "result" not in res:
        print("Invalid response:", res)
        return
    sentiment = res["result"].get("sentiment","neutral").lower()
    PROCESSED.inc()
    if sentiment == "positive":
        POS.inc()
    elif sentiment == "negative":
        NEG.inc()
    else:
        NEU.inc()
    print("Sentiment:", sentiment)

def main():
    # Start metrics server
    start_http_server(int(os.getenv("METRICS_PORT", "8000")))
    print("Agent started. Polling S3:", S3_BUCKET, "transport:", MCP_TRANSPORT)
    while True:
        try:
            for key in list_text_objects():
                print("Processing", key)
                txt = read_s3_object(key)
                if MCP_TRANSPORT == "http":
                    res = call_mcp_http(txt)
                else:
                    res = call_mcp_stdio(txt)
                handle_result(res)
                mark_processed(key)
        except Exception as e:
            print("Error in main loop:", e, file=sys.stderr)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
