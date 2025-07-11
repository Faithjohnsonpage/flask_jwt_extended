#!/usr/bin/env python3
"""Test script for User model"""
from models import storage
from models.user import User

def main():
    # Create a new user
    user = User()
    user.username = "faithjohnson"
    user.email = "faith@example.com"
    user.password = "securepassword123"
    user.profile_picture_url = "https://example.com/profile.jpg"

    # Save the user
    user.save()
    print("User saved successfully!")

    # Retrieve the user by ID
    retrieved = storage.get(User, user.id)
    print("Retrieved:", retrieved)

    # Test password verification
    print("Password correct:", retrieved.verify_password("securepassword123"))  # Should be True
    print("Password incorrect:", retrieved.verify_password("wrongpassword"))    # Should be False


if __name__ == "__main__":
    main()
