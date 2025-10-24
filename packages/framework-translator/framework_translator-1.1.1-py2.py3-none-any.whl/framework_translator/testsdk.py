import framework_translator.sdk as sdk

def test_sdk():
    print("=== Testing Framework Translator SDK ===\n")
    
    # Test authentication status
    print("1. Testing authentication status...")
    logged_in = sdk.is_logged_in()
    print(f"   Logged in: {logged_in}\n")
    
    # Test getting supported info
    print("2. Testing framework information...")
    languages = sdk.get_supported_languages()
    print(f"   Supported languages: {languages}")
    
    groups = sdk.get_supported_groups()
    print(f"   Supported groups: {groups}")
    
    frameworks = sdk.get_supported_frameworks("ml")
    print(f"   ML frameworks: {frameworks}")
    
    all_frameworks = sdk.get_supported_frameworks()
    print(f"   All frameworks: {all_frameworks}\n")
    
    # Test framework info
    print("3. Testing individual framework info...")
    try:
        pytorch_info = sdk.get_framework_info("pytorch")
        print(f"   PyTorch info: {pytorch_info}")
    except Exception as e:
        print(f"   Error getting PyTorch info: {e}")
    
    try:
        tf_info = sdk.get_framework_info("tensorflow")
        print(f"   TensorFlow info: {tf_info}")
    except Exception as e:
        print(f"   Error getting TensorFlow info: {e}\n")
    
    # Test login (will fail without credentials but we can see the error)
    print("4. Testing login (should fail without real credentials)...")
    try:
        login_result = sdk.login("test@example.com", "fake_password")
        print(f"   Login result: {login_result}")
    except Exception as e:
        print(f"   Login failed as expected: {e}\n")
    
    # Test translation (should fail - not logged in)
    print("5. Testing translation (should fail - not logged in)...")
    try:
        result = sdk.translate("import numpy as np", "pytorch")
        print(f"   Translation result: {result}")
    except Exception as e:
        print(f"   Translation failed as expected: {e}\n")
    
    # Test history (should fail - not logged in)
    print("6. Testing history (should fail - not logged in)...")
    try:
        history = sdk.get_history()
        print(f"   History result: {history}")
    except Exception as e:
        print(f"   History failed as expected: {e}\n")
    
    # Test with invalid framework
    print("7. Testing invalid framework...")
    try:
        invalid_info = sdk.get_framework_info("nonexistent")
        print(f"   Invalid framework info: {invalid_info}")
    except Exception as e:
        print(f"   Invalid framework failed as expected: {e}\n")
    
    print("=== SDK Test Complete ===")

    # test logout
    print("8. Testing logout...")
    try:
        logout_result = sdk.logout()
        print(f"   Logout result: {logout_result}")
    except Exception as e:
        print(f"   Logout failed as expected: {e}\n")

if __name__ == "__main__":
    test_sdk()

