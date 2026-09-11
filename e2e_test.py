import requests
import time
import os

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {"email": "e2e_test@example.com", "password": "password123", "name": "E2E Test User"}
PDF_PATH = "test_doc.pdf"

def run_test():
    # 1. Register/Login
    print("Registering user...")
    res = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
    if res.status_code == 400 and "already" in res.text:
        res = requests.post(f"{BASE_URL}/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    
    assert res.status_code in (200, 201), f"Auth failed: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Notebook
    print("Creating notebook...")
    res = requests.post(f"{BASE_URL}/notebooks", json={"title": "E2E Test Notebook"}, headers=headers)
    assert res.status_code == 200, "Failed to create notebook"
    notebook_id = res.json()["_id"]

    # 3. Upload PDF
    print("Uploading PDF...")
    with open(PDF_PATH, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/documents",
            data={"title": "Test PDF"},
            files={"file": (PDF_PATH, f, "application/pdf")},
            headers=headers
        )
    assert res.status_code == 200, f"Upload failed: {res.text}"
    doc_id = res.json()["_id"]

    # Add doc to notebook
    requests.post(f"{BASE_URL}/notebooks/{notebook_id}/documents/{doc_id}", headers=headers)

    # 4. Wait for READY
    print("Waiting for document to be ready...")
    ready = False
    for _ in range(15):
        res = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
        if res.json()["status"] == "ready":
            ready = True
            print("Document READY. Gemini File ID:", res.json().get("gemini_file_id"))
            break
        elif res.json()["status"] == "failed":
            raise Exception("Document processing failed: " + str(res.json().get("processing_error")))
        time.sleep(2)
    
    assert ready, "Document did not reach READY state"

    # 5. Query AI (Notebook scoped)
    print("Querying AI...")
    res = requests.post(
        f"{BASE_URL}/ai/generate",
        json={
            "prompt": "What is the capital of France?",
            "mode": "explain",
            "context_type": "notebook",
            "context_id": notebook_id
        },
        headers=headers
    )
    assert res.status_code == 200, f"AI generation failed: {res.text}"
    data = res.json()
    print("AI Response:", data["text"])
    print("AI Citations:", data["citations"])
    
    assert "Paris" in data["text"], "Answer did not contain 'Paris'"
    assert len(data["citations"]) > 0, "No citations returned"

    # 6. Test Unanswerable
    print("Testing unanswerable question...")
    res = requests.post(
        f"{BASE_URL}/ai/generate",
        json={
            "prompt": "What does the document say about quantum computing?",
            "mode": "explain",
            "context_type": "notebook",
            "context_id": notebook_id
        },
        headers=headers
    )
    unans_text = res.json()["text"]
    print("Unanswerable response:", unans_text)
    assert "quantum computing" not in unans_text.lower() or "not" in unans_text.lower() or "cannot" in unans_text.lower(), "Hallucinated an answer!"

    # 7. Generate Flashcards
    print("Generating flashcards...")
    res = requests.post(
        f"{BASE_URL}/ai/flashcards",
        json={"text": "The capital of France is Paris. The speed of light is 299792 km/s.", "count": 2},
        headers=headers
    )
    assert res.status_code == 200
    cards = res.json()["cards"]
    print("Generated Cards:", cards)
    assert len(cards) > 0, "No cards generated"

    # Cleanup
    print("Cleaning up...")
    requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=headers)
    requests.delete(f"{BASE_URL}/notebooks/{notebook_id}", headers=headers)
    print("E2E Test Passed!")

if __name__ == "__main__":
    run_test()
