# EmpathyEngine - Oracle Cloud Deployment Guide

**Goal:** Deploy EmpathyEngine REST API to Oracle Cloud in 15 minutes.

**Result:** Public API endpoint that works with MoodRing, n8n, and other platforms.

---

## Prerequisites

- Oracle Cloud account (free tier or paid)
- GitHub/GitLab account or local git repo
- `oci` CLI installed (optional, for advanced options)

---

## Step 1: Create Container Registry (2 min)

1. **Login to Oracle Cloud Console**
   - Go to https://www.oracle.com/cloud/sign-in/
   - Navigate to your region (e.g., US-Phoenix)

2. **Create OCI Container Registry**
   - Menu → Developer Services → Container Registry
   - Click "Create Repository"
   - Repository Name: `empathy-engine`
   - Access: `Public` (so n8n can call it)
   - Click "Create"

3. **Get your region code**
   - Look at your endpoint: `phx.ocir.io` (phx = Phoenix)
   - Note: `phx.ocir.io/YOUR_NAMESPACE/empathy-engine`

4. **Create Auth Token**
   - Click your profile (top right) → User Settings
   - Click "Auth Tokens" → "Generate Token"
   - Copy the token (save it!)
   - Format: `ORACLE_USERNAME` is usually `your-email-address`

---

## Step 2: Build & Push Docker Image (5 min)

### Option A: Push from Local Machine

```bash
# 1. Build the Docker image locally
cd /run/media/osint/ext/active-projects/EmpathyEngine
docker build -t empathy-engine:latest .

# 2. Login to Oracle Registry
# Replace phx with your region, USERNAME with your email
echo "YOUR_AUTH_TOKEN_HERE" | docker login -u "YOUR_NAMESPACE/YOUR_EMAIL_ADDRESS" \
  --password-stdin phx.ocir.io

# 3. Tag the image
docker tag empathy-engine:latest phx.ocir.io/YOUR_NAMESPACE/empathy-engine:latest

# 4. Push to Oracle
docker push phx.ocir.io/YOUR_NAMESPACE/empathy-engine:latest
```

### Option B: Build in Oracle Cloud (recommended if Docker blocked locally)

1. **Upload code to GitHub**
   ```bash
   cd /run/media/osint/ext/active-projects/EmpathyEngine
   git init
   git add .
   git commit -m "Initial EmpathyEngine deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/empathy-engine.git
   git push -u origin main
   ```

2. **Use Oracle Cloud Build**
   - Menu → Developer Services → Build
   - Click "Create Build Run"
   - Source: GitHub repository
   - Build file location: `Dockerfile`
   - Registry: Select your OCIR (created above)
   - Click "Run Build"

---

## Step 3: Deploy Container Instance (8 min)

### Fastest Path: Container Instances

1. **Menu → Compute → Container Instances**

2. **Create Container Instance**
   - Name: `empathy-engine-api`
   - Container Image URL: `phx.ocir.io/YOUR_NAMESPACE/empathy-engine:latest`
   - Image pull secrets: Create new
     - Username: `YOUR_NAMESPACE/YOUR_EMAIL`
     - Password: Your Auth Token
   - Port mappings:
     - Container port: `8000`
     - Protocol: `TCP`
   - Memory: `1 GB` (free tier friendly)
   - CPUs: `0.5` or `1`
   - Click "Create"

3. **Wait for status = "Running"** (2-3 min)

4. **Get your public IP**
   - Click the instance
   - Copy the "Public IP Address"
   - Your API is now at: `http://YOUR_PUBLIC_IP:8000`

---

## Step 4: Test the API (1 min)

```bash
# Health check
curl http://YOUR_PUBLIC_IP:8000/

# Should return:
# {
#   "service": "EmpathyEngine API",
#   "version": "0.1.1",
#   "status": "operational"
# }

# Test text analysis
curl -X POST "http://YOUR_PUBLIC_IP:8000/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling great!"}'

# Test voice (requires audio file)
# See examples below
```

---

## Step 5: Configure for Production (Optional)

### Add Custom Domain (if you have one)

1. Oracle DNS or Route53 → Create A record
   - Point to your Container Instance public IP
   - Example: `api.empathyengine.com` → `YOUR_PUBLIC_IP`

2. Update n8n to use the domain instead of IP

### Setup Monitoring

- Container Instances → Logs
- Monitor: memory, CPU, request latency

### Cost Optimization

- **Free tier limits:**
  - 2 container instances
  - 20GB storage
  - You're well within limits for MVP

- **Paid tier:**
  - $0.07/hour per container instance
  - ~$50/month for always-on deployment

---

## Using EmpathyEngine with n8n

### Setup HTTP Request Node in n8n

1. **In n8n workflow:**
   - Add "HTTP Request" node
   - Method: `POST`
   - URL: `http://YOUR_PUBLIC_IP:8000/analyze/text`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "text": "{{ $json.text }}"
   }
   ```

2. **Advanced Usage:**
   ```json
   // Multimodal (text + voice)
   POST http://YOUR_PUBLIC_IP:8000/analyze/multimodal
   Form data:
   - text: "How are you?"
   - file: voice_recording.wav

   // Pattern detection
   POST http://YOUR_PUBLIC_IP:8000/patterns/detect
   {
     "entries": [...],
     "days": 30
   }
   ```

---

## Using EmpathyEngine with MoodRing

### Update MoodRing Configuration

Edit `MoodRing/config.py` or environment:

```python
EMPATHY_API_URL = "http://YOUR_PUBLIC_IP:8000"

