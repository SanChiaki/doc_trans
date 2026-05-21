package com.sanchiaki.doctrans;

import java.nio.file.Path;

public class DocumentConverter {
    private final AsposeAdapter adapter;

    public DocumentConverter(AsposeAdapter adapter) {
        this.adapter = adapter;
    }

    public byte[] convert(Path source, String filename) throws Exception {
        return convert(source, filename, ConversionOptions.defaults());
    }

    public byte[] convert(Path source, String filename, ConversionOptions options) throws Exception {
        DocumentFamily family = DocumentDetector.detect(filename);
        switch (family) {
            case WORD:
                return adapter.convertWord(source);
            case EXCEL:
                return adapter.convertExcel(source, options);
            case PRESENTATION:
                return adapter.convertPresentation(source);
            case EMAIL:
                return adapter.convertEmail(source);
            default:
                throw new UnsupportedFormatException(filename);
        }
    }
}
