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


class MovementType(enum.Enum):
    """Stock movement type enumeration for inventory tracking"""

    IN = "IN"
    OUT = "OUT"


class QuotationStatus(enum.Enum):
    """Quotation status enumeration for quotation management"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class OrderStatus(enum.Enum):
    """Order status enumeration for order management"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.Enum):
    """Payment status enumeration for tracking payment state"""

    UNPAID = "UNPAID"
    PAID = "PAID"


class ReportType(enum.Enum):
    """Report type enumeration for analytics and reporting"""

    SALES = "SALES"
    INVENTORY = "INVENTORY"
    PRODUCT_PERFORMANCE = "PRODUCT_PERFORMANCE"
    LOW_STOCK = "LOW_STOCK"
