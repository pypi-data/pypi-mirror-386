from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

# Stripe usage-based billing: configure meter & record usage. :contentReference[oaicite:9]{index=9}
try:
    import stripe
except Exception:
    stripe = None

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_METER_EVENT_NAME = os.getenv("STRIPE_METER_EVENT", "events_processed")
STRIPE_CUSTOMER_ID_LOOKUP = os.getenv("STRIPE_CUSTOMERS_JSON")  # optional: {"tenantA":"cus_123", ...}

def record_usage(tenant_id: str, metric: str, value: int) -> None:
    if not STRIPE_API_KEY or not stripe:
        return
    stripe.api_key = STRIPE_API_KEY
    # optional mapping from tenant_id -> Stripe customer
    customer_id = None
    if STRIPE_CUSTOMER_ID_LOOKUP:
        import json
        try:
            mapping = json.loads(STRIPE_CUSTOMER_ID_LOOKUP)
            customer_id = mapping.get(tenant_id)
        except Exception:
            pass
    # Send a generic meter event; in Stripe you can create a Meter with event name and aggregation
    try:
        stripe.MeterEvent.create(  # new Meter Events API
            event_name=metric or STRIPE_METER_EVENT_NAME,
            payload={
                "value": value,
                "tenant": tenant_id,
                **({"customer": customer_id} if customer_id else {})
            },
            timestamp=int(datetime.now(timezone.utc).timestamp())
        )
    except Exception:
        # Swallow errors in dev; observability will surface in prod
        pass
