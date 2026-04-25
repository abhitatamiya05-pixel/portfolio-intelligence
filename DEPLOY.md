# Deploy to Streamlit Cloud

## Prerequisites
- GitHub account
- Streamlit Cloud account at https://share.streamlit.io (free tier works)

## Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
gh repo create portfolio-intelligence --public --source=. --push
```

### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io and sign in with GitHub
2. Click **New app**
3. Select your repo (`portfolio-intelligence`), branch (`main`), and set **Main file path** to `app.py`
4. Click **Deploy**

Streamlit Cloud installs `requirements.txt` automatically. No secrets or environment variables needed.

Your app will be live at:
```
https://<your-username>-portfolio-intelligence-app-<hash>.streamlit.app
```

## Notes
- Free tier: 1 GB RAM, sleeps after inactivity (wakes on next visit)
- Data is generated in-memory at startup — no database or external API needed
- To keep the app awake, enable **Always on** in app settings (requires a paid plan)
