package com.lakchemicals.business.repository;

import com.lakchemicals.business.entity.QuotationItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface QuotationItemRepository extends JpaRepository<QuotationItem, Integer> {

    List<QuotationItem> findByQuotation_QuotationId(Integer quotationId);

    List<QuotationItem> findByProduct_Id(UUID productId);
}
