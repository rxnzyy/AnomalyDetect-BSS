import hmac
import hashlib
import json
import os
from typing import Any, Dict

# Секретный ключ из переменной окружения
SECRET_KEY = os.getenv('HMAC_SECRET', 'default_dev_secret_change_me').encode()

def sign_message(message: Dict[str, Any]) -> str:
    """
    Генерирует HMAC-SHA256 подпись для сообщения.
    Поле 'signature' исключается из подписи, если присутствует.
    """
    message_copy = message.copy()
    message_copy.pop("signature", None)
    # Сортируем ключи для детерминированности
    serialized = json.dumps(message_copy, sort_keys=True, separators=(',', ':'))
    return hmac.new(SECRET_KEY, serialized.encode(), hashlib.sha256).hexdigest()

def verify_signature(message: Dict[str, Any]) -> bool:
    """
    Проверяет подпись сообщения.
    Возвращает True, если подпись корректна.
    """
    if "signature" not in message:
        return False
    provided_sig = message["signature"]
    expected_sig = sign_message(message)
    # Постоянное время сравнения для защиты от timing attacks
    return hmac.compare_digest(provided_sig, expected_sig)

def add_signature(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Добавляет поле 'signature' к копии сообщения.
    """
    msg_with_sig = message.copy()
    msg_with_sig["signature"] = sign_message(message)
    return msg_with_sig