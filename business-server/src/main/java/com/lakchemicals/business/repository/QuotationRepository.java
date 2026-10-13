package com.lakchemicals.business.repository;

import com.lakchemicals.business.constants.QuotationStatus;
import com.lakchemicals.business.entity.Quotation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QuotationRepository extends JpaRepository<Quotation, Integer>, JpaSpecificationExecutor<Quotation> {

    List<Quotation> findByUserIdOrderByCreatedAtDesc(String userId);

    Page<Quotation> findByUserId(String userId, Pageable pageable);

    List<Quotation> findByStatusOrderByCreatedAtDesc(QuotationStatus status);
}
