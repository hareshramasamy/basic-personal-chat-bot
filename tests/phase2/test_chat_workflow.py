"""
Phase 2 Chat Workflow Test
Tests: signup → document upload → chat

Usage:
    python test_chat_workflow.py

Requires the server to be running:
    uvicorn api.main:app --reload
"""

import requests
import time

BASE_URL = "http://localhost:8000"

# ── Test user (change if already exists in DynamoDB) ──────────────────────────
TEST_USER = {
    "name": "Haresh Ramasamy",
    "slug": "haresh",
    "email": "haresh_test@example.com",
    "password": "testpassword123",
    "github_username": "hareshramasamy",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def check(label, resp, expected_status=200):
    ok = resp.status_code == expected_status
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label} — HTTP {resp.status_code}")
    if not ok:
        print(f"       {resp.text}")
    return ok, resp.json() if ok else {}


# ── 1. Health check ───────────────────────────────────────────────────────────

print("\n=== 1. Health check ===")
r = requests.get(f"{BASE_URL}/health")
check("GET /health", r)


# ── 2. Signup (first run) or Login (subsequent runs) ─────────────────────────

print("\n=== 2. Signup ===")
r = requests.post(f"{BASE_URL}/signup", json=TEST_USER)
signup_ok, signup_data = check("POST /signup", r)

if signup_ok:
    # Fresh signup — all tokens available directly
    access_token = signup_data["access_token"]
    user_id = signup_data["user_id"]
    embed_token = signup_data["embed_token"]
else:
    # User already exists — login to get JWT, embed_token stored in DynamoDB
    print("       (user already exists, logging in...)")
    print("\n=== 3. Login ===")
    r = requests.post(f"{BASE_URL}/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
    })
    ok, data = check("POST /login", r)
    if not ok:
        print("Cannot continue without auth token.")
        raise SystemExit(1)
    access_token = data["access_token"]
    user_id = data["user_id"]
    embed_token = data.get("embed_token", "")
    if not embed_token:
        print("[FAIL] embed_token not returned — delete the test user from DynamoDB and re-run to start fresh.")
        raise SystemExit(1)

print(f"       user_id    = {user_id}")
print(f"       embed_token = {embed_token}")

headers = {"Authorization": f"Bearer {access_token}"}


# ── 4. Upload a document ──────────────────────────────────────────────────────

print("\n=== 4. Upload document (raw text) ===")
r = requests.post(
    f"{BASE_URL}/users/{user_id}/documents",
    headers=headers,
    data={
        "raw_text": (
            "Haresh Ramasamy is a software engineer with 5 years of experience. "
            "He specialises in Python, AWS, and machine learning systems. "
            "He has built production RAG pipelines and agentic AI platforms. "
            "He is currently open to senior ML/backend engineering roles."
        ),
    },
)
ok, doc_data = check("POST /users/{user_id}/documents", r)
if ok:
    print(f"       doc_id = {doc_data.get('doc_id')}")
    print("       Waiting 5s for async ingestion to complete...")
    time.sleep(5)


# ── 5. Upload GitHub profile ─────────────────────────────────────────────────

print("\n=== 5. Upload GitHub profile (static ingestion) ===")
r = requests.post(
    f"{BASE_URL}/users/{user_id}/documents",
    headers=headers,
    data={"github_profile_url": f"https://github.com/{TEST_USER['github_username']}"},
)
ok, github_doc_data = check("POST /users/{user_id}/documents (github_profile)", r)
if ok:
    print(f"       doc_id = {github_doc_data.get('doc_id')}")
    print("       Waiting 10s for async GitHub ingestion to complete...")
    time.sleep(10)


# ── 6. Upload LinkedIn PDF ───────────────────────────────────────────────────

ME_DIR = "/Users/hareshramasamy/Workspace/Projects/avatar-ai/me"

print("\n=== 6. Upload LinkedIn PDF ===")
with open(f"{ME_DIR}/linkedin.pdf", "rb") as f:
    r = requests.post(
        f"{BASE_URL}/users/{user_id}/documents",
        headers=headers,
        files={"file": ("linkedin.pdf", f, "application/pdf")},
    )
ok, linkedin_doc_data = check("POST /users/{user_id}/documents (linkedin.pdf)", r)
if ok:
    print(f"       doc_id = {linkedin_doc_data.get('doc_id')}")

print("\n=== 6b. Upload summary.txt ===")
with open(f"{ME_DIR}/summary.txt", "rb") as f:
    r = requests.post(
        f"{BASE_URL}/users/{user_id}/documents",
        headers=headers,
        files={"file": ("summary.txt", f, "text/plain")},
    )
ok, summary_doc_data = check("POST /users/{user_id}/documents (summary.txt)", r)
if ok:
    print(f"       doc_id = {summary_doc_data.get('doc_id')}")

print("       Waiting 5s for async ingestion to complete...")
time.sleep(5)


# ── 7. Chat – basic question ──────────────────────────────────────────────────

print("\n=== 7. Chat — basic question ===")
r = requests.post(f"{BASE_URL}/chat", json={
    "embed_token": embed_token,
    "message": "What are your main technical skills?",
    "history": [],
})
ok, chat_data = check("POST /chat (skills question)", r)
if ok:
    print(f"\n   Response:\n   {chat_data['response']}\n")


# ── 8. Chat – LinkedIn question ──────────────────────────────────────────────

print("\n=== 8. Chat — LinkedIn question ===")
r = requests.post(f"{BASE_URL}/chat", json={
    "embed_token": embed_token,
    "message": "What companies have you worked at?",
    "history": [],
})
ok, linkedin_chat = check("POST /chat (linkedin work experience)", r)
if ok:
    print(f"\n   Response:\n   {linkedin_chat['response']}\n")


# ── 9. Chat – multi-turn (history passed) ────────────────────────────────────

print("\n=== 9. Chat — multi-turn with history ===")
history = [
    {"role": "user", "content": "What are your main technical skills?"},
    {"role": "assistant", "content": chat_data.get("response", "")},
]
r = requests.post(f"{BASE_URL}/chat", json={
    "embed_token": embed_token,
    "message": "Are you open to new opportunities?",
    "history": history,
})
ok, chat_data2 = check("POST /chat (follow-up question)", r)
if ok:
    print(f"\n   Response:\n   {chat_data2['response']}\n")


# ── 10. Chat – unknown question (triggers record_unknown_question tool) ───────

print("\n=== 10. Chat — unknown question ===")
r = requests.post(f"{BASE_URL}/chat", json={
    "embed_token": embed_token,
    "message": "What is your favourite recipe for pasta?",
    "history": [],
})
ok, chat_data3 = check("POST /chat (unknown question)", r)
if ok:
    print(f"\n   Response:\n   {chat_data3['response']}\n")


# ── 11. Chat – live GitHub fetch ─────────────────────────────────────────────

print("\n=== 11. Chat — live GitHub fetch ===")
r = requests.post(f"{BASE_URL}/chat", json={
    "embed_token": embed_token,
    "message": "What have you been working on recently?",
    "history": [],
})
ok, chat_data4 = check("POST /chat (recent projects — triggers fetch_live_github_stats)", r)
if ok:
    print(f"\n   Response:\n   {chat_data4['response']}\n")


print("\n=== Done ===")
