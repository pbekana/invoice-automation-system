"""
Approval Rules Service - Automatic routing and approval chain management.

Provides:
- Rule-based approval routing
- Amount-based approval thresholds
- Multi-level approval chains
- Automatic approver assignment
- Escalation rules
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from logger_config import logger
from bson import ObjectId  # type: ignore


class ApprovalRule:
    """Represents an approval rule."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        conditions: Dict,
        approvers: List[str],
        required_approvals: int = 1,
        priority: int = 0,
        active: bool = True
    ):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.approvers = approvers
        self.required_approvals = required_approvals
        self.priority = priority
        self.active = active
    
    def matches(self, invoice: Dict) -> bool:
        """Check if invoice matches this rule's conditions."""
        conditions = self.conditions
        
        # Amount threshold
        if 'min_amount' in conditions:
            if invoice.get('total', 0) < conditions['min_amount']:
                return False
        
        if 'max_amount' in conditions:
            if invoice.get('total', 0) > conditions['max_amount']:
                return False
        
        # Category match
        if 'categories' in conditions:
            if invoice.get('category') not in conditions['categories']:
                return False
        
        # Vendor match
        if 'vendor_ids' in conditions:
            if str(invoice.get('vendor_id')) not in conditions['vendor_ids']:
                return False
        
        # Department match
        if 'departments' in conditions:
            submitter_dept = invoice.get('submitter_department')
            if submitter_dept not in conditions['departments']:
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'conditions': self.conditions,
            'approvers': self.approvers,
            'required_approvals': self.required_approvals,
            'priority': self.priority,
            'active': self.active
        }


