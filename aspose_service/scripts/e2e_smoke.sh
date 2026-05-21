#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

source "${ROOT_DIR}/runtime/.env.runtime"
export ASPOSE_SERVICE_WORKER_LIBRARY_PATH
export ASPOSE_SERVICE_WORD_PYTHON
export ASPOSE_SERVICE_CELLS_PYTHON
export ASPOSE_SERVICE_SLIDES_PYTHON
export ASPOSE_SERVICE_EMAIL_PYTHON
export LD_LIBRARY_PATH="${ASPOSE_SERVICE_WORKER_LIBRARY_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

SERVICE_PYTHON="${SERVICE_PYTHON:-${ROOT_DIR}/.venv/bin/python}"
PORT="${PORT:-18000}"
BASE_URL="http://127.0.0.1:${PORT}"
E2E_DIR="${ROOT_DIR}/runtime/e2e"

mkdir -p "${E2E_DIR}"
rm -f "${E2E_DIR}"/sample.* "${E2E_DIR}"/*.pdf "${E2E_DIR}/uvicorn.log"

"${ASPOSE_SERVICE_WORD_PYTHON}" - <<'PY'
from pathlib import Path
import aspose.words as aw

base = Path("runtime/e2e")
doc = aw.Document()
builder = aw.DocumentBuilder(doc)
builder.writeln("Aspose service verification")
doc.save(str(base / "sample.docx"))
PY

"${ASPOSE_SERVICE_CELLS_PYTHON}" - <<'PY'
from pathlib import Path
import aspose.cells as cells

base = Path("runtime/e2e")
workbook = cells.Workbook()
sheet = workbook.worksheets[0]
sheet.cells.get("A1").put_value("Aspose service verification")
workbook.save(str(base / "sample.xlsx"))
PY

"${ASPOSE_SERVICE_SLIDES_PYTHON}" - <<'PY'
from pathlib import Path
import aspose.slides as slides

base = Path("runtime/e2e")
with slides.Presentation() as presentation:
    presentation.save(str(base / "sample.pptx"), slides.export.SaveFormat.PPTX)
PY

cat > "${E2E_DIR}/sample.eml" <<'EOF'
From: sender@example.com
To: receiver@example.com
Subject: Aspose service verification
Date: Thu, 21 May 2026 01:00:00 +0800
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Aspose service verification email.
EOF

"${ASPOSE_SERVICE_WORD_PYTHON}" -m app.workers.aspose_convert word "${E2E_DIR}/sample.docx" "${E2E_DIR}/worker-sample.pdf"

"${SERVICE_PYTHON}" - <<'PY'
from pathlib import Path

pdf = Path("runtime/e2e/worker-sample.pdf")
assert pdf.exists(), "worker PDF does not exist"
assert pdf.stat().st_size > 0, "worker PDF is empty"
assert pdf.read_bytes()[:4] == b"%PDF", "worker output is not a PDF"
print("worker-pdf-ok", pdf.stat().st_size)
PY

"${SERVICE_PYTHON}" -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" > "${E2E_DIR}/uvicorn.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "${SERVER_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

"${SERVICE_PYTHON}" - <<PY
import time
import urllib.request

url = "${BASE_URL}/health"
last_error = None
for _ in range(60):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            if response.status == 200:
                print("health-ok")
                raise SystemExit(0)
    except Exception as exc:
        last_error = exc
        time.sleep(0.5)
raise SystemExit(f"service did not become healthy: {last_error}")
PY

"${SERVICE_PYTHON}" - <<PY
import http.client
from pathlib import Path

cases = [
    ("sample.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("sample.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("sample.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ("sample.eml", "message/rfc822"),
]

for filename, content_type in cases:
    boundary = f"----aspose-service-e2e-{filename.replace('.', '-')}"
    source = Path("runtime/e2e", filename).read_bytes()
    body = b"".join([
        f"--{boundary}\\r\\n".encode(),
        b'Content-Disposition: form-data; name="response_mode"\\r\\n\\r\\n',
        b"stream\\r\\n",
        f"--{boundary}\\r\\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\\r\\n'.encode(),
        f"Content-Type: {content_type}\\r\\n\\r\\n".encode(),
        source,
        b"\\r\\n",
        f"--{boundary}--\\r\\n".encode(),
    ])

    conn = http.client.HTTPConnection("127.0.0.1", ${PORT}, timeout=120)
    conn.request("POST", "/api/v1/convert", body=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    })
    response = conn.getresponse()
    payload = response.read()
    if response.status != 200:
        raise SystemExit(f"{filename} convert failed: {response.status} {payload[:500]!r}")
    if payload[:4] != b"%PDF":
        raise SystemExit(f"{filename} response is not a PDF: {payload[:20]!r}")
    output = Path("runtime/e2e", f"api-{filename}.pdf")
    output.write_bytes(payload)
    print("api-pdf-ok", filename, len(payload))
PY
