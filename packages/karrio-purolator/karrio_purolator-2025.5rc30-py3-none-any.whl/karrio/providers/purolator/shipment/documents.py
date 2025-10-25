from karrio.schemas.purolator.shipping_documents_service_1_3_0 import (
    GetDocumentsRequest,
    RequestContext,
    DocumentCriteria,
    ArrayOfDocumentCriteria,
    PIN,
    DocumentTypes,
)
from karrio.core.utils.soap import Envelope, create_envelope, apply_namespaceprefix
from karrio.core.models import ShipmentRequest
from karrio.core.utils import Serializable, XP, SF
from karrio.providers.purolator.units import PrintType
from karrio.providers.purolator.utils import Settings


def get_shipping_documents_request(
    pin: str, payload: ShipmentRequest, settings: Settings
) -> Serializable:
    is_international = payload.shipper.country_code != payload.recipient.country_code
    label_type = PrintType.map(payload.label_type or "PDF").name
    documents = [
        SF.concat_str(
            ("International" if is_international else "Domestic"),
            "BillOfLading",
            ("Thermal" if label_type == "ZPL" else ""),
            separator="",
            join=True,
        )
    ]

    # TODO: Find what is missing to get customs invoice.
    # if is_international:
    #     documents.append("CustomsInvoice")

    request = create_envelope(
        header_content=RequestContext(
            Version="1.3",
            Language=settings.language,
            GroupID="",
            RequestReference=(getattr(payload, "id", None) or ""),
            UserToken=settings.user_token,
        ),
        body_content=GetDocumentsRequest(
            OutputType=label_type,
            Synchronous=True,
            DocumentCriterium=ArrayOfDocumentCriteria(
                DocumentCriteria=[
                    DocumentCriteria(
                        PIN=PIN(Value=pin),
                        DocumentTypes=DocumentTypes(DocumentType=documents),
                    )
                ]
            ),
        ),
    )
    return Serializable(request, _request_serializer)


def _request_serializer(envelope: Envelope) -> str:
    namespacedef_ = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://purolator.com/pws/datatypes/v1"'
    envelope.ns_prefix_ = "soap"
    envelope.Body.ns_prefix_ = envelope.ns_prefix_
    envelope.Header.ns_prefix_ = envelope.ns_prefix_
    apply_namespaceprefix(envelope.Body.anytypeobjs_[0], "v1")
    apply_namespaceprefix(envelope.Header.anytypeobjs_[0], "v1")
    return XP.export(envelope, namespacedef_=namespacedef_)
