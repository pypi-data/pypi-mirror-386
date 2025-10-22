"""CSV exporter classes - your original code"""

from django.http import StreamingHttpResponse, HttpResponse
from typing import List, Optional
import csv


class CSVBuffer:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Return the string to write."""
        return value


class StreamingCSVExporter:
    def __init__(
        self,
        headers: Optional[List[str]] = None,
        filename: str = "export",
        serializer=None,
        iterator=None
    ):
        self._headers = headers
        self._filename = filename
        self._serializer = serializer
        self._iterator = iterator
        self._writer = csv.writer(CSVBuffer())

    def _stream(self):
        if self._headers:
            yield self._writer.writerow(self._headers)
        for data in self._iterator:
            yield self._writer.writerow(self._serializer(data))

    def export(self):
        response = StreamingHttpResponse(self._stream(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{self._filename}.csv"'
        return response


class CSVExporter:
    def __init__(self, headers: List[str], filename: str = "export", validation: bool = True):
        self.row_count: int = 0
        self._headers: List[str] = headers
        self._validation: bool = validation
        self._http_response: HttpResponse = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.csv"'
            }
        )
        self._writer = csv.writer(self._http_response)
        self._writer.writerow(self._headers)

    def add_row(self, row: List) -> 'CSVExporter':
        if self._validation and len(row) != len(self._headers):
            raise ValueError(
                f"Row length ({len(row)}) doesn't match headers length ({len(self._headers)})"
            )
        self._writer.writerow(row)
        self.row_count += 1
        return self

    def add_rows(self, rows: List[List]) -> 'CSVExporter':
        if self._validation:
            for row in rows:
                if len(row) != len(self._headers):
                    raise ValueError(
                        f"Row length ({len(row)}) doesn't match headers length ({len(self._headers)})"
                    )
        self._writer.writerows(rows)
        self.row_count += len(rows)
        return self

    def export(self) -> HttpResponse:
        return self._http_response

    def __len__(self) -> int:
        return self.row_count

    def __repr__(self) -> str:
        return f"CSVExporter(headers={self._headers}, rows={self.row_count})"