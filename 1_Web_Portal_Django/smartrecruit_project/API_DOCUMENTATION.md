# SmartRecruit REST API Documentation

## Base URL
```
http://127.0.0.1:8000/api/v1/
```

## Authentication

The API uses Token Authentication. To obtain a token:

### Get Auth Token
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Using the Token
Include the token in the Authorization header for all subsequent requests:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## Endpoints

### 1. Jobs

#### List All Jobs
```http
GET /api/v1/jobs/
```

**Query Parameters:**
- `search` - Search in title, description, and skills
- `technology` - Filter by technology stack
- `location` - Filter by location
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/v1/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Senior Python Developer",
      "job_type": "FULL_TIME",
      "location": "San Francisco, CA",
      "technology_stack": "Python, Django, PostgreSQL",
      "min_experience": 5,
      "status": "OPEN",
      "recruiter_name": "John Doe",
      "created_at": "2026-02-14T03:00:00Z"
    }
  ]
}
```

#### Get Job Details
```http
GET /api/v1/jobs/{id}/
```

**Response:**
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "description": "We are looking for an experienced Python developer...",
  "job_type": "FULL_TIME",
  "location": "San Francisco, CA",
  "salary_range": "$120,000 - $160,000",
  "required_skills": "Python, Django, REST APIs, PostgreSQL",
  "min_experience": 5,
  "technology_stack": "Python, Django, PostgreSQL",
  "deadline": "2026-03-15",
  "status": "OPEN",
  "recruiter": {
    "id": 2,
    "username": "recruiter1",
    "email": "recruiter@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_recruiter": true
  },
  "created_at": "2026-02-14T03:00:00Z",
  "updated_at": "2026-02-14T03:00:00Z",
  "application_count": 15
}
```

#### Create Job (Recruiters Only)
```http
POST /api/v1/jobs/
Authorization: Token {your_token}
Content-Type: application/json

{
  "title": "Senior Python Developer",
  "description": "We are looking for...",
  "job_type": "FULL_TIME",
  "location": "San Francisco, CA",
  "salary_range": "$120,000 - $160,000",
  "required_skills": "Python, Django, REST APIs",
  "min_experience": 5,
  "technology_stack": "Python, Django, PostgreSQL",
  "deadline": "2026-03-15"
}
```

#### Update Job (Recruiters Only)
```http
PUT /api/v1/jobs/{id}/
PATCH /api/v1/jobs/{id}/
Authorization: Token {your_token}
```

#### Delete Job (Recruiters Only)
```http
DELETE /api/v1/jobs/{id}/
Authorization: Token {your_token}
```

#### Get Job Applications
```http
GET /api/v1/jobs/{id}/applications/
Authorization: Token {your_token}
```

#### Get Recommended Jobs
```http
GET /api/v1/jobs/recommended/
Authorization: Token {your_token}
```

**Response:**
```json
[
  {
    "job": {
      "id": 1,
      "title": "Senior Python Developer",
      "job_type": "FULL_TIME",
      "location": "San Francisco, CA",
      "technology_stack": "Python, Django",
      "min_experience": 5,
      "status": "OPEN",
      "recruiter_name": "John Doe",
      "created_at": "2026-02-14T03:00:00Z"
    },
    "match_score": 85.5,
    "reasons": [
      "Excellent match for your skills",
      "Uses Python, Django",
      "Located in San Francisco, CA"
    ]
  }
]
```

---

### 2. Applications

#### List Applications
```http
GET /api/v1/applications/
Authorization: Token {your_token}
```

**Note:** Candidates see their own applications, recruiters see applications for their jobs.

**Query Parameters:**
- `page` - Page number
- `page_size` - Items per page

**Response:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "candidate": {
        "id": 3,
        "username": "candidate1",
        "email": "candidate@example.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "is_recruiter": false
      },
      "job": {
        "id": 1,
        "title": "Senior Python Developer",
        "job_type": "FULL_TIME",
        "location": "San Francisco, CA",
        "technology_stack": "Python, Django",
        "min_experience": 5,
        "status": "OPEN",
        "recruiter_name": "John Doe",
        "created_at": "2026-02-14T03:00:00Z"
      },
      "status": "RESUME_SELECTED",
      "applied_at": "2026-02-10T10:30:00Z",
      "ai_score": 85.5,
      "round1_score": 78.0,
      "round2_score": 82.5,
      "ai_interview_score": 88.0,
      "hr_interview_score": 90.0,
      "overall_score": 84.8,
      "resume": "/media/resumes/candidate1_resume.pdf"
    }
  ]
}
```

#### Get Application Details
```http
GET /api/v1/applications/{id}/
Authorization: Token {your_token}
```

#### Create Application
```http
POST /api/v1/applications/
Authorization: Token {your_token}
Content-Type: multipart/form-data

