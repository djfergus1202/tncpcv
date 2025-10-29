# 🚀 Render Deployment Guide - NextGen CellDynamics

Complete guide to deploy your cellular dynamics platform on Render.com (FREE tier).

---

## 📋 Prerequisites

1. **GitHub Account** - Your code needs to be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free)

---

## 🔧 Quick Fix for Your Current Deployment

Your build is failing because SciPy needs Fortran compilers. Here's the fix:

### **Step 1: Update Your Repository**

Replace these files in your GitHub repo:

1. **`requirements.txt`** - Updated with pre-built wheels:
```txt
# Core Framework
Flask==3.0.3
flask-cors==4.0.1

# Scientific Computing - Pre-built wheels
numpy==1.26.4
scipy==1.13.0

# Production server
gunicorn==21.2.0
```

2. **`runtime.txt`** (new file) - Specify Python version:
```txt
python-3.11.0
```

3. **`Procfile`** (new file) - Start command:
```txt
web: gunicorn advanced_cell_backend:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### **Step 2: Update Render Settings**

In your Render dashboard for `cell-dynamics-visual-aid`:

1. Go to **Settings** → **Build & Deploy**
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `gunicorn advanced_cell_backend:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Click **"Manual Deploy"** → **"Deploy latest commit"**

### **Step 3: Verify**

Once deployed, test your API:
```
https://cell-dynamics-visual-aid.onrender.com/api/health
```

You should see:
```json
{
  "status": "healthy",
  "version": "2.0",
  "features": [...]
}
```

---

## 🎯 Complete Deployment (Two Services)

For the best setup, deploy both backend API and frontend separately:

### **Option A: Backend Only (What You Have Now)**

✅ **You're already doing this!**

Just fix the requirements.txt as shown above, and your API will work at:
```
https://cell-dynamics-visual-aid.onrender.com/api/
```

Then update your local `nextgen_cell_dynamics.html` to point to this URL instead of localhost.

### **Option B: Backend + Frontend (Full Deployment)**

Deploy two separate services on Render:

#### **1. Backend API Service**

- **Type**: Web Service
- **Name**: `cell-dynamics-api`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn advanced_cell_backend:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- **Plan**: Free

#### **2. Frontend Static Site**

- **Type**: Static Site
- **Name**: `cell-dynamics-frontend`
- **Build Command**: (leave empty)
- **Publish Directory**: `.` (root)
- **Plan**: Free

---

## 📝 Detailed Setup Instructions

### **Method 1: Using Render Dashboard (Easiest)**

#### **Deploy Backend API:**

1. **Log into Render** → Click **"New +"** → **"Web Service"**

2. **Connect Repository**:
   - Connect your GitHub account
   - Select your repository: `djfergus1202/cell-dynamics-visual-aid`

3. **Configure Service**:
   - **Name**: `cell-dynamics-api` (or keep current name)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn advanced_cell_backend:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

4. **Environment**:
   - **Python Version**: 3.11.0 (add in Settings → Environment)

5. **Plan**: Free

6. **Click**: "Create Web Service"

#### **Deploy Frontend (Optional):**

1. **New +** → **"Static Site"**

2. **Connect same repository**

3. **Configure**:
   - **Name**: `cell-dynamics-frontend`
   - **Publish Directory**: `.`
   - **No build command needed**

4. **Create Static Site**

5. **Update HTML**: Change API_BASE to point to your backend URL

---

### **Method 2: Using render.yaml (Infrastructure as Code)**

1. **Add `render.yaml`** to your repository root:

```yaml
services:
  - type: web
    name: cell-dynamics-api
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn advanced_cell_backend:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
    healthCheckPath: /api/health
```

2. **In Render**: 
   - Click **"New +"** → **"Blueprint"**
   - Select your repository
   - Render will auto-detect `render.yaml` and create services

---

## 🔍 Troubleshooting

### **Build Fails: "Unknown compiler(s): gfortran"**

✅ **Solution**: Use updated `requirements.txt` with newer SciPy version (1.13.0) and Python 3.11

### **Build Fails: "numpy 1.26.2 requires Python >=3.9"**

✅ **Solution**: Add `runtime.txt` with `python-3.11.0`

### **502 Bad Gateway / App Not Starting**

