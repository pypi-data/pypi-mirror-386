import csv
import time
import os
from typing import List, Any
from csvpath.util.line_monitor import LineMonitor
from .file_readers import DataFileReader


class LineCounter:
    """CsvPath and FilesManager uses the line counter to find the total number of lines
    and the first data line to use as headers.
    """

    #
    # csvpathx can be either CsvPath or CsvPaths
    #
    def __init__(self, csvpathx) -> None:
        # just need quotechar, delimiter, and logger
        self.csvpathx = csvpathx

    def get_lines_and_headers(
        self, path: str
    ) -> tuple[LineMonitor, List[Any]]:  # pylint: disable=C0116
        lm = LineMonitor()
        headers = None
        start = time.time()
        # we just created lm. how could it not be None/-1?
        if lm.physical_end_line_number is None or lm.physical_end_line_number == -1:
            lm.reset()
            reader = DataFileReader(
                path,
                delimiter=self.csvpathx.delimiter,
                quotechar=self.csvpathx.quotechar,
            )
            for line in reader.next():
                lm.next_line(last_line=[], data=line)
                if len(line) == 0 and self.csvpathx.skip_blank_lines:
                    continue
                if (not headers or len(headers) == 0) and len(line) > 0:
                    headers = line[:]
        if not headers:
            headers = []
        headers = LineCounter.clean_headers(headers)
        end = time.time()
        self.csvpathx.logger.info(
            "Counting lines and getting headers took %s", round(end - start, 2)
        )
        lm.set_end_lines_and_reset()
        return (lm, headers)

    @classmethod
    def clean_headers(self, headers: List[str]) -> List[str]:
        hs = []
        for header in headers:
            header = header.strip()
            header = header.replace(";", "")
            header = header.replace(",", "")
            header = header.replace("|", "")
            header = header.replace("\t", "")
            header = header.replace("`", "")
            hs.append(header)
        return hs
