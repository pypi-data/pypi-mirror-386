# Apgard SDK

Apgard is a Python SDK designed to help AI companion companies build **safe, compliant, and caring chat experiences**. It tracks user interactions across chat sessions and provides real-time guidance to keep conversations on track.

## Key Capabilities

- **Break Tracker** – Monitors ongoing chat sessions and gently prompts users to take breaks when needed. By default, it also reminds users every three hours to a break.

- **Content Monitoring & Intervention** – Detects risky content such as self-harm, suicidal ideation, or sexually explicit material. When escalating risks are detected, it responds with whether to intervene, escalate and a suggested message.

Apgard helps teams continue to **innovate safely**, ensuring that AI companions lead with care while meeting regulatory requirements such as California’s SB 243.

# API Key

Reach out for an API Key via this Google form: https://forms.gle/q6CekCHiDaEdL1CD8 

---

## Installation

```
pip install apgard
```

# Initialize client
By default, ApgardClient is synchronous. The SDK also has an asynchronous client. Reach out for more details.
```
from apgard import ApgardClient

client = ApgardClient(api_key="your-api-key")
```


# Get apgard user_id
```
apgard_user_id = client.get_or_create_user() # Optional: passing your external_user_id for mapping
# e.g. user_123
```

## Break Tracker

# Track breaks during user conversations
Call record_activity() whenever the user interacts with your chatbot:
```
break_status = client.breaks.activity(user_id="user_123")

if break_status.break_due:
    # Display break reminder
    print(break_status.message)
else:
    # Continue chatbot interaction
    print("User can continue chatting")
```

## Content Monitoring

Call moderate_message() with the inputs and outputs of chat conversations:
```
moderation = client.moderation.moderate_message(
    user_id="user_123", # apgard's user_id
    content="What is the meaning of life?",
    role="user", # user or model
    thread_id="1" # Optional mapping for your thread ID
)
```
Payload

message_id: str
thread_id: str
should_intervene: bool
reason_codes: List
guiding_message: str