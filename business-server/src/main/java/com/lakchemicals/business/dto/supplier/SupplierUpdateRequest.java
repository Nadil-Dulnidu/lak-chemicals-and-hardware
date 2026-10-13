package com.lakchemicals.business.dto.supplier;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SupplierUpdateRequest {

    private String name;

    @JsonProperty("contact_person")
    private String contactPerson;

    @JsonProperty("contact_number")
    private String contactNumber;

    @Email(message = "Valid email address is required")
    private String email;

    private String address;

    @JsonProperty("is_active")
    private Boolean isActive;
}
