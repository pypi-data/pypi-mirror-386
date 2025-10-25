from typing import List, Tuple
from functools import partial
from karrio.schemas.aramex.array_of_string import ArrayOfstring
from karrio.schemas.aramex.tracking import (
    ShipmentTrackingRequest,
    ClientInfo,
    TrackingResult,
)
from karrio.core.utils import (
    create_envelope,
    Element,
    Serializable,
    XP,
    DF,
)
from karrio.core.models import (
    TrackingEvent,
    TrackingDetails,
    TrackingRequest,
    Message,
)
from karrio.providers.aramex.utils import Settings
from karrio.providers.aramex.error import parse_error_response
import karrio.lib as lib


def parse_tracking_response(
    _response: lib.Deserializable[lib.Element],
    settings: Settings,
) -> Tuple[List[TrackingDetails], List[Message]]:
    response = _response.deserialize()
    non_existents = next(
        (
            XP.to_object(ArrayOfstring, n)
            for n in lib.find_element("NonExistingWaybills", response)
        ),
        ArrayOfstring(),
    )
    results = lib.find_element("TrackingResult", response)
    tracking_details = [_extract_detail(node, settings) for node in results]
    errors = _extract_errors(non_existents, settings) + parse_error_response(
        response, settings
    )

    return tracking_details, errors


def _extract_errors(non_existents: ArrayOfstring, settings: Settings) -> List[Message]:
    return [
        Message(
            carrier_name=settings.carrier_name,
            carrier_id=settings.carrier_id,
            message=f'Waybill "{waybill}" Not Found',
        )
        for waybill in non_existents.string
    ]


def _extract_detail(node: Element, settings: Settings) -> TrackingDetails:
    detail = XP.to_object(TrackingResult, node)

    return TrackingDetails(
        carrier_name=settings.carrier_name,
        carrier_id=settings.carrier_id,
        tracking_number=detail.WaybillNumber,
        events=[
            TrackingEvent(
                date=DF.date(detail.UpdateDateTime, "%Y-%m-%dT%H:%M:%S"),
                description=detail.UpdateDescription,
                location=detail.UpdateLocation,
                code=detail.UpdateCode,
                time=DF.ftime(detail.UpdateDateTime, "%Y-%m-%dT%H:%M:%S"),
            )
        ],
    )


def tracking_request(payload: TrackingRequest, settings: Settings) -> Serializable:
    request = create_envelope(
        body_content=ShipmentTrackingRequest(
            ClientInfo=ClientInfo(
                UserName=settings.username,
                Password=settings.password,
                Version="1.0",
                AccountNumber=settings.account_number,
                AccountPin=settings.account_pin,
                AccountEntity=settings.account_entity,
                AccountCountryCode=settings.account_country_code,
            ),
            Transaction=None,
            Shipments=ArrayOfstring(string=payload.tracking_numbers),
            GetLastTrackingUpdateOnly=False,
        )
    )

    return Serializable(
        request,
        partial(
            settings.standard_request_serializer,
            extra_namespace='xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays',
            special_prefixes=dict(string="arr"),
        ),
    )
