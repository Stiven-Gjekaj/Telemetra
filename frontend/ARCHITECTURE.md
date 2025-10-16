# Telemetra Frontend Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Telemetra Dashboard                       │
│                   (React + TypeScript)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket
                              │ ws://localhost:8000/live/demo_stream
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend WebSocket Server                  │
│                      (FastAPI/Python)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                           App.tsx                                 │
│                      (Root Component)                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Dashboard.tsx                               │
│                    (Main Dashboard Page)                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │         useWebSocket Hook                             │       │
│  │  • Auto-reconnect logic                               │       │
│  │  • Message routing                                    │       │
│  │  • State management                                   │       │
│  └──────────────────────────────────────────────────────┘       │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  PulseBar   │  │  ChatFlow   │  │ EmoteCloud  │            │
│  │             │  │             │  │             │            │
│  │  • Viewer   │  │  • Recharts │  │  • D3.js    │            │
│  │    count    │  │  • Line     │  │  • Word     │            │
│  │  • Pulse    │  │    chart    │  │    cloud    │            │
│  │    effect   │  │  • Real-    │  │  • Bubble   │            │
│  │  • Trends   │  │    time     │  │    chart    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              MomentsTimeline                          │       │
│  │  • Anomaly detection                                  │       │
│  │  • Timeline view                                      │       │
│  │  • Severity indicators                                │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Backend WebSocket                useWebSocket Hook              Components
     Server                         (State Mgmt)                 (Rendering)
────────────────              ────────────────────           ─────────────

      │                              │                              │
      │ WebSocket                    │                              │
      │ Message                      │                              │
      ├─────────────────────────────>│                              │
      │ {type: "metrics"}            │                              │
      │                              │ Parse &                      │
      │                              │ Update State                 │
      │                              │                              │
      │                              ├─────────────────────────────>│
      │                              │ metrics: StreamMetrics       │
      │                              │                              │
      │                              │                         Render
      │                              │                         Components
      │                              │                              │
      │                              │<─────────────────────────────┤
      │                              │ User interaction             │
      │<─────────────────────────────┤ (reconnect, etc.)           │
      │ WebSocket                    │                              │
      │ reconnect                    │                              │
      │                              │                              │
      ▼                              ▼                              ▼
```

---

## Type System

```typescript
// Core Types Hierarchy

ConnectionState (enum)
├── CONNECTING
├── CONNECTED
├── DISCONNECTED
└── ERROR

StreamMetrics (interface)
├── streamId: string
├── timestamp: number
├── viewers: ViewerMetrics
│   ├── current: number
│   ├── peak: number
│   ├── average: number
│   └── history: TimeSeriesDataPoint[]
├── chatRate: ChatRateMetrics
│   ├── data: TimeSeriesDataPoint[]
│   ├── currentRate: number
│   ├── averageRate: number
│   └── peakRate: number
├── topEmotes: Emote[]
│   ├── name: string
│   └── count: number
├── sentiment?: SentimentMetrics
│   ├── score: number
│   ├── positive: number
│   ├── negative: number
│   └── neutral: number
└── moments: Moment[]
    ├── id: string
    ├── timestamp: number
    ├── type: 'chat_spike' | 'viewer_spike' | 'sentiment_shift'
    ├── description: string
    ├── severity: number
    └── metadata?: Record<string, unknown>

WebSocketMessage<T> (interface)
├── type: 'metrics' | 'moment' | 'error' | 'ping' | 'pong'
├── data: T
└── timestamp: number
```

---

## WebSocket Connection Lifecycle

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │  DISCONNECTED │
              └───────────────┘
                      │
                      │ connect()
                      ▼
              ┌───────────────┐
              │  CONNECTING   │◄─────────┐
              └───────────────┘          │
                      │                  │
                      │ onopen           │ retry
                      ▼                  │
              ┌───────────────┐          │
              │   CONNECTED   │          │
              └───────────────┘          │
                      │                  │
        ┌─────────────┼─────────────┐   │
        │             │             │   │
    onmessage     heartbeat     onerror │
        │             │             │   │
        ▼             ▼             ▼   │
   Handle         Send Ping      ERROR  │
   Message         │                │   │
                   ▼                │   │
              Keep-Alive            │   │
                                    └───┘
                                  (auto-reconnect)
```

---

## Component State Management

```
┌────────────────────────────────────────────────────────────┐
│                    useWebSocket Hook                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  State:                          Refs:                      │
│  ├─ state: ConnectionState       ├─ wsRef: WebSocket       │
│  ├─ error: string | null         ├─ reconnectAttempts      │
│  └─ metrics: StreamMetrics       ├─ reconnectTimeout       │
│                                   └─ heartbeatInterval      │
│  Methods:                                                   │
│  ├─ reconnect()                                            │
│  ├─ disconnect()                                           │
│  └─ send()                                                 │
│                                                             │
│  Effects:                                                   │
│  ├─ Connect on mount                                       │
│  ├─ Cleanup on unmount                                     │
│  ├─ Start heartbeat on connect                            │
│  └─ Auto-reconnect on disconnect                          │
└────────────────────────────────────────────────────────────┘
```

---

## Build Pipeline

```
Development:
  npm run dev
      │
      ▼
  Vite Dev Server ──────> http://localhost:3000
      │                   (Hot Module Replacement)
      ▼
  TypeScript Transpilation
      │
      ▼
  Tailwind CSS Processing
      │
      ▼
  React Fast Refresh

Production:
  npm run build
      │
      ▼
  TypeScript Check ───> tsc --noEmit
      │                 (Type validation)
      ▼
  Vite Build
      │
      ├─> Tree Shaking
      ├─> Code Splitting
      ├─> Minification
      └─> Source Maps
      │
      ▼
  dist/ folder
      │
      ▼
  Docker Build (Multi-stage)
      │
      ├─> Stage 1: Build app (Node 20 Alpine)
      │   └─> npm install + npm run build
      │
      └─> Stage 2: Serve app (Nginx Alpine)
          └─> Copy dist/ + nginx.conf
      │
      ▼
  Production Image
      │
      ▼
  docker run -p 3000:80
```

