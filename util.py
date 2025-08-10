## util.py

import json
from typing import List

def to_list_from_products_field(products_field: str | list) -> List[str]:
    if isinstance(products_field, list):
        return [str(x) for x in products_field]
    if isinstance(products_field, str):
        try:
            data = json.loads(products_field)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass
        return [p.strip() for p in products_field.split(",") if p.strip()]
    return []


def to_backend_products_field(products: List[str]) -> str:
    return json.dumps(products, ensure_ascii=False)
