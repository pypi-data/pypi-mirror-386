"""
Tests for type definitions
"""

from datetime import datetime

from boiler_sdk.types.common import (
    AuthResponse,
    ForgotPasswordResponse,
    RegisterResponse,
    ResetPasswordResponse,
    User,
    UserRegisterInput,
)


def test_user_creation():
    """Test User dataclass creation"""
    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    assert user.id == "user123"
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.status == "active"
    assert user.created_at is None
    assert user.updated_at is None


def test_user_with_timestamps():
    """Test User with timestamp fields"""
    created = datetime(2024, 1, 1, 12, 0, 0)
    updated = datetime(2024, 1, 2, 12, 0, 0)

    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
        created_at=created,
        updated_at=updated,
    )

    assert user.created_at == created
    assert user.updated_at == updated


def test_auth_response():
    """Test AuthResponse dataclass"""
    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    auth_response = AuthResponse(
        default_org_name="Test Org",
        token="jwt_token_here",
        user=user,
        workspaces_and_tenants=[
            {"workspace_id": "ws1", "workspace_name": "Workspace 1"}
        ],
    )

    assert auth_response.default_org_name == "Test Org"
    assert auth_response.token == "jwt_token_here"
    assert auth_response.user == user
    assert len(auth_response.workspaces_and_tenants) == 1


def test_auth_response_minimal():
    """Test AuthResponse with minimal fields"""
    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    auth_response = AuthResponse(
        default_org_name=None,
        token="jwt_token_here",
        user=user,
    )

    assert auth_response.default_org_name is None
    assert auth_response.token == "jwt_token_here"
    assert auth_response.user == user
    assert auth_response.workspaces_and_tenants is None


def test_register_response():
    """Test RegisterResponse dataclass"""
    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="pending",
    )

    register_response = RegisterResponse(user=user)

    assert register_response.user == user


def test_forgot_password_response():
    """Test ForgotPasswordResponse dataclass"""
    response = ForgotPasswordResponse(success=True)
    assert response.success is True

    response = ForgotPasswordResponse(success=False)
    assert response.success is False


def test_reset_password_response():
    """Test ResetPasswordResponse dataclass"""
    response = ResetPasswordResponse(success=True)
    assert response.success is True

    response = ResetPasswordResponse(success=False)
    assert response.success is False


def test_user_register_input():
    """Test UserRegisterInput dataclass"""
    input_data = UserRegisterInput(
        email="newuser@example.com",
        name="New User",
        password="secure_password",
    )

    assert input_data.email == "newuser@example.com"
    assert input_data.name == "New User"
    assert input_data.password == "secure_password"


def test_dataclass_equality():
    """Test dataclass equality comparison"""
    user1 = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    user2 = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    user3 = User(
        id="user456",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    assert user1 == user2
    assert user1 != user3


def test_dataclass_immutability():
    """Test that dataclasses work as expected with field assignment"""
    user = User(
        id="user123",
        email="test@example.com",
        name="Test User",
        status="active",
    )

    # Should be able to modify fields (dataclasses are mutable by default)
    user.name = "Updated Name"
    assert user.name == "Updated Name"
