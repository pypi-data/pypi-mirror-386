from typing import List, Any
from karrio.core.utils import (
    Serializable,
    Deserializable,
    Envelope,
    Pipeline,
    Job,
    XP,
    request as http,
    exec_parrallel,
)
from karrio.mappers.canpar.settings import Settings
from karrio.api.proxy import Proxy as BaseProxy


class Proxy(BaseProxy):
    settings: Settings

    def _send_request(self, path: str, soapaction: str, request: Serializable) -> str:
        return http(
            url=f"{self.settings.server_url}{path}",
            data=request.serialize(),
            trace=self.trace_as("xml"),
            method="POST",
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "soapaction": soapaction,
            },
        )

    def validate_address(self, request: Serializable) -> Deserializable:
        response = self._send_request(
            path="/CanparRatingService.CanparRatingServiceHttpSoap12Endpoint/",
            soapaction="urn:searchCanadaPost",
            request=request,
        )

        return Deserializable(response, XP.to_xml)

    def get_rates(self, request: Serializable) -> Deserializable:
        response = self._send_request(
            path="/CanparRatingService.CanparRatingServiceHttpSoap12Endpoint/",
            soapaction="urn:rateShipment",
            request=request,
        )

        return Deserializable(response, XP.to_xml)

    def get_tracking(self, request: Serializable) -> Deserializable:
        """
        get_tracking make parallel request for each TrackRequest
        """

        def get_tracking(track_request: str):
            return self._send_request(
                path="/CanparAddonsService.CanparAddonsServiceHttpSoap12Endpoint/",
                soapaction="urn:trackByBarcodeV2",
                request=Serializable(track_request),
            )

        response: List[str] = exec_parrallel(get_tracking, request.serialize())

        return Deserializable(XP.bundle_xml(xml_strings=response), XP.to_xml)

    def create_shipment(self, request: Serializable) -> Deserializable:
        def process(job: Job):
            if job.data is None:
                return job.fallback

            return self._send_request(
                path="/CanshipBusinessService.CanshipBusinessServiceHttpSoap12Endpoint/",
                request=job.data,
                soapaction=dict(
                    process="urn:processShipment",
                    get_label="urn:getLabels",
                )[job.id],
            )

        pipeline: Pipeline = request.serialize()
        response = pipeline.apply(process)

        return Deserializable(XP.bundle_xml(response), XP.to_xml)

    def cancel_shipment(self, request: Serializable) -> Deserializable:
        response = self._send_request(
            path="/CanshipBusinessService.CanshipBusinessServiceHttpSoap12Endpoint/",
            soapaction="urn:voidShipment",
            request=request,
        )

        return Deserializable(response, XP.to_xml)

    def schedule_pickup(self, request: Serializable) -> Deserializable:
        response = self._send_request(
            path="/CanparAddonsService.CanparAddonsServiceHttpSoap12Endpoint/",
            soapaction="urn:schedulePickupV2",
            request=request,
        )

        return Deserializable(response, XP.to_xml)

    def modify_pickup(self, request: Serializable) -> Deserializable:
        def process(job: Job):
            if job.data is None:
                return job.fallback

            return self._send_request(
                path="/CanparAddonsService.CanparAddonsServiceHttpSoap12Endpoint/",
                request=job.data,
                soapaction=dict(
                    cancel="urn:cancelPickup",
                    schedule="urn:schedulePickupV2",
                )[job.id],
            )

        pipeline: Pipeline = request.serialize()
        response = pipeline.apply(process)

        return Deserializable(XP.bundle_xml(response), XP.to_xml)

    def cancel_pickup(self, request: Serializable) -> Deserializable:
        response = self._send_request(
            path="/CanparAddonsService.CanparAddonsServiceHttpSoap12Endpoint/",
            soapaction="urn:cancelPickup",
            request=request,
        )

        return Deserializable(response, XP.to_xml)
