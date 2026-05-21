package com.sanchiaki.doctrans;

public class UnsupportedFormatException extends RuntimeException {
    public UnsupportedFormatException(String filename) {
        super("Unsupported document format: " + filename);
    }
}
