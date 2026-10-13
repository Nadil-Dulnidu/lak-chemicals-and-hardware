package com.lakchemicals.business.repository;

import com.lakchemicals.business.constants.MovementType;
import com.lakchemicals.business.entity.StockMovement;
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
public interface StockMovementRepository extends JpaRepository<StockMovement, Integer> {

    List<StockMovement> findByProduct_IdOrderByMovementDateDesc(UUID productId);

    Page<StockMovement> findByProduct_Id(UUID productId, Pageable pageable);

    List<StockMovement> findByMovementDateBetweenOrderByMovementDateDesc(LocalDateTime start, LocalDateTime end);

    List<StockMovement> findByMovementTypeOrderByMovementDateDesc(MovementType movementType);

    @Query("SELECT sm FROM StockMovement sm WHERE sm.product.id = :productId AND sm.movementDate BETWEEN :startDate AND :endDate ORDER BY sm.movementDate DESC")
    List<StockMovement> findByProductAndDateRange(
            @Param("productId") UUID productId,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate
    );
}
