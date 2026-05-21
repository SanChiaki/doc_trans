package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class AsposeAdapterIntegrationTest {
    @TempDir
    Path tempDir;

    @Test
    void convertsWordExcelPresentationAndEmailInOneJvm() throws Exception {
        JavaAsposeAdapter adapter = new JavaAsposeAdapter();

        assertPdf(adapter.convertWord(createDocx()));
        assertPdf(adapter.convertExcel(createXlsx()));
        assertPdf(adapter.convertPresentation(createPptx()));
        assertPdf(adapter.convertEmail(createEml()));
    }

    private Path createDocx() throws Exception {
        Path path = tempDir.resolve("sample.docx");
        com.aspose.words.Document document = new com.aspose.words.Document();
        com.aspose.words.DocumentBuilder builder = new com.aspose.words.DocumentBuilder(document);
        builder.writeln("Java Aspose verification");
        document.save(path.toString());
        return path;
    }

    private Path createXlsx() throws Exception {
        Path path = tempDir.resolve("sample.xlsx");
        com.aspose.cells.Workbook workbook = new com.aspose.cells.Workbook();
        workbook.getWorksheets().get(0).getCells().get("A1").putValue("Java Aspose verification");
        workbook.save(path.toString());
        return path;
    }

    private Path createPptx() throws Exception {
        Path path = tempDir.resolve("sample.pptx");
        com.aspose.slides.Presentation presentation = new com.aspose.slides.Presentation();
        try {
            presentation.save(path.toString(), com.aspose.slides.SaveFormat.Pptx);
        } finally {
            presentation.dispose();
        }
        return path;
    }

    private Path createEml() throws Exception {
        Path path = tempDir.resolve("sample.eml");
        String content = ""
                + "From: sender@example.com\r\n"
                + "To: receiver@example.com\r\n"
                + "Subject: Java Aspose verification\r\n"
                + "Date: Thu, 21 May 2026 01:00:00 +0800\r\n"
                + "MIME-Version: 1.0\r\n"
                + "Content-Type: text/plain; charset=utf-8\r\n"
                + "\r\n"
                + "Java Aspose verification email.\r\n";
        Files.writeString(path, content);
        return path;
    }

    private void assertPdf(byte[] bytes) {
        assertTrue(bytes.length > 0);
        assertTrue(bytes[0] == '%' && bytes[1] == 'P' && bytes[2] == 'D' && bytes[3] == 'F');
    }
}
