import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TradingPerformance = ({ trades, holdings }) => {
  // 수익률 계산
  const calculatePerformance = () => {
    if (!trades || trades.length === 0) {
      return {
        totalProfit: 0,
        totalReturn: 0,
        winRate: 0,
        totalTrades: 0
      };
    }

    let totalInvested = 0;
    let totalReturned = 0;
    let wins = 0;
    let completedTrades = 0;

    const tradesBySymbol = {};

    trades.forEach(trade => {
      if (!tradesBySymbol[trade.symbol]) {
        tradesBySymbol[trade.symbol] = { buys: [], sells: [] };
      }

      if (trade.action === 'buy') {
        tradesBySymbol[trade.symbol].buys.push(trade);
        totalInvested += trade.quantity * trade.price;
      } else if (trade.action === 'sell') {
        tradesBySymbol[trade.symbol].sells.push(trade);
        totalReturned += trade.quantity * trade.price;
      }
    });

    // 완료된 거래 쌍 계산
    Object.values(tradesBySymbol).forEach(({ buys, sells }) => {
      const minLength = Math.min(buys.length, sells.length);
      for (let i = 0; i < minLength; i++) {
        completedTrades++;
        const buyValue = buys[i].quantity * buys[i].price;
        const sellValue = sells[i].quantity * sells[i].price;
        if (sellValue > buyValue) wins++;
      }
    });

    const totalProfit = totalReturned - totalInvested;
    const totalReturn = totalInvested > 0 ? (totalProfit / totalInvested) * 100 : 0;
    const winRate = completedTrades > 0 ? (wins / completedTrades) * 100 : 0;

    return {
      totalProfit,
      totalReturn,
      winRate,
      totalTrades: trades.length
    };
  };

  // 일별 수익률 데이터 생성
  const generateChartData = () => {
    if (!trades || trades.length === 0) {
      return {
        labels: [],
        datasets: []
      };
    }

    // 날짜별로 거래 그룹화
    const dailyData = {};
    let cumulativeProfit = 0;

    trades
      .sort((a, b) => new Date(a.timestamp || a.created_at) - new Date(b.timestamp || b.created_at))
      .forEach(trade => {
        const date = new Date(trade.timestamp || trade.created_at).toLocaleDateString('ko-KR');
        const value = trade.quantity * trade.price;
        
        if (!dailyData[date]) {
          dailyData[date] = 0;
        }

        if (trade.action === 'sell') {
          dailyData[date] += value;
        } else if (trade.action === 'buy') {
          dailyData[date] -= value;
        }
      });

    const labels = Object.keys(dailyData);
    const data = labels.map(date => {
      cumulativeProfit += dailyData[date];
      return cumulativeProfit;
    });

    return {
      labels,
      datasets: [
        {
          label: '누적 수익',
          data,
          borderColor: data[data.length - 1] >= 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
          backgroundColor: data[data.length - 1] >= 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    };
  };

  const performance = calculatePerformance();
  const chartData = generateChartData();

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `수익: ${new Intl.NumberFormat('ko-KR', {
              style: 'currency',
              currency: 'KRW'
            }).format(context.parsed.y)}`;
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: (value) => {
            return new Intl.NumberFormat('ko-KR', {
              notation: 'compact',
              compactDisplay: 'short'
            }).format(value) + '원';
          }
        }
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">거래 성과</h2>
      
      {/* 성과 지표 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">총 수익</p>
          <p className={`text-xl font-bold ${
            performance.totalProfit >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {new Intl.NumberFormat('ko-KR', {
              style: 'currency',
              currency: 'KRW',
              signDisplay: 'always'
            }).format(performance.totalProfit)}
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">수익률</p>
          <p className={`text-xl font-bold ${
            performance.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {performance.totalReturn >= 0 ? '+' : ''}{performance.totalReturn.toFixed(2)}%
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">승률</p>
          <p className="text-xl font-bold text-blue-600">
            {performance.winRate.toFixed(1)}%
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">총 거래</p>
          <p className="text-xl font-bold text-gray-800">
            {performance.totalTrades}
          </p>
        </div>
      </div>

      {/* 수익률 차트 */}
      {chartData.labels.length > 0 ? (
        <div className="h-64">
          <Line data={chartData} options={chartOptions} />
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center text-gray-500">
          거래 데이터가 충분하지 않습니다
        </div>
      )}

      {/* 현재 포지션 */}
      {holdings && holdings.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">현재 포지션</h3>
          <div className="space-y-2">
            {holdings.map((holding, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">{holding.symbol}</p>
                  <p className="text-sm text-gray-600">{holding.quantity}주</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-800">
                    {new Intl.NumberFormat('ko-KR', {
                      style: 'currency',
                      currency: 'KRW'
                    }).format(holding.current_price * holding.quantity)}
                  </p>
                  <p className={`text-sm ${
                    holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {holding.profit_loss >= 0 ? '+' : ''}{holding.profit_loss?.toFixed(2)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingPerformance;
