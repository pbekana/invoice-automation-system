"""
Tests for notification service.
"""

import pytest
from services.notification_service import NotificationService, EmailTemplate, NotificationType
from datetime import datetime


@pytest.fixture
def notification_service(mongo_db):
    """Create notification service instance."""
    return NotificationService(mongo_db)


@pytest.fixture
def sample_invoice():
    """Sample invoice for testing."""
    return {
        '_id': 'test_invoice_123',
        'invoice_number': 'INV-001',
        'company': 'Test Vendor Inc.',
        'total': 1250.50,
        'category': 'Software',
        'date': '2026-07-01',
        'status': 'pending_approval'
    }


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return {
        '_id': 'user_123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'roles': ['submitter']
    }


@pytest.fixture
def sample_approver():
    """Sample approver for testing."""
    return {
        '_id': 'approver_123',
        'name': 'Jane Smith',
        'email': 'jane@example.com',
        'roles': ['approver']
    }


class TestEmailTemplates:
    """Test email template generation."""
    
    def test_invoice_submitted_template(self, sample_invoice, sample_user):
        """Test invoice submitted email template."""
        template = EmailTemplate.invoice_submitted(sample_invoice, sample_user)
        
        assert 'subject' in template
        assert 'body' in template
        assert 'INV-001' in template['subject']
        assert '$1250.50' in template['subject']
        assert 'Test Vendor Inc.' in template['body']
        assert 'John Doe' in template['body']
    
    def test_invoice_approved_template(self, sample_invoice, sample_approver):
        """Test invoice approved email template."""
        template = EmailTemplate.invoice_approved(sample_invoice, sample_approver)
        
        assert 'Approved' in template['subject']
        assert 'Jane Smith' in template['body']
        assert 'INV-001' in template['body']
    
    def test_invoice_rejected_template(self, sample_invoice, sample_approver):
        """Test invoice rejected email template."""
        comments = "Missing receipt"
        template = EmailTemplate.invoice_rejected(sample_invoice, sample_approver, comments)
        
        assert 'Rejected' in template['subject']
        assert 'Missing receipt' in template['body']
        assert 'Jane Smith' in template['body']
    
    def test_approval_required_template(self, sample_invoice, sample_approver):
        """Test approval required email template."""
        template = EmailTemplate.approval_required(sample_invoice, sample_approver)
        
        assert 'Action Required' in template['subject']
        assert '$1250.50' in template['subject']
        assert 'Jane Smith' in template['body']


class TestNotificationService:
    """Test notification service."""
    
    def test_send_email_without_smtp(self, notification_service, sample_user):
        """Test email sending without SMTP config (logs only)."""
        result = notification_service.send_email(
            to_email=sample_user['email'],
            subject="Test Subject",
            body="Test Body"
        )
        
        assert result is True  # Should succeed with logging
    
    def test_log_notification(self, notification_service, sample_invoice, sample_user):
        """Test notification logging to database."""
        notification_service._log_notification(
            notification_type=NotificationType.INVOICE_SUBMITTED,
            recipient_id=sample_user['_id'],
            invoice_id=sample_invoice['_id'],
            details={'test': 'data'}
        )
        
        # Check if logged
        notifications = list(notification_service.notifications.find({
            'recipient_id': sample_user['_id']
        }))
        
        assert len(notifications) > 0
        assert notifications[0]['type'] == NotificationType.INVOICE_SUBMITTED
    
    def test_get_user_notifications(self, notification_service, sample_user):
        """Test retrieving user notifications."""
        # Log some notifications
        for i in range(3):
            notification_service._log_notification(
                notification_type=NotificationType.INVOICE_SUBMITTED,
                recipient_id=sample_user['_id'],
                invoice_id=f'invoice_{i}',
                details={'index': i}
            )
        
        notifications = notification_service.get_user_notifications(sample_user['_id'], limit=10)
        
        assert len(notifications) >= 3
        assert all(n['recipient_id'] == sample_user['_id'] for n in notifications)
    
    def test_notify_invoice_submitted(self, notification_service, sample_invoice, sample_user, sample_approver):
        """Test invoice submitted notification."""
        notification_service.notify_invoice_submitted(
            invoice=sample_invoice,
            submitter=sample_user,
            approvers=[sample_approver],
            smtp_config=None  # Will log only
        )
        
        # Check notification was logged
        notifications = list(notification_service.notifications.find({
            'recipient_id': sample_approver['_id']
        }))
        
        assert len(notifications) > 0
    
    def test_notify_invoice_approved(self, notification_service, sample_invoice, sample_user, sample_approver):
        """Test invoice approved notification."""
        notification_service.notify_invoice_approved(
            invoice=sample_invoice,
            approver=sample_approver,
            submitter=sample_user,
            smtp_config=None
        )
        
        notifications = list(notification_service.notifications.find({
            'recipient_id': sample_user['_id'],
            'type': NotificationType.INVOICE_APPROVED
        }))
        
        assert len(notifications) > 0
