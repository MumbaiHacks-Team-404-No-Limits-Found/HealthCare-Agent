#!/usr/bin/env python3
"""
Test script for NotificationAPI integration with Celery.

This script tests the complete SMS notification flow:
1. Sends a test SMS via NotificationAPI
2. Verifies Celery task queuing
3. Monitors task execution

Usage:
    python test_notificationapi_integration.py

Prerequisites:
    - Redis server running
    - Celery worker running
    - NotificationAPI credentials configured in .env
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import settings
from app.notificationapi_sms import (
    send_sms_notification,
    send_assignment_notification_via_notificationapi,
    validate_notificationapi_config,
    get_notificationapi_client
)
from app.tasks.sms_tasks import send_sms_to_volunteer


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_success(text: str):
    """Print success message in green."""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message in red."""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ️  {text}")


async def test_notificationapi_config():
    """Test NotificationAPI configuration."""
    print_header("Test 1: NotificationAPI Configuration")
    
    try:
        # Check environment variables
        print_info(f"NOTIFICATIONAPI_CLIENT_ID: {settings.notificationapi_client_id[:10]}..." if settings.notificationapi_client_id else "Not set")
        print_info(f"NOTIFICATIONAPI_CLIENT_SECRET: {'*' * 20}" if settings.notificationapi_client_secret else "Not set")
        print_info(f"REDIS_URL: {settings.redis_url}")
        
        # Validate configuration
        validate_notificationapi_config()
        print_success("NotificationAPI credentials are configured")
        
        # Initialize client
        client = get_notificationapi_client()
        if client:
            print_success("NotificationAPI client initialized successfully")
            return True
        else:
            print_error("Failed to initialize NotificationAPI client")
            return False
            
    except ValueError as e:
        print_error(f"Configuration error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def test_direct_sms_send():
    """Test sending SMS directly via NotificationAPI (without Celery)."""
    print_header("Test 2: Direct SMS Send (Without Celery)")
    
    # Test phone number (replace with your actual test number)
    test_volunteer_id = "test_volunteer_001"
    test_phone = "+919876543210"  # Replace with your test phone number
    test_message = f"Test SMS from NotificationAPI - {datetime.utcnow().isoformat()}"
    
    print_info(f"Sending test SMS to: {test_phone}")
    print_info(f"Message: {test_message}")
    
    try:
        result = await send_sms_notification(
            volunteer_id=test_volunteer_id,
            phone_number=test_phone,
            message=test_message,
            notification_type="volunteer_alert"
        )
        
        if result["success"]:
            print_success("SMS sent successfully via NotificationAPI")
            print_info(f"Notification ID: {result.get('notification_id')}")
            print_info(f"Status: {result.get('status')}")
            print_info(f"Timestamp: {result.get('timestamp')}")
            return True
        else:
            print_error(f"SMS failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print_error(f"Failed to send SMS: {e}")
        return False


async def test_assignment_notification():
    """Test sending assignment notification."""
    print_header("Test 3: Assignment Notification (Without Celery)")
    
    # Test data
    test_volunteer_id = "test_volunteer_001"
    test_phone = "+919876543210"  # Replace with your test phone number
    test_volunteer_name = "John Doe"
    test_camp_name = "Community Health Camp"
    test_role = "Nurse"
    test_slot = "morning"
    test_camp_location = "City Hospital"
    test_camp_date = "2024-01-15"
    
    print_info(f"Sending assignment notification to: {test_volunteer_name} ({test_phone})")
    print_info(f"Camp: {test_camp_name}")
    print_info(f"Role: {test_role}, Slot: {test_slot}")
    
    try:
        success = await send_assignment_notification_via_notificationapi(
            volunteer_id=test_volunteer_id,
            phone_number=test_phone,
            volunteer_name=test_volunteer_name,
            camp_name=test_camp_name,
            role=test_role,
            slot=test_slot,
            camp_location=test_camp_location,
            camp_date=test_camp_date
        )
        
        if success:
            print_success("Assignment notification sent successfully")
            return True
        else:
            print_error("Assignment notification failed")
            return False
            
    except Exception as e:
        print_error(f"Failed to send assignment notification: {e}")
        return False


def test_celery_task_queuing():
    """Test queuing SMS task to Celery."""
    print_header("Test 4: Celery Task Queuing")
    
    # Test data
    test_volunteer_id = "test_volunteer_002"
    test_phone = "+919876543210"  # Replace with your test phone number
    test_message = f"Test SMS via Celery - {datetime.utcnow().isoformat()}"
    
    print_info(f"Queuing SMS task to Celery")
    print_info(f"Volunteer ID: {test_volunteer_id}")
    print_info(f"Phone: {test_phone}")
    print_info(f"Message: {test_message}")
    
    try:
        # Queue the task
        task = send_sms_to_volunteer.delay(
            volunteer_id=test_volunteer_id,
            phone_number=test_phone,
            message=test_message,
            notification_type="volunteer_alert"
        )
        
        print_success(f"Task queued successfully - Task ID: {task.id}")
        print_info(f"Task state: {task.state}")
        
        # Wait for task to complete (with timeout)
        print_info("Waiting for task to complete (timeout: 30 seconds)...")
        
        try:
            result = task.get(timeout=30)
            
            if result and result.get("success"):
                print_success("Task completed successfully!")
                print_info(f"Result: {result}")
                return True
            else:
                print_error(f"Task completed but SMS failed: {result}")
                return False
                
        except Exception as e:
            print_error(f"Task execution failed or timed out: {e}")
            print_info("Check Celery worker logs for details")
            return False
            
    except Exception as e:
        print_error(f"Failed to queue task: {e}")
        print_info("Make sure Redis and Celery worker are running")
        return False


def check_prerequisites():
    """Check if all prerequisites are met."""
    print_header("Checking Prerequisites")
    
    all_good = True
    
    # Check Redis connection
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        print_success("Redis is running and accessible")
    except Exception as e:
        print_error(f"Redis connection failed: {e}")
        print_info("Start Redis: redis-server")
        all_good = False
    
    # Check NotificationAPI credentials
    if settings.notificationapi_client_id and settings.notificationapi_client_secret:
        print_success("NotificationAPI credentials are configured")
    else:
        print_error("NotificationAPI credentials not configured")
        print_info("Set NOTIFICATIONAPI_CLIENT_ID and NOTIFICATIONAPI_CLIENT_SECRET in .env")
        all_good = False
    
    # Check Celery worker (by checking for running tasks)
    try:
        from celery import Celery
        app = Celery(broker=settings.redis_url, backend=settings.redis_url)
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print_success(f"Celery worker is running ({len(active_workers)} worker(s))")
        else:
            print_error("No active Celery workers detected")
            print_info("Start Celery: celery -A app.celery_worker worker --loglevel=info")
            all_good = False
    except Exception as e:
        print_error(f"Failed to check Celery worker: {e}")
        all_good = False
    
    return all_good


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  NotificationAPI Integration Test Suite")
    print("  " + datetime.utcnow().isoformat())
    print("=" * 80)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n" + "=" * 80)
        print_error("Prerequisites not met. Please fix the issues above and try again.")
        print("=" * 80 + "\n")
        return
    
    # Run tests
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration", await test_notificationapi_config()))
    
    # Test 2: Direct SMS send
    results.append(("Direct SMS Send", await test_direct_sms_send()))
    
    # Test 3: Assignment notification
    results.append(("Assignment Notification", await test_assignment_notification()))
    
    # Test 4: Celery task queuing
    results.append(("Celery Task Queuing", test_celery_task_queuing()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("-" * 80 + "\n")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        print_info("NotificationAPI integration is working correctly")
    else:
        print_error(f"{total - passed} test(s) failed")
        print_info("Check the error messages above and fix the issues")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Update test phone number before running!")
    print("Edit this file and replace +919876543210 with your actual test number\n")
    
    response = input("Have you updated the test phone number? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Please update the phone number and try again.")
        sys.exit(0)
    
    # Run tests
    asyncio.run(main())

