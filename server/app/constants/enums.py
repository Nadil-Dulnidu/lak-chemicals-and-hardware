import enum


class ProductCategory(enum.Enum):
    """Product category enumeration for hardware and chemical products"""

    CHEMICALS = "chemicals"
    HARDWARE = "hardware"
    TOOLS = "tools"
    PAINTS = "paints"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    BUILDING_MATERIALS = "building_materials"
    SAFETY_EQUIPMENT = "safety_equipment"
    OTHER = "other"
