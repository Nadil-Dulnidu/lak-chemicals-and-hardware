package com.lakchemicals.business.repository;

import com.lakchemicals.business.entity.Sale;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface SaleRepository extends JpaRepository<Sale, Integer> {

    List<Sale> findByOrder_OrderId(Integer orderId);

    List<Sale> findByProduct_Id(UUID productId);

    List<Sale> findBySaleDateBetweenOrderBySaleDateAsc(LocalDateTime start, LocalDateTime end);

    Page<Sale> findBySaleDateBetween(LocalDateTime start, LocalDateTime end, Pageable pageable);

    @Query("SELECT s FROM Sale s WHERE s.saleDate BETWEEN :start AND :end AND (:productId IS NULL OR s.product.id = :productId)")
    List<Sale> findSalesForReport(
            @Param("start") LocalDateTime start,
            @Param("end") LocalDateTime end,
            @Param("productId") UUID productId
    );
}
