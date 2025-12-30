"""
Settings model for application configuration.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
import enum

from app.database import Base


class SettingType(str, enum.Enum):
    """Type of setting value."""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"


class Settings(Base):
    """Model for application settings stored in database."""
    
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, nullable=True)
    setting_type = Column(Enum(SettingType), default=SettingType.STRING, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Settings(key='{self.setting_key}', value='{self.setting_value}')>"
    
    def to_dict(self):
        """Convert setting to dictionary."""
        return {
            "key": self.setting_key,
            "value": self.get_typed_value(),
            "type": self.setting_type.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_typed_value(self):
        """Get setting value with proper type conversion."""
        if self.setting_value is None:
            return None
        
        if self.setting_type == SettingType.INT:
            return int(self.setting_value)
        elif self.setting_type == SettingType.FLOAT:
            return float(self.setting_value)
        elif self.setting_type == SettingType.BOOL:
            return self.setting_value.lower() in ('true', '1', 'yes')
        elif self.setting_type == SettingType.JSON:
            import json
            return json.loads(self.setting_value)
        else:
            return self.setting_value
    
    def set_typed_value(self, value):
        """Set setting value with proper type conversion."""
        if value is None:
            self.setting_value = None
            return
        
        if self.setting_type == SettingType.JSON:
            import json
            self.setting_value = json.dumps(value)
        elif self.setting_type == SettingType.BOOL:
            self.setting_value = 'true' if value else 'false'
        else:
            self.setting_value = str(value)
