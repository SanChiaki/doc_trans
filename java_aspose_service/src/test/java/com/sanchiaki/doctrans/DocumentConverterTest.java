package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;

class DocumentConverterTest {
    @Test
    void dispatchesToWordConverter() throws Exception {
        FakeAsposeAdapter adapter = new FakeAsposeAdapter();
        DocumentConverter converter = new DocumentConverter(adapter);

        byte[] pdf = converter.convert(Path.of("sample.docx"), "sample.docx");

        assertArrayEquals("word-pdf".getBytes(), pdf);
        assertEquals("word", adapter.calledFamily);
    }

    @Test
    void dispatchesToEmailConverter() throws Exception {
        FakeAsposeAdapter adapter = new FakeAsposeAdapter();
        DocumentConverter converter = new DocumentConverter(adapter);

        byte[] pdf = converter.convert(Path.of("message.eml"), "message.eml");

        assertArrayEquals("email-pdf".getBytes(), pdf);
        assertEquals("email", adapter.calledFamily);
    }

    static class FakeAsposeAdapter implements AsposeAdapter {
        String calledFamily;

        @Override
        public byte[] convertWord(Path source) {
            calledFamily = "word";
            return "word-pdf".getBytes();
        }

        @Override
        public byte[] convertExcel(Path source) {
            calledFamily = "excel";
            return "excel-pdf".getBytes();
        }

        @Override
        public byte[] convertPresentation(Path source) {
            calledFamily = "presentation";
            return "presentation-pdf".getBytes();
        }

        @Override
        public byte[] convertEmail(Path source) {
            calledFamily = "email";
            return "email-pdf".getBytes();
        }
    }
}
