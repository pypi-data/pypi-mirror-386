import requests
import hashlib
import time
from typing import Optional, Dict, Any
from .config import get_backend_url, load_config, save_config

class APIClient:
    """Client for communicating with the backend API"""
    
    def __init__(self):
        self.base_url = get_backend_url()
        self.session = requests.Session()
    
    def _get_stored_credentials(self) -> Optional[Dict[str, str]]:
        """Get stored login credentials"""
        cfg = load_config()
        username = cfg.get("username")
        password = cfg.get("password")
        if username and password:
            return {"username": username, "password": password}
        return None
    
    def _save_credentials(self, username: str, password: str) -> None:
        """Save login credentials to config"""
        cfg = load_config()
        cfg["username"] = username
        cfg["password"] = password
        save_config(cfg)
    
    def _clear_credentials(self) -> None:
        """Clear stored credentials"""
        cfg = load_config()
        cfg.pop("username", None)
        cfg.pop("password", None)
        save_config(cfg)
    
    def _get_fresh_token(self) -> str:
        """Get a fresh access token using stored credentials"""
        credentials = self._get_stored_credentials()
        if not credentials:
            raise requests.RequestException("No stored credentials found. Please login first.")
        
        form_data = {
            "username": credentials["username"],
            "password": credentials["password"]
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if not response.ok:
            # Clear invalid credentials
            self._clear_credentials()
            try:
                error_body = response.json()
                if error_body and "detail" in error_body:
                    detail = error_body["detail"]
                    error_msg = detail if isinstance(detail, str) else "Authentication failed"
                    raise requests.RequestException(error_msg)
            except (ValueError, KeyError):
                pass
            raise requests.RequestException("Authentication failed. Please login again.")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise requests.RequestException("No access token received")
        
        return access_token
    
    def is_authenticated(self) -> bool:
        """Check if user has stored credentials"""
        return self._get_stored_credentials() is not None
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login to the backend with username and password
        
        Args:
            username (str): User's username/email
            password (str): User's password
            
        Returns:
            dict: Login response containing token
            
        Raises:
            requests.RequestException: If login fails
        """
        # Test login with provided credentials
        form_data = {
            "username": username,
            "password": password
        }
        
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )
        
        if not response.ok:
            try:
                error_body = response.json()
                if error_body and "detail" in error_body:
                    detail = error_body["detail"]
                    error_msg = detail if isinstance(detail, str) else "Login failed"
                    raise requests.RequestException(error_msg)
            except (ValueError, KeyError):
                pass
            raise requests.RequestException("Failed to login")
        
        # If login successful, save credentials for future use
        self._save_credentials(username, password)
        
        return response.json()
    
    def logout(self) -> None:
        """Clear stored credentials"""
        self._clear_credentials()
    
    def create_translation(
        self,
        source_code: str,
        target_framework: str,
        translated_code: str,
        source_framework: Optional[str] = None,
        model_used: Optional[str] = None,
        temperature: Optional[float] = None,
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a translation record in the database
        
        Args:
            source_code (str): Original source code
            target_framework (str): Target framework name
            translated_code (str): Generated/translated code
            source_framework (Optional[str]): Source framework name
            model_used (Optional[str]): Model used for generation
            temperature (Optional[float]): Temperature used for generation
            duration_ms (Optional[int]): Duration of generation in milliseconds
            
        Returns:
            dict: TranslationResponse object
            
        Raises:
            requests.RequestException: If creation fails
        """
        # Get fresh token for this request
        token = self._get_fresh_token()
        
        payload = {
            "source_code": source_code,
            "source_lang": source_framework,
            "target_lang": target_framework,
            "translated_code": translated_code,
            "model_used": model_used,
            "temperature": temperature,
            "duration_ms": duration_ms,
            "status": "completed"
        }
        
        response = requests.post(
            f"{self.base_url}/translations/addTranslation",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()

    def generate_code(
        self,
        code: str,
        target_framework: str,
        source_framework: Optional[str] = None
    ) -> str:
        """
        Generate code using the backend API
        
        Args:
            code (str): Source code to translate
            target_framework (str): Target framework name
            source_framework (Optional[str]): Source framework name
            
        Returns:
            str: Generated code
            
        Raises:
            requests.RequestException: If generation fails
        """
        # Check if we have credentials
        if not self.is_authenticated():
            raise requests.RequestException("Not authenticated. Please login first.")
        
        # Get fresh token for this request
        token = self._get_fresh_token()

        # Track generation time
        start_time = time.time()
        
        payload = {
            "code": code,
            "target_framework": target_framework,
            "prompt_cache_key": "framework_translator_cache_key",
        }
        if source_framework:
            payload["source_framework"] = source_framework
            
        response = requests.post(
            f"{self.base_url}/generate/",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=payload,
            timeout=120,
        )
        
        response.raise_for_status()
        
        # Calculate generation time
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        generated_code = response.json()["generated_code"]
        model = response.json()["model"]
        temperature = response.json()["temperature"]

        # Save translation to database
        try:
            self.create_translation(
                source_code=code,
                target_framework=target_framework,
                translated_code=generated_code,
                source_framework=source_framework,
                model_used=model,
                temperature=temperature,
                duration_ms=duration_ms
            )
        except Exception as e:
            # Don't fail the main operation if logging fails
            print(f"Warning: Failed to save translation to database: {e}")
        
        return generated_code

    def get_translations(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get user's translation history
        
        Args:
            page (int): Page number for pagination
            per_page (int): Number of translations per page
            
        Returns:
            dict: Translation list response with translations, total, page, per_page
            
        Raises:
            requests.RequestException: If request fails
        """
        # Check if we have credentials
        if not self.is_authenticated():
            raise requests.RequestException("Not authenticated. Please login first.")
        
        # Get fresh token for this request
        token = self._get_fresh_token()

        params = {
            "page": page,
            "per_page": per_page
        }
            
        response = requests.get(
            f"{self.base_url}/translations/",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params=params,
            timeout=30,
        )
        
        response.raise_for_status()
        return response.json()

api_client = APIClient()
