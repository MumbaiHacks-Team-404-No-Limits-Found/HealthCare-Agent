# Twilio WhatsApp Testing Guide

## 🎯 Purpose
Send a test WhatsApp message to Anita Rao (+918125817577) to verify Twilio WhatsApp integration.

## 📋 Prerequisites

### 1. Get Twilio Credentials
Go to [Twilio Console](https://console.twilio.com/) and get:
- **Account SID** (starts with `AC...`)
- **Auth Token** (secret key)

### 2. Set Up WhatsApp Sandbox (For Testing)
1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. Join the sandbox by sending the code from your WhatsApp to Twilio's number
3. **Important**: Anita also needs to join the sandbox by sending the same code to Twilio

### 3. WhatsApp Sandbox Number
- Default: `whatsapp:+14155238886`
- Check your console for your specific sandbox number

## 🚀 Method 1: Using Shell Script

### Edit the script:
```bash
cd /Users/dokuparthinilesh/Desktop/hacke/healthcare_agent/backend
nano send_test_whatsapp.sh
```

### Replace credentials:
```bash
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token_here"
```

### Run it:
```bash
chmod +x send_test_whatsapp.sh
./send_test_whatsapp.sh
```

## 🚀 Method 2: Direct curl Command

### Basic WhatsApp Message:
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=whatsapp:+14155238886" \
  --data-urlencode "To=whatsapp:+918125817577" \
  --data-urlencode "Body=Hi Anita, this is a test from Healthcare Volunteer Coordinator!" \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

### Assignment Notification Example:
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=whatsapp:+14155238886" \
  --data-urlencode "To=whatsapp:+918125817577" \
  --data-urlencode "Body=Hi Anita Rao, you've been assigned to Bangalore Central Camp as Triage Nurse for the morning slot (9am-12pm). Reply CONFIRM to accept or CANCEL to decline." \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

### Check Message Status:
```bash
# Replace MESSAGE_SID with the SID from the response
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages/SMXXXXXXXXXXXXXXXXXXXXXXX.json" \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

## 📱 Expected Response (Success)

```json
{
  "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "date_created": "Thu, 29 Nov 2025 09:30:00 +0000",
  "date_updated": "Thu, 29 Nov 2025 09:30:00 +0000",
  "date_sent": null,
  "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "to": "whatsapp:+918125817577",
  "from": "whatsapp:+14155238886",
  "messaging_service_sid": null,
  "body": "Hi Anita, this is a test from Healthcare Volunteer Coordinator!",
  "status": "queued",
  "num_segments": "1",
  "num_media": "0",
  "direction": "outbound-api",
  "api_version": "2010-04-01",
  "price": null,
  "price_unit": "USD",
  "error_code": null,
  "error_message": null,
  "uri": "/2010-04-01/Accounts/ACxxxxx/Messages/SMxxxxx.json"
}
```

## 🔴 Common Issues & Solutions

### Issue 1: "To number is not a valid WhatsApp number"
**Solution**: Recipient must join WhatsApp sandbox first
- Send the join code from WhatsApp to Twilio's sandbox number
- Example: "join <code>" to +14155238886

### Issue 2: "Authentication Error"
**Solution**: Check your Account SID and Auth Token
- Make sure no extra spaces
- Auth Token is case-sensitive

### Issue 3: "From number must be a valid WhatsApp number"
**Solution**: 
- Use sandbox number: `whatsapp:+14155238886`
- OR configure a production WhatsApp Business number

### Issue 4: Message status is "failed"
**Solution**: Check the error_code in response:
```bash
# Common error codes:
# 21211 - Invalid 'To' Number
# 21408 - Permission to send not enabled
# 21606 - The "From" phone number is not enabled for WhatsApp
```

## 🧪 Testing the Full Flow

### Step 1: Send message to Anita
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=whatsapp:+14155238886" \
  --data-urlencode "To=whatsapp:+918125817577" \
  --data-urlencode "Body=Test assignment: Reply CONFIRM or CANCEL" \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

### Step 2: Anita replies "CONFIRM" or "CANCEL"

### Step 3: Webhook receives the reply
Your webhook at `http://localhost:8000/twilio/webhook` will process it

### Step 4: Check backend logs
```bash
tail -f /tmp/backend.log | grep twilio_webhook
```

## 📝 Environment Variables Setup

Add to `.env` file:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

## 🔍 Debug Tips

### 1. Check Twilio Console Logs
https://console.twilio.com/us1/monitor/logs/sms

### 2. Enable detailed curl output:
```bash
curl -v -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=whatsapp:+14155238886" \
  --data-urlencode "To=whatsapp:+918125817577" \
  --data-urlencode "Body=Test" \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

### 3. Test with Postman
Import the Twilio Messaging API collection for easier testing

## ✅ Success Checklist

- [ ] Twilio Account SID and Auth Token obtained
- [ ] WhatsApp sandbox joined (send join code to Twilio number)
- [ ] Anita's phone (+918125817577) joined sandbox
- [ ] Test message sent successfully (status: queued/sent)
- [ ] Message delivered (check Twilio console)
- [ ] Anita received message on WhatsApp
- [ ] Webhook receives replies correctly

## 📞 Alternative: Test with SMS Instead

If WhatsApp sandbox is not working, test with SMS:
```bash
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json" \
  --data-urlencode "From=+1234567890" \
  --data-urlencode "To=+918125817577" \
  --data-urlencode "Body=Test SMS from Healthcare Volunteer" \
  -u "YOUR_ACCOUNT_SID:YOUR_AUTH_TOKEN"
```

Note: You need a Twilio phone number for SMS (not sandbox)

