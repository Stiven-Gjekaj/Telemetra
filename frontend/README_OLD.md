# Telemetra Frontend

Real-time streaming analytics dashboard built with React, TypeScript, and Vite.

## Features

- **Real-time WebSocket Connection**: Auto-reconnect with configurable retry logic
- **Live Metrics Visualization**:
  - PulseBar: Animated viewer count display with pulse effects
  - ChatFlow: Real-time chat rate line chart with Recharts
  - EmoteCloud: D3-powered word cloud for top emotes
  - MomentsTimeline: Chronological list of detected anomalies
- **Responsive Design**: Dark theme optimized for streaming analytics
- **TypeScript**: Full type safety with strict compiler settings
- **Production Ready**: Multi-stage Docker build with nginx

## Tech Stack

- **React 18** - UI framework
- **TypeScript 5.3** - Type safety
- **Vite 5** - Build tool and dev server
- **Tailwind CSS 3** - Styling
- **Recharts** - Line charts for chat activity
- **D3.js** - Word cloud and advanced visualizations
- **Nginx** - Production web server

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── PulseBar.tsx     # Viewer count with pulse animation
│   │   ├── ChatFlow.tsx     # Chat rate line chart
│   │   ├── EmoteCloud.tsx   # D3 word cloud for emotes
│   │   └── MomentsTimeline.tsx  # Anomaly detection timeline
│   ├── hooks/
│   │   └── useWebSocket.ts  # WebSocket hook with auto-reconnect
│   ├── pages/
│   │   └── Dashboard.tsx    # Main dashboard page
│   ├── types/
│   │   └── metrics.ts       # TypeScript type definitions
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── Dockerfile               # Multi-stage production build
├── nginx.conf               # Nginx configuration
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── package.json             # Dependencies and scripts
```

## Prerequisites

- Node.js 18+ and npm
- Docker (for containerized deployment)
- Backend WebSocket server running on port 8000

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_WS_RECONNECT_INTERVAL=3000
VITE_WS_MAX_RECONNECT_ATTEMPTS=10
```

### 3. Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t telemetra-frontend .
```

### Run Container

```bash
docker run -p 3000:80 telemetra-frontend
```

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://backend:8000
      - VITE_WS_URL=ws://backend:8000
    depends_on:
      - backend
```

## Component Documentation

### PulseBar

Displays current viewer count with animated pulse effect.

```tsx
<PulseBar metrics={viewerMetrics} className="h-full" />
```

**Props**:
- `metrics`: ViewerMetrics | null
- `className?`: string

**Features**:
- Real-time viewer count with pulse animation
- Peak and average statistics
- Trend indicator (growing/declining/stable)
- Visual progress bar

### ChatFlow

Line chart showing chat rate over time.

```tsx
<ChatFlow metrics={chatRateMetrics} height={350} />
```

**Props**:
- `metrics`: ChatRateMetrics | null
- `className?`: string
- `height?`: number (default: 300)

**Features**:
- Area chart with gradient fill
- Real-time data updates
- Average and peak rate display
- Activity level indicator

### EmoteCloud

D3-powered word cloud for top emotes.

```tsx
<EmoteCloud emotes={topEmotes} height={400} maxEmotes={40} />
```

**Props**:
- `emotes`: Emote[]
- `className?`: string
- `width?`: number (default: 600)
- `height?`: number (default: 400)
- `maxEmotes?`: number (default: 30)

**Features**:
- Interactive word cloud with D3.js
- Alternative list view
- Size-based frequency visualization
- Color gradient for frequency intensity

### MomentsTimeline

Timeline of detected anomalies and moments.

```tsx
<MomentsTimeline moments={detectedMoments} maxMoments={15} />
```

**Props**:
- `moments`: Moment[]
- `className?`: string
- `maxMoments?`: number (default: 10)

**Features**:
- Chronological moment listing
- Severity indicators
- Expandable details
- Type-based filtering
- Relative timestamps

## WebSocket Integration

The `useWebSocket` hook manages WebSocket connections with automatic reconnection:

```tsx
const { state, metrics, error, reconnect, disconnect } = useWebSocket({
  url: 'ws://localhost:8000/live/demo_stream',
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
});
```

**Features**:
- Auto-reconnect on disconnect
- Connection state management
- Heartbeat/ping-pong
- Message type routing
- Time-series data aggregation

**WebSocket Message Format**:

```typescript
interface WebSocketMessage<T> {
  type: 'metrics' | 'moment' | 'error' | 'ping' | 'pong';
  data: T;
  timestamp: number;
}
```

**Metrics Update**:
```json
{
  "type": "metrics",
  "data": {
    "viewer_count": 1500,
    "chat_rate": 120.5,
    "top_emotes": [
      { "name": "Kappa", "count": 450 },
      { "name": "PogChamp", "count": 380 }
    ],
    "sentiment_score": 0.65,
    "timestamp": 1634567890000
  },
  "timestamp": 1634567890000
}
```

**Moment Detection**:
```json
{
  "type": "moment",
  "data": {
    "id": "moment-123",
    "type": "chat_spike",
    "description": "Chat activity increased by 250%",
    "severity": 0.85,
    "timestamp": 1634567890000,
    "metadata": {
      "previous_rate": 50,
      "current_rate": 175
    }
  },
  "timestamp": 1634567890000
}
```

## Type Definitions

All TypeScript types are defined in `src/types/metrics.ts`:

- `ConnectionState` - WebSocket connection states
- `Emote` - Emote data structure
- `Moment` - Anomaly detection result
- `TimeSeriesDataPoint` - Chart data point
- `ChatRateMetrics` - Chat activity metrics
- `ViewerMetrics` - Viewer count metrics
- `StreamMetrics` - Aggregated stream metrics
- `WebSocketMessage<T>` - Message envelope

## Development

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

### Project Commands

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## Configuration

### Vite Configuration

`vite.config.ts` includes:
- React plugin
- Path aliases (`@/` for `src/`)
- Proxy for API requests
- Production build settings

### TypeScript Configuration

`tsconfig.json` uses strict mode with:
- ES2020 target
- ESNext modules
- Strict type checking
- Path aliases support

### Tailwind Configuration

`tailwind.config.js` extends:
- Custom color palette (primary, dark)
- Animation utilities
- Custom keyframes

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

## Performance

- Code splitting with Vite
- Lazy loading for heavy components
- Efficient WebSocket message handling
- Optimized re-renders with React memoization
- Gzip compression in production (nginx)

## Troubleshooting

### WebSocket Connection Issues

1. Check backend is running on port 8000
2. Verify WebSocket URL in `.env`
3. Check browser console for connection errors
4. Ensure firewall allows WebSocket connections

### Build Errors

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   npm run dev
   ```

### Type Errors

1. Run type check to see detailed errors:
   ```bash
   npm run type-check
   ```

2. Ensure all dependencies are installed:
   ```bash
   npm install
   ```

## License

Part of the Telemetra MVP project.
