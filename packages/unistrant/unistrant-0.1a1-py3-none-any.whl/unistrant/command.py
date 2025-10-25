import datetime
import logging
import shutil
from abc import ABC, abstractmethod
from collections.abc import Set
from pathlib import Path

from unistrant.http import CertificateAuthentication, HttpProtocol
from unistrant.options import Options
from unistrant.record import RecordDocument
from unistrant.sams import SamsClient

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    def __init__(self, options: Options):
        super().__init__()
        self.options = options
        self.error = False

        authentication = CertificateAuthentication(options.sams_certificate, options.sams_key)
        protocol = HttpProtocol(authentication)
        self.sams = SamsClient(options.sams_url, protocol)

    @abstractmethod
    def run(self) -> None:
        pass

    def fail(self) -> None:
        if not self.error:
            self.error = True

    @property
    def record_files(self) -> Set[Path]:
        return {file for file in self.options.records_directory.iterdir() if file.is_file()}


class RegisterCommand(BaseCommand):
    def run(self) -> None:
        for path in self.record_files:
            logger.info(f"Processing {path.name}")
            try:
                self.process(path)
            except Exception as e:
                logger.error(f"Error processing {path.name}: {str(e)}")
                self.fail()

    def process(self, path: Path) -> None:
        self.upload(path)
        self.archive(path)

    def upload(self, path: Path) -> None:
        document = RecordDocument(path)
        self.sams.upload_record_document(document)

    def archive(self, path: Path) -> None:
        if (destination := self.options.archive_directory / path.name).exists():
            timestamp = datetime.datetime.now(datetime.UTC).astimezone().isoformat()
            destination = destination.with_name(f"{path.name}-{timestamp}")
        logger.debug(f"Archiving {path.name} to {destination}")
        shutil.move(path, destination)
