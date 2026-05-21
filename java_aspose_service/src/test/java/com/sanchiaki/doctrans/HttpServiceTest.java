package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.ServerSocket;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class HttpServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void healthReturnsOk() throws Exception {
        int port = freePort();
        DocumentConversionServer server = new DocumentConversionServer(port, tempDir, new DocumentConverter(new FakeAsposeAdapter()));
        server.start();
        try {
            HttpURLConnection connection = (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/health").openConnection();
            assertEquals(200, connection.getResponseCode());
            assertTrue(new String(connection.getInputStream().readAllBytes(), StandardCharsets.UTF_8).contains("\"ok\""));
        } finally {
            server.stop();
        }
    }

    @Test
    void convertStreamsPdf() throws Exception {
        int port = freePort();
        DocumentConversionServer server = new DocumentConversionServer(port, tempDir, new DocumentConverter(new FakeAsposeAdapter()));
        server.start();
        try {
            byte[] body = multipart("sample.docx", "source".getBytes(StandardCharsets.UTF_8));
            HttpURLConnection connection = (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/api/v1/convert").openConnection();
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=test-boundary");
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            assertEquals(200, connection.getResponseCode());
            assertEquals("application/pdf", connection.getHeaderField("Content-Type"));
            assertPdf(connection.getInputStream().readAllBytes());
        } finally {
            server.stop();
        }
    }

    @Test
    void convertFileModePersistsAndDownloadsPdf() throws Exception {
        int port = freePort();
        DocumentConversionServer server = new DocumentConversionServer(port, tempDir, new DocumentConverter(new FakeAsposeAdapter()));
        server.start();
        try {
            byte[] body = multipart("sample.docx", "source".getBytes(StandardCharsets.UTF_8), "file");
            HttpURLConnection connection = (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/api/v1/convert").openConnection();
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=test-boundary");
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            assertEquals(200, connection.getResponseCode());
            String payload = new String(connection.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
            String downloadUrl = payload.replaceAll(".*\\\"download_url\\\":\\\"([^\\\"]+)\\\".*", "$1");
            HttpURLConnection download = (HttpURLConnection) new URL("http://127.0.0.1:" + port + downloadUrl).openConnection();
            assertEquals(200, download.getResponseCode());
            assertPdf(download.getInputStream().readAllBytes());
        } finally {
            server.stop();
        }
    }

    @Test
    void convertPassesExcelSinglePageOption() throws Exception {
        int port = freePort();
        FakeAsposeAdapter adapter = new FakeAsposeAdapter();
        DocumentConversionServer server = new DocumentConversionServer(port, tempDir, new DocumentConverter(adapter));
        server.start();
        try {
            byte[] body = multipart("sample.xlsx", "source".getBytes(StandardCharsets.UTF_8), "stream", "true");
            HttpURLConnection connection = (HttpURLConnection) new URL("http://127.0.0.1:" + port + "/api/v1/convert").openConnection();
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=test-boundary");
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }

            assertEquals(200, connection.getResponseCode());
            assertPdf(connection.getInputStream().readAllBytes());
            assertTrue(adapter.excelOptions.excelOnePagePerSheet());
        } finally {
            server.stop();
        }
    }

    private static byte[] multipart(String filename, byte[] fileBytes) {
        return multipart(filename, fileBytes, "stream");
    }

    private static byte[] multipart(String filename, byte[] fileBytes, String responseMode) {
        return multipart(filename, fileBytes, responseMode, null);
    }

    private static byte[] multipart(String filename, byte[] fileBytes, String responseMode, String excelOnePagePerSheet) {
        String optionPart = excelOnePagePerSheet == null ? "" : ""
                + "--test-boundary\r\n"
                + "Content-Disposition: form-data; name=\"excel_one_page_per_sheet\"\r\n\r\n"
                + excelOnePagePerSheet + "\r\n";
        byte[] prefix = ("--test-boundary\r\n"
                + "Content-Disposition: form-data; name=\"response_mode\"\r\n\r\n"
                + responseMode + "\r\n"
                + optionPart
                + "--test-boundary\r\n"
                + "Content-Disposition: form-data; name=\"file\"; filename=\"" + filename + "\"\r\n"
                + "Content-Type: application/octet-stream\r\n\r\n").getBytes(StandardCharsets.UTF_8);
        byte[] suffix = "\r\n--test-boundary--\r\n".getBytes(StandardCharsets.UTF_8);
        byte[] body = new byte[prefix.length + fileBytes.length + suffix.length];
        System.arraycopy(prefix, 0, body, 0, prefix.length);
        System.arraycopy(fileBytes, 0, body, prefix.length, fileBytes.length);
        System.arraycopy(suffix, 0, body, prefix.length + fileBytes.length, suffix.length);
        return body;
    }

    private static int freePort() throws Exception {
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }

    private static void assertPdf(byte[] bytes) {
        assertTrue(bytes.length >= 4);
        assertEquals('%', bytes[0]);
        assertEquals('P', bytes[1]);
        assertEquals('D', bytes[2]);
        assertEquals('F', bytes[3]);
    }

    static class FakeAsposeAdapter implements AsposeAdapter {
        @Override
        public byte[] convertWord(Path source) throws Exception {
            Files.readAllBytes(source);
            return "%PDF fake".getBytes(StandardCharsets.UTF_8);
        }

        ConversionOptions excelOptions = ConversionOptions.defaults();

        @Override
        public byte[] convertExcel(Path source, ConversionOptions options) {
            excelOptions = options;
            return "%PDF fake".getBytes(StandardCharsets.UTF_8);
        }

        @Override
        public byte[] convertPresentation(Path source) {
            return "%PDF fake".getBytes(StandardCharsets.UTF_8);
        }

        @Override
        public byte[] convertEmail(Path source) {
            return "%PDF fake".getBytes(StandardCharsets.UTF_8);
        }
    }
}