---

## Nginx Routing

```
Client Request
      │
      ▼
┌─────────────────────────────────────────┐
│         Nginx (Port 80)                  │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────┐    │
│  │ Location: /                     │    │
│  │ → Serve static files            │    │
│  │ → SPA routing (index.html)      │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │ Location: /api/*                │    │
│  │ → Proxy to backend:8000         │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │ Location: /live/*               │    │
│  │ → WebSocket proxy               │    │
│  │ → Upgrade connection            │    │
│  │ → Long timeout (24h)            │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────────────────────┐    │
│  │ Location: /health               │    │
│  │ → Return 200 OK                 │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

---

## Performance Optimizations

```
1. Code Splitting
   ├─ Dynamic imports for heavy components
   ├─ Vite automatic chunking
   └─ Lazy loading of D3 visualizations

2. Memoization
   ├─ useCallback for event handlers
   ├─ useMemo for computed values
   └─ React.memo for pure components

3. Data Management
   ├─ Limited history (100 points max)
   ├─ Efficient state updates
   └─ Debounced animations

4. Network
   ├─ WebSocket for efficient real-time data
   ├─ Gzip compression in nginx
   ├─ Static asset caching (1 year)
   └─ Heartbeat for keep-alive

5. Build
   ├─ Tree shaking
   ├─ Minification
   ├─ Source maps for debugging
   └─ Multi-stage Docker build
```

---

## Directory Structure

```
frontend/
├── public/                  # Static assets
│   └── vite.svg
├── src/
│   ├── components/          # React components
│   │   ├── PulseBar.tsx
│   │   ├── ChatFlow.tsx
│   │   ├── EmoteCloud.tsx
│   │   └── MomentsTimeline.tsx
│   ├── hooks/               # Custom React hooks
│   │   └── useWebSocket.ts
│   ├── pages/               # Page components
│   │   └── Dashboard.tsx
│   ├── types/               # TypeScript types
│   │   └── metrics.ts
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   ├── vite-env.d.ts        # Vite types
│   └── index.css            # Global styles
├── Dockerfile               # Production build
├── nginx.conf               # Web server config
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite config
├── tailwind.config.js       # Tailwind theme
├── postcss.config.js        # PostCSS config
├── .eslintrc.cjs            # ESLint rules
├── .env.example             # Environment template
├── README.md                # Full documentation
├── QUICKSTART.md            # Quick start guide
└── ARCHITECTURE.md          # This file
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                   Frontend Stack                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  UI Framework:         React 18.2                   │
│  Language:             TypeScript 5.3               │
│  Build Tool:           Vite 5.0                     │
│  Styling:              Tailwind CSS 3.4             │
│  Charts:               Recharts 2.10                │
│  Visualizations:       D3.js 7.8 + d3-cloud 1.2    │
│  Web Server:           Nginx (Alpine)               │
│  Container:            Docker (Multi-stage)         │
│  Linting:              ESLint 8.55                  │
│  PostCSS:              Autoprefixer                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Deployment Scenarios

### 1. Docker Compose (Recommended)

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### 2. Standalone Docker

```bash
docker build -t telemetra-frontend .
docker run -p 3000:80 telemetra-frontend
```

### 3. Static Hosting

```bash
npm run build
# Deploy dist/ folder to:
# - Netlify
# - Vercel
# - AWS S3 + CloudFront
# - GitHub Pages
```

### 4. Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: frontend
        image: telemetra-frontend:latest
        ports:
        - containerPort: 80
```

---

## Security Considerations

```
1. Headers
   ├─ X-Frame-Options: SAMEORIGIN
   ├─ X-Content-Type-Options: nosniff
   ├─ X-XSS-Protection: 1; mode=block
   └─ Referrer-Policy: no-referrer-when-downgrade

2. Environment Variables
   ├─ Never commit .env files
   ├─ Use .env.example for templates
   └─ Configure in deployment environment

3. WebSocket
   ├─ Validate all incoming messages
   ├─ Handle malformed JSON gracefully
   └─ Implement reconnection limits

4. CORS
   └─ Handled by backend, proxied through nginx

5. Input Validation
   └─ TypeScript guards for message types
```

---

## Monitoring & Debugging

```
Development:
  ├─ React DevTools
  ├─ TypeScript error checking
  ├─ Vite HMR overlay
  ├─ Browser console
  └─ Network tab for WebSocket

Production:
  ├─ Nginx access logs
  ├─ Nginx error logs
  ├─ Browser error tracking
  ├─ Performance monitoring
  └─ WebSocket connection metrics
```

---

## Future Enhancements

1. **Additional Visualizations**
   - Sentiment trend chart
   - Geographic viewer distribution
   - Revenue/donations tracker
   - Follower growth chart

2. **Features**
   - Multi-stream support
   - Historical data playback
   - Alert notifications
   - Custom dashboard layouts
   - Export metrics as CSV/JSON

3. **Performance**
   - Service Worker for offline support
   - Progressive Web App (PWA)
   - Virtual scrolling for large lists
   - Web Workers for heavy computations

4. **Testing**
   - Unit tests with Vitest
   - Component tests with React Testing Library
   - E2E tests with Playwright
   - WebSocket mock server for testing

---

**Last Updated**: 2025-10-16
**Version**: 1.0.0
**Status**: Production Ready
