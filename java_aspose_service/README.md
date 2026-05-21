# Java Aspose Document Conversion Service

Single-JVM Java implementation for converting Office and email documents to PDF with Aspose for Java.

## Why This Version Exists

Unlike Aspose Python via .NET, the Java products can be loaded together in one JVM. This implementation is designed for one container and one runtime environment.

## API

- `GET /health`
- `POST /api/v1/convert`
  - multipart field `file`
  - form field `response_mode`: `stream` or `file`
- `GET /api/v1/files/{file_id}`

## Run In WSL

```bash
cd java_aspose_service
mvn test-compile
CP="target/classes"
for jar in ~/.m2/repository/com/aspose/**/*.jar ~/.m2/repository/com/twelvemonkeys/**/*.jar; do CP="$CP:$jar"; done
PORT=8000 java -cp "$CP" com.sanchiaki.doctrans.App
```

For Linux containers, install fonts for reliable layout:

```bash
apt-get update
apt-get install -y fontconfig fonts-noto-cjk
```

## Verification

```bash
mvn test
bash scripts/e2e_smoke.sh
```

## Container

```bash
docker build -t java-aspose-service .
docker run --rm -p 8000:8000 java-aspose-service
```
