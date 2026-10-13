package com.lakchemicals.business.dto.product;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.ProductCategory;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductUpdateRequest {

    private String name;
    private String description;
    private String brand;
    private ProductCategory category;

    @DecimalMin(value = "0.01", message = "Price must be greater than 0")
    private Double price;

    @Min(value = 0, message = "Stock quantity cannot be negative")
    @JsonProperty("stock_qty")
    private Integer stockQty;

    @Min(value = 0, message = "Reorder level cannot be negative")
    @JsonProperty("reorder_level")
    private Integer reorderLevel;

    @JsonProperty("image_url")
    private String imageUrl;

    @JsonProperty("is_active")
    private Boolean isActive;
}
