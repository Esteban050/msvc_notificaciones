from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database.connection import get_db
from app.models.notification import (
    Notification,
    NotificationTemplate,
    UserNotificationPreference,
    NotificationStatus
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    UserNotificationPreferenceCreate,
    UserNotificationPreferenceUpdate,
    UserNotificationPreferenceResponse
)

router = APIRouter()


# ==================== Notification Endpoints ====================

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    user_id: UUID = None,
    status: NotificationStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all notifications with optional filters"""
    query = db.query(Notification)

    if user_id:
        query = query.filter(Notification.user_id == user_id)

    if status:
        query = query.filter(Notification.status == status)

    notifications = query.offset(skip).limit(limit).all()
    return notifications


@router.get("/notifications/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: UUID, db: Session = Depends(get_db)):
    """Get a specific notification by ID"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return notification


@router.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all notifications for a specific user"""
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    return notifications


# ==================== Template Endpoints ====================

@router.get("/templates", response_model=List[NotificationTemplateResponse])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all notification templates"""
    templates = db.query(NotificationTemplate).offset(skip).limit(limit).all()
    return templates


@router.get("/templates/{event_type}", response_model=List[NotificationTemplateResponse])
def get_template_by_event(event_type: str, db: Session = Depends(get_db)):
    """Get templates for a specific event type"""
    templates = db.query(NotificationTemplate).filter(
        NotificationTemplate.event_type == event_type
    ).all()

    if not templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No templates found for event type: {event_type}"
        )

    return templates


@router.post("/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template: NotificationTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification template"""
    # Check if template already exists for this event type and notification type
    existing = db.query(NotificationTemplate).filter(
        NotificationTemplate.event_type == template.event_type,
        NotificationTemplate.notification_type == template.notification_type
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template already exists for event type '{template.event_type}' "
                   f"and notification type '{template.notification_type}'"
        )

    db_template = NotificationTemplate(
        event_type=template.event_type,
        notification_type=template.notification_type,
        subject_template=template.subject_template,
        title_template=template.title_template,
        body_template=template.body_template,
        priority=template.priority,
        is_active=1 if template.is_active else 0
    )

    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    return db_template


@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
def update_template(
    template_id: UUID,
    template_update: NotificationTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing notification template"""
    db_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()

    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Update fields
    update_data = template_update.model_dump(exclude_unset=True)

    # Convert is_active to integer if present
    if 'is_active' in update_data:
        update_data['is_active'] = 1 if update_data['is_active'] else 0

    for field, value in update_data.items():
        setattr(db_template, field, value)

    db.commit()
    db.refresh(db_template)

    return db_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: UUID, db: Session = Depends(get_db)):
    """Delete a notification template"""
    db_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()

    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    db.delete(db_template)
    db.commit()

    return None


# ==================== User Preferences Endpoints ====================

@router.get("/preferences/{user_id}", response_model=UserNotificationPreferenceResponse)
def get_user_preferences(user_id: UUID, db: Session = Depends(get_db)):
    """Get notification preferences for a user"""
    preferences = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == user_id
    ).first()

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )

    return preferences


@router.post("/preferences", response_model=UserNotificationPreferenceResponse, status_code=status.HTTP_201_CREATED)
def create_user_preferences(
    preferences: UserNotificationPreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create notification preferences for a user"""
    # Check if preferences already exist
    existing = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == preferences.user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preferences already exist for this user"
        )

    db_preferences = UserNotificationPreference(
        user_id=preferences.user_id,
        fcm_token=preferences.fcm_token,
        email_enabled=1 if preferences.email_enabled else 0,
        push_enabled=1 if preferences.push_enabled else 0,
        event_preferences=preferences.event_preferences or {}
    )

    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)

    return db_preferences


@router.put("/preferences/{user_id}", response_model=UserNotificationPreferenceResponse)
def update_user_preferences(
    user_id: UUID,
    preferences_update: UserNotificationPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """Update notification preferences for a user"""
    db_preferences = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == user_id
    ).first()

    if not db_preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )

    # Update fields
    update_data = preferences_update.model_dump(exclude_unset=True)

    # Convert boolean fields to integers
    if 'email_enabled' in update_data:
        update_data['email_enabled'] = 1 if update_data['email_enabled'] else 0
    if 'push_enabled' in update_data:
        update_data['push_enabled'] = 1 if update_data['push_enabled'] else 0

    for field, value in update_data.items():
        setattr(db_preferences, field, value)

    db.commit()
    db.refresh(db_preferences)

    return db_preferences


@router.put("/preferences/{user_id}/fcm-token")
def update_fcm_token(
    user_id: UUID,
    fcm_token: str,
    db: Session = Depends(get_db)
):
    """Update FCM token for a user"""
    db_preferences = db.query(UserNotificationPreference).filter(
        UserNotificationPreference.user_id == user_id
    ).first()

    if not db_preferences:
        # Create preferences if they don't exist
        db_preferences = UserNotificationPreference(
            user_id=user_id,
            fcm_token=fcm_token,
            email_enabled=1,
            push_enabled=1
        )
        db.add(db_preferences)
    else:
        db_preferences.fcm_token = fcm_token

    db.commit()
    db.refresh(db_preferences)

    return {"message": "FCM token updated successfully", "user_id": str(user_id)}


# ==================== Health Check ====================

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notifications"}
