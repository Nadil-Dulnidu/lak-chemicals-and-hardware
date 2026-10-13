package com.lakchemicals.business.repository;

import com.lakchemicals.business.constants.ReportType;
import com.lakchemicals.business.entity.Report;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ReportRepository extends JpaRepository<Report, Integer> {

    List<Report> findByReportTypeOrderByCreatedAtDesc(ReportType reportType);

    List<Report> findByCreatedByOrderByCreatedAtDesc(String createdBy);

    Page<Report> findByReportType(ReportType reportType, Pageable pageable);
}
