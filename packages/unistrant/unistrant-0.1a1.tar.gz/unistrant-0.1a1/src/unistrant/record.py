import enum
import xml.etree.ElementTree as ET
from pathlib import Path

from unistrant.error import RecordError


class RecordType(enum.StrEnum):
    UsageRecord = "{http://schema.ogf.org/urf/2003/09/urf}UsageRecords"
    StorageUsageRecord = "{http://eu-emi.eu/namespaces/2011/02/storagerecord}StorageUsageRecords"
    CloudRecord = "{http://sams.snic.se/namespaces/2016/04/cloudrecords}CloudRecords"
    SoftwareAccountingRecord = "{http://sams.snic.se/namespaces/2019/01/softwareaccountingrecords}SoftwareAccountingRecord"


class RecordDocument:
    def __init__(self, path: Path):
        with path.open("rb") as f:
            try:
                tree = ET.parse(f)
            except ET.ParseError as e:
                raise RecordError(f"Record parser error: {str(e)}")
        ET.indent(tree)
        if root := tree.getroot():
            root_tag = root.tag
        else:
            raise RecordError("Missing root tag")
        try:
            self._record_file_type = RecordType(root_tag)
        except ValueError:
            raise RecordError(f"Unsupported root tag: {root_tag}")
        self.tree = tree

    @property
    def record_file_type(self) -> RecordType:
        return self._record_file_type

    @property
    def bytes(self) -> bytes:
        return ET.tostring(self.tree.getroot())
