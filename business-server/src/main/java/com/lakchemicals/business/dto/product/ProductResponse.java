package com.lakchemicals.business.dto.product;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.ProductCategory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductResponse {

    private UUID id;
    private String name;
    private String description;
    private String brand;
    private ProductCategory category;
    private Double price;

    @JsonProperty("stock_qty")
    private Integer stockQty;

    @JsonProperty("reorder_level")
    private Integer reorderLevel;

    @JsonProperty("image_url")
    private String imageUrl;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;

    @JsonProperty("is_active")
    private Boolean isActive;
}
