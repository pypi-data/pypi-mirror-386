# Copyright (c) 2024 Fernando Libedinsky
# Product: IAToolkit
#
# IAToolkit is open source software.

from abc import ABC, abstractmethod
from typing import List


class FileConnector(ABC):
    @abstractmethod
    def list_files(self) -> List[str]:
        pass

    @abstractmethod
    def get_file_content(self, file_path: str) -> bytes:
        pass