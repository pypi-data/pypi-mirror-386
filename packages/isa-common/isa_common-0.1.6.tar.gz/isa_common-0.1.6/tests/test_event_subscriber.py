#!/usr/bin/env python3
"""
Test BaseEventSubscriber JetStream subscription implementation
"""

import sys
import os
import asyncio
import logging
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isa_common.nats_client import NATSClient
from isa_common.consul_client import ConsulRegistry
from isa_common.events import BaseEventSubscriber, EventHandler
from isa_common.events.billing_events import UsageEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestUsageEventHandler(EventHandler):
    """Test handler for usage events"""

    def __init__(self):
        self.events_received = []

    async def handle(self, event: UsageEvent) -> bool:
        """Handle usage event"""
        logger.info(f"✅ Handler received event: user_id={event.user_id}, product_id={event.product_id}, amount={event.usage_amount}")
        self.events_received.append(event)
        return True

    def event_type(self) -> str:
        return "usage.recorded"  # Must match the event_type field in the event data


class TestEventSubscriber(BaseEventSubscriber):
    """Test event subscriber"""

    def __init__(self, nats_client: NATSClient):
        super().__init__(
            service_name="test_subscriber",
            nats_client=nats_client,
            idempotency_storage="memory"
        )

        # Register test handler
        self.handler = TestUsageEventHandler()
        self.register_handler(self.handler)

    async def start(self):
        """Start subscriptions"""
        logger.info("Starting test event subscriptions...")

        # Subscribe to usage.recorded.* events
        await self.subscribe(
            subject="usage.recorded.*",
            queue="test-workers",
            durable="test-consumer"
        )

        logger.info("Test event subscriptions active")

    async def stop(self):
        """Stop subscriptions"""
        logger.info("Stopping test event subscriptions...")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if self.nats_client:
            self.nats_client.close()

        logger.info("Test event subscriptions stopped")


async def test_event_subscriber():
    """Test the event subscriber functionality"""

    print("="*80)
    print("Testing BaseEventSubscriber JetStream Implementation")
    print("="*80)

    # 1. Setup
    print("\n1. Setting up NATS client (direct connection)...")
    nats_host = os.getenv('NATS_HOST', 'localhost')
    nats_port = int(os.getenv('NATS_PORT', '50056'))

    # IMPORTANT: Use same user_id for subscriber and publisher
    # to ensure they share the same NATS namespace
    test_user_id = 'billing_service'

    print(f"   Connecting to: {nats_host}:{nats_port}")
    print(f"   User ID: {test_user_id}")

    # Create NATS client with direct connection
    nats_client = NATSClient(
        host=nats_host,
        port=nats_port,
        user_id=test_user_id
    )

    # Check health
    health = nats_client.health_check()
    if not health:
        print("   ❌ Cannot connect to NATS service")
        return False

    # JetStream is what we need for event subscription
    if not health.get('jetstream_enabled'):
        print("   ❌ JetStream not enabled")
        return False

    print(f"   ✅ NATS service connected")
    print(f"      Status: {health.get('nats_status')}")
    print(f"      JetStream: {health.get('jetstream_enabled')}")
    print(f"      Connections: {health.get('connections')}")

    # 2. Create and start subscriber
    print("\n2. Creating event subscriber...")
    subscriber = TestEventSubscriber(nats_client)

    print("\n3. Starting subscriber (will create JetStream consumer)...")
    await subscriber.start()

    print("   ✅ Subscriber started")
    print(f"   ✅ Subscriptions: {subscriber.subscriptions}")

    # Give background task time to start
    await asyncio.sleep(0.5)

    # 3. Publish test events
    print("\n4. Publishing test events...")

    # Create a separate publisher client (use same user_id!)
    publisher_client = NATSClient(
        host=nats_host,
        port=nats_port,
        user_id=test_user_id  # Same user_id as subscriber
    )

    # Publish 3 test events with correct format
    test_events = [
        {
            "event_type": "usage.recorded",
            "event_id": "test_event_1",
            "user_id": "test_user_1",
            "product_id": "gpt-5-nano",
            "usage_amount": "100",
            "unit_type": "token",
            "timestamp": datetime.now().isoformat() + "Z"
        },
        {
            "event_type": "usage.recorded",
            "event_id": "test_event_2",
            "user_id": "test_user_2",
            "product_id": "claude-3-opus",
            "usage_amount": "200",
            "unit_type": "token",
            "timestamp": datetime.now().isoformat() + "Z"
        },
        {
            "event_type": "usage.recorded",
            "event_id": "test_event_3",
            "user_id": "test_user_3",
            "product_id": "gpt-4o",
            "usage_amount": "300",
            "unit_type": "token",
            "timestamp": datetime.now().isoformat() + "Z"
        }
    ]

    for i, event_data in enumerate(test_events, 1):
        subject = f"usage.recorded.{event_data['product_id']}"
        payload = json.dumps(event_data).encode()

        result = publisher_client.publish(subject, payload)
        if result:
            print(f"   ✅ Event {i}/3 published to {subject}")
        else:
            print(f"   ❌ Event {i}/3 failed")
            return False

    # 4. Wait for events to be processed
    print("\n5. Waiting for events to be processed...")
    print("   (Subscriber is pulling messages in background)")

    for attempt in range(10):
        await asyncio.sleep(1)
        received_count = len(subscriber.handler.events_received)
        print(f"   Attempt {attempt + 1}/10: Received {received_count}/3 events")

        if received_count >= 3:
            break

    # 5. Verify results
    print("\n6. Verifying results...")
    received_count = len(subscriber.handler.events_received)

    if received_count == 3:
        print(f"   ✅ SUCCESS: All 3 events received and processed!")
        print(f"\n   Events received:")
        for event in subscriber.handler.events_received:
            print(f"      - user={event.user_id}, product={event.product_id}, amount={event.usage_amount}")
    elif received_count > 0:
        print(f"   ⚠️  PARTIAL: {received_count}/3 events received")
    else:
        print(f"   ❌ FAILED: No events received")
        print(f"\n   Debugging info:")
        print(f"      - Subscriptions: {subscriber.subscriptions}")
        print(f"      - Background tasks: {len(subscriber._background_tasks)} tasks")
        print(f"      - Handlers: {list(subscriber.handlers.keys())}")

    # 6. Cleanup
    print("\n7. Cleaning up...")
    await subscriber.stop()
    publisher_client.close()

    print("\n" + "="*80)
    if received_count == 3:
        print("✅ TEST PASSED: Event subscription working correctly!")
    else:
        print(f"❌ TEST FAILED: Only {received_count}/3 events processed")
    print("="*80)

    return received_count == 3


if __name__ == "__main__":
    try:
        success = asyncio.run(test_event_subscriber())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
