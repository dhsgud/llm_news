# Component Showcase - Market Dashboard

## 1. MarketDashboard (Main Page)

**Location**: `src/pages/MarketDashboard.jsx`

**Purpose**: Main container page that orchestrates all dashboard components

**Key Features**:
- State management for analysis results
- API integration
- Error handling
- Responsive layout

**Props**: None (top-level page component)

**State**:
```javascript
{
  lastUpdated: string | null,      // ISO timestamp
  loading: boolean,                 // API call in progress
  error: string | null,             // Error message
  analysisResult: object | null     // Analysis data
}
```

---

## 2. AnalysisResults Component

**Location**: `src/components/AnalysisResults.jsx`

**Purpose**: Display analysis results with gauge chart and summary

**Props**:
```javascript
{
  result: {
    buy_sell_ratio: number,    // 0-100
    trend_summary: string,     // AI-generated summary
    vix: number               // VIX index value
  }
}
```

**Features**:
- Integrates GaugeChart component
- Color-coded recommendation badge
- Formatted trend summary
- VIX information display

**Example Usage**:
```jsx
<AnalysisResults 
  result={{
    buy_sell_ratio: 75,
    trend_summary: "Market shows positive sentiment...",
    vix: 18.50
  }}
/>
```

---

## 3. GaugeChart Component

**Location**: `src/components/GaugeChart.jsx`

**Purpose**: Visual gauge chart for buy/sell ratio

**Props**:
```javascript
{
  value: number  // 0-100
}
```

**Color Logic**:
```javascript
value <= 30  → Red (#EF4444)
value <= 70  → Yellow (#F59E0B)
value > 70   → Green (#10B981)
```

**Chart Configuration**:
- Type: Doughnut (semi-circle)
- Rotation: 270° (bottom half)
- Circumference: 180° (half circle)
- No legend or tooltip

**Example Usage**:
```jsx
<GaugeChart value={75} />
```

**Visual Output**:
```
     ╭─────────╮
    │    75    │  ← Large number
     ╰─────────╯
   Buy/Sell Ratio  ← Label
```

---

## 4. AdditionalInfoPanel Component

**Location**: `src/components/AdditionalInfoPanel.jsx`

**Purpose**: Collapsible panel showing detailed daily sentiment data

**Props**: None (fetches its own data)

**Features**:
- Toggle expand/collapse
- Lazy data loading
- Loading state
- Error handling
- Integrates DailySentimentChart
- Data table view

**State**:
```javascript
{
  isOpen: boolean,
  dailyData: array | null,
  loading: boolean,
  error: string | null
}
```

**API Call**: `getDailySentiment(7)` when panel opens

**Example Usage**:
```jsx
<AdditionalInfoPanel />
```

---

## 5. DailySentimentChart Component

**Location**: `src/components/DailySentimentChart.jsx`

**Purpose**: Bar chart showing 7 days of sentiment scores

**Props**:
```javascript
{
  dailyData: [
    {
      date: string,    // ISO date
      score: number    // -1.5 to 1.0
    }
  ]
}
```

**Color Logic**:
```javascript
score > 0  → Green (Positive)
score < 0  → Red (Negative)
score = 0  → Gray (Neutral)
```

**Chart Configuration**:
- Type: Bar
- Height: 256px (h-64)
- Responsive: true
- Title: "7-Day Sentiment Scores"
- Y-axis: Sentiment Score
- X-axis: Dates (Korean format)

**Example Usage**:
```jsx
<DailySentimentChart 
  dailyData={[
    { date: "2025-10-01", score: 0.5 },
    { date: "2025-10-02", score: -1.5 }
  ]}
/>
```

---

## Component Interaction Flow

```
User clicks "Analyze Market"
         ↓
MarketDashboard.handleAnalyze()
         ↓
API call: analyzeMarket('general')
         ↓
Set analysisResult state
         ↓
Render AnalysisResults component
    ├── GaugeChart (with buy_sell_ratio)
    ├── Recommendation badge
    ├── Trend summary
    └── VIX info
         ↓
Render AdditionalInfoPanel
         ↓
User clicks to expand panel
         ↓
AdditionalInfoPanel.fetchDailyData()
         ↓
API call: getDailySentiment(7)
         ↓
Render DailySentimentChart
    └── Bar chart with 7 days data
```

