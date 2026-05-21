package com.sanchiaki.doctrans;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

public class JavaAsposeAdapter implements AsposeAdapter {
    @Override
    public byte[] convertWord(Path source) throws Exception {
        com.aspose.words.Document document = new com.aspose.words.Document(source.toString());
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        document.save(output, com.aspose.words.SaveFormat.PDF);
        return output.toByteArray();
    }

    @Override
    public byte[] convertExcel(Path source, ConversionOptions options) throws Exception {
        com.aspose.cells.Workbook workbook = new com.aspose.cells.Workbook(source.toString());
        com.aspose.cells.PdfSaveOptions saveOptions = new com.aspose.cells.PdfSaveOptions();
        if (options.excelOnePagePerSheet()) {
            fitEachWorksheetToSinglePage(workbook);
            saveOptions.setOnePagePerSheet(true);
        }
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        workbook.save(output, saveOptions);
        return output.toByteArray();
    }

    @Override
    public byte[] convertPresentation(Path source) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        com.aspose.slides.Presentation presentation = new com.aspose.slides.Presentation(source.toString());
        try {
            presentation.save(output, com.aspose.slides.SaveFormat.Pdf);
        } finally {
            presentation.dispose();
        }
        return output.toByteArray();
    }

    @Override
    public byte[] convertEmail(Path source) throws Exception {
        Path mhtml = Files.createTempFile("aspose-email-", ".mhtml");
        try {
            com.aspose.email.MailMessage message = com.aspose.email.MailMessage.load(source.toString());
            message.save(mhtml.toString(), com.aspose.email.SaveOptions.getDefaultMhtml());
            return convertWord(mhtml);
        } finally {
            Files.deleteIfExists(mhtml);
        }
    }

    private void fitEachWorksheetToSinglePage(com.aspose.cells.Workbook workbook) {
        for (int index = 0; index < workbook.getWorksheets().getCount(); index++) {
            com.aspose.cells.PageSetup pageSetup = workbook.getWorksheets().get(index).getPageSetup();
            pageSetup.setPercentScale(false);
            pageSetup.setFitToPagesWide(1);
            pageSetup.setFitToPagesTall(1);
        }
    }
}
