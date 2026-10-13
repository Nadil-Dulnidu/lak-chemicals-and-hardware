package com.lakchemicals.business;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.constants.ReportType;
import com.lakchemicals.business.dto.report.*;
import com.lakchemicals.business.entity.Order;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.entity.Report;
import com.lakchemicals.business.entity.Sale;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.repository.ReportRepository;
import com.lakchemicals.business.repository.SaleRepository;
import com.lakchemicals.business.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ReportServiceTest {

    @Mock
    private ReportRepository reportRepository;

    @Mock
    private SaleRepository saleRepository;

    @Mock
    private ProductRepository productRepository;

    @Spy
    private ObjectMapper objectMapper = new ObjectMapper();

    @InjectMocks
    private ReportService reportService;

    private Product product;
    private Order order;
    private Sale sale;

    @BeforeEach
    void setUp() {
        product = Product.builder()
                .id(UUID.randomUUID())
                .name("Wood Primer")
                .price(1800.0)
                .stockQty(4)
                .reorderLevel(10)
                .category(ProductCategory.PAINTS)
                .isActive(true)
                .build();

        order = Order.builder()
                .orderId(1)
                .userId("user_1")
                .totalAmount(BigDecimal.valueOf(3600))
                .build();

        sale = Sale.builder()
                .saleId(1)
                .order(order)
                .product(product)
                .quantity(2)
                .revenue(BigDecimal.valueOf(3600))
                .saleDate(LocalDateTime.now())
                .build();
    }

    @Test
    void testCreateReport_Success() {
        ReportCreateRequest request = ReportCreateRequest.builder()
                .reportName("Monthly Sales")
                .reportType(ReportType.SALES)
                .description("Monthly sales report")
                .build();

        Report saved = Report.builder()
                .reportId(1)
                .reportName("Monthly Sales")
                .reportType(ReportType.SALES)
                .createdBy("admin")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(reportRepository.save(any(Report.class))).thenReturn(saved);

        ReportResponse response = reportService.createReport("admin", request);

        assertNotNull(response);
        assertEquals(1, response.getReportId());
        assertEquals("Monthly Sales", response.getReportName());
    }

    @Test
    void testGenerateSalesReport() {
        SalesReportParams params = SalesReportParams.builder()
                .startDate(LocalDateTime.now().minusDays(7))
                .endDate(LocalDateTime.now().plusDays(1))
                .groupBy("day")
                .build();

        when(saleRepository.findBySaleDateBetweenOrderBySaleDateAsc(any(), any()))
                .thenReturn(List.of(sale));

        SalesReportData data = reportService.generateSalesReport(params);

        assertNotNull(data);
        assertEquals("SALES", data.getReportType());
        assertEquals(BigDecimal.valueOf(3600), data.getSummary().get("total_revenue"));
        assertEquals(2, data.getSummary().get("total_quantity"));
        assertEquals(1, data.getItems().size());
    }

    @Test
    void testGenerateInventoryReport() {
        InventoryReportParams params = InventoryReportParams.builder().build();

        when(productRepository.findAll()).thenReturn(List.of(product));

        InventoryReportData data = reportService.generateInventoryReport(params);

        assertNotNull(data);
        assertEquals("INVENTORY", data.getReportType());
        assertEquals(1, data.getItems().size());
        assertEquals("LOW", data.getItems().get(0).getStatus()); // stock 4 <= reorder 10
        assertEquals(1, data.getLowStockItems().size());
    }

    @Test
    void testGenerateProductPerformanceReport() {
        ProductPerformanceParams params = ProductPerformanceParams.builder()
                .startDate(LocalDateTime.now().minusDays(30))
                .endDate(LocalDateTime.now().plusDays(1))
                .topN(5)
                .build();

        when(saleRepository.findBySaleDateBetweenOrderBySaleDateAsc(any(), any()))
                .thenReturn(List.of(sale));

        ProductPerformanceData data = reportService.generateProductPerformanceReport(params);

        assertNotNull(data);
        assertEquals(1, data.getTopProducts().size());
        assertEquals(2, data.getTopProducts().get(0).getTotalQuantitySold());
    }

    @Test
    void testGenerateLowStockReport() {
        LowStockReportParams params = LowStockReportParams.builder()
                .thresholdPercentage(20)
                .build();

        when(productRepository.findAll()).thenReturn(List.of(product));

        LowStockReportData data = reportService.generateLowStockReport(params);

        assertNotNull(data);
        assertEquals(1, data.getItems().size());
        assertEquals(product.getId(), data.getItems().get(0).getProductId());
    }
}
