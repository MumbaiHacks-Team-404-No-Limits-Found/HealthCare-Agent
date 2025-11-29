#!/bin/bash
# Test script to send WhatsApp message via Twilio to Anita Rao

# ⚠️ IMPORTANT: Replace these with your actual Twilio credentials
# Get them from: https://console.twilio.com/
TWILIO_ACCOUNT_SID="YOUR_ACCOUNT_SID_HERE"
TWILIO_AUTH_TOKEN="YOUR_AUTH_TOKEN_HERE"

# Twilio WhatsApp number (use sandbox number for testing or your approved number)
# Sandbox number: whatsapp:+14155238886 (Twilio's default sandbox)
TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"

# Recipient: Anita Rao
TO_NUMBER="whatsapp:+918125817577"

# Test message
MESSAGE_BODY="Hi Anita, this is a test message from Healthcare Volunteer Coordinator. You've been assigned to a camp as Triage Nurse for the morning slot. Reply CONFIRM to accept or CANCEL to decline."

echo "===================================="
echo "Sending WhatsApp Test Message"
echo "===================================="
echo "From: $TWILIO_WHATSAPP_FROM"
echo "To: $TO_NUMBER"
echo "Message: $MESSAGE_BODY"
echo "===================================="
echo ""

# Send the message via Twilio API
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=$TWILIO_WHATSAPP_FROM" \
  --data-urlencode "To=$TO_NUMBER" \
  --data-urlencode "Body=$MESSAGE_BODY" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"

echo ""
echo ""
echo "===================================="
echo "Message sent! Check response above"
echo "===================================="

