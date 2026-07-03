#!/usr/bin/env python3
"""Script to create an initial admin user."""
import sys
import getpass
from db import db_manager
from services.auth_service import AuthService
from models.user import UserRole

def create_admin():
    """Interactive script to create admin user."""
    print("=" * 50)
    print("Create Admin User for Invoice Automation System")
    print("=" * 50)
    print()
    
    if not db_manager.db:
        print("❌ Error: Could not connect to database")
        print(f"   Make sure MongoDB is running at: {db_manager.uri}")
        sys.exit(1)
    
    # Initialize auth service
    auth_service = AuthService(db_manager.db)
    
    # Get user input
    print("Enter admin user details:")
    email = input("Email: ").strip()
    name = input("Full Name: ").strip()
    department = input("Department (optional): ").strip() or None
    
    # Get password (hidden)
    while True:
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match. Try again.\n")
            continue
        break
    
    # Create admin user
    print("\nCreating admin user...")
    success, user, error = auth_service.register_user(
        email=email,
        name=name,
        password=password,
        roles=[UserRole.ADMIN, UserRole.APPROVER, UserRole.SUBMITTER],
        department=department
    )
    
    if success:
        print(f"\n✅ Admin user created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   Roles: {', '.join(user.roles)}")
        print(f"   User ID: {user._id}")
        print("\nYou can now login with these credentials.")
    else:
        print(f"\n❌ Failed to create admin user: {error}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
