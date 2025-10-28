# Receipt Scanner - API Documentation

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication

Currently, the API does not require authentication. For production deployment, implement:
- API Keys
- OAuth2
- JWT tokens

## Endpoints

### Health Check

#### `GET /health`

Check API health status.

**Response**

```json
{
  "status": "healthy",
  "timestamp": "2024-10-19T10:30:00.000Z",
  "storage_backend": "s3"
}
```

**Status Codes**
- `200 OK` - Service is healthy

---

### Receipt Upload

#### `POST /upload`

Upload receipt images for processing.

**Request**

- **Content-Type**: `multipart/form-data`
- **Body Parameters**:
  - `files` (required): List of image files (JPG, PNG, PDF)
  - Maximum 10 files per request
  - Maximum file size: 10 MB per file

**Example (curl)**

```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@receipt1.jpg" \
  -F "files=@receipt2.jpg"
```

**Response**

```json
{
  "message": "Uploaded 2 files",
  "job_ids": [
    "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "b2c3d4e5-6789-01bc-def0-234567890abc"
  ]
}
```

**Status Codes**
- `200 OK` - Upload successful
- `400 Bad Request` - Invalid file type or too many files
- `500 Internal Server Error` - Server error

---

### List Receipts

#### `GET /receipts`

Retrieve all receipts with optional filtering and pagination.

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum number of results (1-1000) |
| `skip` | integer | 0 | Number of results to skip (pagination) |
| `category` | string | - | Filter by category |
| `start_date` | string | - | Filter from date (YYYY-MM-DD) |
| `end_date` | string | - | Filter to date (YYYY-MM-DD) |

**Example Request**

```bash
GET /receipts?limit=10&category=Thực%20Phẩm&start_date=2024-10-01
```

**Response**

```json
[
  {
    "id": "receipt-123",
    "merchant_name": "Siêu Thị ABC",
    "receipt_date": "2024-10-15",
    "total_amount": 352000.0,
    "category": "Thực Phẩm",
    "confidence": 0.95,
    "items": ["Thịt bò", "Rau xanh", "Gạo 5kg"],
    "raw_text": "SIÊU THỊ ABC\n...",
    "image_path": "https://minio/receipts/images/abc123.jpg",
    "processed_at": "2024-10-15T10:30:00.000Z",
    "corrected": false
  }
]
```

**Status Codes**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

---

### Get Single Receipt

#### `GET /receipts/{receipt_id}`

Retrieve a single receipt by ID.

**Path Parameters**
- `receipt_id` (required): Receipt ID

**Example Request**

```bash
GET /receipts/receipt-123
```

**Response**

```json
{
  "id": "receipt-123",
  "merchant_name": "Siêu Thị ABC",
  "receipt_date": "2024-10-15",
  "total_amount": 352000.0,
  "category": "Thực Phẩm",
  "confidence": 0.95,
  "items": ["Thịt bò", "Rau xanh"],
  "raw_text": "...",
  "image_path": "...",
  "processed_at": "2024-10-15T10:30:00.000Z",
  "corrected": false
}
```

**Status Codes**
- `200 OK` - Success
- `404 Not Found` - Receipt not found
- `500 Internal Server Error` - Server error

---

### Update Receipt

#### `PUT /receipts/{receipt_id}`

Update receipt information and save as correction for ML feedback.

**Path Parameters**
- `receipt_id` (required): Receipt ID

**Request Body**

```json
{
  "merchant_name": "Updated Store Name",
  "receipt_date": "2024-10-15",
  "total_amount": 400000.0,
  "category": "Thực Phẩm",
  "items": ["Item 1", "Item 2"],
  "raw_text": "Updated text..."
}
```

All fields are optional. Only provided fields will be updated.

**Response**

```json
{
  "id": "receipt-123",
  "merchant_name": "Updated Store Name",
  "receipt_date": "2024-10-15",
  "total_amount": 400000.0,
  "category": "Thực Phẩm",
  "confidence": 0.95,
  "items": ["Item 1", "Item 2"],
  "raw_text": "Updated text...",
  "image_path": "...",
  "processed_at": "2024-10-15T10:30:00.000Z",
  "corrected": true
}
```

**Status Codes**
- `200 OK` - Update successful
- `404 Not Found` - Receipt not found
- `500 Internal Server Error` - Server error

---

### Delete Receipt

#### `DELETE /receipts/{receipt_id}`

Delete a receipt.

**Path Parameters**
- `receipt_id` (required): Receipt ID

**Response**

```json
{
  "message": "Receipt deleted successfully"
}
```

**Status Codes**
- `200 OK` - Deletion successful
- `404 Not Found` - Receipt not found
- `500 Internal Server Error` - Server error

---

