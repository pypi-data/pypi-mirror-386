import hashlib
import hmac
import json
from typing import Any, Dict, Union
from urllib.parse import urlencode


class MerchantUtilsManager:
    def check_sign(self, client_signature: str, client_key: str,
                   request_body: Union[Dict[str, Any], str, bytes]) -> bool:
        if isinstance(request_body, dict):
            string_body = json.dumps(request_body, sort_keys=True, separators=(',', ':'))
        elif isinstance(request_body, bytes):
            string_body = request_body.decode('utf-8')
        else:
            string_body = request_body

        message = string_body + client_key

        calculated_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()

        return hmac.compare_digest(calculated_hash, client_signature)

    def generate_link(self, host: str, store_uuid: str, client_id: str, email: str) -> str:
        query_params = urlencode({'email': email})
        return f"{host}/{store_uuid}/{client_id}?{query_params}"
