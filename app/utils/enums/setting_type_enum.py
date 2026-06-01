"""Setting Type Enum - HTML input types for settings"""
from enum import Enum


class SettingTypeEnum(str, Enum):
    """
    HTML input types that settings can accept.
    Used to validate and render UI controls.
    """
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PASSWORD = "password"
    TEXTAREA = "textarea"
    COLOR = "color"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    MULTISELECT = "multiselect"
    FILE = "file"
    URL = "url"
    PHONE = "phone"
    SWITCH = "switch"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid setting type"""
        return value in [item.value for item in cls]
