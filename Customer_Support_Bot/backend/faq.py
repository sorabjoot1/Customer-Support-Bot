FAQ_KNOWLEDGE = """
Company: NovaMart Online Store
Support hours: Monday–Friday 9:00–18:00 (UTC)
Return window: 30 days from delivery for unused items in original packaging
Shipping: Standard 3–5 business days, Express 1–2 business days
Payment methods: Credit/debit cards, PayPal, Apple Pay, Google Pay
Warranty: 12 months manufacturer warranty on electronics
Account reset: Password reset link is sent to the registered email within 5 minutes
Order tracking: Available in Account > Orders after shipment label is created
Refunds: Processed within 5–7 business days after return is received
Damaged items: Photo evidence required; replacement or refund offered within 48 hours of review
Subscription: Cancel anytime from Account > Subscriptions; billed monthly
Privacy: Customer data is never sold; see privacy policy on website
"""

ESCALATION_KEYWORDS = [
    "speak to a human",
    "talk to a person",
    "human agent",
    "real person",
    "manager",
    "escalate",
    "lawsuit",
    "legal action",
    "chargeback",
    "fraud",
    "police",
    "attorney",
    "lawyer",
]


def should_escalate(message: str, llm_flag: bool = False) -> bool:
    lowered = message.lower()
    if llm_flag:
        return True
    return any(keyword in lowered for keyword in ESCALATION_KEYWORDS)


SYSTEM_PROMPT = f"""You are NovaMart's intelligent customer support assistant.
Be empathetic, concise, and accurate. Use the FAQ knowledge below when relevant.
If the user asks something outside your knowledge or needs account-specific actions
you cannot perform (refunds already disputed, legal threats, safety issues, or
explicit requests for a human), set escalate to true.

FAQ Knowledge:
{FAQ_KNOWLEDGE}

Always respond in JSON with this exact shape:
{{
  "reply": "helpful customer-facing response",
  "escalate": false,
  "category": "faq|complaint|order|billing|technical|other",
  "confidence": 0.0
}}
Do not wrap the JSON in markdown fences.
"""
