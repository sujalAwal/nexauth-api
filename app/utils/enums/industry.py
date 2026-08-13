from enum import Enum

class Industry(str,Enum):
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    RETAIL = "Retail"
    OTHER = "Other"