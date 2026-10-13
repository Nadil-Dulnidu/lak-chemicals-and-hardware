package com.lakchemicals.business.dto.supplier;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SupplierCreateRequest {

    @NotBlank(message = "Supplier name is required")
    private String name;

    @JsonProperty("contact_person")
    private String contactPerson;

    @NotBlank(message = "Contact number is required")
    @JsonProperty("contact_number")
    private String contactNumber;

    @NotBlank(message = "Email is required")
    @Email(message = "Valid email address is required")
    private String email;

    private String address;
}
