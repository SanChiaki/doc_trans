#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PORT="${PORT:-18080}"
E2E_DIR="${ROOT_DIR}/target/e2e"
mkdir -p "${E2E_DIR}"
find "${E2E_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

mvn -q test-compile

CP="target/classes"
while IFS= read -r jar; do
  CP="${CP}:${jar}"
done < <(find "${HOME}/.m2/repository" -type f -name '*.jar' \
  \( -path '*/com/aspose/*' \
  -o -path '*/com/twelvemonkeys/*' \
  -o -path '*/org/slf4j/*' \
  -o -path '*/org/apache/logging/log4j/*' \) | sort)

cat > "${E2E_DIR}/MakeSamples.java" <<'JAVA'
import java.nio.file.*;

public class MakeSamples {
  public static void main(String[] args) throws Exception {
    Path dir = Paths.get(args[0]);
    com.aspose.words.Document doc = new com.aspose.words.Document();
    new com.aspose.words.DocumentBuilder(doc).writeln("Java Aspose service verification");
    doc.save(dir.resolve("sample.docx").toString());

    com.aspose.cells.Workbook workbook = new com.aspose.cells.Workbook();
    com.aspose.cells.Cells cells = workbook.getWorksheets().get(0).getCells();
    for (int row = 0; row < 40; row++) {
      for (int column = 0; column < 15; column++) {
        cells.get(row, column).putValue("Java Aspose service verification " + row + "-" + column);
      }
    }
    workbook.save(dir.resolve("sample.xlsx").toString());

    com.aspose.slides.Presentation presentation = new com.aspose.slides.Presentation();
    try {
      presentation.save(dir.resolve("sample.pptx").toString(), com.aspose.slides.SaveFormat.Pptx);
    } finally {
      presentation.dispose();
    }

    Files.write(dir.resolve("sample.eml"), (""
      + "From: sender@example.com\r\n"
      + "To: receiver@example.com\r\n"
      + "Subject: Java Aspose service verification\r\n"
      + "Date: Thu, 21 May 2026 01:00:00 +0800\r\n"
      + "MIME-Version: 1.0\r\n"
      + "Content-Type: text/plain; charset=utf-8\r\n"
      + "\r\n"
      + "Java Aspose service verification email.\r\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
  }
}
JAVA

javac -cp "${CP}" "${E2E_DIR}/MakeSamples.java"
java -cp "${CP}:${E2E_DIR}" MakeSamples "${E2E_DIR}"

JAVA_ASPOSE_RUNTIME_DIR="${E2E_DIR}/runtime" PORT="${PORT}" java -cp "${CP}" com.sanchiaki.doctrans.App > "${E2E_DIR}/server.log" 2>&1 &
SERVER_PID=$!
cleanup() {
  kill "${SERVER_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

python3 - <<PY
import time
import urllib.request

for _ in range(60):
    try:
        with urllib.request.urlopen("http://127.0.0.1:${PORT}/health", timeout=1) as response:
            if response.status == 200:
                print("health-ok")
                raise SystemExit(0)
    except Exception:
        time.sleep(0.5)
raise SystemExit("service did not become healthy")
PY

python3 - <<PY
import http.client
from pathlib import Path

cases = ["sample.docx", "sample.xlsx", "sample.pptx", "sample.eml"]
for filename in cases:
    boundary = "----java-aspose-e2e-" + filename.replace(".", "-")
    source = Path("${E2E_DIR}", filename).read_bytes()
    excel_options = []
    if filename.endswith(".xlsx"):
        excel_options = [
            f"--{boundary}\\r\\n".encode(),
            b'Content-Disposition: form-data; name="excel_one_page_per_sheet"\\r\\n\\r\\n',
            b"true\\r\\n",
        ]
    body = b"".join([
        f"--{boundary}\\r\\n".encode(),
        b'Content-Disposition: form-data; name="response_mode"\\r\\n\\r\\n',
        b"stream\\r\\n",
        *excel_options,
        f"--{boundary}\\r\\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\\r\\n'.encode(),
        b"Content-Type: application/octet-stream\\r\\n\\r\\n",
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
        raise SystemExit(f"{filename} failed: {response.status} {payload[:500]!r}")
    if payload[:4] != b"%PDF":
        raise SystemExit(f"{filename} did not return PDF: {payload[:20]!r}")
    Path("${E2E_DIR}", "api-" + filename + ".pdf").write_bytes(payload)
    print("api-pdf-ok", filename, len(payload))
PY
