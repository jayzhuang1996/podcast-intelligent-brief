# Railway Deployment Guide

## Quick Deploy Steps

### 1. Create GitHub Repository (if you haven't)
```bash
cd /path/to/ai-podcast
git init
git add .
git commit -m "Initial commit: Podcast Intelligent Brief"
git branch -M main
```

Create a new repository on GitHub.com, then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/podcast-intelligent-brief.git
git push -u origin main
```

### 2. Deploy to Railway

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `podcast-intelligent-brief` repository
5. Railway will auto-detect Python project

### 3. Set Environment Variables

In Railway dashboard, go to Variables and add:

```
ANTHROPIC_API_KEY=your-api-key-here
```

### 4. Get Your Live URL

Railway will provide a URL like: `https://your-app.up.railway.app`

Share this URL with your friends!

## Frontend Deployment (Vercel)

The backend will be on Railway, but you need to deploy the frontend separately:

### Option 1: Vercel (Recommended)

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Go to https://vercel.com
3. Click "Add New" → "Project"
4. Import your GitHub repo
5. Set root directory to `frontend`
6. Add environment variable:
   - `VITE_API_URL` = your Railway backend URL

### Option 2: Netlify

1. Same steps as Vercel
2. Build command: `npm run build`
3. Publish directory: `dist`

## Important Notes

- **Free tier limits**: Railway gives $5/month free credit
- **Database**: SQLite will work but consider upgrading to PostgreSQL for production
- **CORS**: The backend already has CORS enabled for all origins

## Costs

- Railway: Free $5/month (enough for ~500 briefings)
- Vercel: Free (unlimited for personal projects)
- Total: **FREE** for moderate usage

Your friends can now access:
- Frontend: `https://your-app.vercel.app`
- API Docs: `https://your-app.up.railway.app/docs`
