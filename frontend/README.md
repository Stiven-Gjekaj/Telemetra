<div align="center">

# 🎨 Telemetra — Frontend

### Interactive React Dashboard for Real-time Analytics

_Real-time visualization powered by React, TypeScript, and D3.js_

<p align="center">
  <img src="https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind"/>
</p>

<p align="center" style="font-weight: bold;">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-components">Components</a> •
  <a href="#-real-time-updates">Real-Time</a> •
  <a href="#-features">Features</a>
</p>

[← Back to main README](../README.md)

</div>

---

## 📖 Overview

The Telemetra frontend is a **React application** built with TypeScript and Vite that provides an interactive dashboard for visualizing real-time streaming analytics. It connects to the FastAPI backend via REST endpoints and WebSocket for live data updates.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📊 Real-Time Metrics

- ✅ Live viewer count with pulse indicator
- ✅ Chat rate line charts (Recharts)
- ✅ Sentiment analysis visualization
- ✅ Auto-updating every 1-2 seconds

### ☁️ Data Visualizations

- ✅ D3-powered emote word cloud
- ✅ Interactive time-series charts
- ✅ Moments timeline with filtering
- ✅ Responsive chart layouts

</td>
<td width="50%">

### 🎨 User Experience

- ✅ Auto-reconnect WebSocket
- ✅ Loading states & skeleton screens
- ✅ Graceful error handling
- ✅ Mobile-responsive design

### 🛠️ Developer Experience

- ✅ Hot Module Replacement (HMR)
- ✅ TypeScript type safety
- ✅ Component-based architecture
- ✅ Tailwind CSS utility classes

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 📋 Prerequisites

<p>
<img src="https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white" alt="Node.js 18+"/>
<img src="https://img.shields.io/badge/npm-9+-CB3837?style=flat-square&logo=npm&logoColor=white" alt="npm 9+"/>
</p>

### ⏱️ Local Development Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Access the dashboard
# Open http://localhost:5173 in your browser
```

### 🌐 Access Points

<table>
<tr>
<th>Service</th>
<th>URL</th>
<th>Description</th>
</tr>
<tr>
<td><b>Frontend</b></td>
<td><a href="http://localhost:5173">http://localhost:5173</a></td>
<td>Development server with HMR</td>
</tr>
<tr>
<td><b>Backend API</b></td>
<td><a href="http://localhost:8000">http://localhost:8000</a></td>
<td>Required for data</td>
</tr>
</table>

### ✔️ Verify Frontend

1. Open http://localhost:5173 in your browser
2. Check browser console for any errors
3. Verify WebSocket connection status in the UI
4. Data should start flowing within 2-3 seconds

---

## 🎨 Components

### Main Components

<table>
<tr>
<th>Component</th>
<th>Description</th>
<th>Props</th>
</tr>
<tr>
<td><code>App.tsx</code></td>
<td>Main application with routing and layout</td>
<td>-</td>
</tr>
<tr>
<td><code>StreamHeader.tsx</code></td>
<td>Stream title and metadata display</td>
<td><code>streamId, title, createdAt</code></td>
</tr>
<tr>
<td><code>ViewerPulse.tsx</code></td>
<td>Animated viewer count with pulse effect</td>
<td><code>viewerCount, isLive</code></td>
</tr>
<tr>
<td><code>ChatRateChart.tsx</code></td>
<td>Line chart for chat messages per minute</td>
<td><code>data, height?</code></td>
</tr>
<tr>
<td><code>EmoteCloud.tsx</code></td>
<td>D3 word cloud for popular emotes</td>
<td><code>emotes, width, height</code></td>
</tr>
<tr>
<td><code>MomentsTimeline.tsx</code></td>
<td>Timeline of detected anomalies</td>
<td><code>moments</code></td>
</tr>
</table>

---

## 📡 Real-Time Updates

### WebSocket Hook: `useWebSocket.ts`

Custom React hook for managing WebSocket connections:

```typescript
const { data, isConnected, error } = useWebSocket(streamId);
```

**Features:**

- ✅ Automatic connection on mount
- ✅ Auto-reconnect with exponential backoff
- ✅ Connection state tracking
- ✅ Error handling and logging
- ✅ Clean disconnect on unmount

**Connection Flow:**

1. Component mounts → Hook initializes WebSocket
2. Backend sends metrics every 1-2 seconds
3. Hook updates `data` state → Component re-renders
4. If connection drops → Auto-reconnect after 3s, 6s, 12s...
5. Component unmounts → Clean disconnect

---

## 🛠️ Tech Stack

<p>
<img src="https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
<img src="https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
<img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite"/>
<img src="https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind"/>
<img src="https://img.shields.io/badge/Recharts-2.10-8884D8?style=for-the-badge" alt="Recharts"/>
<img src="https://img.shields.io/badge/D3.js-7.8-F9A03C?style=for-the-badge&logo=d3.js&logoColor=white" alt="D3.js"/>
</p>

---

## 🐋 Docker Deployment

```bash
# Start frontend service
docker compose -f ../infra/docker-compose.yml up frontend -d

# View logs
docker compose -f ../infra/docker-compose.yml logs -f frontend

# Restart after code changes
docker compose -f ../infra/docker-compose.yml build frontend --no-cache
docker compose -f ../infra/docker-compose.yml restart frontend
```

---

## 🏗️ Build & Deploy

### Production Build

```bash
# Create optimized production build
npm run build

# Output: dist/ directory with:
# - index.html (entry point)
# - assets/ (bundled JS, CSS, images)
# - Minified and tree-shaken code
```

### Preview Production Build

```bash
# Preview build locally (port 4173)
npm run preview
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in frontend directory:

```bash
# Backend API URL (default: http://localhost:8000)
VITE_API_URL=http://localhost:8000

# WebSocket URL (default: ws://localhost:8000)
VITE_WS_URL=ws://localhost:8000

# Enable debug logging (default: false)
VITE_DEBUG=false
```

---

## 🔧 Development

### Development Scripts

```bash
# Start dev server with hot reload
npm run dev

# Type-check without emitting files
npm run type-check

# Lint code with ESLint
npm run lint

# Build for production
npm run build

# Preview production build locally
npm run preview
```

---

## 🔧 Troubleshooting

<details>
<summary><b>🔌 Cannot Connect to Backend</b></summary>

```bash
# Check backend is running
curl http://localhost:8000/health

# View browser console for errors
# Open DevTools (F12) → Console tab
```

</details>

<details>
<summary><b>📡 WebSocket Connection Failed</b></summary>

```bash
# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/live/demo_stream

# Verify stream ID exists
curl http://localhost:8000/api/v1/streams
```

</details>

<details>
<summary><b>🖼️ No Data Displayed</b></summary>

```bash
# Check backend has data
curl http://localhost:8000/api/v1/streams/demo_stream/metrics

# Open browser DevTools → Network tab
# Look for failed API requests
```

</details>

---

## 📚 Additional Resources

<div align="center">

<table>
<tr>
<td align="center" width="33%">
<h3><a href="../README.md">🏠 Main README</a></h3>
<p>Project overview</p>
</td>
<td align="center" width="33%">
<h3><a href="../backend/README.md">🔌 Backend</a></h3>
<p>FastAPI service</p>
</td>
<td align="center" width="33%">
<h3><a href="../data_pipeline/README.md">⚡ Pipeline</a></h3>
<p>Data processing</p>
</td>
</tr>
</table>

</div>

---

<div align="center">

**Built with React** ⚛️ | **Powered by TypeScript** 📘

[← Back to main README](../README.md)

</div>
