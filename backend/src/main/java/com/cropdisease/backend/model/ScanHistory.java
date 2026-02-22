package com.cropdisease.backend.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Document(collection = "scan_history")
public class ScanHistory {

    @Id
    private String id;

    private String fileName;

    private String disease;

    private String confidence;

    private String severity;

    private String treatment;

    private Instant createdAt;
}
