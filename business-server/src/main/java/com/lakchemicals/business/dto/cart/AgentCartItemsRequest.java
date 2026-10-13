package com.lakchemicals.business.dto.cart;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
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
public class AgentCartItemsRequest {

    @NotBlank(message = "User ID is required")
    @JsonProperty("user_id")
    private String userId;

    @NotEmpty(message = "Items list cannot be empty")
    @Valid
    private List<AddToCartRequest> items;
}
