"""
Python SDK for Framework Translator

This module provides programmatic access to the Framework Translator functionality,
allowing users to integrate translation capabilities directly into their Python code.
"""

from typing import Optional
from .config import is_logged_in_session, set_session_logged_in
from .framework import registry, Framework
from .api_client import api_client
import requests


def is_logged_in() -> bool:
    """
    Check if user is logged into the backend service for this session.
    
    Returns:
        bool: True if logged in, False otherwise
    """
    return is_logged_in_session()


def login(username: str, password: str) -> bool:
    """
    Login to the backend service using username and password.
    
    Args:
        username (str): User's username/email
        password (str): User's password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        api_client.login(username, password)
        set_session_logged_in(True)
        return True
    except requests.RequestException:
        return False


def logout() -> None:
    """
    Logout from the backend service.
    
    Clears the stored authentication token and session state.
    """
    api_client.logout()
    set_session_logged_in(False)


def translate(
    code: str,
    target_framework: str,
    source_framework: Optional[str] = None
) -> str:
    """
    Translate code from one framework to another.
    
    Args:
        code (str): The source code to translate
        target_framework (str): Name of the target framework (e.g., 'pytorch', 'tensorflow')
        source_framework (Optional[str]): Name of the source framework (if None, model will infer)
        
    Returns:
        str: The translated code
        
    Raises:
        RuntimeError: If user is not logged in
        ValueError: If target framework is not supported
        Exception: If translation fails
    """
    if not is_logged_in():
        raise RuntimeError("Not logged in. Run 'ft login' or call login() first.")
    
    # Get framework instance to validate
    target_framework_obj = registry.get_framework_by_name(target_framework)
    if not target_framework_obj:
        supported = registry.get_supported_frameworks("ml")
        raise ValueError(f"Unsupported target framework: {target_framework}. Supported: {supported}")
    
    # Use backend API instead of direct translation
    return api_client.generate_code(
        code=code,
        target_framework=target_framework,
        source_framework=source_framework
    )


def get_supported_frameworks(group: Optional[str] = None) -> list[str]:
    """
    Get list of supported frameworks.
    
    Args:
        group (Optional[str]): Framework group to filter by (e.g., 'ml')
        
    Returns:
        list[str]: List of supported framework names
    """
    if group:
        return registry.get_supported_frameworks(group)
    else:
        # Return all frameworks
        all_frameworks = []
        for group_name in registry.get_supported_groups("python"):  # Assuming python for now
            all_frameworks.extend(registry.get_supported_frameworks(group_name))
        return sorted(list(set(all_frameworks)))


def get_supported_groups() -> list[str]:
    """
    Get list of supported framework groups.
    
    Returns:
        list[str]: List of supported groups
    """
    return registry.get_supported_groups("python")  # Assuming python for now


def get_supported_languages() -> list[str]:
    """
    Get list of supported programming languages.
    
    Returns:
        list[str]: List of supported languages
    """
    return registry.get_supported_languages()


def get_framework_info(framework_name: str) -> dict:
    """
    Get information about a specific framework.
    
    Args:
        framework_name (str): Name of the framework
        
    Returns:
        dict: Framework information including name, language, group, model, and temperature
        
    Raises:
        ValueError: If framework is not found
    """
    framework = registry.get_framework_by_name(framework_name)
    if not framework:
        raise ValueError(f"Framework '{framework_name}' not found")
    
    return {
        "name": framework.name,
        "language": framework.language,
        "group": framework.group,
        "model": framework.get_model(),
        "temperature": framework.get_temperature()
    }


def get_history(page: int = 1, per_page: int = 50) -> list[dict]:
    """
    Get translation history for the current user.
    
    Args:
        page (int): Page number for pagination (default: 1)
        per_page (int): Number of translations per page (default: 50)
        
    Returns:
        list[dict]: List of translation records ordered by most recent first
        
    Raises:
        RuntimeError: If user is not logged in
        Exception: If request fails
    """
    if not is_logged_in():
        raise RuntimeError("Not logged in. Run 'ft login' or call login() first.")
    
    response = api_client.get_translations(page=page, per_page=per_page)
    return response.get("translations", [])