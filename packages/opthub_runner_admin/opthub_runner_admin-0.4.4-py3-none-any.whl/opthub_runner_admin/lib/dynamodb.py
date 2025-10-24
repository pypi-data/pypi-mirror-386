"""This module provides a wrapper class for Amazon DynamoDB."""

import logging
from typing import Any, TypedDict, cast

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import BotoCoreError

from opthub_runner_admin.models.schema import FlagSchema, Schema

LOGGER = logging.getLogger(__name__)


class PrimaryKey(TypedDict):
    """This class represents the primary key."""

    ID: str
    Trial: str


class DynamoDBOptions(TypedDict):
    """The options for DynamoDB."""

    region_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    table_name: str


class DynamoDB:
    """This class provides a wrapper for Amazon DynamoDB."""

    def __init__(
        self,
        options: DynamoDBOptions,
    ) -> None:
        """Initialize the class.

        Args:
            options (DynamoDBOptions): The options for DynamoDB.
        """
        self.dynamoDB = boto3.resource(
            service_name="dynamodb",
            region_name=options["region_name"],
            aws_access_key_id=options["aws_access_key_id"],
            aws_secret_access_key=options["aws_secret_access_key"],
        )
        self.table_name = options["table_name"]
        self.table = self.dynamoDB.Table(self.table_name)

        self.client = boto3.client(
            service_name="dynamodb",
            region_name=options["region_name"],
            aws_access_key_id=options["aws_access_key_id"],
            aws_secret_access_key=options["aws_secret_access_key"],
        )

        self.serializer = TypeSerializer()

    def check_accessible(self) -> None:
        """Check if the table is accessible."""
        self.table.get_item(Key={"ID": "dummyID", "Trial": "dummyTrial"})

    def get_item(self, primary_key_value: PrimaryKey) -> dict[str, Any] | None:
        """Get item from DynamoDB.

        Args:
            primary_key_value (PrimaryKey): The primary key value.

        Returns:
            Any | None: The item.
        """
        item: dict[str, Any] | None = self.table.get_item(Key=cast(dict[str, Any], primary_key_value)).get("Item")
        return item

    def is_exist(self, primary_key_value: PrimaryKey) -> bool:
        """Check if the item exists in DynamoDB.

        Args:
            primary_key_value (PrimaryKey): The primary key value.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        item = self.get_item(primary_key_value)
        return item is not None

    def put_item(self, item: Schema) -> None:
        """Put item to DynamoDB.

        Args:
            item (Schema): The item to put.
        """
        try:
            flag_item: FlagSchema = {
                "ID": item["ID"],
                "Trial": item["TrialNo"],
                "IgnoreStream": True,
            }
            serialized_item = {key: self.serializer.serialize(value) for key, value in item.items()}
            serialized_flag_item = {key: self.serializer.serialize(value) for key, value in flag_item.items()}

            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": serialized_item,
                        },
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": serialized_flag_item,
                            "ConditionExpression": "attribute_not_exists(ID)",
                        },
                    },
                ],
            )
        except BotoCoreError as e:
            msg = "Failed to put item to DynamoDB."
            LOGGER.exception(msg)
            raise BotoCoreError from e

    def get_items_between_least_and_greatest(
        self,
        partition_key: str,
        least_trial: str,
        greatest_trial: str,
        attributes: list[str],
    ) -> list[Any]:
        """Get items from DynamoDB between least_trial and greatest_trial.

        Args:
            partition_key (str): The partition key.
            least_trial (str): The least trial.
            greatest_trial (str): The greatest trial.
            attributes (list[str]): The attributes to get.

        Returns:
            list[Any]: The items.
        """
        items: list[dict[str, Any]] = []
        last_evaluated_key: dict[str, Any] | None = None

        while True:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": Key("ID").eq(partition_key)
                & Key("Trial").between(least_trial, greatest_trial),
            }

            if last_evaluated_key:
                query_kwargs["ExclusiveStartKey"] = last_evaluated_key

            if attributes:
                query_kwargs["ProjectionExpression"] = ",".join([f"#attr{i}" for i in range(len(attributes))])
                query_kwargs["ExpressionAttributeNames"] = {f"#attr{i}": attr for i, attr in enumerate(attributes)}

            response = self.table.query(**query_kwargs)

            # Append fetched items
            items.extend(response.get("Items", []))

            # Check if there are more items to fetch
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break

        return items
