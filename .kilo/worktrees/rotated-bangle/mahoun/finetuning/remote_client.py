"""
Remote Training Client
======================
Client for submitting training jobs to remote H100 GPU server.

Features:
- Async HTTP client with retry logic
- File upload with progress tracking
- Job status polling with exponential backoff
- Model download with resume support
- Authentication via API key
- Graceful error handling

Usage:
    client = RemoteTrainingClient(
        server_url="https://h100.example.com",
        api_key="your-api-key"
    )
    
    # Submit training job
    job_id = await client.submit_training_job(
        dataset_path="./datasets/legal_qa.jsonl",
        config={
            "base_model": "unsloth/llama-3-70b-bnb-4bit",
            "training_mode": "lora",
            "num_epochs": 3,
            "learning_rate": 0.0002
        }
    )
    
    # Poll job status
    while True:
        status = await client.get_job_status(job_id)
        if status["status"] in ["completed", "failed"]:
            break
        await asyncio.sleep(30)
    
    # Download trained model
    if status["status"] == "completed":
        await c