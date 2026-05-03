import hmac
import hashlib
import json
import os
from typing import Any, Dict

SECRET_KEY = os.getenv('HMAC_SECRET', 'default_dev_secret_change_me').encode()

def sign_message(message: Dict[str, Any]) -> str:
    message_copy = message.copy()
    message_copy.pop("signature", None)
    serialized = json.dumps(message_copy, sort_keys=True, separators=(',', ':'))
    return hmac.new(SECRET_KEY, serialized.encode(), hashlib.sha256).hexdigest()

def verify_signature(message: Dict[str, Any]) -> bool:
    if "signature" not in message:
        return False
    provided_sig = message["signature"]
    expected_sig = sign_message(message)
    return hmac.compare_digest(provided_sig, expected_sig)

def add_signature(message: Dict[str, Any]) -> Dict[str, Any]:
    msg_with_sig = message.copy()
    msg_with_sig["signature"] = sign_message(message)
    return msg_with_sig