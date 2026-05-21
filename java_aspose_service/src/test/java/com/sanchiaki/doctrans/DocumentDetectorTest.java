package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

class DocumentDetectorTest {
    @ParameterizedTest
    @CsvSource({
            "sample.doc, WORD",
            "sample.docx, WORD",
            "sample.rtf, WORD",
            "sample.odt, WORD",
            "sample.txt, WORD",
            "sample.html, WORD",
            "sample.mhtml, WORD",
            "sample.xls, EXCEL",
            "sample.xlsx, EXCEL",
            "sample.xlsm, EXCEL",
            "sample.csv, EXCEL",
            "sample.ods, EXCEL",
            "sample.ppt, PRESENTATION",
            "sample.pptx, PRESENTATION",
            "sample.pps, PRESENTATION",
            "sample.ppsx, PRESENTATION",
            "sample.odp, PRESENTATION",
            "sample.eml, EMAIL",
            "sample.msg, EMAIL"
    })
    void detectsSupportedFamilies(String filename, DocumentFamily expected) {
        assertEquals(expected, DocumentDetector.detect(filename));
    }

    @ParameterizedTest
    @ValueSource(strings = {"archive.zip", "no_extension", ".hidden"})
    void rejectsUnsupportedFiles(String filename) {
        assertThrows(UnsupportedFormatException.class, () -> DocumentDetector.detect(filename));
    }
}
