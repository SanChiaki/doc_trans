package com.sanchiaki.doctrans;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;

class DependencySmokeTest {
    @Test
    void asposeClassesAreAvailableInOneJvm() {
        assertNotNull(com.aspose.words.Document.class);
        assertNotNull(com.aspose.cells.Workbook.class);
        assertNotNull(com.aspose.slides.Presentation.class);
        assertNotNull(com.aspose.email.MailMessage.class);
    }
}
