"""
Tests for approval rules service.
"""

import pytest
from services.approval_rules_service import ApprovalRulesService, ApprovalRule
from datetime import datetime, timedelta


@pytest.fixture
def approval_rules_service(mongo_db):
    """Create approval rules service instance."""
    return ApprovalRulesService(mongo_db)


@pytest.fixture
def sample_invoice_small():
    """Sample small expense invoice."""
    return {
        '_id': 'inv_small_123',
        'total': 250.00,
        'category': 'Office',
        'vendor_id': 'vendor_123',
        'status': 'submitted'
    }


@pytest.fixture
def sample_invoice_large():
    """Sample large expense invoice."""
    return {
        '_id': 'inv_large_123',
        'total': 15000.00,
        'category': 'Software',
        'vendor_id': 'vendor_456',
        'status': 'submitted'
    }


@pytest.fixture
def sample_invoice_very_large():
    """Sample very large expense invoice."""
    return {
        '_id': 'inv_very_large_123',
        'total': 50000.00,
        'category': 'Equipment',
        'vendor_id': 'vendor_789',
        'status': 'submitted'
    }


class TestApprovalRule:
    """Test ApprovalRule class."""
    
    def test_rule_creation(self):
        """Test creating an approval rule."""
        rule = ApprovalRule(
            rule_id='test_rule',
            name='Test Rule',
            conditions={'min_amount': 0, 'max_amount': 1000},
            approvers=['any_approver'],
            required_approvals=1,
            priority=1
        )
        
        assert rule.rule_id == 'test_rule'
        assert rule.name == 'Test Rule'
        assert rule.active is True
    
    def test_rule_matches_amount_range(self, sample_invoice_small):
        """Test rule matching by amount range."""
        rule = ApprovalRule(
            rule_id='small_rule',
            name='Small Expenses',
            conditions={'min_amount': 0, 'max_amount': 500},
            approvers=['any_approver'],
            required_approvals=1,
            priority=1
        )
        
        assert rule.matches(sample_invoice_small) is True
    
    def test_rule_does_not_match_amount_range(self, sample_invoice_large):
        """Test rule not matching amount range."""
        rule = ApprovalRule(
            rule_id='small_rule',
            name='Small Expenses',
            conditions={'min_amount': 0, 'max_amount': 500},
            approvers=['any_approver'],
            required_approvals=1,
            priority=1
        )
        
        assert rule.matches(sample_invoice_large) is False
    
    def test_rule_matches_category(self, sample_invoice_small):
        """Test rule matching by category."""
        rule = ApprovalRule(
            rule_id='office_rule',
            name='Office Expenses',
            conditions={'categories': ['Office', 'Supplies']},
            approvers=['any_approver'],
            required_approvals=1,
            priority=1
        )
        
        assert rule.matches(sample_invoice_small) is True
    
    def test_rule_to_dict(self):
        """Test converting rule to dictionary."""
        rule = ApprovalRule(
            rule_id='test_rule',
            name='Test Rule',
            conditions={'min_amount': 0},
            approvers=['approver1'],
            required_approvals=1,
            priority=1
        )
        
        rule_dict = rule.to_dict()
        
        assert rule_dict['rule_id'] == 'test_rule'
        assert rule_dict['name'] == 'Test Rule'
        assert 'conditions' in rule_dict
        assert 'approvers' in rule_dict


