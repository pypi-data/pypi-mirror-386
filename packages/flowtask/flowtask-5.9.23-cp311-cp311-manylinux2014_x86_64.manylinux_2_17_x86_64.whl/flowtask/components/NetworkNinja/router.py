from collections.abc import Callable
import asyncio
import logging
from datetime import datetime, timezone
import time
from typing import List, Optional, Union
import pandas as pd
import backoff
from datamodel import BaseModel
from asyncdb import AsyncDB, AsyncPool
from datamodel.parsers.json import json_encoder, json_decoder
from datamodel.exceptions import ValidationError
from querysource.interfaces.databases.mongo import DocumentDB
from querysource.conf import default_dsn, async_default_dsn
from querysource.outputs.tables import PgOutput
from ...exceptions import (
    ComponentError,
    DataError,
    ConfigError,
    DataNotFound
)
from ...components import FlowComponent
from ...interfaces.http import HTTPService
from ...conf import (
    NETWORKNINJA_API_KEY,
    NETWORKNINJA_BASE_URL,
    NETWORKNINJA_ENV
)
from .models import NetworkNinja_Map, NN_Order
from .models.abstract import AbstractPayload


logging.getLogger('pymongo').setLevel(logging.INFO)
logging.getLogger('pymongo.client').setLevel(logging.WARNING)


class EmptyQueue(BaseException):
    """Exception raised when the Queue is empty.

    Attributes:
        message -- explanation of the error


        Example:

        ```yaml
        NetworkNinja:
          comment: Download Batch from NetworkNinja.
          action: get_batch
          avoid_acceptance: true
        ```

    """
    pass

