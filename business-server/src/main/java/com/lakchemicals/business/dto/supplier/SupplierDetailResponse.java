package com.lakchemicals.business.dto.supplier;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SupplierDetailResponse {

    private UUID id;
    private String name;

    @JsonProperty("contact_person")
    private String contactPerson;

    @JsonProperty("contact_number")
    private String contactNumber;

    private String email;
    private String address;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;

    @JsonProperty("last_purchase_date")
    private LocalDateTime lastPurchaseDate;

    @JsonProperty("is_active")
    private Boolean isActive;

    @Builder.Default
    private List<ProductSupplierInfo> products = new ArrayList<>();
}