class TestApprovalRulesService:
    """Test approval rules service."""
    
    def test_default_rules_created(self, approval_rules_service):
        """Test that default rules are created."""
        rules = approval_rules_service.get_all_rules()
        
        assert len(rules) >= 4  # Should have at least 4 default rules
        rule_ids = [r.rule_id for r in rules]
        assert 'small_expense' in rule_ids
        assert 'large_expense' in rule_ids
    
    def test_get_matching_rules_small_expense(self, approval_rules_service, sample_invoice_small):
        """Test getting matching rules for small expense."""
        matching_rules = approval_rules_service.get_matching_rules(sample_invoice_small)
        
        assert len(matching_rules) > 0
        # Should match small expense rule
        assert any(r.rule_id == 'small_expense' for r in matching_rules)
    
    def test_get_matching_rules_large_expense(self, approval_rules_service, sample_invoice_large):
        """Test getting matching rules for large expense."""
        matching_rules = approval_rules_service.get_matching_rules(sample_invoice_large)
        
        assert len(matching_rules) > 0
        # Should match large expense rule
        assert any(r.rule_id == 'large_expense' for r in matching_rules)
    
    def test_get_matching_rules_very_large_expense(self, approval_rules_service, sample_invoice_very_large):
        """Test getting matching rules for very large expense."""
        matching_rules = approval_rules_service.get_matching_rules(sample_invoice_very_large)
        
        assert len(matching_rules) > 0
        # Should match very large expense rule
        assert any(r.rule_id == 'very_large_expense' for r in matching_rules)
    
    def test_determine_approvers(self, approval_rules_service, sample_invoice_small, mongo_db):
        """Test determining approvers for an invoice."""
        # Create test users
        mongo_db.users.insert_one({
            '_id': 'approver_1',
            'email': 'approver1@example.com',
            'name': 'Approver One',
            'roles': ['approver'],
            'status': 'active'
        })
        
        approvers, required_count = approval_rules_service.determine_approvers(
            sample_invoice_small,
            mongo_db.users
        )
        
        assert len(approvers) > 0
        assert required_count >= 1
    
    def test_check_escalation_not_required(self, approval_rules_service):
        """Test escalation check for recent invoice."""
        invoice = {
            '_id': 'inv_123',
            'status': 'pending_approval',
            'submitted_at': datetime.utcnow()
        }
        
        needs_escalation = approval_rules_service.check_escalation_required(invoice, escalation_days=3)
        
        assert needs_escalation is False
    
    def test_check_escalation_required(self, approval_rules_service):
        """Test escalation check for overdue invoice."""
        invoice = {
            '_id': 'inv_123',
            'status': 'pending_approval',
            'submitted_at': datetime.utcnow() - timedelta(days=5)
        }
        
        needs_escalation = approval_rules_service.check_escalation_required(invoice, escalation_days=3)
        
        assert needs_escalation is True
    
    def test_create_custom_rule(self, approval_rules_service):
        """Test creating a custom approval rule."""
        success, rule_doc, error = approval_rules_service.create_rule(
            rule_id='custom_rule_test',
            name='Custom Test Rule',
            conditions={'min_amount': 1000, 'max_amount': 2000},
            approvers=['manager1', 'manager2'],
            required_approvals=2,
            priority=5
        )
        
        assert success is True
        assert rule_doc is not None
        assert error is None
        assert rule_doc['rule_id'] == 'custom_rule_test'
    
    def test_create_duplicate_rule_fails(self, approval_rules_service):
        """Test that creating duplicate rule fails."""
        # Create first rule
        approval_rules_service.create_rule(
            rule_id='duplicate_test',
            name='Duplicate Test',
            conditions={'min_amount': 0},
            approvers=['approver1'],
            required_approvals=1,
            priority=1
        )
        
        # Try to create duplicate
        success, rule_doc, error = approval_rules_service.create_rule(
            rule_id='duplicate_test',
            name='Duplicate Test 2',
            conditions={'min_amount': 0},
            approvers=['approver2'],
            required_approvals=1,
            priority=1
        )
        
        assert success is False
        assert error is not None
    
    def test_update_rule(self, approval_rules_service):
        """Test updating an approval rule."""
        # Create a rule
        approval_rules_service.create_rule(
            rule_id='update_test',
            name='Update Test',
            conditions={'min_amount': 0},
            approvers=['approver1'],
            required_approvals=1,
            priority=1
        )
        
        # Update it
        success, error = approval_rules_service.update_rule(
            'update_test',
            {'name': 'Updated Name', 'priority': 10}
        )
        
        assert success is True
        assert error is None
        
        # Verify update
        rule = approval_rules_service.get_rule('update_test')
        assert rule.name == 'Updated Name'
        assert rule.priority == 10
    
    def test_delete_rule(self, approval_rules_service):
        """Test deleting (deactivating) a rule."""
        # Create a rule
        approval_rules_service.create_rule(
            rule_id='delete_test',
            name='Delete Test',
            conditions={'min_amount': 0},
            approvers=['approver1'],
            required_approvals=1,
            priority=1
        )
        
        # Delete it
        success, error = approval_rules_service.delete_rule('delete_test')
        
        assert success is True
        assert error is None
        
        # Verify it's not in active rules
        active_rules = approval_rules_service.get_all_rules(active_only=True)
        assert not any(r.rule_id == 'delete_test' for r in active_rules)
        
        # But still exists when querying all rules
        all_rules = approval_rules_service.get_all_rules(active_only=False)
        deleted_rule = next((r for r in all_rules if r.rule_id == 'delete_test'), None)
        assert deleted_rule is not None
        assert deleted_rule.active is False
