# CNRI JSON Streaming

This library provides a streaming API for reading JSON from inputs including file-like objects.
This can be useful when needing to read from very large JSON objects.
Instead of reading the entire object into memory, objects can be read off of it one by one.

The current implementation uses [ijson](https://pypi.org/project/ijson/).
Exceptions are raised as ijson.JsonError.

## Installation

    pip install cnri_json_streaming

## Usage

The library provides two main ways to parse JSON:

1. `JsonReader` - A streaming reader for incremental JSON parsing
2. `json_parse` - A simple function for parsing entire JSON content using JsonReader

### Using JsonReader

The `JsonReader` class provides a high level of control over the parsing process, allowing you to read JSON incrementally:

```python
from urllib.request import urlopen
from cnri_json_streaming import JsonReader

## Create a reader from a urlopen response
with urlopen('https://example.com/large_data.json') as response:
    with JsonReader(response.read()) as json_reader:
        # Read a JSON object incrementally
        json_reader.start_map()
        while json_reader.has_next():
            property_name = json_reader.next_map_key()
            if property_name == 'results':
                # Read an array of objects
                json_reader.start_array()
                while json_reader.has_next():
                    result = json_reader.next_json()
                    print(result['id'])
                json_reader.end_array()
            elif property_name == 'size':
                # Read a number
                count = json_reader.next_json()
                print(f"Total results: {count}")
            else:
                # Skip properties we don't care about
                print(f"Skipping property: {property_name}")
                json_reader.skip_value()
        json_reader.end_map()
```

### Using json_parse

The `json_parse` function provides a way to parse JSON from various input sources including file-like objects.
json_parse should be more memory-efficient than reading an entire stream into a string and then using json.loads.
This function is mostly used for testing.

```python
from urllib.request import urlopen
from cnri_json_streaming import json_parse

#  Parse JSON from a string
data = json_parse('{"item": "Widget", "count": 1000}')
print(data['item'])  # "Widget"

# Parse JSON from a fetch response
with urlopen('https://example.com/large_data.json') as response:
    result = json_parse(response.read())
    print(result['size'])
    print(result['results'][0])
    print(result['results'][0]['id'])
```