# Update analysis code
def analyze_entry(text, audio_path):
    import requests

    if audio_path:
        # Multimodal
        files = {'file': open(audio_path, 'rb')}
        data = {'text': text}
        response = requests.post(
            f"{EMPATHY_API_URL}/analyze/multimodal",
            files=files,
            data=data
        )
    else:
        # Text only
        response = requests.post(
            f"{EMPATHY_API_URL}/analyze/text",
            json={"text": text}
        )

    return response.json()['result']
```

---

## API Endpoints Quick Reference

### Core Analysis
- `POST /analyze/text` - Text sentiment + emotion
- `POST /analyze/voice` - Voice prosody analysis
- `POST /analyze/multimodal` - Text + voice fusion (THE MAGIC)

### Advanced Analysis
- `POST /analyze/contextual` - With historical patterns
- `POST /patterns/detect` - Find emotional patterns
- `POST /summaries/generate` - Daily/weekly/monthly summaries

### Intelligence Layer (Advanced)
- `POST /advanced/crisis` - Assess crisis risk
- `POST /advanced/baseline/build` - Build emotional baseline
- `POST /advanced/triggers/identify` - Find emotional triggers
- `POST /advanced/predict/next` - Predict next emotional state

### Health & Monitoring
- `GET /health` - Full feature list + status
- `GET /` - Basic health check

---

## Troubleshooting

### Container Won't Start

**Error: "Image pull failed"**
- Check auth token is correct
- Verify repository is `Public`
- Check image name matches exactly

**Error: "Port 8000 already in use"**
- This shouldn't happen on Container Instances
- Check logs: Container Instances → Logs

### API Not Responding

**Timeout connecting to YOUR_PUBLIC_IP:8000**
- Verify instance status is "Running"
- Check security group allows inbound 8000
- Menu → Networking → Network Security Groups
- Add Ingress rule: port 8000, source 0.0.0.0/0

**502 Bad Gateway**
- Check logs: Container Instances → Logs
- Usually means the API crashed
- Check model downloads (first request is slow)

### Model Loading Issues

**"Model not found" on first request**
- First request loads transformers model (~100MB)
- This takes 20-30 seconds
- Subsequent requests are fast
- This is normal

**Fix: Do a warm-up request after deployment**
```bash
curl -X POST "http://YOUR_PUBLIC_IP:8000/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "warmup"}'
# Wait for response...
```

---

## Security Best Practices (Optional)

### Rate Limiting (Future)

When you have budget, add:
- API Gateway in front of Container Instance
- Rate limit: 100 req/min per IP
- Authentication: API key header

### HTTPS (Recommended for Production)

1. **Use Oracle Load Balancer**
   - Menu → Networking → Load Balancer
   - Backend: your Container Instance
   - Frontend: HTTPS (certificate from Let's Encrypt)

2. **Or use Cloudflare**
   - Point domain to Cloudflare
   - Cloudflare proxies → your IP
   - Automatic HTTPS

### Input Validation (Future)

- Add max request size: 10MB
- Add max text length: 100,000 chars
- Validate audio format: WAV/MP3 only

---

## Monitoring & Observability

### View Logs

```bash
# In Oracle Cloud Console
Container Instances → empathy-engine-api → Logs

# Track:
- Model loading time
- Request latency
- Error rates
- Memory usage
```

### Custom Metrics (Future)

Add to server.py:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('empathy_requests_total', 'Total requests')
request_duration = Histogram('empathy_request_seconds', 'Request duration')

@app.middleware("http")
async def track_metrics(request, call_next):
    request_count.inc()
    # ... timing code ...
    return response
```

---

## Next Steps

1. ✅ Deploy to Oracle Cloud (done!)
2. 🔄 **Integrate with n8n** - Start calling from workflows
3. 🔄 **Integrate with MoodRing** - Use remote API
4. 📊 **Add monitoring** - Track usage patterns
5. 🔐 **Add authentication** - Secure endpoints with API keys
6. 💰 **Setup billing alerts** - Monitor Oracle Cloud costs

---

## Cost Summary (Monthly)

**Free Tier:**
- 2 container instances
- 20GB storage
- **Cost: $0**

**Small Production ($50-100/month):**
- 1 container instance (always-on)
- 1 TB data egress
- **Cost: ~$50**

**Medium Production ($200-500/month):**
- 2-3 container instances (high availability)
- Load balancer
- Database (if adding persistence)
- **Cost: ~$200-500**

---

## Cheat Sheet

```bash
# Quick commands

# Push image (after building locally)
docker push phx.ocir.io/YOUR_NAMESPACE/empathy-engine:latest

# Test API from Oracle instance
curl http://INSTANCE_IP:8000/health

# Update n8n webhook
http://INSTANCE_IP:8000/analyze/text

# View logs
oci compute-instance-agent-config list

# Stop/start instance (save costs)
Menu → Container Instances → Actions → Stop/Start
```

---

## Support

**Stuck?**
1. Check troubleshooting section above
2. Review logs in Oracle Console
3. Test locally first: `python empathy_engine/api/server.py`
4. Ask in Claude Chat with error message + logs

**Need more scale?**
- Use Oracle Kubernetes Service (OKE)
- Set up auto-scaling
- Add load balancing
- (Future work)

---

**Deployed with ☕ and ❤️**

EmpathyEngine is now live and ready for the world.

Questions? Start pitching! 🚀
