package com.sanchiaki.doctrans;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Executors;

public class DocumentConversionServer {
    private final int port;
    private final Path runtimeDir;
    private final Path uploadDir;
    private final Path outputDir;
    private final DocumentConverter converter;
    private HttpServer server;

    public DocumentConversionServer(int port, Path runtimeDir, DocumentConverter converter) {
        this.port = port;
        this.runtimeDir = runtimeDir;
        this.uploadDir = runtimeDir.resolve("uploads");
        this.outputDir = runtimeDir.resolve("outputs");
        this.converter = converter;
    }

    public void start() throws IOException {
        Files.createDirectories(uploadDir);
        Files.createDirectories(outputDir);
        server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
        server.createContext("/health", this::health);
        server.createContext("/api/v1/convert", this::convert);
        server.createContext("/api/v1/files", this::download);
        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
    }

    public void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    private void health(HttpExchange exchange) throws IOException {
        writeJson(exchange, 200, "{\"status\":\"ok\"}");
    }

    private void convert(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            writeJson(exchange, 405, "{\"code\":\"method_not_allowed\",\"message\":\"Use POST.\"}");
            return;
        }
        try {
            MultipartRequest request = MultipartRequest.parse(
                    exchange.getRequestHeaders().getFirst("Content-Type"),
                    exchange.getRequestBody().readAllBytes());
            if (request.fileBytes.length == 0) {
                writeJson(exchange, 400, "{\"code\":\"bad_request\",\"message\":\"Uploaded file is empty.\"}");
                return;
            }

            Path source = uploadDir.resolve(UUID.randomUUID() + extensionOf(request.filename));
            Files.write(source, request.fileBytes);
            byte[] pdf;
            try {
                pdf = converter.convert(source, request.filename, ConversionOptions.fromFields(request.fields));
            } finally {
                Files.deleteIfExists(source);
            }

            if ("file".equals(request.fields.getOrDefault("response_mode", "stream"))) {
                String id = UUID.randomUUID().toString().replace("-", "");
                Path output = outputDir.resolve(id + ".pdf");
                Files.write(output, pdf);
                writeJson(exchange, 200, "{\"file_id\":\"" + id + "\",\"download_url\":\"/api/v1/files/" + id
                        + "\",\"filename\":\"" + pdfFilename(request.filename) + "\",\"content_type\":\"application/pdf\"}");
                return;
            }

            exchange.getResponseHeaders().set("Content-Type", "application/pdf");
            exchange.getResponseHeaders().set("Content-Disposition", "attachment; filename=\"" + pdfFilename(request.filename) + "\"");
            exchange.sendResponseHeaders(200, pdf.length);
            try (OutputStream output = exchange.getResponseBody()) {
                output.write(pdf);
            }
        } catch (UnsupportedFormatException exc) {
            writeJson(exchange, 415, "{\"code\":\"unsupported_format\",\"message\":\"" + json(exc.getMessage()) + "\"}");
        } catch (Exception exc) {
            writeJson(exchange, 422, "{\"code\":\"conversion_failed\",\"message\":\"" + json(exc.getMessage()) + "\"}");
        }
    }

    private void download(HttpExchange exchange) throws IOException {
        URI uri = exchange.getRequestURI();
        String prefix = "/api/v1/files/";
        String path = uri.getPath();
        if (!path.startsWith(prefix) || path.length() <= prefix.length()) {
            writeJson(exchange, 404, "{\"code\":\"not_found\",\"message\":\"File not found.\"}");
            return;
        }
        String id = path.substring(prefix.length());
        Path output = outputDir.resolve(id + ".pdf");
        if (!Files.exists(output)) {
            writeJson(exchange, 404, "{\"code\":\"not_found\",\"message\":\"File not found.\"}");
            return;
        }
        byte[] pdf = Files.readAllBytes(output);
        exchange.getResponseHeaders().set("Content-Type", "application/pdf");
        exchange.sendResponseHeaders(200, pdf.length);
        try (OutputStream response = exchange.getResponseBody()) {
            response.write(pdf);
        }
    }

    private static void writeJson(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }

    private static String extensionOf(String filename) {
        int index = filename == null ? -1 : filename.lastIndexOf('.');
        return index > 0 ? filename.substring(index).toLowerCase() : ".bin";
    }

    private static String pdfFilename(String filename) {
        String name = filename == null || filename.isBlank() ? "converted" : filename;
        int index = name.lastIndexOf('.');
        String stem = index > 0 ? name.substring(0, index) : name;
        return stem + ".pdf";
    }

    private static String json(String value) {
        return value == null ? "" : value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    static class MultipartRequest {
        final String filename;
        final byte[] fileBytes;
        final Map<String, String> fields;

        MultipartRequest(String filename, byte[] fileBytes, Map<String, String> fields) {
            this.filename = filename;
            this.fileBytes = fileBytes;
            this.fields = fields;
        }

        static MultipartRequest parse(String contentType, byte[] body) {
            String boundary = "--" + contentType.substring(contentType.indexOf("boundary=") + "boundary=".length());
            String content = new String(body, StandardCharsets.ISO_8859_1);
            String filename = "upload.bin";
            byte[] fileBytes = new byte[0];
            Map<String, String> fields = new HashMap<>();
            for (String part : content.split(java.util.regex.Pattern.quote(boundary))) {
                if (!part.contains("Content-Disposition")) {
                    continue;
                }
                int split = part.indexOf("\r\n\r\n");
                if (split < 0) {
                    continue;
                }
                String headers = part.substring(0, split);
                String value = part.substring(split + 4);
                if (value.endsWith("\r\n")) {
                    value = value.substring(0, value.length() - 2);
                }
                if (headers.contains("filename=\"")) {
                    filename = between(headers, "filename=\"", "\"");
                    fileBytes = value.getBytes(StandardCharsets.ISO_8859_1);
                } else if (headers.contains("name=\"")) {
                    String name = between(headers, "name=\"", "\"");
                    fields.put(name, value);
                }
            }
            return new MultipartRequest(filename, fileBytes, fields);
        }

        private static String between(String text, String start, String end) {
            int from = text.indexOf(start);
            if (from < 0) {
                return "";
            }
            int valueStart = from + start.length();
            int valueEnd = text.indexOf(end, valueStart);
            return valueEnd < 0 ? text.substring(valueStart) : text.substring(valueStart, valueEnd);
        }
    }
}
