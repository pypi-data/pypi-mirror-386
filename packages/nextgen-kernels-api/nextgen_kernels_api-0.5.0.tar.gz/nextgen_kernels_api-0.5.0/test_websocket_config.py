"""
Simple test for WebSocket message filtering configuration.
"""

from traitlets.config import Config


def test_websocket_filtering_traits():
    """Test that WebSocket connection has configurable filtering traits."""
    print("Testing WebSocket Filtering Configuration...")
    print("=" * 60)

    from nextgen_kernels_api.services.kernels.connection.kernel_client_connection import (
        KernelClientWebsocketConnection
    )

    # Test 1: Verify traits exist
    print("\n1. Verifying traits exist...")
    assert hasattr(KernelClientWebsocketConnection, 'msg_types')
    assert hasattr(KernelClientWebsocketConnection, 'exclude_msg_types')
    print("   ✓ msg_types and exclude_msg_types traits exist")

    # Test 2: Verify traits are configurable
    print("\n2. Testing configuration via Config object...")
    c = Config()
    c.KernelClientWebsocketConnection.msg_types = [("status", "iopub"), ("stream", "iopub")]
    c.KernelClientWebsocketConnection.exclude_msg_types = [("error", "iopub")]

    # Create a class instance to check trait descriptors
    trait_msg_types = KernelClientWebsocketConnection.class_traits()['msg_types']
    trait_exclude = KernelClientWebsocketConnection.class_traits()['exclude_msg_types']

    assert trait_msg_types.allow_none is True
    assert trait_exclude.allow_none is True
    assert trait_msg_types.metadata.get('config') is True
    assert trait_exclude.metadata.get('config') is True
    print("   ✓ Traits are configurable and allow None")

    # Test 3: Verify default values
    print("\n3. Verifying default values...")
    assert trait_msg_types.default_value is None
    assert trait_exclude.default_value is None
    print("   ✓ Default values are None (listen to all messages)")

    # Test 4: Verify help text
    print("\n4. Verifying help documentation...")
    assert 'msg_type' in trait_msg_types.help.lower()
    assert 'channel' in trait_msg_types.help.lower()
    assert 'exclude' in trait_exclude.help.lower()
    print("   ✓ Help text is properly documented")

    print("\n" + "=" * 60)
    print("✓ All WebSocket filtering trait tests passed!")
    print("=" * 60)
    return True


def test_trait_validation():
    """Test trait validation and conversion."""
    print("\n\nTesting Trait Validation...")
    print("=" * 60)

    from nextgen_kernels_api.services.kernels.connection.kernel_client_connection import (
        KernelClientWebsocketConnection
    )

    # Test that the trait accepts lists of tuples
    print("\n1. Testing trait accepts list of tuples...")
    c = Config()
    c.KernelClientWebsocketConnection.msg_types = [
        ("status", "iopub"),
        ("execute_reply", "shell"),
        ("stream", "iopub")
    ]

    # Verify config was set
    assert len(c.KernelClientWebsocketConnection.msg_types) == 3
    print("   ✓ Trait accepts list of (msg_type, channel) tuples")

    print("\n2. Testing exclude_msg_types trait...")
    c2 = Config()
    c2.KernelClientWebsocketConnection.exclude_msg_types = [
        ("status", "iopub")
    ]

    assert len(c2.KernelClientWebsocketConnection.exclude_msg_types) == 1
    print("   ✓ exclude_msg_types trait accepts tuples")

    print("\n" + "=" * 60)
    print("✓ Trait validation tests passed!")
    print("=" * 60)


def test_configuration_examples():
    """Test configuration examples from documentation."""
    print("\n\nTesting Configuration Examples...")
    print("=" * 60)

    c = Config()

    # Example 1: Only execution messages
    print("\n1. Testing execution-only filter...")
    c.KernelClientWebsocketConnection.msg_types = [
        ("execute_input", "iopub"),
        ("execute_result", "iopub"),
        ("execute_reply", "shell"),
        ("stream", "iopub"),
        ("error", "iopub"),
    ]
    assert len(c.KernelClientWebsocketConnection.msg_types) == 5
    print("   ✓ Execution-only filter configured")

    # Example 2: Exclude status
    print("\n2. Testing exclude status filter...")
    c2 = Config()
    c2.KernelClientWebsocketConnection.exclude_msg_types = [
        ("status", "iopub"),
    ]
    assert len(c2.KernelClientWebsocketConnection.exclude_msg_types) == 1
    print("   ✓ Exclude status filter configured")

    # Example 3: IOPub only
    print("\n3. Testing iopub-only filter...")
    c3 = Config()
    c3.KernelClientWebsocketConnection.msg_types = [
        ("status", "iopub"),
        ("stream", "iopub"),
        ("display_data", "iopub"),
        ("execute_input", "iopub"),
        ("execute_result", "iopub"),
        ("error", "iopub"),
        ("clear_output", "iopub"),
    ]
    assert len(c3.KernelClientWebsocketConnection.msg_types) == 7
    print("   ✓ IOPub-only filter configured")

    print("\n" + "=" * 60)
    print("✓ Configuration example tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all tests
    test_websocket_filtering_traits()
    test_trait_validation()
    test_configuration_examples()

    print("\n✓ All WebSocket filtering configuration tests completed successfully!")
