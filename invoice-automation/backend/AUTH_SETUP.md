# Authentication Setup Guide

## Overview
The invoice automation system now includes JWT-based authentication with role-based access control (RBAC).

## Features Implemented

### 1. User Authentication
- ✅ JWT token-based authentication
- ✅ Bcrypt password hashing
- ✅ Access tokens (1 hour expiry)
- ✅ Refresh tokens (30 days expiry)
- ✅ Account lockout after 5 failed attempts
- ✅ Password strength validation

### 2. User Roles
- **Admin**: Full system access, can manage users
- **Approver**: Can approve invoices and submit
- **Submitter**: Can upload and view own invoices
- **Viewer**: Read-only access

### 3. Protected Endpoints
All invoice-related endpoints now require authentication:
- `POST /upload` - Requires authentication
- `GET /invoices` - Requires authentication
- `GET /dashboard` - Requires authentication
- `POST /chat` - Requires authentication

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create or update `.env` file:
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# CORS (comma-separated for multiple origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**⚠️ IMPORTANT**: Change `JWT_SECRET_KEY` in production! Use a strong random string.

### 3. Create Admin User
Run the interactive script to create your first admin user:
```bash
python3 create_admin.py
```

Follow the prompts to enter:
- Email address
- Full name
- Department (optional)
- Password (hidden input)

Example output:
```
==================================================
Create Admin User for Invoice Automation System
==================================================

Enter admin user details:
Email: admin@example.com
Full Name: John Doe
Department (optional): IT
Password: ********
Confirm Password: ********

Creating admin user...

✅ Admin user created successfully!
   Email: admin@example.com
   Name: John Doe
   Roles: admin, approver, submitter
   User ID: 507f1f77bcf86cd799439011

You can now login with these credentials.
```

### 4. Start the Server
```bash
python3 app.py
```

## API Usage

### Register a New User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "Jane Smith",
  "password": "SecurePass123",
  "roles": ["submitter"],
  "department": "Finance"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "YourPassword123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "admin@example.com",
    "name": "John Doe",
    "roles": ["admin", "approver", "submitter"],
    "status": "active",
    "department": "IT"
  }
}
```

### Use Access Token
Include the access token in the Authorization header for protected endpoints:

```bash
GET /invoices
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Refresh Token
When the access token expires, use the refresh token to get a new one:

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get Current User Info
```bash
GET /api/auth/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Change Password
```bash
POST /api/auth/change-password
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json

{
  "old_password": "CurrentPass123",
  "new_password": "NewSecurePass456"
}
```

## Frontend Integration

### Store Tokens
After successful login, store both tokens securely:

```javascript
// Store tokens in localStorage (or use httpOnly cookies for better security)
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('refresh_token', response.refresh_token);
localStorage.setItem('user', JSON.stringify(response.user));
```

### Add Token to Requests
Update your API client to include the Authorization header:

```javascript
// In src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken
        });
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

## Security Best Practices

### Production Deployment
1. **Use HTTPS only** - Never send tokens over HTTP
2. **Secure JWT secret** - Use a strong random string (min 32 characters)
3. **Short token expiry** - Keep access tokens short-lived (15-60 minutes)
4. **HttpOnly cookies** - Consider using httpOnly cookies instead of localStorage
5. **CORS configuration** - Restrict CORS_ORIGINS to your actual frontend domains
6. **Rate limiting** - Add rate limiting to prevent brute force attacks
7. **Environment variables** - Never commit secrets to version control

### Recommended .env for Production
```bash
JWT_SECRET_KEY=<generate-with: openssl rand -base64 32>
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days
CORS_ORIGINS=https://yourdomain.com
FLASK_DEBUG=false
```

### Generate Secure Secret Key
```bash
# On Linux/Mac
openssl rand -base64 32

# Or with Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Troubleshooting

### "Invalid token" error
- Token may have expired - use refresh token to get new access token
- Token format incorrect - ensure "Bearer " prefix in Authorization header
- JWT_SECRET_KEY mismatch - verify secret key is same across restarts

### "Account locked" error
- User entered wrong password 5 times
- Admin needs to manually unlock in database or create user management endpoint

### "Database not available" error
- MongoDB is not running
- Check MONGO_URI in .env file
- Verify connection with: `mongo <MONGO_URI>`

### CORS errors
- Add your frontend URL to CORS_ORIGINS in .env
- Check that frontend is using correct API base URL

## Next Steps

To complete the authentication system, consider adding:

1. **Password reset flow** - Email-based password reset
2. **Email verification** - Verify email addresses on registration
3. **User management endpoints** - Admin can create/edit/delete users
4. **Audit logging** - Track all authentication events
5. **Session management** - Track active sessions, allow logout from all devices
6. **2FA/MFA** - Two-factor authentication for enhanced security
7. **OAuth/SSO** - Social login or enterprise SSO integration