✅ **Check**:
- Start command includes `--bind 0.0.0.0:$PORT`
- Not using `app.run()` directly
- Using `gunicorn` (production server)

### **CORS Errors in Browser**

✅ **Solution**: Backend already configured to allow:
- `localhost:*`
- `*.onrender.com`

### **Free Instance Spins Down**

⚠️ Render's free tier sleeps after 15 min of inactivity
- First request after sleep takes 50+ seconds
- **Upgrade to paid tier** ($7/month) for always-on

---

## 🌐 Testing Your Deployment

### **Test Backend API:**

```bash
# Health check
curl https://your-app.onrender.com/api/health

# Cell lines
curl https://your-app.onrender.com/api/cell-lines

# Simulation (POST request)
curl -X POST https://your-app.onrender.com/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "cellLineName": "HeLa",
    "environment": {"temperature": 37, "pH": 7.4},
    "treatment": {"type": "none", "concentration": 0},
    "experimentParams": {"initialCells": 500, "duration": 72, "timeInterval": 1.0}
  }'
```

### **Test Frontend:**

If you deployed the frontend as a static site:
```
https://your-frontend.onrender.com
```

---

## 📊 Current Status Fix

Based on your logs, here's what to do RIGHT NOW:

1. **In your GitHub repository**, update `requirements.txt`:
```txt
Flask==3.0.3
flask-cors==4.0.1
numpy==1.26.4
scipy==1.13.0
gunicorn==21.2.0
```

2. **Add `runtime.txt`** to repository:
```txt
python-3.11.0
```

3. **Commit and push** to GitHub

4. **In Render Dashboard**:
   - Go to your service: `cell-dynamics-visual-aid`
   - Click **"Manual Deploy"** → **"Deploy latest commit"**

5. **Wait 3-5 minutes** for build to complete

6. **Test**: Visit `https://cell-dynamics-visual-aid.onrender.com/api/health`

---

## 💡 Pro Tips

### **Faster Builds**
Add `.slugignore` to skip unnecessary files:
```
*.md
*.txt
validate_system.py
```

### **Environment Variables**
In Render Dashboard → Settings → Environment:
- Add any API keys
- Set `PYTHON_VERSION=3.11.0`
- Set `PORT` (auto-set by Render)

### **Custom Domain**
- Render supports custom domains on free tier!
- Settings → Custom Domain → Add your domain

### **Logs**
- Dashboard → Logs → Live tail
- Monitor startup and errors in real-time

---

## 🚨 Common Mistakes

❌ **Don't**: Use `scipy==1.11.4` (needs Fortran)
✅ **Do**: Use `scipy==1.13.0` (pre-built wheels)

❌ **Don't**: Use `python-3.13` (limited wheels)
✅ **Do**: Use `python-3.11.0` (best compatibility)

❌ **Don't**: Forget `gunicorn` in requirements
✅ **Do**: Add `gunicorn==21.2.0`

❌ **Don't**: Use `app.run(debug=True)` in production
✅ **Do**: Use `gunicorn` start command

---

## 📚 Resources

- **Render Docs**: https://render.com/docs
- **Python Version**: https://render.com/docs/python-version
- **Build Troubleshooting**: https://render.com/docs/troubleshooting-deploys
- **Free Tier Limits**: https://render.com/docs/free

---

## ✅ Success Checklist

- [ ] `requirements.txt` updated with scipy 1.13.0
- [ ] `runtime.txt` created with python-3.11.0
- [ ] `Procfile` created with gunicorn command
- [ ] Files committed and pushed to GitHub
- [ ] Manual deploy triggered in Render
- [ ] Build completes successfully (check logs)
- [ ] Health endpoint returns 200 OK
- [ ] API endpoints respond correctly

---

## 🎉 Next Steps After Deployment

1. **Update Frontend**: Point `API_BASE` to your Render URL
2. **Test Simulations**: Run full experiments
3. **Share Link**: Your API is now publicly accessible!
4. **Monitor**: Check logs for any errors
5. **Upgrade** (optional): $7/month for always-on service

---

**Questions?** Check the Render logs first - they show exactly what's failing!

Your deployment URL: `https://cell-dynamics-visual-aid.onrender.com`
