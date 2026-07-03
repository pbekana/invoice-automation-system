# Invoice Automation API Documentation

## Base URL
```
http://localhost:5000
```

## Authentication
All API endpoints (except registration and login) require authentication using JWT tokens.

Include the access token in the Authorization header:
```
Authorization: Bearer <your-access-token>
```

---

## Authentication Endpoints

### Register User
```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePass123",
  "roles": ["submitter"],
  "department": "Finance"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["submitter"],
    "status": "active",
    "department": "Finance"
  }
}
```

### Login
```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { ... }
}
```

### Refresh Token
```http
POST /api/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["submitter"],
    "status": "active"
  }
}
```

### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "old_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

---

## Vendor Endpoints

### Create Vendor
```http
POST /api/vendors
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Acme Corporation",
  "email": "billing@acme.com",
  "phone": "555-1234",
  "address": "123 Main St, City, State 12345",
  "tax_id": "12-3456789",
  "payment_terms": "Net 30",
  "default_category": "Supplies",
  "notes": "Primary office supplier"
}
```

**Response:** `201 Created`
```json
{
  "message": "Vendor created successfully",
  "vendor": {
    "id": "507f1f77bcf86cd799439012",
    "name": "Acme Corporation",
    "email": "billing@acme.com",
    "status": "active",
    "payment_terms": "Net 30"
  }
}
```

### List Vendors
```http
GET /api/vendors?status=active&search=acme&limit=50&skip=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): Filter by status (active, inactive, blocked)
- `search` (optional): Search by name or email
- `limit` (optional): Number of results (default: 100, max: 200)
- `skip` (optional): Number of results to skip (pagination)

**Response:** `200 OK`
```json
{
  "vendors": [
    {
      "id": "507f1f77bcf86cd799439012",
      "name": "Acme Corporation",
      "email": "billing@acme.com",
      "status": "active",
      "payment_terms": "Net 30"
    }
  ],
  "total": 15,
  "limit": 50,
  "skip": 0
}
```

### Get Vendor
```http
GET /api/vendors/{vendor_id}
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "vendor": {
    "id": "507f1f77bcf86cd799439012",
    "name": "Acme Corporation",
    "email": "billing@acme.com",
    "phone": "555-1234",
    "status": "active",
    "payment_terms": "Net 30"
  }
}
```

### Update Vendor
```http
PATCH /api/vendors/{vendor_id}
Authorization: Bearer <token>
Roles: admin, approver
```

**Request Body:**
```json
{
  "email": "newemail@acme.com",
  "phone": "555-5678",
  "payment_terms": "Net 45"
}
```

**Response:** `200 OK`
```json
{
  "message": "Vendor updated successfully",
  "vendor": { ... }
}
```

### Deactivate Vendor
```http
POST /api/vendors/{vendor_id}/deactivate
Authorization: Bearer <token>
Roles: admin
```

**Response:** `200 OK`
```json
{
  "message": "Vendor deactivated successfully"
}
```

### Block Vendor
```http
POST /api/vendors/{vendor_id}/block
Authorization: Bearer <token>
Roles: admin
```

**Request Body:**
```json
{
  "reason": "Fraudulent activity detected"
}
```

**Response:** `200 OK`
```json
{
  "message": "Vendor blocked successfully"
}
```

---

## Invoice Endpoints

### Upload Invoice
```http
POST /upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: PDF or image file (max 16MB)

**Response:** `200 OK`
```json
{
  "message": "Invoice processed successfully",
  "id": "507f1f77bcf86cd799439013",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "company": "Amazon.com",
    "date": "2026-03-15",
    "total": 120.50,
    "category": "Supplies",
    "status": "submitted",
    "vendor_id": "507f1f77bcf86cd799439012"
  },
  "vendor_created": true,
  "warning": "Potential duplicate detected: Invoice 507f... from 2026-03-15"
}
```

