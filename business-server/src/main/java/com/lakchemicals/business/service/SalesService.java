package com.lakchemicals.business.service;

import com.lakchemicals.business.dto.order.SaleResponse;
import com.lakchemicals.business.dto.order.SalesListResponse;
import com.lakchemicals.business.dto.order.SalesSummaryResponse;
import com.lakchemicals.business.entity.Sale;
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
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class SalesService {

    private final SaleRepository saleRepository;

    @Transactional(readOnly = true)
    public List<SaleResponse> getSalesByOrder(Integer orderId) {
        return saleRepository.findByOrder_OrderId(orderId).stream().map(this::mapToResponse).toList();
    }

    @Transactional(readOnly = true)
    public SalesListResponse getAllSales(int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "saleDate"));
        Page<Sale> salesPage = saleRepository.findAll(pageable);

        return SalesListResponse.builder()
                .sales(salesPage.getContent().stream().map(this::mapToResponse).toList())
                .total(salesPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(salesPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public SalesListResponse filterSales(UUID productId, LocalDateTime start, LocalDateTime end, int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "saleDate"));

        Page<Sale> salesPage = (start != null && end != null) ?
                saleRepository.findBySaleDateBetween(start, end, pageable) :
                saleRepository.findAll(pageable);

        List<SaleResponse> dtos = salesPage.getContent().stream()
                .filter(s -> productId == null || s.getProduct().getId().equals(productId))
                .map(this::mapToResponse)
                .toList();

        return SalesListResponse.builder()
                .sales(dtos)
                .total(salesPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(salesPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public SalesSummaryResponse getSalesSummary(LocalDateTime start, LocalDateTime end) {
        LocalDateTime s = start != null ? start : LocalDateTime.now().minusDays(30);
        LocalDateTime e = end != null ? end : LocalDateTime.now();

        List<Sale> sales = saleRepository.findBySaleDateBetweenOrderBySaleDateAsc(s, e);
        BigDecimal totalRevenue = sales.stream().map(Sale::getRevenue).reduce(BigDecimal.ZERO, BigDecimal::add);

        return SalesSummaryResponse.builder()
                .totalSales((long) sales.size())
                .totalRevenue(totalRevenue)
                .startDate(start)
                .endDate(end)
                .build();
    }

    public SaleResponse mapToResponse(Sale sale) {
        return SaleResponse.builder()
                .saleId(sale.getSaleId())
                .orderId(sale.getOrder().getOrderId())
                .productId(sale.getProduct().getId())
                .productName(sale.getProduct().getName())
                .quantity(sale.getQuantity())
                .revenue(sale.getRevenue())
                .saleDate(sale.getSaleDate())
                .build();
    }
}
