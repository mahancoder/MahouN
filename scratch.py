import re

with open("api/routers/ingest.py", "r") as f:
    content = f.read()

# Remove _unified_loader definitions
content = re.sub(r'_unified_loader: Optional\[Any\] = None\n', '', content)

# Remove get_unified_loader function completely
content = re.sub(r'async def get_unified_loader\(\):.*?return _unified_loader\n', '', content, flags=re.DOTALL)

# Find and remove all Phase 6 Async Job endpoints and DLQ endpoints
endpoints_to_remove = [
    r'@router.post\("/submit".*?def submit_ingestion_job.*?return JobSubmissionResponse[^\n]*\n\s*\)[^\n]*\n',
    r'@router.get\("/jobs/\{job_id\}".*?def get_job_status.*?return JobStatusResponse[^\n]*\n\s*\)[^\n]*\n',
    r'@router.get\("/jobs".*?def list_jobs.*?return JobListResponse[^\n]*\n\s*\)[^\n]*\n',
    r'@router.get\("/dlq".*?def list_dlq_items.*?return DLQListResponse[^\n]*\n\s*\)[^\n]*\n',
    r'@router.get\("/dlq/\{job_id\}".*?def get_dlq_item.*?return DLQItem[^\n]*\n\s*\)[^\n]*\n',
    r'@router.post\("/dlq/\{job_id\}/retry".*?def retry_dlq_item.*?return DLQRetryResponse[^\n]*\n\s*\)[^\n]*\n'
]

for ep in endpoints_to_remove:
    # We will just strip them out manually if regex is too complex
    pass
