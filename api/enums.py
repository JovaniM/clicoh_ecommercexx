from enum import Enum


class Errors(Enum):
    DUPLICATED_PRODUCT_ERROR = "A product is duplicated on the same Order."
    INTEGRITY_PRODUCT_ERROR = "Problems saving the Product due integrity."
    MISSING_ORDER_ERROR = "No Order was found for the given id."
    GREATER_EQUAL_ZERO_ERROR = "Value must be greater or equal than zero."
    GREATER_ZERO_ERROR = "Value must be greater or equal than zero."
    NOT_EDITABLE_ORDER_ERROR = "Order cant be modified at this point."
    PRODUCT_NOT_AVAILABLE_ERROR = "The requested product is not available."
    PROTECTED_PRODUCT_ERROR = "You can't delete this Product because it have some references."
    STOCK_AVAILABILITY_ERROR = "This order cant be supplied due stock availability."
    ORDER_ALREADY_CANCELLED = "Already cancelled."
