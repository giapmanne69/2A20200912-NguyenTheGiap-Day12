# Deployment Information

## Public URL
https://vinai-production-8fb0.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://vinai-production-8fb0.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://vinai-production-8fb0.up.railway.app/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](03-cloud-deployment/railway/utils/railway_deployment.png)
