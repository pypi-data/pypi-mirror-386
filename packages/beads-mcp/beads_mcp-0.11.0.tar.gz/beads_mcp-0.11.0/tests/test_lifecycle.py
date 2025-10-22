"""Tests for MCP server lifecycle management."""

import asyncio
import signal
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_cleanup_handlers_registered():
    """Test that cleanup handlers are registered on server import."""
    # Server is already imported, so handlers are already registered
    # We can verify the cleanup function and signal handler exist
    import beads_mcp.server as server
    
    # Verify cleanup function exists and is callable
    assert hasattr(server, 'cleanup')
    assert callable(server.cleanup)
    
    # Verify signal handler exists and is callable
    assert hasattr(server, 'signal_handler')
    assert callable(server.signal_handler)
    
    # Verify global state exists
    assert hasattr(server, '_daemon_clients')
    assert hasattr(server, '_cleanup_done')


def test_cleanup_function_safe_to_call_multiple_times():
    """Test that cleanup function can be called multiple times safely."""
    from beads_mcp.server import cleanup, _daemon_clients
    
    # Mock client
    mock_client = MagicMock()
    _daemon_clients.append(mock_client)
    
    # Call cleanup multiple times
    cleanup()
    cleanup()
    cleanup()
    
    # Client should only be closed once
    assert mock_client.close.call_count == 1
    assert len(_daemon_clients) == 0


def test_cleanup_handles_client_errors_gracefully():
    """Test that cleanup continues even if a client raises an error."""
    from beads_mcp.server import cleanup, _daemon_clients
    
    # Reset state
    import beads_mcp.server as server
    server._cleanup_done = False
    
    # Create mock clients - one that raises, one that doesn't
    failing_client = MagicMock()
    failing_client.close.side_effect = Exception("Connection failed")
    
    good_client = MagicMock()
    
    _daemon_clients.clear()
    _daemon_clients.extend([failing_client, good_client])
    
    # Cleanup should not raise
    cleanup()
    
    # Both clients should have been attempted
    assert failing_client.close.called
    assert good_client.close.called
    assert len(_daemon_clients) == 0


def test_signal_handler_calls_cleanup():
    """Test that signal handler calls cleanup and exits."""
    from beads_mcp.server import signal_handler
    
    with patch('beads_mcp.server.cleanup') as mock_cleanup:
        with patch('sys.exit') as mock_exit:
            # Call signal handler
            signal_handler(signal.SIGTERM, None)
            
            # Verify cleanup was called
            assert mock_cleanup.called
            
            # Verify exit was called
            assert mock_exit.called


@pytest.mark.asyncio
async def test_client_registration_on_first_use():
    """Test that client is registered for cleanup on first use."""
    from beads_mcp.tools import _get_client
    from beads_mcp.server import _daemon_clients
    
    # Clear existing clients
    _daemon_clients.clear()
    
    # Reset global client state
    import beads_mcp.tools as tools
    tools._client = None
    tools._client_registered = False
    
    # Get client (will create and register it)
    with patch('beads_mcp.bd_client.create_bd_client') as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        client = await _get_client()
        
        # Client should be in the cleanup list
        assert client in _daemon_clients


def test_cleanup_logs_lifecycle_events(caplog):
    """Test that cleanup logs informative messages."""
    import logging
    from beads_mcp.server import cleanup
    
    # Reset state
    import beads_mcp.server as server
    server._cleanup_done = False
    server._daemon_clients.clear()
    
    with caplog.at_level(logging.INFO):
        cleanup()
    
    # Check for lifecycle log messages
    log_messages = [record.message for record in caplog.records]
    assert any("Cleaning up" in msg for msg in log_messages)
    assert any("Cleanup complete" in msg for msg in log_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
