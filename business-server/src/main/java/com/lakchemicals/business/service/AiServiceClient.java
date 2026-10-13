package com.lakchemicals.business.service;

import com.lakchemicals.business.dto.report.AiReportAnalysisRequest;
import com.lakchemicals.business.dto.report.AiReportAnalysisResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.util.List;

@Slf4j
@Service
public class AiServiceClient {

    private final RestClient restClient;
    private final String baseUrl;
    private final String apiKey;

    public AiServiceClient(
            @Value("${ai-service.base-url:http://localhost:8001}") String baseUrl,
            @Value("${ai-service.api-key:}") String apiKey
    ) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;

        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) Duration.ofSeconds(10).toMillis());
        factory.setReadTimeout((int) Duration.ofSeconds(60).toMillis());

        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(factory)
                .build();

        log.info("AiServiceClient initialized pointing to {}", baseUrl);
    }

    public AiReportAnalysisResponse analyzeReport(AiReportAnalysisRequest request) {
        log.info("Sending report analysis request to AI service for type: {}", request.getReportType());

        try {
            return restClient.post()
                    .uri("/api/v1/reports/analyze")
                    .header("x-api-key", apiKey)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(AiReportAnalysisResponse.class);
        } catch (Exception e) {
            log.error("Failed to call AI service at {}/api/v1/reports/analyze: {}", baseUrl, e.getMessage(), e);
            // Return fallback analysis so report generation succeeds even if AI service is restarting
            return AiReportAnalysisResponse.builder()
                    .reportType(request.getReportType())
                    .summary("Heuristic summary: report generated successfully (AI reasoning service was temporarily unavailable).")
                    .insights(List.of(
                            "Database metrics were successfully compiled and validated.",
                            "Review line items for notable variations or outliers."
                    ))
                    .recommendations(List.of(
                            "Validate current figures against business goals for this period.",
                            "Consult departmental heads on inventory reorder thresholds."
                    ))
                    .riskAlerts(List.of())
                    .build();
        }
    }
}
