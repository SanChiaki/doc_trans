package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
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
        assertPdf(adapter.convertExcel(createXlsx(), ConversionOptions.defaults()));
        assertPdf(adapter.convertPresentation(createPptx()));
        assertPdf(adapter.convertEmail(createEml()));
    }

    @Test
    void convertsEachExcelSheetToOnePdfPageWhenRequested() throws Exception {
        JavaAsposeAdapter adapter = new JavaAsposeAdapter();
        Path workbook = createWideXlsx();

        byte[] defaultPdf = adapter.convertExcel(workbook, ConversionOptions.defaults());
        byte[] singlePagePdf = adapter.convertExcel(workbook, new ConversionOptions(true));

        int defaultPages = countPdfPages(defaultPdf);
        int singlePagePages = countPdfPages(singlePagePdf);

        assertTrue(defaultPages > singlePagePages);
        assertTrue(singlePagePages <= 2);
    }

    @Test
    void keepsExcelTextSelectableWhenSinglePageModeIsRequested() throws Exception {
        JavaAsposeAdapter adapter = new JavaAsposeAdapter();

        byte[] pdf = adapter.convertExcel(createWideXlsx(), new ConversionOptions(true));

        assertTrue(extractPdfText(pdf).contains("cell-0-0-wide-text"));
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

    private Path createWideXlsx() throws Exception {
        Path path = tempDir.resolve("wide.xlsx");
        com.aspose.cells.Workbook workbook = new com.aspose.cells.Workbook();
        com.aspose.cells.Cells cells = workbook.getWorksheets().get(0).getCells();
        for (int row = 0; row < 80; row++) {
            for (int column = 0; column < 25; column++) {
                cells.get(row, column).putValue("cell-" + row + "-" + column + "-wide-text");
            }
        }
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

    private int countPdfPages(byte[] pdf) throws Exception {
        com.aspose.pdf.Document document = new com.aspose.pdf.Document(new ByteArrayInputStream(pdf));
        return document.getPages().size();
    }

    private String extractPdfText(byte[] pdf) throws Exception {
        try (org.apache.pdfbox.pdmodel.PDDocument document = org.apache.pdfbox.Loader.loadPDF(pdf)) {
            return new org.apache.pdfbox.text.PDFTextStripper().getText(document);
        }
    }
}
