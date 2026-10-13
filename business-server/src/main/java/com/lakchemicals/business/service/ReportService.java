package com.lakchemicals.business.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.constants.ReportType;
import com.lakchemicals.business.dto.report.*;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.entity.Report;
import com.lakchemicals.business.entity.Sale;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.repository.ReportRepository;
import com.lakchemicals.business.repository.SaleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReportService {

    private final ReportRepository reportRepository;
    private final SaleRepository saleRepository;
    private final ProductRepository productRepository;
    private final ObjectMapper objectMapper;

    // ─────────────────────────────────────────────────────────────────────────
    // REPORT CRUD
    // ─────────────────────────────────────────────────────────────────────────

    @Transactional
    public ReportResponse createReport(String userId, ReportCreateRequest request) {
        log.info("Creating report configuration: {} by {}", request.getReportName(), userId);

        String paramJson = null;
        if (request.getParameters() != null) {
            try {
                paramJson = objectMapper.writeValueAsString(request.getParameters());
            } catch (Exception e) {
                log.warn("Could not serialize report parameters: {}", e.getMessage());
            }
        }

        Report report = Report.builder()
                .reportName(request.getReportName())
                .reportType(request.getReportType())
                .parameters(paramJson)
                .createdBy(userId != null ? userId : "system")
                .description(request.getDescription())
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        Report saved = reportRepository.save(report);
        return mapToResponse(saved);
    }

    @Transactional(readOnly = true)
    public ReportResponse getReportById(Integer reportId) {
        Report report = reportRepository.findById(reportId)
                .orElseThrow(() -> new ResourceNotFoundException("Report not found with id: " + reportId));
        return mapToResponse(report);
    }

    @Transactional
    public ReportResponse updateReport(Integer reportId, ReportUpdateRequest request) {
        Report report = reportRepository.findById(reportId)
                .orElseThrow(() -> new ResourceNotFoundException("Report not found with id: " + reportId));

        if (request.getReportName() != null) {
            report.setReportName(request.getReportName());
        }
        if (request.getDescription() != null) {
            report.setDescription(request.getDescription());
        }
        if (request.getParameters() != null) {
            try {
                report.setParameters(objectMapper.writeValueAsString(request.getParameters()));
            } catch (Exception e) {
                log.warn("Could not serialize report parameters: {}", e.getMessage());
            }
        }
        report.setUpdatedAt(LocalDateTime.now());

        return mapToResponse(reportRepository.save(report));
    }

    @Transactional
    public void deleteReport(Integer reportId) {
        Report report = reportRepository.findById(reportId)
                .orElseThrow(() -> new ResourceNotFoundException("Report not found with id: " + reportId));
        reportRepository.delete(report);
    }

    @Transactional(readOnly = true)
    public ReportListResponse getAllReports(ReportType reportType, int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "createdAt"));

        Page<Report> reportPage = reportType != null ?
                reportRepository.findByReportType(reportType, pageable) :
                reportRepository.findAll(pageable);

        List<ReportResponse> dtos = reportPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return ReportListResponse.builder()
                .reports(dtos)
                .total(reportPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(reportPage.hasNext())
                .build();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // REPORT GENERATION
    // ─────────────────────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public SalesReportData generateSalesReport(SalesReportParams params) {
        if (params.getEndDate().isBefore(params.getStartDate()) || params.getEndDate().isEqual(params.getStartDate())) {
            throw new BadRequestException("end_date must be after start_date");
        }

        List<Sale> sales = saleRepository.findBySaleDateBetweenOrderBySaleDateAsc(params.getStartDate(), params.getEndDate());

        if (params.getProductId() != null) {
            sales = sales.stream().filter(s -> s.getProduct().getId().equals(params.getProductId())).toList();
        }

        if (params.getCategory() != null && !params.getCategory().isBlank()) {
            sales = sales.stream().filter(s -> s.getProduct().getCategory() != null &&
                    s.getProduct().getCategory().name().equalsIgnoreCase(params.getCategory())).toList();
        }

        BigDecimal totalRevenue = sales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add);
        int totalQuantity = sales.stream().mapToInt(Sale::getQuantity).sum();
        int totalSales = sales.size();

        // Group by period (day, week, month)
        DateTimeFormatter formatter = "month".equalsIgnoreCase(params.getGroupBy()) ?
                DateTimeFormatter.ofPattern("yyyy-MM") :
                DateTimeFormatter.ofPattern("yyyy-MM-dd");

        Map<String, List<Sale>> groupedByPeriod = sales.stream()
                .collect(Collectors.groupingBy(s -> s.getSaleDate().format(formatter)));

        List<SalesReportItem> items = new ArrayList<>();
        groupedByPeriod.keySet().stream().sorted().forEach(period -> {
            List<Sale> periodSales = groupedByPeriod.get(period);
            BigDecimal periodRevenue = periodSales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add);
            int periodQty = periodSales.stream().mapToInt(Sale::getQuantity).sum();
            items.add(SalesReportItem.builder()
                    .period(period)
                    .totalSales(periodSales.size())
                    .totalRevenue(periodRevenue)
                    .totalQuantity(periodQty)
                    .build());
        });

        // Product Breakdown
        Map<Product, List<Sale>> productGrouped = sales.stream().collect(Collectors.groupingBy(Sale::getProduct));
        List<Map<String, Object>> productBreakdown = new ArrayList<>();
        productGrouped.forEach((product, pSales) -> {
            Map<String, Object> map = new HashMap<>();
            map.put("product_id", product.getId().toString());
            map.put("product_name", product.getName());
            map.put("category", product.getCategory() != null ? product.getCategory().name() : null);
            map.put("quantity_sold", pSales.stream().mapToInt(Sale::getQuantity).sum());
            map.put("revenue", pSales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add));
            productBreakdown.add(map);
        });

        // Category Breakdown
        Map<String, List<Sale>> categoryGrouped = sales.stream()
                .collect(Collectors.groupingBy(s -> s.getProduct().getCategory() != null ? s.getProduct().getCategory().name() : "OTHER"));
        List<Map<String, Object>> categoryBreakdown = new ArrayList<>();
        categoryGrouped.forEach((category, cSales) -> {
            Map<String, Object> map = new HashMap<>();
            map.put("category", category);
            map.put("quantity_sold", cSales.stream().mapToInt(Sale::getQuantity).sum());
            map.put("revenue", cSales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add));
            categoryBreakdown.add(map);
        });

        Map<String, Object> summary = new HashMap<>();
        summary.put("total_sales", totalSales);
        summary.put("total_revenue", totalRevenue);
        summary.put("total_quantity", totalQuantity);
        summary.put("average_order_value", totalSales > 0 ? totalRevenue.divide(BigDecimal.valueOf(totalSales), 2, RoundingMode.HALF_UP) : BigDecimal.ZERO);

        return SalesReportData.builder()
                .reportType("SALES")
                .startDate(params.getStartDate())
                .endDate(params.getEndDate())
                .summary(summary)
                .items(items)
                .productBreakdown(productBreakdown)
                .categoryBreakdown(categoryBreakdown)
                .build();
    }

    @Transactional(readOnly = true)
    public InventoryReportData generateInventoryReport(InventoryReportParams params) {
        List<Product> products = productRepository.findAll();

        if (params.getCategory() != null && !params.getCategory().isBlank()) {
            products = products.stream()
                    .filter(p -> p.getCategory() != null && p.getCategory().name().equalsIgnoreCase(params.getCategory()))
                    .toList();
        }

        if (Boolean.TRUE.equals(params.getLowStockOnly())) {
            products = products.stream()
                    .filter(p -> p.getStockQty() <= p.getReorderLevel())
                    .toList();
        }

        List<InventoryReportItem> items = new ArrayList<>();
        List<InventoryReportItem> lowStockItems = new ArrayList<>();

        BigDecimal totalStockValue = BigDecimal.ZERO;
        int totalItemsInStock = 0;
        int lowStockCount = 0;
        int outOfStockCount = 0;

        for (Product p : products) {
            BigDecimal price = BigDecimal.valueOf(p.getPrice());
            BigDecimal value = price.multiply(BigDecimal.valueOf(p.getStockQty()));
            totalStockValue = totalStockValue.add(value);
            totalItemsInStock += p.getStockQty();

            String status = p.getStockQty() == 0 ? "OUT_OF_STOCK" :
                    (p.getStockQty() <= p.getReorderLevel() ? "LOW" : "OK");

            if ("LOW".equals(status)) lowStockCount++;
            if ("OUT_OF_STOCK".equals(status)) outOfStockCount++;

            InventoryReportItem item = InventoryReportItem.builder()
                    .productId(p.getId())
                    .productName(p.getName())
                    .category(p.getCategory() != null ? p.getCategory().name() : "OTHER")
                    .currentStock(p.getStockQty())
                    .reorderLevel(p.getReorderLevel())
                    .stockValue(value)
                    .status(status)
                    .build();

            items.add(item);
            if (!"OK".equals(status)) {
                lowStockItems.add(item);
            }
        }

        Map<String, Object> summary = new HashMap<>();
        summary.put("total_products", products.size());
        summary.put("total_items_in_stock", totalItemsInStock);
        summary.put("total_stock_value", totalStockValue);
        summary.put("low_stock_products_count", lowStockCount);
        summary.put("out_of_stock_products_count", outOfStockCount);

        return InventoryReportData.builder()
                .reportType("INVENTORY")
                .generatedAt(LocalDateTime.now())
                .summary(summary)
                .items(items)
                .lowStockItems(lowStockItems)
                .build();
    }

    @Transactional(readOnly = true)
    public ProductPerformanceData generateProductPerformanceReport(ProductPerformanceParams params) {
        if (params.getEndDate().isBefore(params.getStartDate()) || params.getEndDate().isEqual(params.getStartDate())) {
            throw new BadRequestException("end_date must be after start_date");
        }

        List<Sale> sales = saleRepository.findBySaleDateBetweenOrderBySaleDateAsc(params.getStartDate(), params.getEndDate());

        if (params.getCategory() != null && !params.getCategory().isBlank()) {
            sales = sales.stream()
                    .filter(s -> s.getProduct().getCategory() != null && s.getProduct().getCategory().name().equalsIgnoreCase(params.getCategory()))
                    .toList();
        }

        Map<Product, List<Sale>> productGrouped = sales.stream().collect(Collectors.groupingBy(Sale::getProduct));

        List<ProductPerformanceItem> allItems = new ArrayList<>();
        for (Map.Entry<Product, List<Sale>> entry : productGrouped.entrySet()) {
            Product p = entry.getKey();
            List<Sale> pSales = entry.getValue();

            int totalQty = pSales.stream().mapToInt(Sale::getQuantity).sum();
            BigDecimal totalRev = pSales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add);
            int orderCount = pSales.size();
            BigDecimal avgQty = orderCount > 0 ?
                    BigDecimal.valueOf(totalQty).divide(BigDecimal.valueOf(orderCount), 2, RoundingMode.HALF_UP) : BigDecimal.ZERO;

            allItems.add(ProductPerformanceItem.builder()
                    .productId(p.getId())
                    .productName(p.getName())
                    .category(p.getCategory() != null ? p.getCategory().name() : "OTHER")
                    .totalQuantitySold(totalQty)
                    .totalRevenue(totalRev)
                    .numberOfOrders(orderCount)
                    .averageOrderQuantity(avgQty)
                    .build());
        }

        // Sort descending by total revenue
        allItems.sort(Comparator.comparing(ProductPerformanceItem::getTotalRevenue).reversed());

        int limit = Math.min(params.getTopN() != null ? params.getTopN() : 10, allItems.size());
        List<ProductPerformanceItem> topProducts = allItems.subList(0, limit);

        // Category breakdown
        Map<String, List<ProductPerformanceItem>> catGrouped = allItems.stream()
                .collect(Collectors.groupingBy(ProductPerformanceItem::getCategory));
        List<Map<String, Object>> categoryPerf = new ArrayList<>();
        catGrouped.forEach((cat, catItems) -> {
            Map<String, Object> map = new HashMap<>();
            map.put("category", cat);
            map.put("total_quantity", catItems.stream().mapToInt(ProductPerformanceItem::getTotalQuantitySold).sum());
            map.put("total_revenue", catItems.stream().map(ProductPerformanceItem::getTotalRevenue).reduce(BigDecimal.ZERO, BigDecimal::add));
            categoryPerf.add(map);
        });

        BigDecimal totalRevenue = allItems.stream().map(ProductPerformanceItem::getTotalRevenue).reduce(BigDecimal.ZERO, BigDecimal::add);
        int totalUnits = allItems.stream().mapToInt(ProductPerformanceItem::getTotalQuantitySold).sum();

        Map<String, Object> summary = new HashMap<>();
        summary.put("total_revenue", totalRevenue);
        summary.put("total_units_sold", totalUnits);
        summary.put("total_unique_products_sold", allItems.size());

        return ProductPerformanceData.builder()
                .reportType("PRODUCT_PERFORMANCE")
                .startDate(params.getStartDate())
                .endDate(params.getEndDate())
                .summary(summary)
                .topProducts(topProducts)
                .categoryPerformance(categoryPerf)
                .build();
    }

    @Transactional(readOnly = true)
    public LowStockReportData generateLowStockReport(LowStockReportParams params) {
        List<Product> products = productRepository.findAll();

        if (params.getCategory() != null && !params.getCategory().isBlank()) {
            products = products.stream()
                    .filter(p -> p.getCategory() != null && p.getCategory().name().equalsIgnoreCase(params.getCategory()))
                    .toList();
        }

        int threshold = params.getThresholdPercentage() != null ? params.getThresholdPercentage() : 20;

        List<LowStockItem> lowStockItems = new ArrayList<>();
        for (Product p : products) {
            if (p.getStockQty() <= p.getReorderLevel()) {
                BigDecimal pct = p.getReorderLevel() > 0 ?
                        BigDecimal.valueOf(p.getStockQty() * 100.0 / p.getReorderLevel()).setScale(2, RoundingMode.HALF_UP) : BigDecimal.ZERO;
                int recOrder = Math.max(0, (p.getReorderLevel() * 2) - p.getStockQty());

                lowStockItems.add(LowStockItem.builder()
                        .productId(p.getId())
                        .productName(p.getName())
                        .category(p.getCategory() != null ? p.getCategory().name() : "OTHER")
                        .currentStock(p.getStockQty())
                        .reorderLevel(p.getReorderLevel())
                        .stockPercentage(pct)
                        .recommendedOrderQuantity(recOrder)
                        .build());
            }
        }

        Map<String, Object> summary = new HashMap<>();
        summary.put("total_low_stock_products", lowStockItems.size());
        summary.put("threshold_percentage", threshold);

        return LowStockReportData.builder()
                .reportType("LOW_STOCK")
                .generatedAt(LocalDateTime.now())
                .thresholdPercentage(threshold)
                .summary(summary)
                .items(lowStockItems)
                .build();
    }

    public ReportResponse mapToResponse(Report report) {
        Map<String, Object> params = null;
        if (report.getParameters() != null && !report.getParameters().isBlank()) {
            try {
                params = objectMapper.readValue(report.getParameters(), new TypeReference<Map<String, Object>>() {});
            } catch (Exception e) {
                log.warn("Could not deserialize report parameters for id {}: {}", report.getReportId(), e.getMessage());
            }
        }

        return ReportResponse.builder()
                .reportId(report.getReportId())
                .reportName(report.getReportName())
                .reportType(report.getReportType())
                .parameters(params)
                .createdBy(report.getCreatedBy())
                .createdAt(report.getCreatedAt())
                .updatedAt(report.getUpdatedAt())
                .description(report.getDescription())
                .build();
    }
}
