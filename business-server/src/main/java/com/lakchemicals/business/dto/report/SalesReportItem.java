package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SalesReportItem {

    private String period;

    @JsonProperty("total_sales")
    private Integer totalSales;

    @JsonProperty("total_revenue")
    private BigDecimal totalRevenue;

    @JsonProperty("total_quantity")
    private Integer totalQuantity;
}
