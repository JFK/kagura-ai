#!/usr/bin/env python3
"""OAuth2 Manual Testing Script

This script provides interactive testing of OAuth2 authentication functionality.
It requires actual Google OAuth2 credentials (client_secrets.json).

Prerequisites:
    1. Google Cloud Project with Generative Language API enabled
    2. OAuth 2.0 Client ID (Desktop application)
    3. client_secrets.json saved to ~/.kagura/

Usage:
    python scripts/test_oauth2.py [--test-name]

Available Tests:
    --all           Run all tests
    --login         Test OAuth2 login flow
    --status        Test authentication status
    --token         Test token retrieval
    --refresh       Test token refresh
    --logout        Test logout
    --llm           Test LLM call with OAuth2
    --cli           Test CLI commands
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_success(message: str):
    """Print success message"""
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"✗ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ {message}")


def check_client_secrets() -> bool:
    """Check if client_secrets.json exists"""
    client_secrets = Path.home() / ".kagura" / "client_secrets.json"
    if not client_secrets.exists():
        print_error(f"client_secrets.json not found at: {client_secrets}")
        print_info("Please follow these steps:")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Create OAuth 2.0 Client ID (Desktop application)")
        print("  3. Download JSON and save as: ~/.kagura/client_secrets.json")
        return False
    print_success(f"client_secrets.json found at: {client_secrets}")
    return True


def test_login():
    """Test OAuth2 login flow"""
    print_section("Test 1: OAuth2 Login Flow")

    if not check_client_secrets():
        return False

    try:
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        # Check if already authenticated
        if auth.is_authenticated():
            print_info("Already authenticated. Logout first? (y/n)")
            response = input("> ").strip().lower()
            if response == "y":
                auth.logout()
                print_success("Logged out successfully")

        print_info("Starting OAuth2 login flow...")
        print_info("A browser window will open for authentication")

        auth.login()

        print_success("Login successful!")
        print_success(f"Credentials saved to: {auth.creds_file}")

        return True

    except ImportError:
        print_error("OAuth2 dependencies not installed")
        print_info("Install with: pip install kagura-ai[oauth]")
        return False
    except Exception as e:
        print_error(f"Login failed: {e}")
        return False


def test_status():
    """Test authentication status check"""
    print_section("Test 2: Authentication Status")

    try:
        from kagura.auth import OAuth2Manager

        auth = OAuth2Manager(provider="google")

        if auth.is_authenticated():
            print_success("Authenticated with google")

            # Get credentials to check expiry
            try:
                creds = auth.get_credentials()
                if hasattr(creds, "expiry") and creds.expiry:
                    print_info(f"Token expires: {creds.expiry}")
            except Exception as e:
                print_error(f"Failed to get credentials: {e}")
        else:
            print_error("Not authenticated with google")
            print_info("Run: python scripts/test_oauth2.py --login")

        return True

    except Exception as e:
        print_error(f"Status check failed: {e}")
        return False


def test_token():
    """Test token retrieval"""
    print_section("Test 3: Token Retrieval")

    try:
        from kagura.auth import OAuth2Manager
        from kagura.auth.exceptions import NotAuthenticatedError

        auth = OAuth2Manager(provider="google")

        try:
            token = auth.get_token()
            print_success("Token retrieved successfully")
            print_info(f"Token (first 20 chars): {token[:20]}...")
            print_info(f"Token length: {len(token)} characters")
            return True

        except NotAuthenticatedError:
            print_error("Not authenticated")
            print_info("Run: python scripts/test_oauth2.py --login")
            return False

    except Exception as e:
        print_error(f"Token retrieval failed: {e}")
        return False


def test_refresh():
    """Test token refresh"""
    print_section("Test 4: Token Refresh")

    try:
        from kagura.auth import OAuth2Manager
        from kagura.auth.exceptions import NotAuthenticatedError

        auth = OAuth2Manager(provider="google")

        try:
            creds = auth.get_credentials()

            # Check if token needs refresh
            if hasattr(creds, "expired") and creds.expired:
                print_info("Token is expired, attempting refresh...")
                creds = auth.get_credentials()  # This will trigger refresh
                print_success("Token refreshed successfully")
            else:
                print_info("Token is still valid (no refresh needed)")
                if hasattr(creds, "expiry") and creds.expiry:
                    print_info(f"Token expires: {creds.expiry}")

            return True

        except NotAuthenticatedError:
            print_error("Not authenticated")
            print_info("Run: python scripts/test_oauth2.py --login")
            return False

    except Exception as e:
        print_error(f"Token refresh test failed: {e}")
        return False


def test_logout():
    """Test logout"""
    print_section("Test 5: Logout")

    try:
        from kagura.auth import OAuth2Manager
        from kagura.auth.exceptions import NotAuthenticatedError

        auth = OAuth2Manager(provider="google")

        if not auth.is_authenticated():
            print_error("Not authenticated (nothing to logout)")
            return False

        print_info("Logging out...")
        auth.logout()

        print_success("Logged out successfully")

        # Verify logout
        if not auth.is_authenticated():
            print_success("Verified: No longer authenticated")
            return True
        else:
            print_error("Logout verification failed: Still authenticated")
            return False

    except Exception as e:
        print_error(f"Logout failed: {e}")
        return False


async def test_llm():
    """Test LLM call with OAuth2"""
    print_section("Test 6: LLM Call with OAuth2")

    try:
        from kagura.core.llm import LLMConfig, call_llm
        from kagura.auth import OAuth2Manager
        from kagura.auth.exceptions import NotAuthenticatedError

        # Check authentication
        auth = OAuth2Manager(provider="google")
        if not auth.is_authenticated():
            print_error("Not authenticated")
            print_info("Run: python scripts/test_oauth2.py --login")
            return False

        print_success("Authentication verified")

        # Create OAuth2 config
        config = LLMConfig(
            model="gemini/gemini-1.5-flash",
            auth_type="oauth2",
            oauth_provider="google",
            temperature=0.7,
            max_tokens=50
        )

        print_info("Calling Gemini API with OAuth2...")
        print_info("Prompt: 'What is 2+2? Answer in one word.'")

        # Call LLM
        response = await call_llm("What is 2+2? Answer in one word.", config)

        print_success("LLM call successful!")
        print_info(f"Response: {response}")

        return True

    except NotAuthenticatedError:
        print_error("Not authenticated")
        print_info("Run: python scripts/test_oauth2.py --login")
        return False
    except Exception as e:
        print_error(f"LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli():
    """Test CLI commands"""
    print_section("Test 7: CLI Commands")

    import subprocess

    print_info("Testing: kagura auth status --provider google")

    try:
        result = subprocess.run(
            ["kagura", "auth", "status", "--provider", "google"],
            capture_output=True,
            text=True
        )

        print(result.stdout)

        if result.returncode == 0:
            print_success("CLI status command works")
            return True
        else:
            print_error(f"CLI status command failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print_error("kagura command not found")
        print_info("Install kagura first: pip install -e .")
        return False
    except Exception as e:
        print_error(f"CLI test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print_section("Running All OAuth2 Tests")

    results = {
        "Login Flow": test_login(),
        "Status Check": test_status(),
        "Token Retrieval": test_token(),
        "Token Refresh": test_refresh(),
        "LLM Call": asyncio.run(test_llm()),
        "CLI Commands": test_cli(),
        # Note: Logout is not included in --all to preserve authentication
    }

    # Print summary
    print_section("Test Summary")

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    return all(results.values())


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("  Kagura AI - OAuth2 Manual Testing Script")
    print("=" * 60)

    if len(sys.argv) < 2:
        print(__doc__)
        return

    test_arg = sys.argv[1]

    test_map = {
        "--all": run_all_tests,
        "--login": test_login,
        "--status": test_status,
        "--token": test_token,
        "--refresh": test_refresh,
        "--logout": test_logout,
        "--llm": lambda: asyncio.run(test_llm()),
        "--cli": test_cli,
    }

    if test_arg not in test_map:
        print_error(f"Unknown test: {test_arg}")
        print(__doc__)
        sys.exit(1)

    # Run the test
    success = test_map[test_arg]()

    if success:
        print_section("✓ Test Completed Successfully")
        sys.exit(0)
    else:
        print_section("✗ Test Failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
