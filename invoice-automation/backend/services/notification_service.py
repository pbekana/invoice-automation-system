"""
Notification Service - Email and webhook notifications for workflow events.

Provides:
- Email notifications for invoice workflow events
- Configurable notification preferences
- Template-based email generation
- Webhook support for external integrations
"""

import smtplib
import requests  # type: ignore
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from logger_config import logger


class NotificationType:
    """Notification event types."""
    INVOICE_SUBMITTED = "invoice_submitted"
    INVOICE_APPROVED = "invoice_approved"
    INVOICE_REJECTED = "invoice_rejected"
    INVOICE_PAID = "invoice_paid"
    APPROVAL_REQUIRED = "approval_required"
    INVOICE_OVERDUE = "invoice_overdue"
    BULK_OPERATION = "bulk_operation"


class EmailTemplate:
    """Email templates for different notification types."""
    
    @staticmethod
    def invoice_submitted(invoice: Dict, submitter: Dict) -> Dict[str, str]:
        """Template for invoice submission notification."""
        subject = f"Invoice Submitted: {invoice.get('invoice_number', 'N/A')} - ${invoice.get('total', 0):.2f}"
        body = f"""
A new invoice has been submitted for approval.

Invoice Details:
- Invoice Number: {invoice.get('invoice_number', 'N/A')}
- Vendor: {invoice.get('company', 'Unknown')}
- Amount: ${invoice.get('total', 0):.2f}
- Category: {invoice.get('category', 'Uncategorized')}
- Date: {invoice.get('date', 'N/A')}
- Submitted by: {submitter.get('name', 'Unknown')} ({submitter.get('email', '')})
- Submitted at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please review and approve or reject this invoice.

---
Invoice Automation System
        """
        return {"subject": subject, "body": body.strip()}
    
    @staticmethod
    def invoice_approved(invoice: Dict, approver: Dict) -> Dict[str, str]:
        """Template for invoice approval notification."""
        subject = f"Invoice Approved: {invoice.get('invoice_number', 'N/A')}"
        body = f"""
Your invoice has been approved.

Invoice Details:
- Invoice Number: {invoice.get('invoice_number', 'N/A')}
- Vendor: {invoice.get('company', 'Unknown')}
- Amount: ${invoice.get('total', 0):.2f}
- Category: {invoice.get('category', 'Uncategorized')}
- Approved by: {approver.get('name', 'Unknown')} ({approver.get('email', '')})
- Approved at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

The invoice is now ready for payment processing.

---
Invoice Automation System
        """
        return {"subject": subject, "body": body.strip()}
    
    @staticmethod
    def invoice_rejected(invoice: Dict, approver: Dict, comments: Optional[str] = None) -> Dict[str, str]:
        """Template for invoice rejection notification."""
        subject = f"Invoice Rejected: {invoice.get('invoice_number', 'N/A')}"
        comments_section = f"\nReason: {comments}" if comments else ""
        body = f"""
Your invoice has been rejected.

Invoice Details:
- Invoice Number: {invoice.get('invoice_number', 'N/A')}
- Vendor: {invoice.get('company', 'Unknown')}
- Amount: ${invoice.get('total', 0):.2f}
- Category: {invoice.get('category', 'Uncategorized')}
- Rejected by: {approver.get('name', 'Unknown')} ({approver.get('email', '')})
- Rejected at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}{comments_section}

Please review the comments and resubmit if necessary.

---
Invoice Automation System
        """
        return {"subject": subject, "body": body.strip()}
    
    @staticmethod
    def invoice_paid(invoice: Dict) -> Dict[str, str]:
        """Template for invoice payment notification."""
        subject = f"Invoice Paid: {invoice.get('invoice_number', 'N/A')}"
        body = f"""
Invoice has been marked as paid.

Invoice Details:
- Invoice Number: {invoice.get('invoice_number', 'N/A')}
- Vendor: {invoice.get('company', 'Unknown')}
- Amount: ${invoice.get('total', 0):.2f}
- Category: {invoice.get('category', 'Uncategorized')}
- Paid at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

This invoice is now complete.

---
Invoice Automation System
        """
        return {"subject": subject, "body": body.strip()}
    
    @staticmethod
    def approval_required(invoice: Dict, approver: Dict) -> Dict[str, str]:
        """Template for approval required notification."""
        subject = f"Action Required: Approve Invoice {invoice.get('invoice_number', 'N/A')} - ${invoice.get('total', 0):.2f}"
        body = f"""
An invoice requires your approval.

Invoice Details:
- Invoice Number: {invoice.get('invoice_number', 'N/A')}
- Vendor: {invoice.get('company', 'Unknown')}
- Amount: ${invoice.get('total', 0):.2f}
- Category: {invoice.get('category', 'Uncategorized')}
- Date: {invoice.get('date', 'N/A')}
- Assigned to: {approver.get('name', 'Unknown')}

Please log in to review and take action.

---
Invoice Automation System
        """
        return {"subject": subject, "body": body.strip()}


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, db):
        """Initialize notification service."""
        self.db = db
        self.notifications = db.notifications
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        smtp_config: Optional[Dict] = None
    ) -> bool:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            smtp_config: SMTP configuration (host, port, username, password, use_tls)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not smtp_config:
            # Default to console logging if no SMTP configured
            logger.info(f"[EMAIL] To: {to_email} | Subject: {subject}")
            logger.debug(f"[EMAIL BODY]\n{body}")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email', smtp_config['username'])
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect and send
            if smtp_config.get('use_tls', True):
                server = smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 587))
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_config['host'], smtp_config.get('port', 25))
            
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_webhook(self, webhook_url: str, payload: Dict) -> bool:
        """
        Send webhook notification.
        
        Args:
            webhook_url: Webhook endpoint URL
            payload: JSON payload to send
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Webhook sent to {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
            return False
    
    def notify_invoice_submitted(
        self,
        invoice: Dict,
        submitter: Dict,
        approvers: List[Dict],
        smtp_config: Optional[Dict] = None
    ) -> None:
        """Notify approvers when an invoice is submitted."""
        template = EmailTemplate.invoice_submitted(invoice, submitter)
        
        for approver in approvers:
            if approver.get('email'):
                self.send_email(
                    to_email=approver['email'],
                    subject=template['subject'],
                    body=template['body'],
                    smtp_config=smtp_config
                )
                
                # Log notification
                self._log_notification(
                    notification_type=NotificationType.INVOICE_SUBMITTED,
                    recipient_id=approver.get('_id'),
                    invoice_id=invoice.get('_id'),
                    details={'sent_to': approver['email']}
                )
    
    def notify_invoice_approved(
        self,
        invoice: Dict,
        approver: Dict,
        submitter: Dict,
        smtp_config: Optional[Dict] = None
    ) -> None:
        """Notify submitter when their invoice is approved."""
        template = EmailTemplate.invoice_approved(invoice, approver)
        
        if submitter.get('email'):
            self.send_email(
                to_email=submitter['email'],
                subject=template['subject'],
                body=template['body'],
                smtp_config=smtp_config
            )
            
            # Log notification
            self._log_notification(
                notification_type=NotificationType.INVOICE_APPROVED,
                recipient_id=submitter.get('_id'),
                invoice_id=invoice.get('_id'),
                details={'approved_by': approver.get('email')}
            )
    
    def notify_invoice_rejected(
        self,
        invoice: Dict,
        approver: Dict,
        submitter: Dict,
        comments: Optional[str] = None,
        smtp_config: Optional[Dict] = None
    ) -> None:
        """Notify submitter when their invoice is rejected."""
        template = EmailTemplate.invoice_rejected(invoice, approver, comments)
        
        if submitter.get('email'):
            self.send_email(
                to_email=submitter['email'],
                subject=template['subject'],
                body=template['body'],
                smtp_config=smtp_config
            )
            
            # Log notification
            self._log_notification(
                notification_type=NotificationType.INVOICE_REJECTED,
                recipient_id=submitter.get('_id'),
                invoice_id=invoice.get('_id'),
                details={'rejected_by': approver.get('email'), 'comments': comments}
            )
    
    def notify_invoice_paid(
        self,
        invoice: Dict,
        recipients: List[Dict],
        smtp_config: Optional[Dict] = None
    ) -> None:
        """Notify relevant parties when invoice is paid."""
        template = EmailTemplate.invoice_paid(invoice)
        
        for recipient in recipients:
            if recipient.get('email'):
                self.send_email(
                    to_email=recipient['email'],
                    subject=template['subject'],
                    body=template['body'],
                    smtp_config=smtp_config
                )
                
                # Log notification
                self._log_notification(
                    notification_type=NotificationType.INVOICE_PAID,
                    recipient_id=recipient.get('_id'),
                    invoice_id=invoice.get('_id'),
                    details={'sent_to': recipient['email']}
                )
    
    def notify_approval_required(
        self,
        invoice: Dict,
        approver: Dict,
        smtp_config: Optional[Dict] = None
    ) -> None:
        """Notify specific approver that their action is required."""
        template = EmailTemplate.approval_required(invoice, approver)
        
        if approver.get('email'):
            self.send_email(
                to_email=approver['email'],
                subject=template['subject'],
                body=template['body'],
                smtp_config=smtp_config
            )
            
            # Log notification
            self._log_notification(
                notification_type=NotificationType.APPROVAL_REQUIRED,
                recipient_id=approver.get('_id'),
                invoice_id=invoice.get('_id'),
                details={'sent_to': approver['email']}
            )
    
    def _log_notification(
        self,
        notification_type: str,
        recipient_id: Any,
        invoice_id: Any,
        details: Dict
    ) -> None:
        """Log notification to database."""
        try:
            self.notifications.insert_one({
                'type': notification_type,
                'recipient_id': recipient_id,
                'invoice_id': invoice_id,
                'details': details,
                'sent_at': datetime.utcnow(),
                'status': 'sent'
            })
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    def get_user_notifications(
        self,
        user_id: Any,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent notifications for a user."""
        try:
            notifications = list(
                self.notifications.find({'recipient_id': user_id})
                .sort('sent_at', -1)
                .limit(limit)
            )
            return notifications
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []


# Module-level singleton
notification_service: Optional[NotificationService] = None