{
  "job": 1,
  "resume": <file>
}
```

#### Update Application Status (Recruiters Only)
```http
POST /api/v1/applications/{id}/update_status/
Authorization: Token {your_token}
Content-Type: application/json

{
  "status": "ROUND_1_PASSED"
}
```

**Status Options:**
- `RESUME_SCREENING`
- `RESUME_SELECTED`
- `RESUME_REJECTED`
- `ROUND_1_PASSED`
- `ROUND_1_FAILED`
- `ROUND_2_PASSED`
- `ROUND_2_FAILED`
- `ROUND_3_PASSED`
- `ROUND_3_FAILED`
- `HR_PASSED`
- `HR_FAILED`
- `OFFER_SENT`
- `OFFER_ACCEPTED`
- `OFFER_REJECTED`

---

### 3. Analytics (Recruiters Only)

#### Get Analytics Summary
```http
GET /api/v1/analytics/
Authorization: Token {your_token}
```

**Response:**
```json
{
  "total_applications": 150,
  "active_jobs": 8,
  "pending_reviews": 25,
  "total_hired": 12,
  "average_time_to_hire": 18.5,
  "conversion_rates": {
    "resume_to_round1": 65.2,
    "round1_to_round2": 45.8,
    "round2_to_round3": 38.5,
    "round3_to_hr": 75.0,
    "hr_to_offer": 85.0,
    "offer_to_hired": 70.5
  },
  "status_breakdown": {
    "Resume Screening": 30,
    "Resume Selected": 25,
    "Round 1 Passed": 20,
    "Round 2 Passed": 15,
    "HR Passed": 10,
    "Offer Sent": 8,
    "Offer Accepted": 12
  }
}
```

---

### 4. Enterprise HRMS Integrations

#### Export Hired Candidates
```http
GET /api/v1/hrms/hired-candidates/
Authorization: Token {your_token}
```

**Description:**
Returns a secure JSON list of candidates who are marked as `HIRED` or `OFFER_ACCEPTED`, designed for ingestion into external HR systems like Workday, BambooHR, etc.

**Query Parameters:**
- `job_id` - Filter by specific Job ID
- `start_date` - Filter by candidates updated on or after this date (ISO format)

**Response:**
```json
{
  "count": 1,
  "results": [
    {
      "application_id": 45,
      "status": "HIRED",
      "last_updated": "2026-03-14T15:30:00Z",
      "candidate": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "+1234567890",
        "experience_years": 4.5,
        "current_location": "New York, USA",
        "skills_extracted": "Python, Django, AWS",
        "resume_url": "http://127.0.0.1:8000/media/resumes/alice_resume.pdf"
      },
      "job": {
        "id": 1,
        "title": "Senior Python Developer",
        "department": "Engineering",
        "location": "Remote",
        "job_type": "FULL_TIME"
      },
      "offer": {
        "salary_offered": "$135,000",
        "designation": "Senior Python Developer",
        "joining_date": "2026-04-15"
      }
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid data provided",
  "details": {
    "title": ["This field is required."]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "Only recruiters can access this endpoint"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Rate Limiting

Currently no rate limiting is enforced. In production, consider implementing rate limiting to prevent abuse.

---

## Pagination

All list endpoints support pagination with the following parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

Response format:
```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/v1/jobs/?page=3",
  "previous": "http://127.0.0.1:8000/api/v1/jobs/?page=1",
  "results": [...]
}
```

---

## Example Usage

### Python (requests library)
```python
import requests

# Get token
response = requests.post('http://127.0.0.1:8000/api/v1/auth/token/', json={
    'username': 'candidate1',
    'password': 'password123'
})
token = response.json()['token']

# Get recommended jobs
headers = {'Authorization': f'Token {token}'}
response = requests.get('http://127.0.0.1:8000/api/v1/jobs/recommended/', headers=headers)
jobs = response.json()
print(f"Found {len(jobs)} recommended jobs")
```

### JavaScript (fetch API)
```javascript
// Get token
const tokenResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'candidate1', password: 'password123' })
});
const { token } = await tokenResponse.json();

// Get jobs
const jobsResponse = await fetch('http://127.0.0.1:8000/api/v1/jobs/', {
  headers: { 'Authorization': `Token ${token}` }
});
const jobs = await jobsResponse.json();
console.log(`Found ${jobs.count} jobs`);
```

---

## Testing

Use tools like:
- **Postman** - Import the endpoints and test interactively
- **curl** - Command-line testing
- **Django REST Framework Browsable API** - Visit endpoints in your browser while logged in

---

## Support

For issues or questions, contact the development team.
