import { Bar } from 'react-chartjs-2';
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

const DailySentimentChart = ({ dailyData }) => {
  // Transform data for chart
  const labels = dailyData.map(item => {
    const date = new Date(item.date);
    return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
  });

  const scores = dailyData.map(item => item.score);

  // Color bars based on sentiment
  const backgroundColors = scores.map(score => {
    if (score > 0) return 'rgba(16, 185, 129, 0.8)'; // Green for positive
    if (score < 0) return 'rgba(239, 68, 68, 0.8)'; // Red for negative
    return 'rgba(156, 163, 175, 0.8)'; // Gray for neutral
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Daily Sentiment Score',
        data: scores,
        backgroundColor: backgroundColors,
        borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: '7-Day Sentiment Scores',
        font: {
          size: 16,
          weight: 'bold',
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const score = context.parsed.y;
            const sentiment = score > 0 ? 'Positive' : score < 0 ? 'Negative' : 'Neutral';
            return `${sentiment}: ${score.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Sentiment Score',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div className="h-64">
      <Bar data={data} options={options} />
    </div>
  );
};

export default DailySentimentChart;
