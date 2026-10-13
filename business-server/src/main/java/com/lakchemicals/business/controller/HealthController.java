package com.lakchemicals.business.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@Tag(name = "Main", description = "Root and Health check endpoints")
public class HealthController {

    @GetMapping({"/", "/api/v1"})
    @Operation(summary = "Root API greeting")
    public ResponseEntity<Map<String, String>> root() {
        return ResponseEntity.ok(Map.of("message", "Welcome to Lak Chemicals and Hardware"));
    }

    @GetMapping({"/health", "/api/v1/health"})
    @Operation(summary = "System health check")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("message", "Lak Chemicals and Hardware is healthy"));
    }
}
