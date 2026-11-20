def test_datasets_crud(client):
    # 1. Create dataset with initial test case
    payload = {
        "name": "General Instruction Test",
        "description": "Baseline QA evaluation",
        "task_type": "general",
        "test_cases": [
            {
                "prompt": "What is the capital of France?",
                "expected_output": "Paris",
                "assertions": [{"type": "contains", "value": "Paris"}]
            }
        ]
    }
    create_res = client.post("/api/v1/datasets", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()["data"]
    dataset_id = data["id"]
    assert data["name"] == "General Instruction Test"
    assert data["test_case_count"] == 1
    assert len(data["test_cases"]) == 1

    # 2. Add another test case
    tc_payload = {
        "prompt": "Translate 'hello' to Spanish.",
        "expected_output": "hola",
        "assertions": [{"type": "contains", "value": "hola"}]
    }
    tc_res = client.post(f"/api/v1/datasets/{dataset_id}/test-cases", json=tc_payload)
    assert tc_res.status_code == 201
    tc_data = tc_res.json()["data"]
    assert tc_data["prompt"] == "Translate 'hello' to Spanish."

    # 3. Retrieve dataset
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 200
    dataset_detail = get_res.json()["data"]
    assert dataset_detail["test_case_count"] == 2

    # 4. List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    all_datasets = list_res.json()["data"]
    assert len(all_datasets) >= 1
