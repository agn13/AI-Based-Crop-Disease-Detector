package com.cropdisease.backend.repository;

import com.cropdisease.backend.model.ScanHistory;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface ScanHistoryRepository extends MongoRepository<ScanHistory, String> {

    List<ScanHistory> findTop50ByOrderByCreatedAtDesc();
}
