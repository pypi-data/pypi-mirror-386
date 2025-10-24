"""Demonstration script showing the event loop bug in CredentialManager."""

from realtimex_toolkit import CredentialManager


def main():
    """Test that demonstrates the bug: second call fails due to event loop mismatch."""
    print("Creating CredentialManager...")
    manager = CredentialManager(api_key="test-key")

    print("\nAttempting first get() call...")
    try:
        result1 = manager.get("test")
        print(f"✓ First call succeeded: {result1.credential_id}")
    except Exception as e:
        print(f"✗ First call failed: {type(e).__name__}: {e}")

    print(
        "\nAttempting second get() call with force_refresh=True (this should fail with current implementation)..."
    )
    try:
        result2 = manager.get("test", force_refresh=True)
        print(f"✓ Second call succeeded: {result2.credential_id}")
    except Exception as e:
        print(f"✗ Second call failed: {type(e).__name__}: {e}")

    print("\nAttempting close()...")
    try:
        manager.close()
        print("✓ Close succeeded")
    except Exception as e:
        print(f"✗ Close failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
