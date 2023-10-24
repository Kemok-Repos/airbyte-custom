#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import datetime
from logging import Logger, getLogger
from typing import Any, Iterable, Mapping
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, ConfiguredAirbyteCatalog, DestinationSyncMode, Status, Type
from destination_typesense.writer import TypesenseWriter
from typesense import Client


logger = getLogger("airbyte")


def get_client(config: Mapping[str, Any]) -> Client:
    api_key = config.get("api_key")
    host = config.get("host")
    port = config.get("port") or "8108"
    protocol = config.get("protocol") or "https"
    timeout = config.get("timeout") or 3600
    
    client = Client({"api_key": api_key, "nodes": [{"host": host, "port": port, "protocol": protocol}], "connection_timeout_seconds": timeout})

    return client


class DestinationTypesense(Destination):
    def write(
        self, config: Mapping[str, Any], configured_catalog: ConfiguredAirbyteCatalog, input_messages: Iterable[AirbyteMessage]
    ) -> Iterable[AirbyteMessage]:
        client = get_client(config=config)

        for configured_stream in configured_catalog.streams:
            stream_name = configured_stream.stream.name
            # Variables en caso de ser NPGs
            npg_type = 'npg' in stream_name.lower()
            sufix = '_npg' if npg_type else ''
            
            if configured_stream.destination_sync_mode == DestinationSyncMode.overwrite:
                try:
                    collections = [collection['name'] for collection in client.collections.retrieve()]
                    # En caso de no ser NPGs client.collections.retrieve no regresa el alias
                    if stream_name in collections and not npg_type:
                        logger.info(f"Borrando de typesense la collection {stream_name}")
                        client.collections[stream_name].delete()
                    if npg_type:
                        # Se define el nombre de la nueva colección
                        stream_name += datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                        
                    logger.info(f"Clonando collection template de typesense")
                    client.api_call.post(f'/collections?src_name=template_collection{sufix}', {"name": stream_name})
                    logger.info(f"Se creó la collection {stream_name} exitosamente")
                except Exception as e:
                    logger.error(f"Error recreando collection de typesense {stream_name}: {e}")
                    return

            writer = TypesenseWriter(client, stream_name, config.get("batch_size"))
            for message in input_messages:
                if message.type == Type.STATE:
                    writer.flush()
                    yield message
                elif message.type == Type.RECORD:
                    writer.queue_write_operation(message.record.data)
                else:
                    continue
            writer.flush()
            
            if npg_type:
                expected_collection_name = configured_stream.stream.name
                
                # Se busca el nombre de la colección desactualizada
                old_collection = [alias['collection'] for alias in client.aliases.retrieve()['aliases'] if alias['name'] == expected_collection_name]
                
                # Se crea o actualiza el alias
                client.aliases.upsert(expected_collection_name, aliased_collection = {'collection_name': stream_name})
                
                # Elimación de la colección desactualizada
                if old_collection:
                    client.collections[old_collection[0]].delete()
                

                

            

    def check(self, logger: Logger, config: Mapping[str, Any]) -> AirbyteConnectionStatus:
        try:
            client = get_client(config=config)
            client.collections.create({"name": "_airbyte", "fields": [{"name": "title", "type": "string"}]})
            client.collections["_airbyte"].documents.create({"id": "1", "title": "The Hunger Games"})
            client.collections["_airbyte"].documents["1"].retrieve()
            client.collections["_airbyte"].delete()
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")
