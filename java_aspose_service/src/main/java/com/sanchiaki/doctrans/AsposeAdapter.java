package com.sanchiaki.doctrans;

import java.nio.file.Path;

public interface AsposeAdapter {
    byte[] convertWord(Path source) throws Exception;

    byte[] convertExcel(Path source, ConversionOptions options) throws Exception;

    byte[] convertPresentation(Path source) throws Exception;

    byte[] convertEmail(Path source) throws Exception;
}
