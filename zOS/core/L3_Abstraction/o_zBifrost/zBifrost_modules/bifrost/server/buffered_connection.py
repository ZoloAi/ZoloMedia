# zCLI/subsystems/zBifrost/zBifrost_modules/bifrost/server/buffered_connection.py
"""
Phase 1: Buffered WebSocket Connection with Backpressure Handling.

Wraps WebSocket connections with per-client queues to prevent slow clients
from blocking fast clients during broadcasts. Implements backpressure handling
by disconnecting clients that can't keep up with the message rate.

Key Features:
- Non-blocking sends (returns immediately)
- Per-client message queue (configurable max size)
- Background sender loop (drains queue asynchronously)
- Automatic disconnection on buffer overflow
- Graceful shutdown with queue draining

Usage:
    buffered_ws = BufferedConnection(ws, logger, max_queue=1000)
    await buffered_ws.send(message)  # Returns immediately
    # ... later ...
    await buffered_ws.close()  # Drains queue before closing
"""

from zOS import asyncio, json, Optional, Any
from websockets.server import WebSocketServerProtocol


class BufferedConnection:
    """
    Buffered WebSocket connection wrapper with backpressure handling.
    
    Prevents slow clients from blocking message delivery to fast clients
    by using a per-client queue and background sender task.
    
    Args:
        ws: WebSocket connection to wrap
        logger: Logger instance for debugging
        max_queue: Maximum queue size before disconnecting client (default: 1000)
        disconnect_on_full: Whether to disconnect on buffer overflow (default: True)
    """
    
    def __init__(
        self,
        ws: WebSocketServerProtocol,
        logger: Any,
        max_queue: int = 1000,
        disconnect_on_full: bool = True
    ):
        self.ws = ws
        self.logger = logger
        self.max_queue = max_queue
        self.disconnect_on_full = disconnect_on_full
        
        # Create bounded queue (maxsize enforces backpressure)
        self.queue = asyncio.Queue(maxsize=max_queue)
        self._running = True
        self._disconnected = False
        
        # Start background sender task
        self._sender_task = asyncio.create_task(self._sender_loop())
    
    async def send(self, message: str) -> bool:
        """
        Non-blocking send - enqueues message and returns immediately.
        
        Args:
            message: Message string to send
        
        Returns:
            True if message was queued, False if queue full or disconnected
        """
        if self._disconnected:
            return False
        
        try:
            # Non-blocking: raises QueueFull if queue is at capacity
            self.queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            # Client too slow - buffer overflow
            self.logger.warning(
                f"[BufferedConnection] Queue overflow ({self.max_queue} messages) - "
                f"slow client detected"
            )
            
            if self.disconnect_on_full:
                # Disconnect slow client to prevent memory exhaustion
                await self.disconnect("Buffer overflow - client too slow")
            
            return False
    
    async def _sender_loop(self):
        """
        Background task that drains the queue and sends messages.
        
        Runs continuously until close() is called, then drains remaining messages.
        """
        try:
            while self._running or not self.queue.empty():
                try:
                    # Wait for next message (with timeout to check _running flag)
                    message = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                    
                    # Send to actual WebSocket
                    await self.ws.send(message)
                    
                    # Mark task done
                    self.queue.task_done()
                
                except asyncio.TimeoutError:
                    # No message available - continue to check _running flag
                    continue
                
                except Exception as e:
                    # Send failed - connection likely closed
                    self.logger.debug(f"[BufferedConnection] Send failed: {e}")
                    await self.disconnect(f"Send error: {e}")
                    break
        
        finally:
            self.logger.debug("[BufferedConnection] Sender loop exited")
    
    async def disconnect(self, reason: str):
        """
        Disconnect the client with a reason.
        
        Args:
            reason: Reason for disconnection
        """
        if self._disconnected:
            return
        
        self._disconnected = True
        self._running = False
        
        try:
            # Send disconnect notification
            await self.ws.send(json.dumps({
                "event": "disconnect",
                "reason": reason
            }))
            await self.ws.close(code=1008, reason=reason)
        except Exception as e:
            self.logger.debug(f"[BufferedConnection] Error during disconnect: {e}")
    
    async def close(self):
        """
        Gracefully close the connection, draining remaining messages.
        
        Waits for queue to empty before closing the underlying WebSocket.
        """
        # Stop accepting new messages
        self._running = False
        
        # Wait for queue to drain (with timeout)
        try:
            await asyncio.wait_for(self.queue.join(), timeout=5.0)
        except asyncio.TimeoutError:
            self.logger.warning(
                f"[BufferedConnection] Drain timeout - "
                f"{self.queue.qsize()} messages dropped"
            )
        
        # Cancel sender task
        self._sender_task.cancel()
        try:
            await self._sender_task
        except asyncio.CancelledError:
            pass
        
        # Close underlying WebSocket
        if not self._disconnected:
            try:
                await self.ws.close()
            except Exception as e:
                self.logger.debug(f"[BufferedConnection] Error closing WebSocket: {e}")
    
    @property
    def remote_address(self):
        """Proxy remote_address from underlying WebSocket."""
        return self.ws.remote_address
    
    @property
    def open(self):
        """Check if connection is open."""
        return not self._disconnected and (
            getattr(self.ws, 'open', None) or 
            (not getattr(self.ws, 'closed', False))
        )
    
    @property
    def closed(self):
        """Check if connection is closed."""
        return self._disconnected or getattr(self.ws, 'closed', False)
    
    def __repr__(self):
        return f"<BufferedConnection ws={self.ws} queue={self.queue.qsize()}/{self.max_queue}>"


