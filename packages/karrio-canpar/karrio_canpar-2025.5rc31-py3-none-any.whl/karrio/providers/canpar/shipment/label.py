from jstruct import struct
from karrio.schemas.canpar.CanshipBusinessService import (
    GetLabelsAdvancedRq,
    getLabelsAdvanced,
)
from karrio.core.utils import create_envelope, Serializable, Envelope
from karrio.providers.canpar.utils import Settings


@struct
class LabelRequest:
    shipment_id: str
    thermal: bool = False


def get_label_request(payload: LabelRequest, settings: Settings) -> Serializable:
    request = create_envelope(
        body_content=getLabelsAdvanced(
            request=GetLabelsAdvancedRq(
                horizontal=False,
                id=payload.shipment_id,
                password=settings.password,
                thermal=payload.thermal,
                user_id=settings.username,
            )
        )
    )

    return Serializable(request, Settings.serialize)
