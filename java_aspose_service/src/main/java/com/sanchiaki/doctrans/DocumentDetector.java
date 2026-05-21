package com.sanchiaki.doctrans;

import java.util.Locale;
import java.util.Map;

public final class DocumentDetector {
    private static final Map<String, DocumentFamily> EXTENSIONS = Map.ofEntries(
            Map.entry(".doc", DocumentFamily.WORD),
            Map.entry(".docx", DocumentFamily.WORD),
            Map.entry(".rtf", DocumentFamily.WORD),
            Map.entry(".odt", DocumentFamily.WORD),
            Map.entry(".txt", DocumentFamily.WORD),
            Map.entry(".html", DocumentFamily.WORD),
            Map.entry(".htm", DocumentFamily.WORD),
            Map.entry(".mhtml", DocumentFamily.WORD),
            Map.entry(".xls", DocumentFamily.EXCEL),
            Map.entry(".xlsx", DocumentFamily.EXCEL),
            Map.entry(".xlsm", DocumentFamily.EXCEL),
            Map.entry(".csv", DocumentFamily.EXCEL),
            Map.entry(".ods", DocumentFamily.EXCEL),
            Map.entry(".ppt", DocumentFamily.PRESENTATION),
            Map.entry(".pptx", DocumentFamily.PRESENTATION),
            Map.entry(".pps", DocumentFamily.PRESENTATION),
            Map.entry(".ppsx", DocumentFamily.PRESENTATION),
            Map.entry(".odp", DocumentFamily.PRESENTATION),
            Map.entry(".eml", DocumentFamily.EMAIL),
            Map.entry(".msg", DocumentFamily.EMAIL)
    );

    private DocumentDetector() {
    }

    public static DocumentFamily detect(String filename) {
        String lower = filename == null ? "" : filename.toLowerCase(Locale.ROOT);
        int index = lower.lastIndexOf('.');
        String extension = index > 0 ? lower.substring(index) : "";
        DocumentFamily family = EXTENSIONS.get(extension);
        if (family == null) {
            throw new UnsupportedFormatException(filename);
        }
        return family;
    }
}
