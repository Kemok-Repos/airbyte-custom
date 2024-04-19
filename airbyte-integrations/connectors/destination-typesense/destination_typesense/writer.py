#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

from collections.abc import Mapping
from logging import getLogger
from uuid import uuid4
import re

from typesense import Client

logger = getLogger("airbyte")


class TypesenseWriter:
    write_buffer = []

    def __init__(self, client: Client, stream_name: str, batch_size: int = None):
        self.client = client
        self.stream_name = stream_name
        self.batch_size = batch_size or 10000
        # Initializing text sanitization regex patterns outisde loop for better performance
        self.dot_pattern = re.compile(r'(?<!\d)\.(?!\d)|(?<=\D)\.(?=\d)|(?<=\d)\.(?=\D)')
        self.unit_pattern = re.compile(r'(\d+)([a-zA-Z]+)')

    def queue_write_operation(self, data: Mapping):
        # Set default id if not provided
        data.setdefault("id", str(uuid4()))
        
        # Sanitize necessary text fields
        fields_to_clean = ["nombre", "caracteristicas", "unidad_medida", "detalle"]
        for field in fields_to_clean:
            if field in data:
                data[field] = self.clean_text(data[field])
        
        self.write_buffer.append(data)
        if len(self.write_buffer) == self.batch_size:
            self.flush()

    def flush(self):
        buffer_size = len(self.write_buffer)
        if buffer_size == 0:
            return
        logger.info(f"Uploading {buffer_size} records to Typesense's {self.stream_name} collection")
        self.client.collections[self.stream_name].documents.import_(self.write_buffer, {"action": "upsert"})
        self.write_buffer.clear()

    def clean_text(self, text: str):
        if not text:
            return None
        # Replace all dots with spaces (except decimal places)
        text = self.dot_pattern.sub(' ', text)
        # Separate numbers from units of measurement
        text = self.dot_pattern.sub(r'\1 \2', text)
        return text
