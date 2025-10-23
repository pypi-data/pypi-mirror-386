# Django CSV Exporter

Simple CSV export for Django.

## Installation
```bash
pip install django-csv-exporter
```

## Usage

### Basic Export
```python
from django_csv_exporter import CSVExporter

exporter = CSVExporter(headers=['ID', 'Name'])
exporter.add_row([1, 'Alice'])
exporter.add_row([2, 'Bob'])
return exporter.export()
```

### Streaming Export
```python
from django_csv_exporter import StreamingCSVExporter

exporter = StreamingCSVExporter(
    headers=['ID', 'Name'],
    filename='users',
    serializer=lambda u: [u.id, u.name],
    iterator=User.objects.all().iterator()
)
return exporter.export()
```