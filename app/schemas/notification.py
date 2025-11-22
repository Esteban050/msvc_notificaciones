from pydantic import BaseModel, EmailStr, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.notification import NotificationType, NotificationStatus, NotificationPriority


# Notification Schemas
class NotificationBase(BaseModel):
    user_id: UUID4
    notification_type: NotificationType
    event_type: str
    priority: NotificationPriority = NotificationPriority.NORMAL


class NotificationCreate(NotificationBase):
    recipient_email: Optional[EmailStr] = None
    recipient_fcm_token: Optional[str] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    body: str
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    id: UUID4
    status: NotificationStatus
    recipient_email: Optional[str] = None
    recipient_fcm_token: Optional[str] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    body: str
    data: Optional[Dict[str, Any]] = None
    retry_count: int
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Message Queue Event Schema
class NotificationEvent(BaseModel):
    """Schema for events received from RabbitMQ"""
    user_id: UUID4
    user_email: Optional[EmailStr] = None
    user_phone: Optional[str] = None
    fcm_token: Optional[str] = None
    event_type: str
    data: Dict[str, Any]
    priority: NotificationPriority = NotificationPriority.NORMAL

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_email": "user@example.com",
                "fcm_token": "firebase-token-here",
                "event_type": "RESERVATION_CONFIRMED",
                "data": {
                    "reservation_id": "123e4567-e89b-12d3-a456-426614174001",
                    "parking_name": "Parking Centro",
                    "start_time": "2025-11-10T08:00:00Z",
                    "end_time": "2025-11-10T18:00:00Z",
                    "price": 15.00
                },
                "priority": "normal"
            }
        }


# Template Schemas
class NotificationTemplateBase(BaseModel):
    event_type: str
    notification_type: NotificationType
    subject_template: Optional[str] = None
    title_template: Optional[str] = None
    body_template: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    subject_template: Optional[str] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None
    priority: Optional[NotificationPriority] = None
    is_active: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Preferences Schemas
class UserNotificationPreferenceBase(BaseModel):
    user_id: UUID4
    fcm_token: Optional[str] = None
    email_enabled: bool = True
    push_enabled: bool = True
    event_preferences: Optional[Dict[str, Dict[str, bool]]] = None


class UserNotificationPreferenceCreate(UserNotificationPreferenceBase):
    pass


class UserNotificationPreferenceUpdate(BaseModel):
    fcm_token: Optional[str] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    event_preferences: Optional[Dict[str, Dict[str, bool]]] = None


class UserNotificationPreferenceResponse(UserNotificationPreferenceBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
