#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

from collections.abc import Mapping
from logging import getLogger
from uuid import uuid4

from typesense import Client

logger = getLogger("airbyte")


class TypesenseWriter:
    write_buffer = []

    def __init__(self, client: Client, stream_name: str, batch_size: int = None):
        self.client = client
        self.stream_name = stream_name
        self.batch_size = batch_size or 10000

    def queue_write_operation(self, data: Mapping):
        random_key = str(uuid4())
        data_with_id = data if ("id" in data and data["id"]) else {**data, "id": random_key}
        self.write_buffer.append(data_with_id)
        if len(self.write_buffer) == self.batch_size:
            self.flush()

    def flush(self):
        buffer_size = len(self.write_buffer)
        if buffer_size == 0:
            return
        logger.info(f"uploading {buffer_size} records to Typesense's {self.stream_name} collection")
        self.client.collections[self.stream_name].documents.import_(self.write_buffer, {"action": "upsert"})
        self.write_buffer.clear()
