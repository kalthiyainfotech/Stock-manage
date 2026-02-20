from .models import Buyer
from typing import Optional, Dict


def current_buyer(request) -> Dict[str, Optional[Buyer]]:
    buyer_id = request.session.get("buyer_id")
    buyer = None
    if buyer_id:
        try:
            buyer = Buyer.objects.get(id=buyer_id)
        except Buyer.DoesNotExist:
            buyer = None
    return {"current_buyer": buyer}