class ApprovalRulesService:
    """Service for managing approval rules and automatic routing."""
    
    # Default approval rules
    DEFAULT_RULES = [
        {
            'rule_id': 'small_expense',
            'name': 'Small Expenses (Under $500)',
            'conditions': {'min_amount': 0, 'max_amount': 500},
            'approvers': ['any_approver'],  # Any user with approver role
            'required_approvals': 1,
            'priority': 1,
            'active': True
        },
        {
            'rule_id': 'medium_expense',
            'name': 'Medium Expenses ($500-$5000)',
            'conditions': {'min_amount': 500, 'max_amount': 5000},
            'approvers': ['any_approver'],
            'required_approvals': 1,
            'priority': 2,
            'active': True
        },
        {
            'rule_id': 'large_expense',
            'name': 'Large Expenses ($5000-$25000)',
            'conditions': {'min_amount': 5000, 'max_amount': 25000},
            'approvers': ['department_head', 'finance_manager'],
            'required_approvals': 2,
            'priority': 3,
            'active': True
        },
        {
            'rule_id': 'very_large_expense',
            'name': 'Very Large Expenses (Over $25000)',
            'conditions': {'min_amount': 25000},
            'approvers': ['finance_manager', 'cfo', 'ceo'],
            'required_approvals': 3,
            'priority': 4,
            'active': True
        }
    ]
    
    def __init__(self, db):
        """Initialize approval rules service."""
        self.db = db
        self.rules_collection = db.approval_rules
        self._ensure_default_rules()
    
    def _ensure_default_rules(self) -> None:
        """Ensure default rules exist in database."""
        try:
            for rule_data in self.DEFAULT_RULES:
                existing = self.rules_collection.find_one({'rule_id': rule_data['rule_id']})
                if not existing:
                    rule_data['created_at'] = datetime.utcnow()
                    self.rules_collection.insert_one(rule_data)
                    logger.info(f"Created default approval rule: {rule_data['name']}")
        except Exception as e:
            logger.error(f"Failed to create default rules: {e}")
    
    def get_all_rules(self, active_only: bool = True) -> List[ApprovalRule]:
        """Get all approval rules."""
        try:
            query = {'active': True} if active_only else {}
            rules_data = list(self.rules_collection.find(query).sort('priority', 1))
            return [ApprovalRule(**self._prepare_rule_data(r)) for r in rules_data]
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return []
    
    def _prepare_rule_data(self, rule_doc: Dict) -> Dict:
        """Prepare rule data for ApprovalRule construction."""
        return {
            'rule_id': rule_doc['rule_id'],
            'name': rule_doc['name'],
            'conditions': rule_doc['conditions'],
            'approvers': rule_doc['approvers'],
            'required_approvals': rule_doc.get('required_approvals', 1),
            'priority': rule_doc.get('priority', 0),
            'active': rule_doc.get('active', True)
        }
    
    def get_matching_rules(self, invoice: Dict) -> List[ApprovalRule]:
        """Get all rules that match the invoice."""
        all_rules = self.get_all_rules(active_only=True)
        matching_rules = [rule for rule in all_rules if rule.matches(invoice)]
        # Sort by priority (highest first)
        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        return matching_rules
    
    def determine_approvers(
        self,
        invoice: Dict,
        users_collection
    ) -> Tuple[List[Dict], int]:
        """
        Determine required approvers for an invoice.
        
        Args:
            invoice: Invoice document
            users_collection: MongoDB users collection
        
        Returns:
            Tuple of (list of approver user objects, required approval count)
        """
        matching_rules = self.get_matching_rules(invoice)
        
        if not matching_rules:
            # Default: any approver
            logger.info(f"No matching rules for invoice, using default approvers")
            approvers = list(users_collection.find({'roles': 'approver', 'status': 'active'}))
            return approvers, 1
        
        # Use highest priority matching rule
        primary_rule = matching_rules[0]
        logger.info(f"Applying rule '{primary_rule.name}' to invoice {invoice.get('_id')}")
        
        approver_list = []
        
        for approver_spec in primary_rule.approvers:
            if approver_spec == 'any_approver':
                # Get all active approvers
                approvers = list(users_collection.find({'roles': 'approver', 'status': 'active'}))
                approver_list.extend(approvers)
            
            elif approver_spec in ['department_head', 'finance_manager', 'cfo', 'ceo']:
                # Get users by role (stored in department or custom field)
                approvers = list(users_collection.find({
                    'department': approver_spec,
                    'roles': 'approver',
                    'status': 'active'
                }))
                if not approvers:
                    # Fallback: get any approver with admin role
                    approvers = list(users_collection.find({'roles': 'admin', 'status': 'active'}))
                approver_list.extend(approvers)
            
            else:
                # Try to find specific user by ID or email
                try:
                    if ObjectId.is_valid(approver_spec):
                        user = users_collection.find_one({'_id': ObjectId(approver_spec)})
                        if user:
                            approver_list.append(user)
                    else:
                        user = users_collection.find_one({'email': approver_spec})
                        if user:
                            approver_list.append(user)
                except Exception:
                    pass
        
        # Remove duplicates
        seen_ids = set()
        unique_approvers = []
        for approver in approver_list:
            approver_id = str(approver['_id'])
            if approver_id not in seen_ids:
                seen_ids.add(approver_id)
                unique_approvers.append(approver)
        
        return unique_approvers, primary_rule.required_approvals
    
    def check_escalation_required(
        self,
        invoice: Dict,
        escalation_days: int = 3
    ) -> bool:
        """
        Check if invoice approval is overdue and needs escalation.
        
        Args:
            invoice: Invoice document
            escalation_days: Days after which to escalate
        
        Returns:
            True if escalation is required
        """
        if invoice.get('status') != 'pending_approval':
            return False
        
        submitted_at = invoice.get('submitted_at')
        if not submitted_at:
            return False
        
        if isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
        
        days_pending = (datetime.utcnow() - submitted_at).days
        return days_pending >= escalation_days
    
    def get_escalation_approvers(
        self,
        invoice: Dict,
        users_collection
    ) -> List[Dict]:
        """Get escalation approvers (typically higher management)."""
        # Get admins as escalation approvers
        escalation_approvers = list(users_collection.find({
            'roles': 'admin',
            'status': 'active'
        }))
        
        logger.info(f"Escalating invoice {invoice.get('_id')} to {len(escalation_approvers)} admins")
        return escalation_approvers
    
    def create_rule(
        self,
        rule_id: str,
        name: str,
        conditions: Dict,
        approvers: List[str],
        required_approvals: int = 1,
        priority: int = 0
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Create a new approval rule."""
        try:
            # Check if rule ID already exists
            existing = self.rules_collection.find_one({'rule_id': rule_id})
            if existing:
                return False, None, "Rule ID already exists"
            
            rule_doc = {
                'rule_id': rule_id,
                'name': name,
                'conditions': conditions,
                'approvers': approvers,
                'required_approvals': required_approvals,
                'priority': priority,
                'active': True,
                'created_at': datetime.utcnow()
            }
            
            result = self.rules_collection.insert_one(rule_doc)
            rule_doc['_id'] = result.inserted_id
            
            logger.info(f"Created approval rule: {name}")
            return True, rule_doc, None
            
        except Exception as e:
            logger.error(f"Failed to create rule: {e}")
            return False, None, str(e)
    
    def update_rule(
        self,
        rule_id: str,
        updates: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Update an existing rule."""
        try:
            updates['updated_at'] = datetime.utcnow()
            result = self.rules_collection.update_one(
                {'rule_id': rule_id},
                {'$set': updates}
            )
            
            if result.matched_count == 0:
                return False, "Rule not found"
            
            logger.info(f"Updated approval rule: {rule_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to update rule: {e}")
            return False, str(e)
    
    def delete_rule(self, rule_id: str) -> Tuple[bool, Optional[str]]:
        """Delete (deactivate) a rule."""
        return self.update_rule(rule_id, {'active': False})
    
    def get_rule(self, rule_id: str) -> Optional[ApprovalRule]:
        """Get a specific rule by ID."""
        try:
            rule_doc = self.rules_collection.find_one({'rule_id': rule_id})
            if rule_doc:
                return ApprovalRule(**self._prepare_rule_data(rule_doc))
            return None
        except Exception as e:
            logger.error(f"Failed to get rule: {e}")
            return None


# Module-level singleton
approval_rules_service: Optional[ApprovalRulesService] = None
