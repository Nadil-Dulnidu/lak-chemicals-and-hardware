package com.lakchemicals.business;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.lakchemicals.business.dto.report.SalesReportParams;
import com.lakchemicals.business.service.ProductService;
import com.lakchemicals.business.service.ReportService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestPropertySource(properties = {
        "springdotenv.enabled=false",
        "spring.datasource.url=jdbc:h2:mem:testdb;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password="
})
class ApiControllerSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void testRootEndpoint_Public_Returns200() throws Exception {
        mockMvc.perform(get("/"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Welcome to Lak Chemicals and Hardware"));
    }

    @Test
    void testHealthEndpoint_Public_Returns200() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Lak Chemicals and Hardware is healthy"));
    }

    @Test
    void testGetProducts_Public_Returns200() throws Exception {
        mockMvc.perform(get("/api/v1/products"))
                .andExpect(status().isOk());
    }

    @Test
    void testGetCart_WithoutToken_ReturnsForbiddenOrUnauthorized() throws Exception {
        mockMvc.perform(get("/api/v1/cart"))
                .andExpect(status().isForbidden());
    }

    @Test
    void testGetOrders_WithoutToken_ReturnsForbiddenOrUnauthorized() throws Exception {
        mockMvc.perform(get("/api/v1/orders"))
                .andExpect(status().isForbidden());
    }

    @Test
    void testCreateProduct_WithoutAdminToken_ReturnsForbidden() throws Exception {
        mockMvc.perform(post("/api/v1/products")
                        .param("name", "Test")
                        .param("price", "100")
                        .param("stock_qty", "10"))
                .andExpect(status().isForbidden());
    }

    @Test
    void testGetSuppliers_WithoutAdminToken_ReturnsForbidden() throws Exception {
        mockMvc.perform(get("/api/v1/suppliers"))
                .andExpect(status().isForbidden());
    }

    @Test
    void testAgentTool_WithoutApiKey_ReturnsForbidden() throws Exception {
        SalesReportParams params = SalesReportParams.builder()
                .startDate(LocalDateTime.now().minusDays(1))
                .endDate(LocalDateTime.now())
                .build();

        mockMvc.perform(post("/api/v1/tools/sales")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(params)))
                .andExpect(status().isForbidden());
    }

    @Test
    void testAgentTool_WithValidApiKey_Returns200() throws Exception {
        SalesReportParams params = SalesReportParams.builder()
                .startDate(LocalDateTime.now().minusDays(7))
                .endDate(LocalDateTime.now())
                .build();

        mockMvc.perform(post("/api/v1/tools/sales")
                        .header("x-api-key", "test-api-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(params)))
                .andExpect(status().isOk());
    }
}