### Get Job Status

#### `GET /jobs/{job_id}`

Get the status of a background processing job.

**Path Parameters**
- `job_id` (required): Job ID returned from upload endpoint

**Response**

```json
{
  "job_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "completed",
  "result": {
    "receipt_id": "receipt-123",
    "status": "success",
    "category": "Thực Phẩm",
    "confidence": 0.95,
    "duration": 4.2
  },
  "error": null,
  "created_at": "2024-10-15T10:30:00.000Z",
  "completed_at": "2024-10-15T10:30:04.200Z"
}
```

**Status Values**
- `pending` - Job is queued
- `processing` - Job is being processed
- `completed` - Job completed successfully
- `failed` - Job failed with error

**Status Codes**
- `200 OK` - Success
- `404 Not Found` - Job not found
- `500 Internal Server Error` - Server error

---

### Admin - Get Metrics

#### `GET /admin/metrics`

Get system metrics and statistics.

**Response**

```json
{
  "total_receipts": 1234,
  "total_jobs": 1500,
  "pending_jobs": 5,
  "failed_jobs": 12,
  "avg_processing_time": 4.5,
  "success_rate": 0.99
}
```

**Status Codes**
- `200 OK` - Success
- `500 Internal Server Error` - Server error

---

### Admin - Trigger Retraining

#### `POST /admin/retrain`

Trigger ML model retraining with accumulated corrections.

**Response**

```json
{
  "message": "Retraining job created",
  "job_id": "retrain-a1b2c3d4"
}
```

**Status Codes**
- `200 OK` - Retraining job created
- `500 Internal Server Error` - Server error

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `400` | Bad Request - Invalid input |
| `404` | Not Found - Resource doesn't exist |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error - Server error |

---

## Rate Limiting

Rate limiting can be enabled via environment variables:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

When rate limit is exceeded:

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**Status Code**: `429 Too Many Requests`

---

## Pagination

For list endpoints, use `limit` and `skip` parameters:

```bash
# Get first page (10 items)
GET /receipts?limit=10&skip=0

# Get second page (10 items)
GET /receipts?limit=10&skip=10

# Get third page (10 items)
GET /receipts?limit=10&skip=20
```

---

## Filtering

### By Category

```bash
GET /receipts?category=Thực%20Phẩm
```

Available categories:
- `Thực Phẩm` (Food)
- `Điện Tử` (Electronics)
- `Quần Áo` (Clothing)
- `Y Tế` (Healthcare)
- `Giải Trí` (Entertainment)
- `Du Lịch` (Travel)
- `Gia Dụng` (Household)
- `Khác` (Other)

### By Date Range

```bash
GET /receipts?start_date=2024-10-01&end_date=2024-10-31
```

Date format: `YYYY-MM-DD`

---

## Response Headers

All responses include:

```
Content-Type: application/json
X-Request-ID: <unique-request-id>
```

---

## CORS

CORS is enabled for the following origins (configurable via `.env`):

```
http://localhost:8501
http://localhost:3000
```

---

## Webhooks

Webhooks are not currently supported but planned for future releases.

---

## SDK Examples

### Python

```python
import requests

# Upload receipt
files = {'files': open('receipt.jpg', 'rb')}
response = requests.post('http://localhost:8000/upload', files=files)
job_ids = response.json()['job_ids']

# Check job status
job_id = job_ids[0]
response = requests.get(f'http://localhost:8000/jobs/{job_id}')
print(response.json())

# List receipts
response = requests.get('http://localhost:8000/receipts?limit=10')
receipts = response.json()
```

### JavaScript

```javascript
// Upload receipt
const formData = new FormData();
formData.append('files', fileInput.files[0]);

const response = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data.job_ids);

// Get receipts
const receipts = await fetch('http://localhost:8000/receipts?limit=10')
  .then(res => res.json());
```

### cURL

```bash
# Upload
curl -X POST http://localhost:8000/upload \
  -F "files=@receipt.jpg"

# List receipts
curl http://localhost:8000/receipts?limit=10

# Get receipt
curl http://localhost:8000/receipts/receipt-123

# Update receipt
curl -X PUT http://localhost:8000/receipts/receipt-123 \
  -H "Content-Type: application/json" \
  -d '{"category": "Thực Phẩm"}'

# Delete receipt
curl -X DELETE http://localhost:8000/receipts/receipt-123
```

---

## Best Practices

1. **Poll job status** after upload instead of waiting synchronously
2. **Use pagination** for large datasets
3. **Cache responses** when appropriate
4. **Handle errors** gracefully with proper retry logic
5. **Use filters** to reduce response size
6. **Set timeouts** for API calls (recommended: 30s)

---

## Support

- API Issues: GitHub Issues
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health