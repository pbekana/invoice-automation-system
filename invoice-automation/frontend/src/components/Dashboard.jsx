import React, { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title, PointElement, LineElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { getDashboardData, getInvoices } from '../services/api';
import { TrendingUp, CreditCard, PieChart as PieChartIcon, List, Calendar } from 'lucide-react';
import { motion } from 'framer-motion';

ChartJS.register(
  ArcElement, Tooltip, Legend, 
  CategoryScale, LinearScale, BarElement, Title, PointElement, LineElement
);

const Dashboard = ({ refreshTrigger }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dash, invs] = await Promise.all([getDashboardData(), getInvoices()]);
        setDashboardData(dash);
        setInvoices(invs);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [refreshTrigger]);

  if (loading) return <div className="p-8 text-center text-gray-400">Loading dashboard data...</div>;

  const categoryLabels = Object.keys(dashboardData.categories || {});
  const categoryTotals = Object.values(dashboardData.categories || {}).map(c => c.total);

  const pieData = {
    labels: categoryLabels,
    datasets: [{
      data: categoryTotals,
      backgroundColor: [
        'rgba(99, 102, 241, 0.6)',
        'rgba(236, 72, 153, 0.6)',
        'rgba(59, 130, 246, 0.6)',
        'rgba(16, 185, 129, 0.6)',
      ],
      borderColor: [
        '#6366f1', '#ec4899', '#3b82f6', '#10b981',
      ],
      borderWidth: 1,
    }],
  };

  const monthlyLabels = Object.keys(dashboardData.monthly || {});
  const monthlyTotals = Object.values(dashboardData.monthly || {}).map(m => m.total);

  const barData = {
    labels: monthlyLabels,
    datasets: [{
      label: 'Monthly Spending ($)',
      data: monthlyTotals,
      backgroundColor: 'rgba(99, 102, 241, 0.4)',
      borderColor: '#6366f1',
      borderWidth: 2,
      borderRadius: 8,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#94a3b8', font: { size: 10 } }
      }
    },
    scales: {
      y: { ticks: { color: '#94a3b8' }, grid: { borderDash: [5, 5], color: 'rgba(255, 255, 255, 0.05)' } },
      x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 grid-cols-3 gap-6">
        <StatCard 
          icon={<CreditCard className="text-indigo-400" />} 
          title="Total Spending" 
          value={`$${dashboardData.grand_total.toFixed(2)}`} 
          subtitle={`${dashboardData.total_invoices} Invoices`}
          delay={0}
        />
        <StatCard 
          icon={<PieChartIcon className="text-pink-400" />} 
          title="Top Category" 
          value={categoryLabels.length > 0 ? categoryLabels[categoryTotals.indexOf(Math.max(...categoryTotals))] : "None"} 
          subtitle="Highest expense category"
          delay={0.1}
        />
        <StatCard 
          icon={<TrendingUp className="text-emerald-400" />} 
          title="Avg. Invoice" 
          value={`$${dashboardData.total_invoices > 0 ? (dashboardData.grand_total / dashboardData.total_invoices).toFixed(2) : "0.00"}`} 
          subtitle="Monthly average"
          delay={0.2}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }} className="glass-card">
          <h3 className="text-lg font-semibold flex items-center gap-2"><PieChartIcon size={20} /> Expenses by Category</h3>
          <div className="h-64 mt-4">
            <Pie data={pieData} options={{ ...chartOptions, scales: { x: { display: false }, y: { display: false } } }} />
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }} className="glass-card">
          <h3 className="text-lg font-semibold flex items-center gap-2"><Calendar size={20} /> Monthly Trends</h3>
          <div className="h-64 mt-4">
            <Bar data={barData} options={chartOptions} />
          </div>
        </motion.div>
      </div>

      {/* Recent Invoices Table */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="glass-card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2"><List size={20} /> Recent Invoices</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Date</th>
                <th>Category</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {invoices.slice(0, 5).map((inv, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors">
                  <td className="font-medium">{inv.company}</td>
                  <td className="text-gray-400 font-mono text-sm">{inv.date}</td>
                  <td>
                    <span className={`badge badge-${inv.category.toLowerCase()}`}>
                      {inv.category}
                    </span>
                  </td>
                  <td className="font-mono text-indigo-300 font-semibold">${inv.total.toFixed(2)}</td>
                </tr>
              ))}
              {invoices.length === 0 && (
                <tr><td colSpan="4" className="text-center py-8 text-gray-500 italic">No invoices found. Upload your first invoice to see it here!</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
};

const StatCard = ({ icon, title, value, subtitle, delay }) => (
  <motion.div 
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ delay }}
    className="glass-card flex items-center gap-4"
  >
    <div className="p-3 bg-white/5 rounded-xl border border-white/10">{icon}</div>
    <div>
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">{title}</p>
      <h3 className="text-2xl font-bold bg-none -WebkitTextFillColor-initial !bg-clip-initial m-0" style={{ webkitTextFillColor: 'white' }}>{value}</h3>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </div>
  </motion.div>
);

export default Dashboard;
