# API Key Security Guide

## ⚠️ CRITICAL: Your API Keys Were Exposed!

Your OpenAI and Pinecone API keys were visible in your repository. I've helped secure them, but you should:

### 🚨 IMMEDIATE ACTIONS REQUIRED:

1. **Regenerate Your API Keys NOW**
   - OpenAI: https://platform.openai.com/api-keys → Delete old key → Create new
   - Pinecone: https://app.pinecone.io/ → API Keys → Regenerate

2. **Update Your .env File**
   ```bash
   OPENAI_API_KEY=your-new-key-here
   PINECONE_API_KEY=your-new-key-here
   PINECONE_ENV=us-east-1
   ```

3. **Check Git History**
   - If you've committed .env before, keys are still in git history
   - Consider making repo private or creating fresh repo

## ✅ Security Improvements Implemented:

1. **Created .env.example** - Safe template without real keys
2. **Added config.py** - Centralized, validated configuration
3. **Updated all files** - Now use secure config module
4. **API key validation** - Checks format and presence

## 📋 Security Best Practices:

### Never Commit Sensitive Data:
- ✅ .env is in .gitignore (good!)
- ❌ Never commit .env file
- ✅ Use .env.example for templates

### Key Management:
- Store keys in environment variables
- Use different keys for dev/prod
- Rotate keys regularly (every 90 days)
- Never hardcode keys in source code

### Access Control:
- Limit API key permissions when possible
- Use read-only keys for public demos
- Monitor API usage for anomalies

### For Production:
- Use secret management services (AWS Secrets Manager, Azure Key Vault)
- Implement API key encryption at rest
- Add rate limiting to prevent abuse
- Log API key usage for auditing

## 🔍 How to Check for Exposed Keys:

```bash
# Search for potential keys in your code
grep -r "sk-" . --exclude-dir=.venv
grep -r "pcsk_" . --exclude-dir=.venv

# Check git history for .env
git log --all --full-history -- .env
```

## 📚 Additional Resources:
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OpenAI API Key Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

## 🛡️ Your New Secure Setup:

1. **config.py** validates all API keys
2. Shows helpful errors if keys are missing
3. Masks keys when displaying (shows `sk-xx...xxxx`)
4. Centralized configuration management

Remember: **Security is not a one-time task but an ongoing process!**