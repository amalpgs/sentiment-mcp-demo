---
## `build-and-zip.sh`

```bash
#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")"; pwd)"
cd "$ROOT"
ZIPNAME="sentiment-mcp-demo.zip"
rm -f "$ZIPNAME"
zip -r "$ZIPNAME" README.md services infra .github
echo "Created $ZIPNAME"
