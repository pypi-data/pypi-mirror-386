"""
Test configurable WebSocket message filtering.
"""

import asyncio
from unittest.mock import MagicMock, patch


def test_websocket_filtering_traits():
    """Test that WebSocket connection has configurable filtering traits."""
    print("Testing WebSocket Filtering Configuration...")
    print("=" * 60)

    from nextgen_kernels_api.services.kernels.connection.kernel_client_connection import (
        KernelClientWebsocketConnection
    )

    # Test 1: Default values
    print("\n1. Testing default trait values...")
    conn = KernelClientWebsocketConnection(
        websocket_handler=MagicMock(),
        kernel_manager=MagicMock()
    )
    assert conn.msg_types is None, "msg_types should default to None"
    assert conn.exclude_msg_types is None, "exclude_msg_types should default to None"
    print("   ✓ Default values are None (all messages)")

    # Test 2: Configure msg_types
    print("\n2. Testing msg_types configuration...")
    conn = KernelClientWebsocketConnection(
        websocket_handler=MagicMock(),
        kernel_manager=MagicMock(),
        msg_types=[("status", "iopub"), ("execute_reply", "shell")]
    )
    assert len(conn.msg_types) == 2
    assert ("status", "iopub") in conn.msg_types
    assert ("execute_reply", "shell") in conn.msg_types
    print("   ✓ msg_types configured correctly")

    # Test 3: Configure exclude_msg_types
    print("\n3. Testing exclude_msg_types configuration...")
    conn = KernelClientWebsocketConnection(
        websocket_handler=MagicMock(),
        kernel_manager=MagicMock(),
        exclude_msg_types=[("status", "iopub")]
    )
    assert len(conn.exclude_msg_types) == 1
    assert ("status", "iopub") in conn.exclude_msg_types
    print("   ✓ exclude_msg_types configured correctly")

    # Test 4: Verify traits are configurable via traitlets config
    print("\n4. Testing configuration via traitlets config...")
    from traitlets.config import Config
    c = Config()
    c.KernelClientWebsocketConnection.msg_types = [("stream", "iopub")]

    conn = KernelClientWebsocketConnection(
        websocket_handler=MagicMock(),
        kernel_manager=MagicMock(),
        config=c
    )
    assert len(conn.msg_types) == 1
    assert ("stream", "iopub") in conn.msg_types
    print("   ✓ Configuration via Config object works")

    print("\n" + "=" * 60)
    print("✓ All WebSocket filtering trait tests passed!")
    print("=" * 60)


async def test_websocket_listener_filtering():
    """Test that WebSocket uses filtering when adding listeners."""
    print("\n\nTesting WebSocket Listener Integration...")
    print("=" * 60)

    from nextgen_kernels_api.services.kernels.connection.kernel_client_connection import (
        KernelClientWebsocketConnection
    )

    # Mock the kernel client and manager
    mock_client = MagicMock()
    mock_client.add_listener = MagicMock()
    mock_client.broadcast_state = AsyncMock()

    mock_client_manager = MagicMock()
    mock_client_manager.has_client = MagicMock(return_value=False)
    mock_client_manager.create_client = MagicMock(return_value=mock_client)

    # Test 1: Default (no filtering)
    print("\n1. Testing default behavior (no filtering)...")
    with patch.object(KernelClientWebsocketConnection, '_get_client_manager', return_value=mock_client_manager):
        conn = KernelClientWebsocketConnection(
            websocket_handler=MagicMock(),
            kernel_manager=MagicMock()
        )
        conn.kernel_id = "test-kernel-1"

        await conn.connect()

        # Verify add_listener was called without filters
        mock_client.add_listener.assert_called_once()
        call_kwargs = mock_client.add_listener.call_args.kwargs
        assert 'msg_types' not in call_kwargs
        assert 'exclude_msg_types' not in call_kwargs
        print("   ✓ Listener added without filters (default)")

    # Reset mock
    mock_client.add_listener.reset_mock()

    # Test 2: With msg_types filter
    print("\n2. Testing with msg_types filter...")
    with patch.object(KernelClientWebsocketConnection, '_get_client_manager', return_value=mock_client_manager):
        conn = KernelClientWebsocketConnection(
            websocket_handler=MagicMock(),
            kernel_manager=MagicMock(),
            msg_types=[("status", "iopub"), ("stream", "iopub")]
        )
        conn.kernel_id = "test-kernel-2"

        await conn.connect()

        # Verify add_listener was called with msg_types
        mock_client.add_listener.assert_called_once()
        call_kwargs = mock_client.add_listener.call_args.kwargs
        assert 'msg_types' in call_kwargs
        assert len(call_kwargs['msg_types']) == 2
        assert ("status", "iopub") in call_kwargs['msg_types']
        assert ("stream", "iopub") in call_kwargs['msg_types']
        print("   ✓ Listener added with msg_types filter")

    # Reset mock
    mock_client.add_listener.reset_mock()

    # Test 3: With exclude_msg_types filter
    print("\n3. Testing with exclude_msg_types filter...")
    with patch.object(KernelClientWebsocketConnection, '_get_client_manager', return_value=mock_client_manager):
        conn = KernelClientWebsocketConnection(
            websocket_handler=MagicMock(),
            kernel_manager=MagicMock(),
            exclude_msg_types=[("status", "iopub")]
        )
        conn.kernel_id = "test-kernel-3"

        await conn.connect()

        # Verify add_listener was called with exclude_msg_types
        mock_client.add_listener.assert_called_once()
        call_kwargs = mock_client.add_listener.call_args.kwargs
        assert 'exclude_msg_types' in call_kwargs
        assert len(call_kwargs['exclude_msg_types']) == 1
        assert ("status", "iopub") in call_kwargs['exclude_msg_types']
        print("   ✓ Listener added with exclude_msg_types filter")

    print("\n" + "=" * 60)
    print("✓ WebSocket listener integration tests passed!")
    print("=" * 60)


class AsyncMock(MagicMock):
    """Mock for async functions."""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


if __name__ == "__main__":
    # Run trait tests
    test_websocket_filtering_traits()

    # Run integration tests
    asyncio.run(test_websocket_listener_filtering())

    print("\n✓ All WebSocket filtering tests completed successfully!")
