package com.cropdisease.backend.controller;

import com.cropdisease.backend.model.ScanHistory;
import com.cropdisease.backend.repository.ScanHistoryRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/scans")
public class ScanHistoryController {

    private final ScanHistoryRepository scanHistoryRepository;

    public ScanHistoryController(ScanHistoryRepository scanHistoryRepository) {
        this.scanHistoryRepository = scanHistoryRepository;
    }

    @GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<List<ScanHistory>> listScans() {
        return ResponseEntity.ok(scanHistoryRepository.findTop50ByOrderByCreatedAtDesc());
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> createScan(@RequestBody ScanHistoryRequest request) {
        if (request == null || isBlank(request.disease) || isBlank(request.confidence) || isBlank(request.severity)) {
            return ResponseEntity.badRequest()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(Map.of("error", "disease, confidence, and severity are required"));
        }

        ScanHistory scan = new ScanHistory();
        scan.setFileName(defaultIfBlank(request.fileName, "unknown-file"));
        scan.setDisease(request.disease.trim());
        scan.setConfidence(request.confidence.trim());
        scan.setSeverity(request.severity.trim());
        scan.setTreatment(defaultIfBlank(request.treatment, "No treatment guidance available"));
        scan.setCreatedAt(request.createdAt != null ? request.createdAt : Instant.now());

        ScanHistory saved = scanHistoryRepository.save(scan);
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }

    @DeleteMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> clearScans() {
        long total = scanHistoryRepository.count();
        scanHistoryRepository.deleteAll();
        return ResponseEntity.ok(Map.of("deleted", total));
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private String defaultIfBlank(String value, String fallback) {
        return isBlank(value) ? fallback : value.trim();
    }

    public static class ScanHistoryRequest {
        public String fileName;
        public String disease;
        public String confidence;
        public String severity;
        public String treatment;
        public Instant createdAt;
    }
}
