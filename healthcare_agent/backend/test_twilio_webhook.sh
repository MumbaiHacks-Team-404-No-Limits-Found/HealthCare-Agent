#!/bin/bash
# Test script for Twilio webhook endpoint
# Tests volunteer response handling (confirm/cancel)

BASE_URL="http://localhost:8000"
WEBHOOK_URL="${BASE_URL}/twilio/webhook"

echo "=========================================="
echo "Twilio Webhook Test Script"
echo "=========================================="
echo ""

# Test 1: Confirm assignment
echo "Test 1: Volunteer confirms assignment"
echo "--------------------------------------"
curl -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=confirm" \
  -d "MessageSid=SMtest123" \
  -d "AccountSid=ACtest123" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo ""

# Test 2: Cancel assignment
echo "Test 2: Volunteer cancels assignment"
echo "--------------------------------------"
curl -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=cancel" \
  -d "MessageSid=SMtest456" \
  -d "AccountSid=ACtest456" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo ""

# Test 3: Unknown message
echo "Test 3: Unknown message (should return help text)"
echo "--------------------------------------------------"
curl -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+919392664227" \
  -d "Body=hello" \
  -d "MessageSid=SMtest789" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo ""
echo "=========================================="
echo "Tests completed"
echo "=========================================="

