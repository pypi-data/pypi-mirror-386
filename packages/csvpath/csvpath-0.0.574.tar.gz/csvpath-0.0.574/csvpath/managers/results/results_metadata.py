from csvpath.managers.metadata import Metadata
from datetime import datetime
from uuid import UUID


class ResultsMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        self.run_home: str = None
        self.named_paths_name: str = None
        self.named_paths_uuid: UUID = None
        self.named_results_name: str = None
        self.named_file_uuid: str = None
        self.named_file_name: str = None
        self.named_file_path: str = None
        self.named_file_fingerprint: str = None
        self.named_file_fingerprint_on_file: str = None
        self.named_file_size: str = None
        self.named_file_last_change: str = None
        self.status: str = None
        self.all_completed: bool = None
        self.all_valid: bool = None
        self.error_count: int = 0
        self.all_expected_files: bool = None
        self.by_line: bool = False
        self._run_uuid: UUID = None
        self._method: str = None

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, m: str) -> None:
        self._method = m

    @property
    def run_uuid(self) -> UUID:
        return self._run_uuid

    @run_uuid.setter
    def run_uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._run_uuid = u

    @property
    def run_uuid_string(self) -> str:
        return str(self._run_uuid)

    @run_uuid_string.setter
    def run_uuid_string(self, u: str) -> None:
        self._run_uuid = UUID(u)

    @property
    def named_paths_uuid(self) -> UUID:
        return self._named_paths_uuid

    @named_paths_uuid.setter
    def named_paths_uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._named_paths_uuid = u

    @property
    def named_paths_uuid_string(self) -> str:
        return str(self._named_paths_uuid)

    @named_paths_uuid_string.setter
    def named_paths_uuid_string(self, u: str) -> None:
        self._named_paths_uuid = UUID(u)

    @property
    def named_file_uuid(self) -> UUID:
        return self._named_file_uuid

    @named_file_uuid.setter
    def named_file_uuid(self, u: UUID) -> None:
        if u and not isinstance(u, UUID):
            raise ValueError("Must be a UUID")
        self._named_file_uuid = u

    @property
    def named_file_uuid_string(self) -> str:
        return str(self._named_file_uuid)

    @named_file_uuid_string.setter
    def named_file_uuid_string(self, u: str) -> None:
        self._named_file_uuid = UUID(u)

    def from_manifest(self, m) -> None:
        if m is None:
            return
        super().from_manifest(m)
        self.run_home = m["run_home"]
        self.run_uuid_string = m.get("run_uuid")
        self.named_paths_name = m.get("named_paths_name")
        self.named_paths_uuid_string = m.get("named_paths_uuid")
        self.named_file_name = m.get("named_file_name")
        self.named_file_uuid_string = m.get("named_file_uuid")
        self.named_file_path = m.get("named_file_path")
        self.named_file_fingerprint = m.get("named_file_fingerprint")
        self.named_file_fingerprint_on_file = m.get("")
        # TODO?
        self.named_file_size: str = m.get("")
        self.named_file_last_change = m.get("")
        self.all_completed = m.get("all_completed")
        self.all_valid = m.get("all_valid")
        self.error_count = m.get("error_count")
        self.all_expected_files = m.get("all_expected_files")
        self.method = m.get("method")
