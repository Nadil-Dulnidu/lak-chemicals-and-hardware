package com.lakchemicals.business.repository;

import com.lakchemicals.business.entity.SupplierProduct;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface SupplierProductRepository extends JpaRepository<SupplierProduct, UUID> {

    Optional<SupplierProduct> findBySupplierIdAndProductId(UUID supplierId, UUID productId);

    List<SupplierProduct> findBySupplierId(UUID supplierId);

    List<SupplierProduct> findByProductId(UUID productId);

    void deleteBySupplierIdAndProductId(UUID supplierId, UUID productId);
}
