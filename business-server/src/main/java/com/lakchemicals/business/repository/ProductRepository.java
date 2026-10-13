package com.lakchemicals.business.repository;

import com.lakchemicals.business.constants.ProductCategory;
import com.lakchemicals.business.entity.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ProductRepository extends JpaRepository<Product, UUID>, JpaSpecificationExecutor<Product> {

    Optional<Product> findByNameIgnoreCase(String name);

    Page<Product> findByIsActiveTrue(Pageable pageable);

    @Query("SELECT p FROM Product p WHERE p.isActive = true AND p.stockQty <= p.reorderLevel ORDER BY p.stockQty ASC")
    List<Product> findLowStockProducts();

    @Query("SELECT p FROM Product p WHERE p.isActive = true AND p.stockQty <= :threshold ORDER BY p.stockQty ASC")
    List<Product> findLowStockProductsWithThreshold(@Param("threshold") int threshold);

    List<Product> findByCategoryAndIsActiveTrue(ProductCategory category);

    long countByCategory(ProductCategory category);

    long countByIsActiveTrue();
}
