package com.lakchemicals.business.constants;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum MovementType {
    IN("IN"),
    OUT("OUT");

    private final String value;

    MovementType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static MovementType fromValue(String value) {
        if (value == null) return null;
        for (MovementType type : values()) {
            if (type.value.equalsIgnoreCase(value) || type.name().equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown movement type: " + value);
    }
}
