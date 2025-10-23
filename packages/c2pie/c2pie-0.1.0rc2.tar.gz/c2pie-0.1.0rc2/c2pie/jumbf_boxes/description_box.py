# Description jumbf box class

from c2pie.jumbf_boxes.box import Box
from c2pie.utils.content_types import jumbf_content_types


class DescriptionBox(Box):
    def __init__(
        self,
        content_type: bytes = jumbf_content_types["json"],
        label: str = "",
    ):
        self.label = label
        self.content_type = content_type
        self.toggle = 3

        payload = self.content_type + self.toggle.to_bytes(1, "big") + self.label.encode("utf-8") + b"\x00"

        super().__init__(b"jumd".hex(), payload=payload)

    def get_label(self) -> str:
        return self.label

    def get_content_type(self) -> bytes:
        return self.content_type
