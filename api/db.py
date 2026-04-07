import boto3
from boto3.dynamodb.conditions import Key
import os

def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-2"))
    return dynamodb.Table("avatar-users")

def get_docs_table():
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-2"))
    return dynamodb.Table("avatar-documents")

def create_user(user_id: str, name: str, slug: str, email: str, password_hash: str, embed_token_hash: str):
    get_table().put_item(Item={
        "user_id": user_id,
        "name": name,
        "slug": slug,
        "email": email,
        "password_hash": password_hash,
        "embed_token_hash": embed_token_hash,
    })

def get_user_by_email(email: str) -> dict | None:
    result = get_table().query(
        IndexName="email-index",
        KeyConditionExpression="email = :val",
        ExpressionAttributeValues={":val": email}
    )
    items = result.get("Items", [])
    return items[0] if items else None

def get_user_by_id(user_id: str) -> dict | None:
    result = get_table().get_item(Key={"user_id": user_id})
    return result.get("Item")

def get_user_by_embed_token(embed_token_hash: str) -> dict | None:
    result = get_table().query(
        IndexName="embed-token-index",
        KeyConditionExpression="embed_token_hash = :val",
        ExpressionAttributeValues={":val": embed_token_hash}
    )
    items = result.get("Items", [])
    return items[0] if items else None

def update_github_username(user_id: str, github_username: str):
    get_table().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET github_username = :u",
        ExpressionAttributeValues={":u": github_username}
    )

def update_user_config(user_id: str, config: dict):
    get_table().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET avatar_config = :c",
        ExpressionAttributeValues={":c": config}
    )

# ── Document metadata ─────────────────────────────────────────────────────────

def create_document(user_id: str, doc_id: str, filename: str, source_type: str, uploaded_at: str):
    get_docs_table().put_item(Item={
        "user_id": user_id,
        "doc_id": doc_id,
        "filename": filename,
        "source_type": source_type,
        "status": "processing",
        "uploaded_at": uploaded_at,
    })

def update_document_status(user_id: str, doc_id: str, status: str):
    get_docs_table().update_item(
        Key={"user_id": user_id, "doc_id": doc_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status}
    )

def list_documents(user_id: str) -> list:
    result = get_docs_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    return result.get("Items", [])

def delete_document(user_id: str, doc_id: str):
    get_docs_table().delete_item(Key={"user_id": user_id, "doc_id": doc_id})

def get_document(user_id: str, doc_id: str) -> dict | None:
    result = get_docs_table().get_item(Key={"user_id": user_id, "doc_id": doc_id})
    return result.get("Item")

# ── Unanswered questions ──────────────────────────────────────────────────────

def _unanswered_table():
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-2"))
    return dynamodb.Table("avatar-unanswered")

def save_unanswered_question(user_id: str, question_id: str, question: str, asked_at: str):
    _unanswered_table().put_item(Item={
        "user_id": user_id,
        "question_id": question_id,
        "question": question,
        "asked_at": asked_at,
    })

def list_unanswered_questions(user_id: str) -> list:
    result = _unanswered_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    return result.get("Items", [])

def delete_unanswered_question(user_id: str, question_id: str):
    _unanswered_table().delete_item(Key={"user_id": user_id, "question_id": question_id})

def delete_all_documents(user_id: str):
    docs = list_documents(user_id)
    for doc in docs:
        get_docs_table().delete_item(Key={"user_id": user_id, "doc_id": doc["doc_id"]})

def delete_all_unanswered(user_id: str):
    questions = list_unanswered_questions(user_id)
    for q in questions:
        _unanswered_table().delete_item(Key={"user_id": user_id, "question_id": q["question_id"]})

def delete_user(user_id: str):
    get_table().delete_item(Key={"user_id": user_id})

# ── Visitor contacts ──────────────────────────────────────────────────────────

def _contacts_table():
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-2"))
    return dynamodb.Table("avatar-contacts")

def save_visitor_contact(user_id: str, contact_id: str, name: str, email: str, notes: str, contacted_at: str):
    _contacts_table().put_item(Item={
        "user_id": user_id,
        "contact_id": contact_id,
        "name": name,
        "email": email,
        "notes": notes,
        "contacted_at": contacted_at,
    })

def list_visitor_contacts(user_id: str) -> list:
    result = _contacts_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    return result.get("Items", [])