import enum
import json
from typing import Any

import cbor2

from c2pie.utils.content_types import jumbf_content_types


class C2PA_AssertionTypes(enum.Enum):
    creative_work = 0
    data_hash = 1
    thumbnail = 2


def json_to_bytes(json_object: dict[str, Any]) -> bytes:
    return json.dumps(json_object, separators=(",", ":")).encode("utf-8")


def cbor_to_bytes(json_object: dict[str, Any]) -> bytes:
    return cbor2.dumps(json_object)


def get_assertion_content_type(assertion_type: C2PA_AssertionTypes) -> bytes:
    if assertion_type == C2PA_AssertionTypes.creative_work:
        return jumbf_content_types["json"]
    elif assertion_type == C2PA_AssertionTypes.data_hash:
        return jumbf_content_types["cbor"]
    elif assertion_type == C2PA_AssertionTypes.thumbnail:
        return jumbf_content_types["codestream"]
    else:
        return b""


def get_assertion_content_box_type(assertion_type: C2PA_AssertionTypes) -> str:
    if assertion_type == C2PA_AssertionTypes.creative_work:
        return b"json".hex()
    elif assertion_type == C2PA_AssertionTypes.data_hash:
        return b"cbor".hex()
    elif assertion_type == C2PA_AssertionTypes.thumbnail:
        return b"codestream".hex()  # figure out which content type should be
    else:
        return b"".hex()


def get_assertion_label(assertion_type: C2PA_AssertionTypes) -> str:
    if assertion_type == C2PA_AssertionTypes.creative_work:
        return "stds.schema-org.CreativeWork"
    elif assertion_type == C2PA_AssertionTypes.data_hash:
        return "c2pa.hash.data"
    elif assertion_type == C2PA_AssertionTypes.thumbnail:
        return "c2pa.thumbnail.claim.jpg"
    else:
        return ""
