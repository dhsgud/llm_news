# Market Sentiment Analyzer - Frontend

React-based frontend for the Market Sentiment Analyzer application.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Chart.js** - Data visualization
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Navigation.jsx
│   │   ├── AnalysisResults.jsx
│   │   ├── GaugeChart.jsx
│   │   ├── AdditionalInfoPanel.jsx
│   │   └── DailySentimentChart.jsx
│   ├── pages/           # Page components
│   │   ├── MarketDashboard.jsx
│   │   ├── StockDashboard.jsx
│   │   └── AutoTradingDashboard.jsx
│   ├── services/        # API services
│   │   └── api.js
│   ├── App.jsx          # Main app component with routing
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles (Tailwind)
├── public/              # Static assets
├── .env                 # Environment variables
├── TASK_10_SUMMARY.md   # Task 10 implementation summary
├── DASHBOARD_UI_GUIDE.md # UI component guide
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Features

### Phase 1: Market Analysis Dashboard ✅
- ✅ One-click market sentiment analysis
- ✅ Buy/sell ratio visualization with gauge chart
- ✅ Dynamic color coding (Red: 0-30, Yellow: 31-70, Green: 71-100)
- ✅ AI-generated trend summary display
- ✅ Collapsible 7-day sentiment chart
- ✅ VIX index display
- ✅ Responsive design for all devices
- ✅ Loading states and error handling

### Phase 2: Stock Dashboard (Coming Soon)
- Stock search and selection
- Stock-specific sentiment analysis
- Portfolio view

### Phase 3: Auto Trading Dashboard (Coming Soon)
- Trading configuration
- Auto-trading controls
- Trade history
- Performance metrics

## Development

The frontend communicates with the FastAPI backend running on `http://localhost:8000`. Make sure the backend server is running before starting the frontend development server.

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory, ready for deployment.

## Deployment

The frontend can be deployed to:
- Vercel
- Netlify
- GitHub Pages
- Any static hosting service

Make sure to update the `VITE_API_BASE_URL` environment variable to point to your production backend API.