class NetworkNinja(HTTPService, FlowComponent):
    """
    NetworkNinja.

        Overview: Router for processing NetworkNinja Payloads.

    Properties:
        +---------------+----------+------------------------------------------+
        | Name          | Required | Description                              |
        +---------------+----------+------------------------------------------+
        | action        | Yes      | Type of operation (get_batch, etc)      |
        +---------------+----------+------------------------------------------+
        | credentials   | No       | API credentials (taken from config)      |
        +---------------+----------+------------------------------------------+
        | payload       | No       | Additional payload parameters            |
        +---------------+----------+------------------------------------------+

    Supported Types:
        - get_batch: Retrieves batch acceptance data
    """
    accept: str = 'application/json'

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ) -> None:
        self._action: str = kwargs.pop('action', None)
        self.chunk_size: int = kwargs.get('chunk_size', 100)
        self.use_proxies: bool = kwargs.pop('use_proxies', False)
        self.paid_proxy: bool = kwargs.pop('paid_proxy', False)
        self.base_url = NETWORKNINJA_BASE_URL
        self.avoid_acceptance: bool = kwargs.get('avoid_acceptance', False)
        self.batch_id: Union[str, list] = kwargs.get('batch_id', None)
        super(NetworkNinja, self).__init__(loop=loop, job=job, stat=stat, **kwargs)
        self.semaphore = asyncio.Semaphore(10)  # Adjust the limit as needed
        self._model_caching: dict = kwargs.get('model_cache', {})
        self._max_size: int = kwargs.get('max_size', 20)
        self._returning: str = kwargs.get('returning', None)
        self.avoid_insert_of: List[str] = kwargs.get('avoid_insert_of', [])
        self._result: dict = {}
        self._pool: AsyncPool = None
        self.accept = 'application/json'
        # AWS DocumentDB connection:
        self._document = DocumentDB(use_pandas=False)
        self._pgoutput = PgOutput(dsn=async_default_dsn, use_async=True)
        # Duplicate detection using hashable tuples
        self._processed_payloads: set = set()
        self._duplicate_count: int = 0
        # Cache for primary keys to avoid repeated introspection
        self._pk_cache: dict = {}
        # Track processed updates to avoid duplicates
        self._processed_updates: set = set()

    def _get_primary_keys(self, data_type: str) -> List[str]:
        """
        Get primary keys for a data type from the model automatically.

        Args:
            data_type: The type of data being processed

        Returns:
            List of primary key field names
        """
        # Check cache first
        if data_type in self._pk_cache:
            return self._pk_cache[data_type]

        try:
            # Get the model for this data type
            mdl = NetworkNinja_Map.get(data_type)
            if not mdl:
                return []

            # Create a minimal instance to access fields
            # Use a dummy payload with required fields
            dummy_payload = {'orgid': 0}

            # Try to create an instance and get primary keys
            try:
                instance = mdl(**dummy_payload)
                fields = instance.columns()
                pk_fields = []
                for field_name, field in fields.items():
                    if hasattr(field, 'primary_key') and field.primary_key:
                        pk_fields.append(field_name)

                # Cache the result
                self._pk_cache[data_type] = pk_fields
                return pk_fields

            except Exception:
                # If we can't create an instance, try to get from class annotations
                if hasattr(mdl, '__annotations__'):
                    # Look for fields with primary_key=True in annotations
                    pk_fields = []
                    for field_name, field_type in mdl.__annotations__.items():
                        if hasattr(field_type, 'primary_key') and field_type.primary_key:
                            pk_fields.append(field_name)

                    self._pk_cache[data_type] = pk_fields
                    return pk_fields

                return []

        except Exception as e:
            self._logger.warning(f"Error getting primary keys for {data_type}: {e}")
            return []

    def _make_hashable(self, value):
        """
        Convert any value to a hashable type.

        Args:
            value: Any value to convert

        Returns:
            A hashable version of the value
        """
        if isinstance(value, (int, float, str, bool, type(None))):
            return value
        elif isinstance(value, list):
            return tuple(self._make_hashable(item) for item in value)
        elif isinstance(value, dict):
            return tuple(sorted((k, self._make_hashable(v)) for k, v in value.items()))
        elif isinstance(value, tuple):
            return tuple(self._make_hashable(item) for item in value)
        else:
            return str(value)

    def _create_payload_key(self, data_type: str, payload: dict) -> tuple:
        """
        Create a hashable tuple key for a payload based on its primary keys.

        Args:
            data_type: The type of data being processed
            payload: The payload dictionary

        Returns:
            A hashable tuple that uniquely identifies this payload
        """
        # Get primary keys automatically from the model
        pk_fields = self._get_primary_keys(data_type)

        if not pk_fields:
            # If no primary keys found, use all fields
            pk_fields = list(payload.keys())

        # Create a hashable tuple with data_type and primary key values
        key_values = [data_type]
        for pk_field in pk_fields:
            if pk_field in payload:
                value = payload[pk_field]
                # Convert to hashable type
                hashable_value = self._make_hashable(value)
                key_values.append(hashable_value)

        return tuple(key_values)

    def _get_model_key(self, data_type: str, item, pk_fields: List[str] = None) -> tuple:
        """
        Create a hashable tuple key for a model instance based on primary keys.

        Args:
            data_type: The type of data being processed
            item: The model instance
            pk_fields: Optional list of primary key field names

        Returns:
            A hashable tuple that uniquely identifies this model instance
        """
        if pk_fields is None:
            pk_fields = self._get_primary_keys(data_type)

        if not pk_fields:
            return (data_type,)

        key_values = [data_type]
        for pk_field in pk_fields:
            value = getattr(item, pk_field, None)
            hashable_value = self._make_hashable(value)
            key_values.append(hashable_value)

        return tuple(key_values)

    def _deduplicate_models(
        self,
        data_type: str,
        items: list,
        pk_fields: Optional[List[str]] = None,
    ) -> list:
        """
        Deduplicate model instances by their primary key fields.

        The last occurrence of a duplicated primary key is kept to ensure the
        most recent payload is persisted.
        """
        if not items:
            return items

        if pk_fields is None:
            pk_fields = self._get_primary_keys(data_type)

        if not pk_fields:
            return items

        deduped = {}
        for item in items:
            key = self._get_model_key(data_type, item, pk_fields)
            deduped[key] = item

        if len(deduped) != len(items):
            self._logger.debug(
                "Deduplicated %s items for %s to %s unique entries",
                len(items),
                data_type,
                len(deduped),
            )

        return list(deduped.values())

    def _is_duplicate_payload(self, data_type: str, payload: dict) -> bool:
        """
        Check if a payload is a duplicate using hashable tuple comparison.

        Args:
            data_type: The type of data being processed
            payload: The payload dictionary

        Returns:
            True if this payload is a duplicate, False otherwise
        """
        try:
            payload_key = self._create_payload_key(data_type, payload)

            if data_type == 'store_photo':
                if payload_key in self._processed_payloads:
                    self._duplicate_count += 1
                    form_id = payload.get('form_id', 'unknown')
                    self._logger.debug(
                        "Duplicate payload detected for %s: form_id=%s",
                        data_type,
                        form_id,
                    )
                self._processed_payloads.add(payload_key)
                return False

            if payload_key in self._processed_payloads:
                self._duplicate_count += 1
                # Extract form_id from payload for cleaner logging
                form_id = payload.get('form_id', 'unknown')
                self._logger.debug(f"Duplicate payload detected for {data_type}: form_id={form_id}")
                return True

            # Add to processed payloads
            self._processed_payloads.add(payload_key)
            return False

        except Exception as e:
            # If we can't create a hashable key, skip duplicate detection
            self._logger.warning(f"Error creating hashable key for {data_type}: {e}")
            return False

    def _identify_final_forms(self, data: list) -> set:
        """
        Identify which forms are final (not updated by others) for DataFrame filtering.

        Args:
            data: List of form_data items

        Returns:
            Set of form_ids that are final (not updated by others)
        """
        if not data:
            return set()

        # Create a mapping of update chains
        update_chains = {}

        # First pass: identify all update chains
        for item in data:
            if hasattr(item, 'previous_form_id') and item.previous_form_id:
                # This is an update
                update_chains[item.previous_form_id] = item.form_id
                self._logger.debug(f"Update chain found: {item.previous_form_id} -> {item.form_id}")

        # Log all update chains
        if update_chains:
            self._logger.debug(f"Update chains identified: {update_chains}")

        # Second pass: find the ultimate final forms
        final_form_ids = set()
        for item in data:
            form_id = item.form_id
            # Check if this form_id is updated by another form
            if form_id in update_chains:
                # This form is updated by another, skip it
                self._logger.debug(f"Form {form_id} is updated by {update_chains[form_id]}, skipping from final forms")
                continue
            else:
                # This is a final form (not updated by any other)
                final_form_ids.add(form_id)
                self._logger.debug(f"Form {form_id} is final (not updated by any other)")

        self._logger.debug(f"Final forms identified: {final_form_ids}")
        return final_form_ids

    async def close(self):
        if self._pool:
            await self._pool.close()

    def _evaluate_input(self):
        if self.previous or self.input is not None:
            self.data = self.input

    async def start(self, **kwargs):
        self._counter: int = 0
        self._evaluate_input()

        # Reset duplicate detection for new processing session
        self._processed_payloads.clear()
        self._duplicate_count = 0
        self._processed_updates.clear()

        if not self._action:
            raise RuntimeError(
                'NetworkNinja component requires a *action* Function'
            )
        if self._action in {'get_batch', 'get_batches'}:
            # Calling Download Batch from NN Queue.
            # Set up headers with API key
            self.headers.update({
                "X-Api-Key": NETWORKNINJA_API_KEY
            })
            return await super(NetworkNinja, self).start(**kwargs)
        # in other cases, NN requires a previous dataset downloaded.
        if not isinstance(self.data, (dict, list)):
            raise ComponentError(
                "NetworkNinja requires a Dictionary or a List as Payload"
            )
        return True

    async def run(self):
        """Run NetworkNinja Router."""
        tasks = []
        fn = getattr(self, self._action)
        self.add_metric("ACTION", self._action)
        self._result = {}
        self._pool = AsyncPool('pg', dsn=default_dsn, max_clients=1000)
        await self._pool.connect()
        if self._action == 'get_batch':
            try:
                result = await fn()
            except EmptyQueue:
                result = {}

            # Check Length of the Payload:
            try:
                if isinstance(result, list):
                    num_elements = len(result)
                elif isinstance(result, dict):
                    num_elements = len(result.get('data', []))
            except TypeError:
                num_elements = 0

            # Add metrics
            self.add_metric("PAYLOAD_LENGTH", num_elements)

            if not result:
                raise DataNotFound(
                    "No data returned from Network Ninja"
                )

            self._result = result
            return self._result
        elif self._action == 'get_batches':
            results = await fn()
            try:
                num_elements = len(results)
            except TypeError:
                num_elements = 0
            self._result = results
            return self._result
        elif self._action == 'process_payload':
            if isinstance(self.data, dict):
                # Typical NN payload extract data from dictionary:
                tasks = [
                    fn(
                        idx,
                        row,
                    ) for idx, row in enumerate(self.data.get('data', []))
                ]
            elif isinstance(self.data, list):
                if self.data[0].get('data', []):
                    # If Data has "data" entries, we need to extract them
                    tasks = []
                    for data in self.data:
                        for idx, row in enumerate(data.get('data', [])):
                            tasks.append(
                                fn(
                                    idx,
                                    row,
                                )
                            )
                else:
                    # Is directly the result of "get_batches"
                    tasks = [
                        fn(
                            idx,
                            row,
                        ) for idx, row in enumerate(self.data)
                    ]
            elif isinstance(self.data, pd.DataFrame):
                tasks = [
                    fn(
                        idx,
                        row,
                    ) for idx, row in self.data.iterrows()
                ]
            # Execute tasks concurrently
            await self._processing_tasks(tasks)
        # Processing and saving the elements into DB:
        self._result = await self._saving_results()

        # Add duplicate detection metrics
        self.add_metric("DUPLICATES_DETECTED", self._duplicate_count)
        self.add_metric("UNIQUE_PAYLOADS_PROCESSED", len(self._processed_payloads))

        # Log duplicate detection summary
        if self._duplicate_count > 0:
            self._logger.debug(
                f"Duplicate detection summary: {self._duplicate_count} duplicates detected, "
                f"{len(self._processed_payloads)} unique payloads processed"
            )

        # Check if the result is empty
        if self._result is None:
            raise DataNotFound(
                "No Forms were returned from Network Ninja"
            )
        if isinstance(self._result, pd.DataFrame) and self._result.empty:
            raise DataNotFound(
                "No Forms were returned from Network Ninja"
            )
        return self._result

    async def _saving_results(self):
        """Using Concurrency to save results.
        """
        tasks = []
        data_types = []
        results_by_type = {}
        for data_type in NN_Order:
            if data_type in self._result:
                data = self._result[data_type]
                self._logger.notice(
                    f"Processing Data Type: {data_type}: {len(data)}"
                )
                try:
                    tasks.append(
                        self._saving_payload(data_type, data)
                    )
                    data_types.append(data_type)
                except Exception as e:
                    self._logger.error(
                        f"Error saving {data_type}: {str(e)}"
                    )
                    results_by_type[data_type] = None  # or some error indicator
        # Execute all saving operations concurrently
        result = await asyncio.gather(*tasks)
        # Create a dictionary mapping data_types to their results
        results_by_type = dict(zip(data_types, result))
        if self._returning:
            return results_by_type.get(self._returning, None)
        else:
            return results_by_type

    async def _process_subtasks(self, tasks: list, batch_size: int = 10) -> None:
        """Process tasks concurrently in batches.
            Args:
                tasks: List of coroutine tasks to execute
                batch_size: Number of tasks to process concurrently in each batch
            Returns:
                List of results from all tasks
        """
        results = []
        for chunk in self.split_parts(tasks, batch_size):
            try:
                result = await asyncio.gather(*chunk, return_exceptions=True)
                if result:
                    results.extend(result)
                    await asyncio.sleep(0.01)  # Yield control to the event loop
            except Exception as e:
                # Log the error but continue with next batches
                logging.error(
                    f"Error in batch processing: {e}"
                )
        return results

    @backoff.on_exception(
        backoff.expo,
        (asyncio.TimeoutError),
        max_tries=2
    )
    async def process_payload(
        self,
        idx,
        row
    ):
        async with self.semaphore:
            # Processing first the Metadata:
            metadata = row.get('metadata', {})
            transaction_type = metadata.get('transaction_type', 'UPSERT')
            if transaction_type == 'DELETE':
                # This is a deletion operation, skip processing
                return None, None
            payload = row.get('payload', {})
            if isinstance(payload, list):
                return None, None
            # payload_time = metadata.get('timestamp')
            orgid = metadata.get('orgid', None)
            if not orgid:
                orgid = payload.get('orgid', None)
            if not orgid:
                self._logger.error(
                    (
                        "NetworkNinja: Organization Id not found in Metadata"
                        f" Current Meta: {metadata}"
                    )
                )
                return None, None
            # Data Type:
            data_type = metadata.get('type', None)
            if not data_type:
                raise DataError(
                    (
                        "NetworkNinja: Data Type not found in Metadata"
                        f" Current Meta: {metadata}"
                    )
                )

            # Creating the Model Instances:
            if data_type not in self._result:
                self._result[data_type] = []
            # Get the Model for the Data Type
            try:
                mdl = NetworkNinja_Map.get(data_type)
            except Exception as e:
                raise DataError(
                    f"NetworkNinja: Model not found for Data Type: {data_type}"
                )
            error = None
            try:
                # First: adding client and org to payload:
                payload['orgid'] = orgid
                # Validate the Data
                data = mdl(**dict(payload))

                # Check for duplicates using hashable tuple comparison AFTER creating the model
                if self._is_duplicate_payload(data_type, payload):
                    self._logger.debug(f"Skipping duplicate payload for {data_type}")
                    return None, None

                # Only add to result if not duplicate
                self._result[data_type].append(data)
                return data, error
            except ValidationError as e:
                self._logger.warning('Error: ==== ', e)
                error = e.payload
                self._logger.warning(
                    f'Validation Errors: {e.payload}'
                )
                # TODO: save bad payload to DB
                return None, error
            except Exception as e:
                print(f'Error: {e}')
                error = str(e)
                return None, error

    @backoff.on_exception(
        backoff.expo,
        (asyncio.TimeoutError),
        max_tries=2
    )
    async def _saving_payload(
        self,
        data_type: str,
        data: list[dict]
    ):
        """
        Save the Payload into the Database.
        """
        async with self.semaphore:
            # Iterate over all keys in data:
            results = None
            if not data:
                return results
            tasks = []

            async def process_item(item, pk):
                conn = None
                async with await self._pool.acquire() as conn:
                    try:
                        await item.on_sync(conn)
                    except Exception as e:
                        self._logger.error(
                            f"Error Sync {data_type} item: {str(e)}"
                        )
                    try:
                        await item.save(conn, pk=pk)
                    except Exception as e:
                        self._logger.error(
                            f"DB Error on {item} item: {str(e)}"
                        )
                if conn is not None:
                    await self._pool.release(conn)

            async def sync_item(item):
                async with await self._pool.acquire() as conn:
                    await item.on_sync(conn)

            # # Handle update chains for form_data - process all but track final results
            # if data_type == 'form_data':
            #     # Keep track of which forms are final (not updated by others)
            #     self._final_forms = self._identify_final_forms(data)
            #     if len(self._final_forms) != len(data):
            #         self._logger.debug(
            #             f"Update chain processing: {len(data)} forms -> {len(self._final_forms)} final forms"
            #         )

            if data_type == 'store_photo':
                data = self._deduplicate_models(data_type, data, pk_fields=['photo_id'])

            for item in data:
                if data_type in self.avoid_insert_of:
                    continue
                if data_type == 'client':
                    tasks.append(
                        process_item(item, pk=['client_id'])
                    )
                elif data_type == 'store':
                    tasks.append(process_item(item, pk=['store_number']))
                elif data_type == 'form_metadata':
                    item.column_name = str(item.column_name)
                    if isinstance(item.orgid, BaseModel):
                        item.orgid = item.orgid.orgid
                    if isinstance(item.formid, BaseModel):
                        # Sync the form with the database
                        item.form_name = item.formid.form_name
                        item.formid = item.formid.formid
                    if isinstance(item.client_id, BaseModel):
                        item.client_id = item.client_id.client_id
                    # Process form_metadata atomically (not concurrent)
                    await process_item(item, pk=['client_id', 'column_name', 'formid'])
                elif data_type == 'store_photo':
                    # Saving the Store Photo
                    item.column_name = str(item.column_name)
                    item.question_name = str(item.question_name)
                    item.url_parts = json_encoder(
                        item.url_parts
                    )
                    if item.categories:
                        item.categories = json_encoder(
                            item.categories
                        )
                    await process_item(item, pk=['photo_id'])
                elif data_type == 'staffing_user':
                    # Saving the Staffing User
                    # Converting lists to JSON:
                    item.custom_fields = json_encoder(
                        item.custom_fields
                    )
                    # item.client_name = json_encoder(
                    #     item.client_name
                    # )
                    tasks.append(
                        process_item(item, pk=['user_id'])
                    )
                elif data_type == 'user':
                    # Saving the User
                    tasks.append(
                        process_item(item, pk=['user_id'])
                    )
                elif data_type == 'form_data':
                    # Saving the Form Data
                    store = item.store
                    store.custom_fields = json_encoder(
                        store.custom_fields
                    )
                    tasks.append(
                        sync_item(store)
                    )
                    # Then, saving the Visitor User:
                    try:
                        user = item.user_id
                        tasks.append(
                            process_item(user, pk=['user_id'])
                        )
                        if user:
                            item.user_id = user.user_id
                    except (AttributeError, TypeError) as exc:
                        self._logger.error(
                            f"Failed Saving User with Id ({user}) for Form ID: {item.form_id}, Error: {exc}"
                        )
                    # Check if there is a previous Form:
                    if item.previous_form_id:
                        try:
                            self._logger.debug(
                                f"Processing form update: form_id={item.form_id} updates previous_form_id={item.previous_form_id}"  # noqa
                            )
                            # swapped:
                            item.current_form_id = item.form_id
                            # Update the form_id on existing form:
                            await item.update_form()
                            self._logger.debug(
                                f"Successfully updated form: form_id={item.form_id} replaced previous_form_id={item.previous_form_id}"  # noqa
                            )
                        except Exception as e:
                            self._logger.error(
                                f"Error swapping form_id: {e}"
                            )
                    # Then, create the tasks for form responses:
                    responses = []
                    if item.has_column('field_responses'):
                        for custom in item.field_responses:
                            custom.form_id = item.form_id
                            custom.formid = item.formid
                            # Set Client and OrgId:
                            custom.client_id = item.client_id
                            custom.orgid = item.orgid
                            custom.event_id = item.event_id
                            responses.append(custom)
                    if responses:
                        try:
                            async with self._pgoutput as conn:
                                await conn.upsert_many(
                                    responses,
                                    table_name='form_responses',
                                    schema='networkninja',
                                    primary_keys=["form_id", "formid", "column_name"],
                                )
                        except Exception as e:
                            self._logger.warning(
                                f"Error saving Field Responses: {e}"
                            )
                    # Process form_data atomically (not concurrent)
                    await process_item(item, pk=['form_id', 'formid'])
                elif data_type == 'form':
                    # Sincronize Organization and Client:
                    orgid = item.client_id.orgid
                    if isinstance(orgid, AbstractPayload):
                        tasks.append(
                            process_item(orgid, pk=['orgid'])
                        )
                    client = item.client_id
                    client.orgid = orgid
                    if isinstance(client, AbstractPayload):
                        tasks.append(
                            process_item(client, pk=['client_id'])
                        )
                    # Convert the Question Blocks to JSON:
                    item.question_blocks = json_encoder(
                        item.question_blocks
                    )
                    tasks.append(
                        process_item(item, pk=['formid'])
                    )
                elif data_type == 'event_cico':
                    tasks.append(
                        process_item(item, pk=['cico_id'])
                    )
                elif data_type == 'event':
                    tasks.append(
                        process_item(item, pk=['event_id'])
                    )
                elif data_type in ('retailer', 'store_geography'):
                    if data_type == 'retailer':
                        tasks.append(
                            process_item(item, pk=['account_id'])
                        )
                    elif data_type == 'store_geography':
                        tasks.append(
                            process_item(item, pk=['geoid'])
                        )
                elif data_type == 'store_type':
                    tasks.append(
                        process_item(item, pk=['store_type_id'])
                    )
                elif data_type == 'project':
                    tasks.append(
                        process_item(item, pk=['project_id'])
                    )
                elif data_type == 'photo_category':
                    tasks.append(
                        process_item(item, pk=['category_id'])
                    )
                elif data_type == 'role':
                    tasks.append(
                        process_item(item, pk=['role_id'])
                    )
            # Now process on_sync operations concurrently
            try:
                await self._process_subtasks(tasks, batch_size=50)
            except Exception as e:
                self._logger.error(
                    f"Error in gather for {data_type}: {str(e)}"
                )
            self._logger.debug(
                f"Successfully saved {data_type}: {len(data)} items."
            )
            # Processing the Form Data as a Dataframe:
            if data_type == 'form_data':
                visits = pd.DataFrame(data)

                # Filter to keep only final forms (not updated by others)
                if hasattr(self, '_final_forms') and self._final_forms:
                    visits = visits[visits['form_id'].isin(self._final_forms)]
                    self._logger.debug(f"Filtered DataFrame: kept {len(visits)} final forms out of {len(data)} total")

                # Drop Unused columns:
                visits = visits.drop(
                    columns=['store_custom_fields'],
                    errors='ignore'
                )

                # Remove duplicate fields from field_responses before exploding
                def clean_field_responses(responses):
                    if isinstance(responses, list):
                        for response in responses:
                            if isinstance(response, dict):
                                # Remove fields that will conflict with main columns
                                response.pop('orgid', None)
                                response.pop('client_id', None)
                                response.pop('form_id', None)
                                response.pop('formid', None)
                                response.pop('event_id', None)
                    return responses
                # Explode the field_responses column
                # Apply the cleaning function
                visits['field_responses'] = visits['field_responses'].apply(clean_field_responses)
                visits = visits.explode('field_responses', ignore_index=True)
                # Convert each dict in 'field_responses' into separate columns
                visits = pd.concat(
                    [
                        visits.drop(['field_responses'], axis=1),
                        visits['field_responses'].apply(pd.Series)
                    ],
                    axis=1
                )
                results = visits
            return results

    async def get_batches(self):
        # I need to call get_batch until:
        # - raise EmptyQueue (no more batches)
        # - Max lenght (self._max_size) is reached
        # - Error occurs
        results = []
        num_elements = 0
        batches = []
        while True:
            try:
                result = await self.get_batch()
                if not result:
                    break
                batch = result.get('data', [])
                try:
                    batches.append(result.get('batch_id', None))
                except Exception as e:
                    self._logger.warning(
                        f"Error getting Batch Id: {e}"
                    )
                batch_len = len(batch)
                num_elements += batch_len
                results.extend(batch)
                self._logger.debug(
                    f"Batch Length: {batch_len}"
                )
            except EmptyQueue:
                break
            except Exception as e:
                self._logger.error(
                    f"Error getting Batch: {e}"
                )
                break
            if num_elements >= self._max_size:
                # We have reached the maximum size
                break
        self.add_metric('BATCHES', batches)
        return results

    async def get_multi_batches(self):
        """
        Get Multiples batches at once.
        """
        base_url = f"{self.base_url}/{NETWORKNINJA_ENV}/get_batch"
        results = []
        num_elements = 0
        batches = []
        for batch in self.batch_id:
            url = f"{base_url}?batch_id={batch}"
            args = {
                "method": "get",
                "url": url,
                "use_proxy": False,
                "return_response": True,
            }
            response, result, error = await self.session(**args)
            if response.status_code == 204:
                continue
            if not result or error is not None:
                break
            batch = result.get('data', [])
            try:
                batches.append(result.get('batch_id', None))
            except Exception as e:
                self._logger.warning(
                    f"Error getting Batch Id: {e}"
                )
            batch_len = len(batch)
            num_elements += batch_len
            results.extend(batch)
            self._logger.debug(
                f"Batch Length: {batch_len}"
            )
        self.add_metric('BATCHES', batches)
        return results

    async def get_batch(self):
        """Handle get_batch operation type

        Uses to download a Batch from NetworkNinja SQS Queue.
        """
        url = f"{self.base_url}/{NETWORKNINJA_ENV}/get_batch"
        if isinstance(self.batch_id, list):
            return await self.get_multi_batches()
        if self.batch_id:
            url += f"?batch_id={self.batch_id}"
            self.avoid_acceptance = True  # avoid accepting the batch

        args = {
            "method": "get",
            "url": url,
            "use_proxy": False,
            "return_response": True,
        }

        response, result, error = await self.session(**args)
        if response.status_code == 204:
            # There is no data to download and is normal.
            raise EmptyQueue(
                "No data to download from NetworkNinja"
            )

        if error:
            raise ComponentError(
                f"Error calling Network Ninja API: {error}"
            )

        if not result:
            raise DataNotFound(
                "No data returned from Network Ninja"
            )

        # Saving Batch for security/auditing purposes in DocumentDB:
        try:
            await self._document.write(
                table='batches',
                schema='networkninja',
                data=[result],
                on_conflict='replace'
            )
        except Exception as e:
            self._logger.error(
                f"Error saving Batch into *batches* auditing catalog: {e}"
            )

        # Then, extract batch id and report to NN:
        batch_id = result.get('batch_id')
        self._logger.notice(
            f"Batch Id: {batch_id}"
        )
        self.add_metric('LAST_BATCH', batch_id)
        if self.avoid_acceptance is False:
            # Only report the batch if acceptance is enabled.
            await self.report_batch(batch_id)
        return result

    async def report_batch(self, batch_id: str, report_code: int = 200):
        """Handle report_batch operation type

        Uses to report a Batch to NetworkNinja SQS Queue.
        """
        url = f"{self.base_url}/{NETWORKNINJA_ENV}/report_batch_activity"

        payload = {
            "batch_id": batch_id,
            "status_code": report_code
        }
        args = {
            "url": url,
            "use_proxy": False,
            "payload": payload,
            "full_response": True
        }
        result = None
        try:
            response = await self.api_post(**args)
            # TODO: handle error codes (504, 404, etc)
            if response.status_code != 200:
                if response.status_code == 404:
                    self._logger.error(
                        f"HTTP error: {response.status_code} - Batch {batch_id} not found"
                    )
                elif response.status_code == 504:
                    self._logger.error(
                        f"HTTP error: {response.status_code} - Network Ninja API is unavailable"
                    )
            else:
                result = response.json()
        except Exception as e:
            self._logger.error(
                f"Error Reporting Batch with id {batch_id}: {e}"
            )

        if not result:
            raise DataNotFound(
                "No data returned from Network Ninja"
            )
        return result

    async def upsert_record(self, obj: Union[dict, BaseModel], **kwargs):
        # TODO: Discover primary Keys from Model instead from Database.
        if isinstance(obj, BaseModel):
            name = obj.modelName
            pk = self._model_caching.get(name, None)
            if not pk:
                pk = []
                fields = obj.columns()
                for _, field in fields.items():
                    if field.primary_key:
                        pk.append(field.name)
                self._model_caching[name] = pk
            table_name = obj.Meta.name
            schema = obj.Meta.schema
        else:
            pk = kwargs.get('pk', [])
            table_name = kwargs.get('table_name', None)
            schema = kwargs.get('schema', None)
        async with self._pgoutput as conn:
            await conn.do_upsert(
                obj,
                table_name=table_name,
                schema=schema,
                primary_keys=pk,
                use_conn=conn.get_connection()
            )
            return True

    async def replace_record(self, obj: Union[dict, BaseModel], **kwargs):
        # TODO: Discover primary Keys from Model instead from Database.
        if isinstance(obj, BaseModel):
            name = obj.modelName
            pk = self._model_caching.get(name, None)
            if not pk:
                pk = []
                fields = obj.columns()
                for _, field in fields.items():
                    if field.primary_key:
                        pk.append(field.name)
                self._model_caching[name] = pk
            table_name = obj.Meta.name
            schema = obj.Meta.schema
        else:
            pk = kwargs.get('pk', [])
            table_name = kwargs.get('table_name', None)
            schema = kwargs.get('schema', None)
        async with self._pgoutput as conn:
            await conn.do_replace(
                obj,
                table_name=table_name,
                schema=schema,
                primary_keys=pk,
                use_conn=conn.get_connection()
            )
            return True
