package com.lakchemicals.business.constants;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum ProductCategory {
    CHEMICALS("chemicals"),
    HARDWARE("hardware"),
    TOOLS("tools"),
    PAINTS("paints"),
    ELECTRICAL("electrical"),
    PLUMBING("plumbing"),
    BUILDING_MATERIALS("building_materials"),
    SAFETY_EQUIPMENT("safety_equipment"),
    OTHER("other");

    private final String value;

    ProductCategory(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static ProductCategory fromValue(String value) {
        if (value == null) return null;
        for (ProductCategory category : values()) {
            if (category.value.equalsIgnoreCase(value) || category.name().equalsIgnoreCase(value)) {
                return category;
            }
        }
        throw new IllegalArgumentException("Unknown product category: " + value);
    }
}
