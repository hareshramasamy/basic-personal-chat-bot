"""
Run once to create the DynamoDB tables needed for Phase 4.
Usage: python scripts/create_tables.py
"""
from dotenv import load_dotenv
load_dotenv(override=True)

import boto3
import os

dynamodb = boto3.client("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-2"))

def create_table_if_not_exists(name, key_schema, attr_defs, billing="PAY_PER_REQUEST"):
    existing = dynamodb.list_tables()["TableNames"]
    if name in existing:
        print(f"  {name} already exists, skipping.")
        return
    dynamodb.create_table(
        TableName=name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode=billing,
    )
    print(f"  Created {name}.")

print("Creating avatar-documents table...")
create_table_if_not_exists(
    "avatar-documents",
    key_schema=[
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "doc_id", "KeyType": "RANGE"},
    ],
    attr_defs=[
        {"AttributeName": "user_id", "AttributeType": "S"},
        {"AttributeName": "doc_id", "AttributeType": "S"},
    ],
)

print("Creating avatar-unanswered table...")
create_table_if_not_exists(
    "avatar-unanswered",
    key_schema=[
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "question_id", "KeyType": "RANGE"},
    ],
    attr_defs=[
        {"AttributeName": "user_id", "AttributeType": "S"},
        {"AttributeName": "question_id", "AttributeType": "S"},
    ],
)

print("Creating avatar-contacts table...")
create_table_if_not_exists(
    "avatar-contacts",
    key_schema=[
        {"AttributeName": "user_id", "KeyType": "HASH"},
        {"AttributeName": "contact_id", "KeyType": "RANGE"},
    ],
    attr_defs=[
        {"AttributeName": "user_id", "AttributeType": "S"},
        {"AttributeName": "contact_id", "AttributeType": "S"},
    ],
)

print("Done.")
