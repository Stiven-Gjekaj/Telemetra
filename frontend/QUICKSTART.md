# Telemetra Frontend - Quick Start Guide

## 🚀 Fast Setup (3 minutes)

### Step 1: Install Dependencies (1 min)
```bash
cd frontend
npm install
```

### Step 2: Configure Environment (30 sec)
```bash
cp .env.example .env
```

The default configuration works with the backend running on localhost:8000.

### Step 3: Start Development Server (30 sec)
```bash
npm run dev
```

Visit: **http://localhost:3000**

---

## 🐳 Docker Quick Start

### One Command Deploy
```bash
docker build -t telemetra-frontend . && docker run -p 3000:80 telemetra-frontend
```

Visit: **http://localhost:3000**

---

## 📊 What You'll See

1. **PulseBar** - Live viewer count with animated pulse
2. **ChatFlow** - Real-time chat activity chart
3. **EmoteCloud** - Interactive word cloud of top emotes
4. **MomentsTimeline** - Detected anomalies and spikes

---

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run type-check` | Check TypeScript types |
| `npm run lint` | Run ESLint |

---

## 🔌 WebSocket Connection

The frontend connects to: `ws://localhost:8000/live/demo_stream`

**Make sure your backend is running!**

### Connection States:
- 🟢 **Connected** - Receiving live data
- 🟡 **Connecting** - Attempting connection
- 🔴 **Disconnected** - Connection lost (auto-reconnect enabled)
- ❌ **Error** - Connection error (check backend)

---

## 🛠️ Troubleshooting

### WebSocket won't connect?
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify WebSocket URL in `.env`
3. Check browser console for errors

### Build failing?
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Type errors?
```bash
npm run type-check
```

---

## 📚 Next Steps

- Read [README.md](./README.md) for full documentation
- Explore [src/types/metrics.ts](./src/types/metrics.ts) for TypeScript types
- Check [src/hooks/useWebSocket.ts](./src/hooks/useWebSocket.ts) for WebSocket implementation
- Customize styling in [tailwind.config.js](./tailwind.config.js)

---

## 🎯 Production Deployment

### Build optimized bundle:
```bash
npm run build
```

### Deploy with Docker:
```bash
docker build -t telemetra-frontend:latest .
docker push your-registry/telemetra-frontend:latest
```

### Or deploy `dist/` folder to any static hosting:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Nginx/Apache server

---

## 💡 Pro Tips

1. **Hot Module Replacement**: Changes reflect instantly in dev mode
2. **TypeScript Strict Mode**: Full type safety enabled
3. **Auto-Reconnect**: WebSocket automatically reconnects on disconnect
4. **Dark Theme**: Optimized for streaming analytics
5. **Responsive**: Works on desktop, tablet, and mobile

---

**Ready to build? Run `npm run dev` and start developing!** 🎉