---

## Styling Patterns

### Card Style
```jsx
className="bg-white rounded-lg shadow-lg p-8"
```

### Button Style (Primary)
```jsx
className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg"
```

### Button Style (Disabled)
```jsx
className="bg-gray-400 cursor-not-allowed"
```

### Error Message
```jsx
className="bg-red-50 border border-red-200 rounded-lg p-4"
```

### Badge Style
```jsx
className="bg-green-50 text-green-600 px-6 py-3 rounded-full"
```

---

## Responsive Design

### Mobile (< 640px)
```jsx
className="flex-col sm:flex-row"  // Stack on mobile
className="mt-4 sm:mt-0"          // Margin adjustment
className="px-4 sm:px-6 lg:px-8"  // Padding scale
```

### Tablet (640px - 1024px)
- Two-column layouts
- Medium spacing
- Optimized chart sizes

### Desktop (> 1024px)
- Full layout with max-width: 1280px (max-w-7xl)
- Large spacing
- Full-size charts

---

## Chart.js Registration

Each chart component must register required Chart.js components:

**GaugeChart**:
```javascript
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
ChartJS.register(ArcElement, Tooltip, Legend);
```

**DailySentimentChart**:
```javascript
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);
```

---

## Error Handling Patterns

### API Error
```javascript
try {
  const result = await analyzeMarket('general');
  setAnalysisResult(result);
} catch (err) {
  setError(err.response?.data?.error || 'Failed to analyze market');
}
```

### Display Error
```jsx
{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <p className="text-sm text-red-800">{error}</p>
  </div>
)}
```

---

## Loading States

### Button Loading
```jsx
{loading ? (
  <span className="flex items-center">
    <svg className="animate-spin h-5 w-5 mr-3">...</svg>
    Analyzing Market...
  </span>
) : (
  'Analyze Market'
)}
```

### Panel Loading
```jsx
{loading && (
  <div className="flex justify-center py-8">
    <svg className="animate-spin h-8 w-8">...</svg>
  </div>
)}
```

---

## Date Formatting

### Korean Locale
```javascript
new Date(lastUpdated).toLocaleString('ko-KR', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})
// Output: "2025-10-07 14:30"
```

### Short Date
```javascript
date.toLocaleDateString('ko-KR', { 
  month: 'short', 
  day: 'numeric' 
})
// Output: "10월 7일"
```

---

## Testing Scenarios

### Happy Path
1. Click "Analyze Market"
2. See loading spinner
3. Results appear with gauge showing 75
4. Green badge shows "강력 매수"
5. Trend summary displays
6. Click to expand daily details
7. Bar chart and table appear

### Error Path
1. Backend is down
2. Click "Analyze Market"
3. See loading spinner
4. Error message appears
5. User can retry

### Edge Cases
- Ratio = 0 (minimum)
- Ratio = 100 (maximum)
- Ratio = 30 (boundary)
- Ratio = 70 (boundary)
- Empty trend summary
- Missing VIX data
- No daily data available

---

## Performance Considerations

### Lazy Loading
- Daily sentiment data only loads when panel opens
- Prevents unnecessary API calls

### Memoization Opportunities
- GaugeChart color calculation could be memoized
- Chart data transformation could be memoized

### Bundle Size
- Chart.js: ~150KB (gzipped)
- React: ~40KB (gzipped)
- Total bundle: ~450KB (uncompressed)

---

## Accessibility

### Keyboard Navigation
- Button is focusable and activatable with Enter
- Panel toggle works with Enter/Space

### Screen Readers
- Semantic HTML (header, main, button)
- Descriptive button text
- Alt text for loading spinners (aria-label)

### Color Contrast
- All text meets WCAG AA standards
- Error messages have sufficient contrast
- Chart colors are distinguishable

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features**:
- ES6+ (arrow functions, destructuring)
- CSS Grid and Flexbox
- SVG support
- Canvas API (for Chart.js)

