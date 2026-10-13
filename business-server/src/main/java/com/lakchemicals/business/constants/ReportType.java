package com.lakchemicals.business.constants;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum ReportType {
    SALES("SALES"),
    INVENTORY("INVENTORY"),
    PRODUCT_PERFORMANCE("PRODUCT_PERFORMANCE"),
    LOW_STOCK("LOW_STOCK");

    private final String value;

    ReportType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static ReportType fromValue(String value) {
        if (value == null) return null;
        for (ReportType type : values()) {
            if (type.value.equalsIgnoreCase(value) || type.name().equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown report type: " + value);
    }
}
