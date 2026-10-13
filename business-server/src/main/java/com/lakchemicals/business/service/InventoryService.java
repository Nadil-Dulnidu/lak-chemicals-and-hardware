package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.MovementType;
import com.lakchemicals.business.dto.inventory.*;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.entity.StockMovement;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.repository.StockMovementRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class InventoryService {

    private final StockMovementRepository stockMovementRepository;
    private final ProductRepository productRepository;

    @Transactional
    public StockMovementResponse recordStockMovement(StockMovementCreateRequest request, String userId) {
        log.info("Recording stock movement: {} {} for product: {}", request.getMovementType(), request.getQuantity(), request.getProductId());

        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + request.getProductId()));

        if (request.getMovementType() == MovementType.OUT) {
            if (product.getStockQty() < request.getQuantity()) {
                throw new BadRequestException("Insufficient stock. Available: " + product.getStockQty() + ", Requested: " + request.getQuantity());
            }
            product.setStockQty(product.getStockQty() - request.getQuantity());
        } else {
            product.setStockQty(product.getStockQty() + request.getQuantity());
        }

        productRepository.save(product);

        StockMovement movement = StockMovement.builder()
                .product(product)
                .movementType(request.getMovementType())
                .quantity(request.getQuantity())
                .reference(request.getReference())
                .movementDate(request.getMovementDate() != null ? request.getMovementDate() : LocalDateTime.now())
                .createdBy(userId != null ? userId : "system")
                .build();

        StockMovement saved = stockMovementRepository.save(movement);
        return mapToResponse(saved);
    }

    @Transactional
    public StockMovementResponse adjustStock(StockAdjustmentRequest request, String userId) {
        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + request.getProductId()));

        int diff = request.getTargetQuantity() - product.getStockQty();
        if (diff == 0) {
            throw new BadRequestException("Target quantity is already equal to current stock (" + product.getStockQty() + ")");
        }

        MovementType movementType = diff > 0 ? MovementType.IN : MovementType.OUT;
        int qty = Math.abs(diff);

        product.setStockQty(request.getTargetQuantity());
        productRepository.save(product);

        StockMovement movement = StockMovement.builder()
                .product(product)
                .movementType(movementType)
                .quantity(qty)
                .reference(request.getReference() != null ? request.getReference() : "Stock Adjustment")
                .movementDate(LocalDateTime.now())
                .createdBy(userId != null ? userId : "system")
                .build();

        return mapToResponse(stockMovementRepository.save(movement));
    }

    @Transactional
    public List<StockMovementResponse> recordBulkMovements(BulkStockMovementRequest request, String userId) {
        List<StockMovementResponse> results = new ArrayList<>();
        for (StockMovementCreateRequest item : request.getMovements()) {
            results.add(recordStockMovement(item, userId));
        }
        return results;
    }

    @Transactional(readOnly = true)
    public StockMovementListResponse getMovements(
            UUID productId,
            MovementType movementType,
            LocalDateTime startDate,
            LocalDateTime endDate,
            int skip,
            int limit
    ) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "movementDate"));

        Page<StockMovement> movementPage;
        if (productId != null) {
            movementPage = stockMovementRepository.findByProduct_Id(productId, pageable);
        } else {
            movementPage = stockMovementRepository.findAll(pageable);
        }

        List<StockMovementResponse> dtos = movementPage.getContent().stream()
                .map(this::mapToResponse)
                .toList();

        return StockMovementListResponse.builder()
                .movements(dtos)
                .total(movementPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(movementPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public InventoryLevelResponse getInventoryLevel(UUID productId) {
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + productId));

        List<StockMovement> movements = stockMovementRepository.findByProduct_IdOrderByMovementDateDesc(productId);

        int totalIn = movements.stream().filter(m -> m.getMovementType() == MovementType.IN).mapToInt(StockMovement::getQuantity).sum();
        int totalOut = movements.stream().filter(m -> m.getMovementType() == MovementType.OUT).mapToInt(StockMovement::getQuantity).sum();
        LocalDateTime lastDate = movements.isEmpty() ? null : movements.get(0).getMovementDate();

        return InventoryLevelResponse.builder()
                .productId(product.getId())
                .productName(product.getName())
                .currentStock(product.getStockQty())
                .totalIn(totalIn)
                .totalOut(totalOut)
                .lastMovementDate(lastDate)
                .build();
    }

    @Transactional(readOnly = true)
    public List<ReorderAlertResponse> getReorderAlerts() {
        List<Product> lowStock = productRepository.findLowStockProducts();

        return lowStock.stream().map(p -> {
            int needed = Math.max(0, p.getReorderLevel() - p.getStockQty());
            String priority = p.getStockQty() == 0 ? "critical" :
                    (p.getStockQty() <= p.getReorderLevel() / 2 ? "high" : "medium");

            return ReorderAlertResponse.builder()
                    .productId(p.getId())
                    .productName(p.getName())
                    .currentStock(p.getStockQty())
                    .reorderThreshold(p.getReorderLevel())
                    .quantityNeeded(needed)
                    .priority(priority)
                    .build();
        }).toList();
    }

    @Transactional(readOnly = true)
    public StockSummaryResponse getStockSummary() {
        List<Product> allProducts = productRepository.findAll();
        long totalProducts = allProducts.size();
        double totalStockValue = allProducts.stream().mapToDouble(p -> p.getPrice() * p.getStockQty()).sum();
        long lowStockCount = allProducts.stream().filter(p -> p.getStockQty() <= p.getReorderLevel() && p.getStockQty() > 0).count();
        long outOfStockCount = allProducts.stream().filter(p -> p.getStockQty() == 0).count();

        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();
        LocalDateTime endOfDay = startOfDay.plusDays(1);
        List<StockMovement> todayMovements = stockMovementRepository.findByMovementDateBetweenOrderByMovementDateDesc(startOfDay, endOfDay);

        long todayTotal = todayMovements.size();
        long todayIn = todayMovements.stream().filter(m -> m.getMovementType() == MovementType.IN).mapToLong(StockMovement::getQuantity).sum();
        long todayOut = todayMovements.stream().filter(m -> m.getMovementType() == MovementType.OUT).mapToLong(StockMovement::getQuantity).sum();

        return StockSummaryResponse.builder()
                .totalProducts(totalProducts)
                .totalStockValue(totalStockValue)
                .lowStockCount(lowStockCount)
                .outOfStockCount(outOfStockCount)
                .totalMovementsToday(todayTotal)
                .totalInToday(todayIn)
                .totalOutToday(todayOut)
                .build();
    }

    public StockMovementResponse mapToResponse(StockMovement sm) {
        return StockMovementResponse.builder()
                .movementId(sm.getMovementId())
                .productId(sm.getProduct().getId())
                .productName(sm.getProduct().getName())
                .movementType(sm.getMovementType().name())
                .quantity(sm.getQuantity())
                .reference(sm.getReference())
                .movementDate(sm.getMovementDate())
                .createdBy(sm.getCreatedBy())
                .build();
    }
}
