import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const GaugeChart = ({ value }) => {
  // Determine color based on value ranges
  const getColor = (val) => {
    if (val <= 30) return '#EF4444'; // Red
    if (val <= 70) return '#F59E0B'; // Yellow/Orange
    return '#10B981'; // Green
  };

  const color = getColor(value);
  const remaining = 100 - value;

  const data = {
    datasets: [
      {
        data: [value, remaining],
        backgroundColor: [color, '#E5E7EB'],
        borderWidth: 0,
        circumference: 180,
        rotation: 270,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: false,
      },
    },
  };

  return (
    <div className="relative w-full max-w-sm mx-auto">
      <Doughnut data={data} options={options} />
      <div className="absolute inset-0 flex items-center justify-center" style={{ top: '25%' }}>
        <div className="text-center">
          <div className="text-5xl font-bold" style={{ color }}>
            {value}
          </div>
          <div className="text-sm text-gray-500 mt-1">Buy/Sell Ratio</div>
        </div>
      </div>
    </div>
  );
};

export default GaugeChart;
