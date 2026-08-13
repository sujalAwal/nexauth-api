from enum import Enum

class PlanTier(str,Enum):
    FREE = "Free"
    BASIC = "Basic"
    PRO = "Pro"
    ENTERPRISE = "Enterprise"