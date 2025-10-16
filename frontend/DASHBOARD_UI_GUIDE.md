# Market Dashboard UI Guide

## Component Hierarchy

```
MarketDashboard (Page)
├── Header
│   ├── Title & Subtitle
│   └── Last Updated Timestamp
│
├── Main Container
│   ├── Analyze Button (with loading state)
│   ├── Error Message (conditional)
│   ├── AnalysisResults (conditional)
│   │   ├── GaugeChart
│   │   ├── Recommendation Badge
│   │   ├── Trend Summary
│   │   └── VIX Information
│   │
│   └── AdditionalInfoPanel (conditional)
│       ├── Toggle Button
│       └── Collapsible Content
│           ├── DailySentimentChart
│           └── Data Table
```

## User Flow

### 1. Initial State
```
┌─────────────────────────────────────────┐
│  Market Sentiment Analyzer              │
│  AI-powered market analysis...          │
└─────────────────────────────────────────┘

         ┌──────────────────┐
         │  Analyze Market  │
         └──────────────────┘
```

### 2. Loading State
```
┌─────────────────────────────────────────┐
│  Market Sentiment Analyzer              │
│  AI-powered market analysis...          │
└─────────────────────────────────────────┘

      ┌────────────────────────┐
      │  ⟳ Analyzing Market... │
      └────────────────────────┘
```

### 3. Results Displayed
```
┌─────────────────────────────────────────┐
│  Market Sentiment Analyzer              │
│  Last Updated: 2025-10-07 14:30         │
└─────────────────────────────────────────┘

         ┌──────────────────┐
         │  Analyze Market  │
         └──────────────────┘

┌─────────────────────────────────────────┐
│         ╭─────────╮                     │
│        │    75    │  ← Gauge Chart      │
│         ╰─────────╯                     │
│                                          │
│      [ 강력 매수 ]  ← Badge              │
│                                          │
│  Market Trend Summary                   │
│  ─────────────────────────────          │
│  The market shows positive sentiment... │
│                                          │
│  VIX Index: 18.50                       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Daily Sentiment Details          ▼     │
└─────────────────────────────────────────┘
```

### 4. Expanded Details
```
┌─────────────────────────────────────────┐
│  Daily Sentiment Details          ▲     │
├─────────────────────────────────────────┤
│                                          │
│  7-Day Sentiment Scores                 │
│  ┌────────────────────────────────┐    │
│  │  ▂▄█▆▃▅▇  ← Bar Chart          │    │
│  └────────────────────────────────┘    │
│                                          │
│  Date         Score    Sentiment        │
│  ─────────────────────────────────      │
│  10/01        0.50     Positive         │
│  10/02       -1.50     Negative         │
│  ...                                     │
└─────────────────────────────────────────┘
```

## Color Coding

### Buy/Sell Ratio Colors
- **0-30**: 🔴 Red (#EF4444) - Strong Sell
- **31-70**: 🟡 Yellow (#F59E0B) - Neutral
- **71-100**: 🟢 Green (#10B981) - Strong Buy

### Sentiment Colors (Daily Chart)
- **Positive (> 0)**: Green bars
- **Negative (< 0)**: Red bars
- **Neutral (= 0)**: Gray bars

## Responsive Breakpoints

### Mobile (< 640px)
- Single column layout
- Stacked header elements
- Full-width buttons
- Compact charts

### Tablet (640px - 1024px)
- Two-column header
- Optimized chart sizes
- Comfortable spacing

### Desktop (> 1024px)
- Full layout with max-width container
- Large, prominent charts
- Optimal spacing and typography

## API Data Format

### Expected Response from `/api/analyze`
```json
{
  "buy_sell_ratio": 75,
  "trend_summary": "The market shows positive sentiment...",
  "vix": 18.50,
  "last_updated": "2025-10-07T14:30:00Z"
}
```

### Expected Response from `/api/sentiment/daily`
```json
[
  {
    "date": "2025-10-01",
    "score": 0.50
  },
  {
    "date": "2025-10-02",
    "score": -1.50
  }
  // ... 7 days total
]
```

## Accessibility Features

### Keyboard Navigation
- Button is keyboard accessible (Tab + Enter)
- Collapsible panel toggles with Enter/Space

### Screen Readers
- Semantic HTML structure
- Descriptive button text
- Clear error messages

### Visual Accessibility
- High contrast colors
- Large, readable text
- Clear visual hierarchy
- Loading indicators

## Performance Optimizations

### Lazy Loading
- Daily sentiment data only loads when panel opens
- Charts render only when data is available

### State Management
- Minimal re-renders
- Efficient state updates
- Cached analysis results

### Bundle Size
- Tree-shaken Chart.js components
- Optimized Tailwind CSS
- Code splitting ready

## Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ features used
- CSS Grid and Flexbox
- Chart.js v4 compatible

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Common Issues & Solutions

### Issue: Charts not displaying
**Solution**: Ensure Chart.js components are registered in each chart component

### Issue: API calls failing
**Solution**: Check VITE_API_BASE_URL and backend server status

### Issue: Styles not applying
**Solution**: Verify Tailwind CSS is properly configured in postcss.config.js

### Issue: Build errors
**Solution**: Clear node_modules and reinstall dependencies

## Future Enhancement Ideas

1. **Real-time Updates**: WebSocket connection for live data
2. **Historical Comparison**: Compare current vs previous analyses
3. **Export Functionality**: Download reports as PDF
4. **Notifications**: Browser notifications for significant changes
5. **Dark Mode**: Toggle between light and dark themes
6. **Animations**: Smooth transitions for results appearing
7. **Accessibility**: Enhanced ARIA labels and keyboard shortcuts
8. **Internationalization**: Multi-language support
9. **Customization**: User preferences for chart types
10. **Mobile App**: React Native version

