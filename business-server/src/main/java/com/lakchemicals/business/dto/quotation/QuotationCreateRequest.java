package com.lakchemicals.business.dto.quotation;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QuotationCreateRequest {

    @NotEmpty(message = "At least one item is required")
    @Valid
    private List<QuotationItemRequest> items;

    private String notes;
}
