#!/usr/bin/env python3
"""
Async Message Broker for Unified IPC System
Codex's implementation - High-performance asynchronous message processing
"""

import asyncio
import json
import time
from typing import Dict, Optional, Any, List, Callable, Set
from dataclasses import dataclass, field
from collections import deque
from asyncio import Queue, Task
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AsyncConfig:
    """Configuration for async broker"""
    max_connections: int = 1000
    max_queue_size: int = 10000
    batch_size: int = 100
    batch_timeout: float = 0.1  # 100ms
    connection_pool_size: int = 50
    backpressure_threshold: float = 0.8
    enable_batching: bool = True
    enable_pooling: bool = True


@dataclass
class AsyncMessage:
    """Async message wrapper"""
    id: str
    data: Dict
    timestamp: float
    retries: int = 0
    priority: int = 0
    callback: Optional[Callable] = None


class ConnectionPool:
    """Connection pooling for efficient resource management"""

    def __init__(self, size: int = 50):
        self.size = size
        self.available: Queue = Queue(maxsize=size)
        self.in_use: Set = set()
        self.lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Initialize connection pool"""
        if self._initialized:
            return

        for i in range(self.size):
            connection = self._create_connection(i)
            await self.available.put(connection)

        self._initialized = True
        logger.info(f"Connection pool initialized with {self.size} connections")

    def _create_connection(self, conn_id: int) -> Dict:
        """Create a new connection object"""
        return {
            'id': conn_id,
            'created': time.time(),
            'last_used': None,
            'request_count': 0
        }

    async def acquire(self) -> Dict:
        """Acquire a connection from pool"""
        if not self._initialized:
            await self.initialize()

        connection = await self.available.get()

        async with self.lock:
            self.in_use.add(connection['id'])
            connection['last_used'] = time.time()
            connection['request_count'] += 1

        return connection

    async def release(self, connection: Dict):
        """Release connection back to pool"""
        async with self.lock:
            if connection['id'] in self.in_use:
                self.in_use.remove(connection['id'])

        await self.available.put(connection)

    def get_stats(self) -> Dict:
        """Get pool statistics"""
        return {
            'total': self.size,
            'available': self.available.qsize(),
            'in_use': len(self.in_use)
        }


class MessageBatcher:
    """Batch message processing for efficiency"""

    def __init__(self, batch_size: int = 100, timeout: float = 0.1):
        self.batch_size = batch_size
        self.timeout = timeout
        self.pending: deque = deque()
        self.lock = asyncio.Lock()
        self.process_task: Optional[Task] = None

    async def add_message(self, message: AsyncMessage):
        """Add message to batch"""
        async with self.lock:
            self.pending.append(message)

            # Start processing if not already running
            if not self.process_task or self.process_task.done():
                self.process_task = asyncio.create_task(self._process_batch())

    async def _process_batch(self):
        """Process pending messages in batches"""
        await asyncio.sleep(self.timeout)  # Wait for more messages

        async with self.lock:
            if not self.pending:
                return

            # Get batch
            batch = []
            for _ in range(min(self.batch_size, len(self.pending))):
                batch.append(self.pending.popleft())

        # Process batch
        if batch:
            await self._execute_batch(batch)

    async def _execute_batch(self, batch: List[AsyncMessage]):
        """Execute batch of messages"""
        logger.info(f"Processing batch of {len(batch)} messages")

        # Group by type for efficient processing
        grouped = {}
        for msg in batch:
            msg_type = msg.data.get('type', 'unknown')
            if msg_type not in grouped:
                grouped[msg_type] = []
            grouped[msg_type].append(msg)

        # Process each group
        tasks = []
        for msg_type, messages in grouped.items():
            task = asyncio.create_task(self._process_group(msg_type, messages))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _process_group(self, msg_type: str, messages: List[AsyncMessage]):
        """Process a group of similar messages"""
        for msg in messages:
            if msg.callback:
                try:
                    await msg.callback(msg.data)
                except Exception as e:
                    logger.error(f"Error processing message {msg.id}: {e}")


class BackpressureManager:
    """Manage backpressure in message processing"""

    def __init__(self, threshold: float = 0.8, max_queue: int = 10000):
        self.threshold = threshold
        self.max_queue = max_queue
        self.current_load = 0
        self.dropped_count = 0
        self.lock = asyncio.Lock()

    async def check_pressure(self) -> bool:
        """Check if system is under pressure"""
        async with self.lock:
            return self.current_load / self.max_queue > self.threshold

    async def add_load(self, count: int = 1):
        """Add to current load"""
        async with self.lock:
            self.current_load += count

    async def reduce_load(self, count: int = 1):
        """Reduce current load"""
        async with self.lock:
            self.current_load = max(0, self.current_load - count)

    async def should_accept(self) -> bool:
        """Check if new message should be accepted"""
        if await self.check_pressure():
            async with self.lock:
                self.dropped_count += 1

            if self.dropped_count % 100 == 0:
                logger.warning(f"Backpressure: Dropped {self.dropped_count} messages")

            return False
        return True

    def get_stats(self) -> Dict:
        """Get backpressure statistics"""
        return {
            'current_load': self.current_load,
            'max_queue': self.max_queue,
            'utilization': f"{(self.current_load / self.max_queue) * 100:.1f}%",
            'dropped': self.dropped_count
        }


class AsyncMessageBroker:
    """Main async message broker with all optimizations"""

    def __init__(self, config: AsyncConfig = None):
        self.config = config or AsyncConfig()

        # Core components
        self.message_queue: Queue = Queue(maxsize=self.config.max_queue_size)
        self.connection_pool = ConnectionPool(self.config.connection_pool_size) if self.config.enable_pooling else None
        self.batcher = MessageBatcher(self.config.batch_size, self.config.batch_timeout) if self.config.enable_batching else None
        self.backpressure = BackpressureManager(self.config.backpressure_threshold, self.config.max_queue_size)

        # Processing state
        self.running = False
        self.workers: List[Task] = []
        self.handlers: Dict[str, Callable] = {}
        self.stats = {
            'messages_processed': 0,
            'messages_failed': 0,
            'avg_latency': 0
        }

        logger.info("Async Message Broker initialized")

    async def start(self, worker_count: int = 10):
        """Start the async broker"""
        self.running = True

        # Initialize connection pool
        if self.connection_pool:
            await self.connection_pool.initialize()

        # Start worker tasks
        for i in range(worker_count):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"Started {worker_count} async workers")

    async def stop(self):
        """Stop the async broker"""
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to complete
        await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("Async broker stopped")

    def register_handler(self, msg_type: str, handler: Callable):
        """Register message handler"""
        self.handlers[msg_type] = handler

    async def process_async(self, request: Dict, sync_handler: Callable) -> Dict:
        """Process request asynchronously (hook for main broker)"""
        # Check backpressure
        if not await self.backpressure.should_accept():
            return {'status': 'error', 'message': 'System under load, please retry'}

        # Create async message
        message = AsyncMessage(
            id=request.get('id', str(time.time())),
            data=request,
            timestamp=time.time(),
            priority=request.get('priority', 0)
        )

        # Add to queue
        try:
            await asyncio.wait_for(
                self.message_queue.put(message),
                timeout=1.0
            )

            await self.backpressure.add_load()

            # Return immediate acknowledgment
            return {
                'status': 'accepted',
                'message_id': message.id,
                'queue_size': self.message_queue.qsize()
            }

        except asyncio.TimeoutError:
            return {'status': 'error', 'message': 'Queue full, please retry'}

    async def _worker(self, worker_id: int):
        """Worker task for processing messages"""
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get message from queue
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                # Process message
                start_time = time.time()
                await self._process_message(message)
                latency = time.time() - start_time

                # Update stats
                self.stats['messages_processed'] += 1
                self.stats['avg_latency'] = (
                    self.stats['avg_latency'] * 0.9 + latency * 0.1
                )

                # Reduce backpressure
                await self.backpressure.reduce_load()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.stats['messages_failed'] += 1

        logger.info(f"Worker {worker_id} stopped")

    async def _process_message(self, message: AsyncMessage):
        """Process a single message"""
        msg_type = message.data.get('type')

        # Get handler
        handler = self.handlers.get(msg_type)
        if not handler:
            logger.warning(f"No handler for message type: {msg_type}")
            return

        # Get connection from pool
        connection = None
        if self.connection_pool:
            connection = await self.connection_pool.acquire()

        try:
            # Execute handler
            result = await self._execute_handler(handler, message.data, connection)

            # Execute callback if provided
            if message.callback:
                await message.callback(result)

        finally:
            # Release connection
            if connection and self.connection_pool:
                await self.connection_pool.release(connection)

    async def _execute_handler(self, handler: Callable, data: Dict, connection: Optional[Dict]) -> Any:
        """Execute handler with connection context"""
        # If handler is async
        if asyncio.iscoroutinefunction(handler):
            return await handler(data)
        else:
            # Run sync handler in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, handler, data)

    def get_stats(self) -> Dict:
        """Get broker statistics"""
        stats = self.stats.copy()

        # Add queue stats
        stats['queue_size'] = self.message_queue.qsize()
        stats['queue_capacity'] = self.config.max_queue_size

        # Add pool stats
        if self.connection_pool:
            stats['connection_pool'] = self.connection_pool.get_stats()

        # Add backpressure stats
        stats['backpressure'] = self.backpressure.get_stats()

        return stats


async def test_async_broker():
    """Test async broker functionality"""
    broker = AsyncMessageBroker()

    # Register test handler
    async def test_handler(data):
        logger.info(f"Processing: {data}")
        await asyncio.sleep(0.01)  # Simulate work
        return {'status': 'ok', 'processed': data}

    broker.register_handler('test', test_handler)

    # Start broker
    await broker.start(worker_count=5)

    # Send test messages
    tasks = []
    for i in range(100):
        request = {
            'type': 'test',
            'id': str(i),
            'data': f'Message {i}'
        }
        task = asyncio.create_task(
            broker.process_async(request, lambda x: x)
        )
        tasks.append(task)

    # Wait for processing
    results = await asyncio.gather(*tasks)

    # Check results
    accepted = sum(1 for r in results if r['status'] == 'accepted')
    logger.info(f"Accepted {accepted}/100 messages")

    # Wait a bit for processing
    await asyncio.sleep(2)

    # Get stats
    stats = broker.get_stats()
    logger.info(f"Stats: {json.dumps(stats, indent=2)}")

    # Stop broker
    await broker.stop()


def main():
    """Main test runner"""
    asyncio.run(test_async_broker())


if __name__ == "__main__":
    main()