package com.sanchiaki.doctrans;

import java.nio.file.Path;

public class App {
    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8000"));
        Path runtime = Path.of(System.getenv().getOrDefault("JAVA_ASPOSE_RUNTIME_DIR", "runtime"));
        DocumentConversionServer server = new DocumentConversionServer(port, runtime, new DocumentConverter(new JavaAsposeAdapter()));
        server.start();
        System.out.println("Java Aspose service listening on port " + port);
    }
}
