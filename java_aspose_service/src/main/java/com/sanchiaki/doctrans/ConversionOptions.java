package com.sanchiaki.doctrans;

import java.util.Map;

public class ConversionOptions {
    private final boolean excelOnePagePerSheet;

    public ConversionOptions(boolean excelOnePagePerSheet) {
        this.excelOnePagePerSheet = excelOnePagePerSheet;
    }

    public static ConversionOptions defaults() {
        return new ConversionOptions(false);
    }

    public static ConversionOptions fromFields(Map<String, String> fields) {
        return new ConversionOptions(parseBoolean(fields.get("excel_one_page_per_sheet")));
    }

    public boolean excelOnePagePerSheet() {
        return excelOnePagePerSheet;
    }

    private static boolean parseBoolean(String value) {
        if (value == null) {
            return false;
        }
        String normalized = value.trim().toLowerCase();
        return "true".equals(normalized) || "1".equals(normalized) || "yes".equals(normalized);
    }
}
