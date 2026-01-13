"""
Industry-grade schema definitions for comparison
Purpose: Show typical syntax highlighting patterns for schema definitions
"""

# ============================================================================
# 1. SQLAlchemy ORM (Python - Most Popular)
# ============================================================================
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model with storage management"""
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)  # bcrypt hashed
    
    # Profile
    name = Column(String(100), nullable=False)
    company = Column(String(100), default='')
    avatar_url = Column(String(512))
    avatar_updated_at = Column(DateTime)
    cover_url = Column(String(512))
    cover_updated_at = Column(DateTime)
    phone = Column(String(20))
    
    # Status
    status = Column(String(20), default='active')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Storage management (Phase 1.5)
    storage_quota = Column(Integer, default=1073741824)  # 1GB
    storage_used = Column(Integer, default=0)
    storage_backend = Column(String(20), default='local')
    storage_path = Column(String(255))


# ============================================================================
# 2. Pydantic (Python - Modern API Validation)
# ============================================================================
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    pending = "pending"

class StorageBackend(str, Enum):
    local = "local"
    lfs = "lfs"
    s3 = "s3"
    azure = "azure"

class UserSchema(BaseModel):
    """User schema with validation rules"""
    
    # Primary key
    id: Optional[int] = Field(None, description="Auto-generated ID")
    
    # Authentication
    email: EmailStr = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    
    # Profile
    name: str = Field(..., min_length=2, max_length=100)
    company: Optional[str] = Field("", max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=512)
    avatar_updated_at: Optional[datetime] = None
    cover_url: Optional[str] = Field(None, max_length=512)
    cover_updated_at: Optional[datetime] = None
    phone: Optional[str] = Field(None, regex=r"^\+?[\d\s\-\(\)]+$")
    
    # Status
    status: UserStatus = UserStatus.active
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Storage management
    storage_quota: int = Field(1073741824, ge=0)
    storage_used: int = Field(0, ge=0)
    storage_backend: StorageBackend = StorageBackend.local
    storage_path: Optional[str] = Field(None, max_length=255)
    
    class Config:
        orm_mode = True
        use_enum_values = True


# ============================================================================
# 3. Django ORM (Python - Web Framework)
# ============================================================================
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

class DjangoUser(models.Model):
    """User model in Django ORM"""
    
    # Authentication
    email = models.EmailField(
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(5)]
    )
    password = models.CharField(max_length=255)  # Hashed
    
    # Profile
    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    company = models.CharField(max_length=100, blank=True, default='')
    avatar_url = models.CharField(max_length=512, blank=True, null=True)
    avatar_updated_at = models.DateTimeField(null=True, blank=True)
    cover_url = models.CharField(max_length=512, blank=True, null=True)
    cover_updated_at = models.DateTimeField(null=True, blank=True)
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Invalid phone number format'
            )
        ]
    )
    
    # Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Storage management
    storage_quota = models.BigIntegerField(default=1073741824)
    storage_used = models.BigIntegerField(default=0)
    storage_backend = models.CharField(max_length=20, default='local')
    storage_path = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
