#!/bin/bash
# Complete test script to send WhatsApp message to Anita Rao

echo "================================================================"
echo "WhatsApp Message Test to Anita Rao (+918125817577)"
echo "================================================================"
echo ""

# Step 1: Get Twilio credentials
echo "📋 STEP 1: Enter your Twilio credentials"
echo "Get them from: https://console.twilio.com/"
echo ""
read -p "Enter your Twilio Account SID (starts with AC): " ACCOUNT_SID
read -p "Enter your Twilio Auth Token: " AUTH_TOKEN

if [ -z "$ACCOUNT_SID" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "❌ Error: Credentials cannot be empty"
    exit 1
fi

echo ""
echo "✅ Credentials saved"
echo ""

# Step 2: Configure message
FROM_NUMBER="whatsapp:+14155238886"  # Twilio sandbox number
TO_NUMBER="whatsapp:+918125817577"   # Anita Rao
MESSAGE="Hi Anita Rao, you have been assigned to Bangalore Central Camp as Triage Nurse for the morning slot (9am-12pm). Please reply CONFIRM to accept or CANCEL to decline. - Healthcare Volunteer Team"

echo "================================================================"
echo "📤 STEP 2: Sending WhatsApp message..."
echo "================================================================"
echo "From: $FROM_NUMBER"
echo "To: $TO_NUMBER"
echo "Message: $MESSAGE"
echo ""
echo "⏳ Sending..."
echo ""

# Step 3: Send the message
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=$FROM_NUMBER" \
  --data-urlencode "To=$TO_NUMBER" \
  --data-urlencode "Body=$MESSAGE" \
  -u "$ACCOUNT_SID:$AUTH_TOKEN")

# Extract HTTP status code and response body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "================================================================"
echo "📥 RESPONSE"
echo "================================================================"
echo "HTTP Status: $HTTP_CODE"
echo ""
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

# Step 4: Check result
if [ "$HTTP_CODE" = "201" ]; then
    echo "================================================================"
    echo "✅ SUCCESS! Message sent to Twilio"
    echo "================================================================"
    
    # Extract message SID
    MESSAGE_SID=$(echo "$BODY" | grep -o '"sid": "[^"]*"' | head -1 | cut -d'"' -f4)
    STATUS=$(echo "$BODY" | grep -o '"status": "[^"]*"' | head -1 | cut -d'"' -f4)
    
    echo ""
    echo "📊 Message Details:"
    echo "  - Message SID: $MESSAGE_SID"
    echo "  - Status: $STATUS"
    echo ""
    echo "🔍 Next Steps:"
    echo "  1. Check Twilio console: https://console.twilio.com/us1/monitor/logs/sms"
    echo "  2. Check if Anita received the message on WhatsApp"
    echo "  3. Ask Anita to reply 'CONFIRM' or 'CANCEL'"
    echo "  4. Check your webhook: http://localhost:8000/twilio/webhook"
    echo ""
    echo "⚠️  IMPORTANT: Both you AND Anita must join the WhatsApp sandbox!"
    echo "   Send 'join <code>' to +1 (415) 523-8886 on WhatsApp"
    echo "   Get your code from: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn"
    echo ""
    
    # Check message status
    if [ ! -z "$MESSAGE_SID" ]; then
        echo "⏳ Checking message status..."
        sleep 2
        STATUS_RESPONSE=$(curl -s -X GET \
          "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Messages/$MESSAGE_SID.json" \
          -u "$ACCOUNT_SID:$AUTH_TOKEN")
        
        CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status": "[^"]*"' | head -1 | cut -d'"' -f4)
        ERROR_CODE=$(echo "$STATUS_RESPONSE" | grep -o '"error_code": "[^"]*"' | head -1 | cut -d'"' -f4)
        ERROR_MSG=$(echo "$STATUS_RESPONSE" | grep -o '"error_message": "[^"]*"' | head -1 | cut -d'"' -f4)
        
        echo ""
        echo "📊 Current Status: $CURRENT_STATUS"
        
        if [ ! -z "$ERROR_CODE" ] && [ "$ERROR_CODE" != "null" ]; then
            echo "❌ Error Code: $ERROR_CODE"
            echo "❌ Error Message: $ERROR_MSG"
            echo ""
            echo "Common errors:"
            echo "  - 21211: Invalid 'To' number (Anita needs to join sandbox)"
            echo "  - 21408: Permission not enabled"
            echo "  - 21606: 'From' number not enabled for WhatsApp"
        fi
    fi
    
elif [ "$HTTP_CODE" = "401" ]; then
    echo "================================================================"
    echo "❌ AUTHENTICATION ERROR"
    echo "================================================================"
    echo "Your Account SID or Auth Token is incorrect."
    echo "Please check: https://console.twilio.com/"
    echo ""
    
elif [ "$HTTP_CODE" = "400" ]; then
    echo "================================================================"
    echo "❌ BAD REQUEST"
    echo "================================================================"
    echo "$BODY"
    echo ""
    echo "Common issues:"
    echo "  - Recipient must join WhatsApp sandbox"
    echo "  - Invalid phone number format"
    echo "  - WhatsApp not enabled for your account"
    echo ""
    
else
    echo "================================================================"
    echo "❌ ERROR (HTTP $HTTP_CODE)"
    echo "================================================================"
    echo "$BODY"
    echo ""
fi

echo "================================================================"
echo "Test completed at $(date)"
echo "================================================================"