### List Invoices
```http
GET /invoices?status=submitted&category=Transport&limit=50&skip=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): Filter by status
- `submitter_id` (optional): Filter by submitter
- `vendor_id` (optional): Filter by vendor
- `category` (optional): Filter by category
- `start_date` (optional): Filter by date range (YYYY-MM-DD)
- `end_date` (optional): Filter by date range (YYYY-MM-DD)
- `limit` (optional): Number of results (default: 50, max: 200)
- `skip` (optional): Pagination offset

**Response:** `200 OK`
```json
{
  "invoices": [
    {
      "id": "507f1f77bcf86cd799439013",
      "company": "Amazon.com",
      "date": "2026-03-15",
      "total": 120.50,
      "category": "Supplies",
      "status": "submitted",
      "submitter_id": "507f1f77bcf86cd799439011"
    }
  ],
  "total": 25,
  "limit": 50,
  "skip": 0
}
```

### Get Invoice
```http
GET /api/invoices/{invoice_id}
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "company": "Amazon.com",
    "invoice_number": null,
    "date": "2026-03-15",
    "total": 120.50,
    "category": "Supplies",
    "status": "submitted",
    "vendor_id": "507f1f77bcf86cd799439012",
    "submitter_id": "507f1f77bcf86cd799439011",
    "approval_chain": [],
    "created_at": "2026-07-02T10:30:00Z"
  }
}
```

### Update Invoice
```http
PATCH /api/invoices/{invoice_id}
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "notes": "Updated delivery address",
  "category": "Transport"
}
```

**Response:** `200 OK`
```json
{
  "message": "Invoice updated successfully",
  "invoice": { ... }
}
```

**Note:** Only invoices in `draft`, `submitted`, or `rejected` status can be edited.

### Submit Invoice for Approval
```http
POST /api/invoices/{invoice_id}/submit
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "message": "Invoice submitted for approval",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "status": "pending_approval",
    ...
  }
}
```

### Approve Invoice
```http
POST /api/invoices/{invoice_id}/approve
Authorization: Bearer <token>
Roles: admin, approver
```

**Request Body (optional):**
```json
{
  "comments": "Approved - within budget"
}
```

**Response:** `200 OK`
```json
{
  "message": "Invoice approved successfully",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "status": "approved",
    "approval_chain": [
      {
        "approver_id": "507f1f77bcf86cd799439014",
        "status": "approved",
        "comments": "Approved - within budget",
        "timestamp": "2026-07-02T11:00:00Z"
      }
    ],
    ...
  }
}
```

### Reject Invoice
```http
POST /api/invoices/{invoice_id}/reject
Authorization: Bearer <token>
Roles: admin, approver
```

**Request Body:**
```json
{
  "reason": "Missing purchase order reference"
}
```

**Response:** `200 OK`
```json
{
  "message": "Invoice rejected",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "status": "rejected",
    ...
  }
}
```

### Mark Invoice as Paid
```http
POST /api/invoices/{invoice_id}/paid
Authorization: Bearer <token>
Roles: admin, approver
```

**Request Body (optional):**
```json
{
  "payment_reference": "ACH-20260702-001234"
}
```

**Response:** `200 OK`
```json
{
  "message": "Invoice marked as paid",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "status": "paid",
    "paid_at": "2026-07-02T12:00:00Z",
    ...
  }
}
```

### Cancel Invoice
```http
POST /api/invoices/{invoice_id}/cancel
Authorization: Bearer <token>
Roles: admin
```

**Request Body:**
```json
{
  "reason": "Duplicate entry - cancelling"
}
```

**Response:** `200 OK`
```json
{
  "message": "Invoice cancelled",
  "invoice": {
    "id": "507f1f77bcf86cd799439013",
    "status": "cancelled",
    ...
  }
}
```

### Get Pending Approvals
```http
GET /api/invoices/pending-approvals
Authorization: Bearer <token>
Roles: admin, approver
```

**Response:** `200 OK`
```json
{
  "invoices": [
    {
      "id": "507f1f77bcf86cd799439013",
      "company": "Amazon.com",
      "total": 120.50,
      "status": "pending_approval",
      "submitter_id": "507f1f77bcf86cd799439011"
    }
  ],
  "total": 5
}
```

### Get Invoice History
```http
GET /api/invoices/{invoice_id}/history
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "invoice_id": "507f1f77bcf86cd799439013",
  "history": [
    {
      "id": "507f1f77bcf86cd799439020",
      "action": "invoice_created",
      "user_id": "507f1f77bcf86cd799439011",
      "timestamp": "2026-07-02T10:30:00Z",
      "details": {
        "company": "Amazon.com",
        "total": 120.50
      }
    },
    {
      "id": "507f1f77bcf86cd799439021",
      "action": "invoice_approved",
      "user_id": "507f1f77bcf86cd799439014",
      "timestamp": "2026-07-02T11:00:00Z",
      "details": {
        "comments": "Approved - within budget"
      },
      "changes": {
        "status": {
          "from": "pending_approval",
          "to": "approved"
        }
      }
    }
  ]
}
```

---

## Audit Endpoints

### Get Recent Audit Activity
```http
GET /api/audit/recent?entity_type=invoice&action=invoice_approved&limit=50
Authorization: Bearer <token>
Roles: admin
```

**Query Parameters:**
- `entity_type` (optional): Filter by entity type (invoice, user, vendor)
- `action` (optional): Filter by action
- `limit` (optional): Number of results (default: 50, max: 200)

**Response:** `200 OK`
```json
{
  "activity": [
    {
      "id": "507f1f77bcf86cd799439021",
      "action": "invoice_approved",
      "entity_type": "invoice",
      "entity_id": "507f1f77bcf86cd799439013",
      "user_id": "507f1f77bcf86cd799439014",
      "timestamp": "2026-07-02T11:00:00Z",
      "details": {},
      "changes": {}
    }
  ],
  "total": 150
}
```

### Get User Audit Activity
```http
GET /api/audit/user/{user_id}?limit=100
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "activity": [
    {
      "id": "507f1f77bcf86cd799439020",
      "action": "invoice_created",
      "entity_type": "invoice",
      "entity_id": "507f1f77bcf86cd799439013",
      "timestamp": "2026-07-02T10:30:00Z"
    }
  ],
  "total": 25
}
```

**Note:** Users can only view their own activity unless they have admin role.

### Search Audit Log
```http
GET /api/audit/search?entity_type=invoice&action=invoice_approved&limit=100&skip=0
Authorization: Bearer <token>
Roles: admin
```

**Query Parameters:**
- `user_id` (optional): Filter by user
- `entity_type` (optional): Filter by entity type
- `action` (optional): Filter by action
- `limit` (optional): Number of results (default: 100, max: 200)
- `skip` (optional): Pagination offset

**Response:** `200 OK`
```json
{
  "results": [ ... ],
  "total": 50,
  "limit": 100,
  "skip": 0
}
```

---

## Legacy Endpoints (Backward Compatibility)

### Get Dashboard Summary
```http
GET /dashboard
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "categories": {
    "Transport": {
      "total": 450.00,
      "count": 5
    },
    "Food": {
      "total": 230.50,
      "count": 8
    }
  },
  "total_invoices": 25,
  "grand_total": 1250.75
}
```

### Chat with Expense Bot
```http
POST /chat
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "How much did I spend in total?"
}
```

**Response:** `200 OK`
```json
{
  "response": "📊 Total spend: **$1,250.75** (25 invoices)."
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - Insufficient permissions for this action
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Invoice Status Workflow

```
DRAFT → SUBMITTED → PENDING_APPROVAL → APPROVED → PAID
                                     ↓
                                  REJECTED → SUBMITTED (can resubmit)
                                     ↓
                                 CANCELLED (terminal)
```

**Editable Statuses:** draft, submitted, rejected  
**Terminal Statuses:** paid, cancelled

---

## Role-Based Permissions

| Role | Permissions |
|------|-------------|
| **Viewer** | View own invoices |
| **Submitter** | Upload, view, edit own invoices |
| **Approver** | All submitter permissions + approve/reject invoices |
| **Admin** | All permissions + manage users, vendors, audit logs |

---

## Rate Limiting

Currently no rate limiting is implemented. In production, consider adding rate limiting to prevent abuse.

---

## Notes

1. All dates should be in ISO 8601 format (YYYY-MM-DD)
2. All timestamps are in UTC
3. Monetary amounts are in USD (or configured currency)
4. File uploads are limited to 16MB
5. Pagination defaults to 50 items per page, maximum 200
6. Duplicate detection is automatic on upload
7. Vendor matching is automatic based on company name
8. All actions are logged in the audit trail
