#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import datetime
from logging import Logger, getLogger
from typing import Any, Iterable, Mapping
from airbyte_cdk.destinations import Destination
from airbyte_cdk.models import AirbyteConnectionStatus, AirbyteMessage, ConfiguredAirbyteCatalog, DestinationSyncMode, Status, Type
from destination_typesense.writer import TypesenseWriter
from typesense import Client, exceptions


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
        self,
        config: Mapping[str, Any],
        configured_catalog: ConfiguredAirbyteCatalog,
        input_messages: Iterable[AirbyteMessage]
    ) -> Iterable[AirbyteMessage]:
        client = get_client(config=config)

        for configured_stream in configured_catalog.streams:
            stream_name = target_alias = configured_stream.stream.name
            # Escoger la collection template de typesense correspondiente al proceso
            if 'panama_' in stream_name.lower():
                template_collection = 'panama_template_collection'
            elif 'npg' in stream_name.lower():
                template_collection = 'template_collection_npg'
            else:
                template_collection = 'template_collection'
            
            # Obtener la lista de aliases y collections existentes en Typesense
            collections = [col['name'] for col in client.collections.retrieve()]
            aliases = client.aliases.retrieve().get('aliases', [])

            # Collection vieja que se va a reemplazar
            old_collection = next((alias['collection_name'] for alias in aliases if alias['name'] == target_alias), None)

            # Eliminar posibles collections que hayan quedado stale por algún error de Sync en intentos previos
            collections_to_delete = [col for col in collections if col.startswith(target_alias) and col != old_collection]
            for collection in collections_to_delete:
                try:
                    client.collections[collection].delete()
                    logger.info(f"Se elimino la collection stale '{collection}' exitosamente")
                except Exception as e:
                    logger.error(f"Error eliminando collection de typesense {collection}: {e}")
            
            # Definir el nombre de la nueva colección y se crea como un clon del template
            if configured_stream.destination_sync_mode == DestinationSyncMode.overwrite:
                try:
                    stream_name += f'_{datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")}'
                    logger.info(f"Clonando la collection template '{template_collection}' de typesense")
                    client.api_call.post(f'/collections?src_name={template_collection}', {"name": stream_name})
                    logger.info(f"Se creó la collection {stream_name} exitosamente")
                except Exception as e:
                    logger.error(f"Error creando la nueva collection de typesense ({stream_name}): {e}")
                    raise

            # Transferir los records de postgres a typesense
            try:
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
            except Exception as e:
                logger.error(f"Error escribiendo la data en la nueva collection de typesense: {e}")
                logger.warning(f"Se eliminará la collection recién creada ({stream_name}) para evitar datos incompletos")
                client.collections[stream_name].delete()
                raise
            
            # Crear o actualizar el alias para apuntar a la nueva collection
            client.aliases.upsert(target_alias, {'collection_name': stream_name})
            
            # Eliminar la collection vieja en caso de existir
            if old_collection:
                try:
                    client.collections[old_collection].delete()
                    logger.info(f"Se elimino la collection {old_collection} exitosamente")
                except exceptions.ObjectNotFound:
                    logger.info(f"Omitiendo eliminación de la collection anterior {old_collection}. Ya fue eliminada anteriormente o no existe")
                except Exception as e:
                    logger.error(f"Error eliminando collection anterior de typesense {old_collection}: {e}")
                    raise
                
                
    def check(self, logger: Logger, config: Mapping[str, Any]) -> AirbyteConnectionStatus:
        try:
            client = get_client(config=config)
            client.collections.create({"name": "_airbyte", "fields": [{"name": "title", "type": "string"}]})
            client.collections["_airbyte"].documents.create({"id": "1", "title": "The Hunger Games"})
            client.collections["_airbyte"].documents["1"].retrieve()
            client.collections["_airbyte"].delete()
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except (exceptions.ObjectNotFound, exceptions.ObjectAlreadyExists):
            logger.warning("Durante el check inicial la coleccion _airbyte ya existía de antes o no se consiguió, se asumirá que todo está bien...")
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {repr(e)}")
