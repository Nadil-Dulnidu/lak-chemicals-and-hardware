package com.lakchemicals.business.dto.product;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.ProductCategory;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductCreateRequest {

    @NotBlank(message = "Product name is required")
    private String name;

    private String description;

    private String brand;

    private ProductCategory category;

    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.01", message = "Price must be greater than 0")
    private Double price;

    @NotNull(message = "Stock quantity is required")
    @Min(value = 0, message = "Stock quantity cannot be negative")
    @JsonProperty("stock_qty")
    private Integer stockQty;

    @Min(value = 0, message = "Reorder level cannot be negative")
    @JsonProperty("reorder_level")
    @Builder.Default
    private Integer reorderLevel = 10;

    @JsonProperty("image_url")
    private String imageUrl;
}
