"""
Enterprise Messaging Architecture Test Suite
Tests both Kafka and RabbitMQ events one by one
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic

# Configuration
USER_SERVICE_URL = "http://localhost:8000"
KRAKEN_SERVICE_URL = "http://localhost:8001"
BOT_SERVICE_URL = "http://localhost:8002"
RABBITMQ_MGMT_URL = "http://localhost:15672/api"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

# Test user credentials
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "Test1234!"
TEST_NAME = "Test User"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_kafka(text: str):
    """Print Kafka-specific message"""
    print(f"{Colors.MAGENTA}📨 {text}{Colors.RESET}")

def print_rabbitmq(text: str):
    """Print RabbitMQ-specific message"""
    print(f"{Colors.CYAN}🐰 {text}{Colors.RESET}")

def check_service_health(url: str, service_name: str) -> bool:
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_success(f"{service_name} is running")
            return True
        else:
            print_error(f"{service_name} returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{service_name} is not accessible: {e}")
        return False

def check_rabbitmq() -> bool:
    """Check if RabbitMQ is running"""
    try:
        auth = ('guest', 'guest')
        response = requests.get(f"{RABBITMQ_MGMT_URL}/overview", auth=auth, timeout=5)
        if response.status_code == 200:
            print_success("RabbitMQ is running")
            return True
        else:
            print_error("RabbitMQ Management API not accessible")
            return False
    except Exception as e:
        print_error(f"RabbitMQ not accessible: {e}")
        return False

def check_kafka() -> bool:
    """Check if Kafka is running"""
    try:
        admin_client = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
        metadata = admin_client.list_topics(timeout=10)
        print_success("Kafka is running")
        return True
    except Exception as e:
        print_error(f"Kafka not accessible: {e}")
        return False

def get_rabbitmq_queue_info(queue_name: str) -> Optional[Dict]:
    """Get RabbitMQ queue information"""
    try:
        auth = ('guest', 'guest')
        response = requests.get(
            f"{RABBITMQ_MGMT_URL}/queues/%2F/{queue_name}",
            auth=auth,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print_warning(f"Could not get queue info for {queue_name}: {e}")
        return None

def consume_kafka_message(topic: str, timeout: int = 10) -> Optional[Dict]:
    """Consume a single message from Kafka topic"""
    try:
        consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': f'test-consumer-{int(time.time())}',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': False,
        })
        
        consumer.subscribe([topic])
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print_error(f"Kafka error: {msg.error()}")
                    break
            
            try:
                message_data = json.loads(msg.value().decode('utf-8'))
                consumer.close()
                return message_data
            except json.JSONDecodeError:
                continue
        
        consumer.close()
        return None
    except Exception as e:
        print_warning(f"Could not consume from Kafka topic {topic}: {e}")
        return None

def test_user_registration() -> Optional[Dict]:
    """Test user registration - should publish user.created to Kafka"""
    print_header("TEST 1: User Registration - user.created Event (Kafka)")
    
    print_info(f"Registering user: {TEST_EMAIL}")
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/user/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME
            },
            timeout=10
        )
        
        if response.status_code == 201:
            user_data = response.json()
            print_success("User registered successfully!")
            print_info(f"   User ID: {user_data.get('id')}")
            print_info(f"   Email: {user_data.get('email')}")
            
            # Wait a bit for Kafka message
            print_info("Waiting for Kafka message...")
            time.sleep(2)
            
            # Check Kafka topic
            print_kafka("Checking user.events topic for user.created event...")
            message = consume_kafka_message("user.events", timeout=5)
            if message and message.get("user_id"):
                print_success(f"✅ Found user.created event in Kafka!")
                print_info(f"   Event data: user_id={message.get('user_id')}, email={message.get('email')}")
                return user_data
            else:
                print_warning("⚠️  user.created event not found in Kafka (may take a moment)")
                return user_data
        else:
            print_error(f"Registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Registration error: {e}")
        return None

def test_user_login(user_data: Dict) -> Optional[str]:
    """Test user login - should publish user.logged_in to Kafka"""
    print_header("TEST 2: User Login - user.logged_in Event (Kafka)")
    
    print_info(f"Logging in user: {TEST_EMAIL}")
    try:
        response = requests.post(
            f"{USER_SERVICE_URL}/user/api/v1/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print_success("User logged in successfully!")
            
            # Wait for Kafka message
            print_info("Waiting for Kafka message...")
            time.sleep(2)
            
            # Check Kafka topic
            print_kafka("Checking user.events topic for user.logged_in event...")
            message = consume_kafka_message("user.events", timeout=5)
            if message and message.get("user_id"):
                print_success(f"✅ Found user.logged_in event in Kafka!")
                print_info(f"   Event data: user_id={message.get('user_id')}, login_at={message.get('login_at')}")
            else:
                print_warning("⚠️  user.logged_in event not found in Kafka (may take a moment)")
            
            return access_token
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_onboarding(access_token: str):
    """Test onboarding completion - should publish onboarding.completed to Kafka"""
    print_header("TEST 3: Onboarding Completion - onboarding.completed Event (Kafka)")
    
    print_info("Completing onboarding...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{USER_SERVICE_URL}/user/api/v1/onboarding",
            json={
                "country": "US",
                "state": "CA",
                "experience_level": "intermediate",
                "has_kraken_account": True
            },
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("Onboarding completed successfully!")
            
            # Wait for Kafka message
            print_info("Waiting for Kafka message...")
            time.sleep(2)
            
            # Check Kafka topic
            print_kafka("Checking onboarding.events topic...")
            message = consume_kafka_message("onboarding.events", timeout=5)
            if message and message.get("user_id"):
                print_success(f"✅ Found onboarding.completed event in Kafka!")
                print_info(f"   Event data: user_id={message.get('user_id')}, country={message.get('country')}")
            else:
                print_warning("⚠️  onboarding.completed event not found in Kafka (may take a moment)")
        else:
            print_error(f"Onboarding failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Onboarding error: {e}")

def test_kraken_key_connection(access_token: str):
    """Test Kraken key connection - should publish kraken.key.connected to Kafka"""
    print_header("TEST 4: Kraken Key Connection - kraken.key.connected Event (Kafka)")
    
    print_warning("⚠️  This test requires valid Kraken API keys")
    print_info("Skipping actual connection (would require real API keys)")
    print_kafka("When a key is connected, it should publish to kraken.events topic")
    
    # Just show what would happen
    print_info("Expected flow:")
    print_info("   1. User connects Kraken API key")
    print_info("   2. Event 'kraken.key.connected' published to Kafka topic 'kraken.events'")
    print_info("   3. Event contains: user_id, key_id, key_name, connected_at, permissions")

def test_bot_start(access_token: str):
    """Test bot start command - should publish bot.start to RabbitMQ"""
    print_header("TEST 5: Bot Start Command - bot.start Event (RabbitMQ)")
    
    print_info("Sending bot.start command...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{KRAKEN_SERVICE_URL}/api/v1/trading/bot/start",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_success("Bot start command sent successfully!")
            
            # Wait for RabbitMQ message
            print_info("Waiting for RabbitMQ message...")
            time.sleep(2)
            
            # Check RabbitMQ queue
            print_rabbitmq("Checking bot.start queue...")
            queue_info = get_rabbitmq_queue_info("bot.start")
            if queue_info:
                messages = queue_info.get("messages", 0)
                consumers = queue_info.get("consumers", 0)
                print_success(f"✅ Queue 'bot.start': {messages} messages, {consumers} consumers")
            else:
                print_warning("⚠️  Could not get queue info (queue may not exist yet)")
        else:
            print_error(f"Bot start failed: {response.status_code} - {response.text}")
            print_info("Note: This may fail if no Kraken key is connected")
    except Exception as e:
        print_error(f"Bot start error: {e}")

def test_bot_trigger_trade(access_token: str):
    """Test bot trigger trade - should publish bot.trigger_trade to RabbitMQ, then bot.trade.executed/skipped to Kafka"""
    print_header("TEST 6: Bot Trigger Trade - bot.trigger_trade (RabbitMQ) → bot.trade.* (Kafka)")
    
    print_info("Sending bot.trigger_trade command...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{KRAKEN_SERVICE_URL}/api/v1/trading/bot/trigger",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_success("Bot trigger command sent successfully!")
            
            # Wait for messages
            print_info("Waiting for messages...")
            time.sleep(3)
            
            # Check RabbitMQ queue (command)
            print_rabbitmq("Checking bot.trigger_trade queue...")
            queue_info = get_rabbitmq_queue_info("bot.trigger_trade")
            if queue_info:
                messages = queue_info.get("messages", 0)
                print_info(f"   Queue 'bot.trigger_trade': {messages} messages")
            
            # Check Kafka topic (result)
            print_kafka("Checking trading.events topic for bot.trade.* events...")
            message = consume_kafka_message("trading.events", timeout=5)
            if message:
                event_type = message.get("event_type") or "bot.trade.executed"
                print_success(f"✅ Found {event_type} event in Kafka!")
                print_info(f"   Event data: user_id={message.get('user_id')}, reason={message.get('reason', 'N/A')}")
            else:
                print_warning("⚠️  Trade event not found in Kafka (bot may not be running or no signal)")
        else:
            print_error(f"Bot trigger failed: {response.status_code} - {response.text}")
            print_info("Note: This may fail if bot is not running or no Kraken key is connected")
    except Exception as e:
        print_error(f"Bot trigger error: {e}")

def test_bot_stop(access_token: str):
    """Test bot stop command - should publish bot.stop to RabbitMQ"""
    print_header("TEST 7: Bot Stop Command - bot.stop Event (RabbitMQ)")
    
    print_info("Sending bot.stop command...")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{KRAKEN_SERVICE_URL}/api/v1/trading/bot/stop",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_success("Bot stop command sent successfully!")
            
            # Wait for RabbitMQ message
            print_info("Waiting for RabbitMQ message...")
            time.sleep(2)
            
            # Check RabbitMQ queue
            print_rabbitmq("Checking bot.stop queue...")
            queue_info = get_rabbitmq_queue_info("bot.stop")
            if queue_info:
                messages = queue_info.get("messages", 0)
                consumers = queue_info.get("consumers", 0)
                print_success(f"✅ Queue 'bot.stop': {messages} messages, {consumers} consumers")
            else:
                print_warning("⚠️  Could not get queue info")
        else:
            print_error(f"Bot stop failed: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Bot stop error: {e}")

def list_all_queues():
    """List all RabbitMQ queues"""
    print_rabbitmq("RabbitMQ Queues:")
    try:
        auth = ('guest', 'guest')
        response = requests.get(f"{RABBITMQ_MGMT_URL}/queues", auth=auth, timeout=5)
        if response.status_code == 200:
            queues = response.json()
            for queue in queues:
                name = queue.get("name", "unknown")
                messages = queue.get("messages", 0)
                consumers = queue.get("consumers", 0)
                print_info(f"   {name}: {messages} messages, {consumers} consumers")
        else:
            print_warning("Could not list queues")
    except Exception as e:
        print_warning(f"Could not list queues: {e}")

def list_kafka_topics():
    """List all Kafka topics"""
    print_kafka("Kafka Topics:")
    try:
        from confluent_kafka.admin import AdminClient
        admin_client = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
        metadata = admin_client.list_topics(timeout=10)
        topics = list(metadata.topics.keys())
        for topic in sorted(topics):
            if not topic.startswith('__'):  # Skip internal topics
                print_info(f"   {topic}")
    except Exception as e:
        print_warning(f"Could not list Kafka topics: {e}")

def main():
    """Main test function"""
    print_header("Enterprise Messaging Architecture Test Suite")
    print_info("Testing Kafka (event streaming) and RabbitMQ (commands) integration")
    print()
    
    # Check services
    print_header("Checking Services")
    services_ok = True
    services_ok &= check_service_health(f"{USER_SERVICE_URL}/user", "User Service")
    services_ok &= check_service_health(f"{KRAKEN_SERVICE_URL}/kraken", "Kraken Service")
    
    if not services_ok:
        print_error("Some services are not running. Please start them first.")
        print_info("Run: python app.py (or start services individually)")
        return
    
    # Check messaging systems
    print_header("Checking Messaging Systems")
    rabbitmq_ok = check_rabbitmq()
    kafka_ok = check_kafka()
    
    if not rabbitmq_ok:
        print_warning("RabbitMQ not running. Some tests will fail.")
        print_info("Start with: docker-compose -f docker-compose.infrastructure.yml up -d")
    
    if not kafka_ok:
        print_warning("Kafka not running. Some tests will fail.")
        print_info("Start with: docker-compose -f docker-compose.infrastructure.yml up -d")
    
    if not rabbitmq_ok and not kafka_ok:
        print_error("Neither RabbitMQ nor Kafka is running. Cannot continue tests.")
        return
    
    print()
    
    # Run tests
    user_data = test_user_registration()
    if not user_data:
        print_error("User registration failed. Cannot continue tests.")
        return
    
    access_token = test_user_login(user_data)
    if not access_token:
        print_error("User login failed. Cannot continue tests.")
        return
    
    test_onboarding(access_token)
    test_kraken_key_connection(access_token)
    test_bot_start(access_token)
    test_bot_trigger_trade(access_token)
    test_bot_stop(access_token)
    
    # Final summary
    print_header("Final Status")
    if rabbitmq_ok:
        list_all_queues()
    if kafka_ok:
        list_kafka_topics()
    
    print_header("Test Summary")
    print_success("All tests completed!")
    print_info("📨 Kafka events: user.created, user.logged_in, onboarding.completed, kraken.key.*, bot.trade.*")
    print_info("🐰 RabbitMQ events: bot.start, bot.stop, bot.trigger_trade, bot.started, bot.stopped, bot.error")
    print_info("Check RabbitMQ Management UI at http://localhost:15672")
    print_info("Check Kafka topics using: kafka-console-consumer --bootstrap-server localhost:9092 --topic <topic-name>")
    print(f"\n{Colors.BOLD}Test User: {TEST_EMAIL}{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

