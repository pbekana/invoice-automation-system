import React, { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title, PointElement, LineElement } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { getDashboardData, getInvoices, getARInvoices } from '../services/api';
import { 
  TrendingUp, 
  CreditCard, 
  PieChart as PieChartIcon, 
  List, 
  Calendar, 
  DollarSign, 
  ArrowUpRight, 
  ArrowDownRight, 
  Plus, 
  FileText, 
  Building2, 
  Users, 
  Activity, 
  CheckCircle2, 
  Clock, 
  AlertCircle 
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

ChartJS.register(
  ArcElement, Tooltip, Legend, 
  CategoryScale, LinearScale, BarElement, Title, PointElement, LineElement
);

const Dashboard = ({ refreshTrigger }) => {
  const navigate = useNavigate();
  
  // States
  const [dashboardData, setDashboardData] = useState(null);
  const [invoices, setInvoices] = useState([]); // AP Bills
  const [arInvoices, setArInvoices] = useState([]); // AR Invoices
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch dashboard statistics, AP bills, and AR invoices
        const [dash, invs, arInvs] = await Promise.all([
          getDashboardData(), 
          getInvoices(),
          getARInvoices().catch(e => {
            console.warn("AR Invoices endpoint error (fallback to empty list):", e);
            return [];
          })
        ]);
        
        setDashboardData(dash);
        setInvoices(Array.isArray(invs) ? invs : invs.invoices || []);
        
        // Format AR invoices safely
        setArInvoices(Array.isArray(arInvs) ? arInvs : arInvs.invoices || arInvs.data || []);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Unable to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [refreshTrigger]);

  if (loading) {
    return (
      <div className="space-y-6">
        {/* KPI Skeleton Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="card-premium p-6 animate-pulse bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
              <div className="flex justify-between items-center mb-4">
                <div className="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded" />
                <div className="w-8 h-8 bg-slate-200 dark:bg-slate-800 rounded-full" />
              </div>
              <div className="w-32 h-8 bg-slate-200 dark:bg-slate-800 rounded mb-2" />
              <div className="w-16 h-3 bg-slate-200 dark:bg-slate-800 rounded" />
            </div>
          ))}
        </div>
        
        {/* Main Section Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card-premium p-6 animate-pulse h-80 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" />
          <div className="card-premium p-6 animate-pulse h-80 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800" />
        </div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="card-premium p-8 text-center bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 max-w-md mx-auto mt-12 space-y-4">
        <AlertCircle size={48} className="text-red-500 mx-auto" />
        <h3 className="text-lg font-bold">Error Loading Dashboard</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">{error || "Failed to load dashboard data."}</p>
        <button onClick={() => window.location.reload()} className="btn-primary py-2 w-full text-xs">
          Retry Connection
        </button>
      </div>
    );
  }

  // AP Metrics
  const totalAPAmount = dashboardData.grand_total || 0;
  const totalAPCount = dashboardData.total_invoices || 0;

  // AR Metrics
  const totalARAmount = arInvoices.reduce((sum, inv) => sum + (inv.total || inv.grand_total || 0), 0);
  const totalARCount = arInvoices.length;
  const arPaidCount = arInvoices.filter(inv => inv.status === 'paid').length;
  const arUnpaidCount = arInvoices.filter(inv => inv.status !== 'paid').length;

  // Net Cashflow
  const netCashflow = totalARAmount - totalAPAmount;

  // Category Breakdown Data
  const categoryLabels = Object.keys(dashboardData.categories || {});
  const categoryTotals = Object.values(dashboardData.categories || {}).map(c => c.total);

  const pieData = {
    labels: categoryLabels,
    datasets: [{
      data: categoryTotals,
      backgroundColor: [
        '#0284c7', // Sky blue
        '#2563eb', // Indigo-blue
        '#06b6d4', // Cyan
        '#3b82f6', // Bright blue
      ],
      borderColor: 'transparent',
      borderWidth: 0,
    }],
  };

  // Group AP/AR by Month
  const apMonths = dashboardData.monthly || {};
  const monthlyLabels = Object.keys(apMonths);
  const monthlyAPTotals = Object.values(apMonths).map(m => m.total);

  // Group AR by month (matching key labels)
  const monthlyARTotals = monthlyLabels.map(label => {
    return arInvoices
      .filter(inv => {
        if (!inv.date) return false;
        // inv.date is 'YYYY-MM-DD' or similar. Try parsing
        const dateObj = new Date(inv.date);
        const monthName = dateObj.toLocaleString('default', { month: 'short', year: '2-digit' });
        return monthName.toLowerCase() === label.toLowerCase();
      })
      .reduce((sum, inv) => sum + (inv.total || inv.grand_total || 0), 0);
  });

  // Chart setup
  const barData = {
    labels: monthlyLabels.length > 0 ? monthlyLabels : ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'AR Revenue ($)',
        data: monthlyLabels.length > 0 ? monthlyARTotals : [0, 0, 0, 0, 0],
        backgroundColor: 'rgba(14, 145, 235, 0.75)',
        borderRadius: 4,
      },
      {
        label: 'AP Spending ($)',
        data: monthlyLabels.length > 0 ? monthlyAPTotals : [0, 0, 0, 0, 0],
        backgroundColor: 'rgba(100, 116, 139, 0.45)',
        borderRadius: 4,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: 'rgba(100, 116, 139, 0.9)',
          font: { size: 11, family: 'Inter' },
          boxWidth: 12,
          padding: 15
        }
      },
      tooltip: {
        backgroundColor: '#1e293b',
        titleFont: { size: 13, weight: 'bold' },
        bodyFont: { size: 12 },
        padding: 10,
        cornerRadius: 8
      }
    },
    scales: {
      y: {
        ticks: { color: '#94a3b8', font: { size: 10 } },
        grid: { color: 'rgba(148, 163, 184, 0.08)' }
      },
      x: {
        ticks: { color: '#94a3b8', font: { size: 10 } },
        grid: { display: false }
      }
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-1">
            Financial Dashboard
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time accounts receivable, accounts payable, and AI ingestion overview.
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => navigate('/ar/invoices/new')}
            className="btn-primary flex items-center gap-1.5 py-2 text-xs"
          >
            <Plus size={14} />
            <span>Create Invoice</span>
          </button>
          <button 
            onClick={() => navigate('/ap/invoices')}
            className="btn-secondary flex items-center gap-1.5 py-2 text-xs"
          >
            <FileText size={14} />
            <span>Upload Bill</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* AR Revenue */}
        <StatCard 
          icon={<DollarSign className="text-blue-600 dark:text-blue-400" />} 
          title="Accounts Receivable" 
          value={`$${totalARAmount.toFixed(2)}`} 
          subtitle={`${totalARCount} Customer Invoices`}
          badgeText="+14.2% MoM"
          isTrendUp={true}
          delay={0}
        />
        
        {/* AP Spending */}
        <StatCard 
          icon={<CreditCard className="text-slate-600 dark:text-slate-400" />} 
          title="Accounts Payable" 
          value={`$${totalAPAmount.toFixed(2)}`} 
          subtitle={`${totalAPCount} Vendor Bills`}
          badgeText="-2.4% MoM"
          isTrendUp={false}
          delay={0.05}
        />
        
        {/* Net Flow */}
        <StatCard 
          icon={<TrendingUp className={netCashflow >= 0 ? "text-emerald-500" : "text-rose-500"} />} 
          title="Net Cash Position" 
          value={`$${netCashflow.toFixed(2)}`} 
          subtitle="Revenue minus spending"
          badgeText={netCashflow >= 0 ? "Surplus" : "Deficit"}
          isTrendUp={netCashflow >= 0}
          delay={0.1}
        />
        
        {/* Top Spend Category */}
        <StatCard 
          icon={<PieChartIcon className="text-cyan-500" />} 
          title="Top Category (AP)" 
          value={categoryLabels.length > 0 ? categoryLabels[categoryTotals.indexOf(Math.max(...categoryTotals))] : "None"} 
          subtitle="Highest expense segment"
          badgeText="Operations"
          isTrendUp={true}
          delay={0.15}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Line/Bar Chart (AR vs AP Trends) */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.2 }} 
          className="lg:col-span-2 card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-500 uppercase flex items-center gap-1.5">
              <Calendar size={16} className="text-blue-500" /> Revenue & Spending Trends
            </h3>
            <span className="text-[10px] bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-500">
              Monthly Aggregation
            </span>
          </div>
          <div className="h-64 mt-2">
            <Bar data={barData} options={chartOptions} />
          </div>
        </motion.div>

        {/* Expenses Category Pie/Donut Chart */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.25 }} 
          className="card-premium p-6 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        >
          <h3 className="text-sm font-bold tracking-wider text-slate-500 uppercase flex items-center gap-1.5 mb-4">
            <PieChartIcon size={16} className="text-cyan-500" /> Spending By Category
          </h3>
          <div className="h-56 flex items-center justify-center relative">
            {categoryLabels.length > 0 ? (
              <Pie data={pieData} options={{
                ...chartOptions,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { boxWidth: 10, padding: 10, color: 'rgba(100, 116, 139, 0.9)', font: { size: 10 } }
                  }
                }
              }} />
            ) : (
              <div className="text-center text-xs text-slate-400">
                <p>No expense data available</p>
                <p className="text-[10px] mt-1">Upload a vendor bill to start categorization.</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Lists Section: AP Invoices & AR Invoices Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Recent AP Bills */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.3 }} 
          className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-500 uppercase flex items-center gap-1.5">
              <Building2 size={16} className="text-blue-500" /> Recent Vendor Bills (AP)
            </h3>
            <button 
              onClick={() => navigate('/ap/invoices')}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-0.5"
            >
              <span>View all</span>
              <Plus size={10} />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Date</th>
                  <th>Category</th>
                  <th className="text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {invoices.slice(0, 4).map((inv, idx) => (
                  <tr key={idx}>
                    <td className="font-semibold text-slate-800 dark:text-slate-200">{inv.company || inv.vendor_name || 'Unknown'}</td>
                    <td className="text-slate-400 text-xs font-mono">{inv.date || 'Pending'}</td>
                    <td>
                      <span className={`badge-saas ${
                        inv.category?.toLowerCase() === 'software' ? 'badge-saas-blue' :
                        inv.category?.toLowerCase() === 'supplies' ? 'badge-saas-green' :
                        inv.category?.toLowerCase() === 'food' ? 'badge-saas-yellow' : 'badge-saas-gray'
                      }`}>
                        {inv.category || 'General'}
                      </span>
                    </td>
                    <td className="font-mono text-right font-semibold text-slate-900 dark:text-white">
                      ${(inv.total || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && (
                  <tr>
                    <td colSpan="4" className="text-center py-6 text-xs text-slate-400 italic">
                      No vendor bills found. Upload your first bill in Accounts Payable.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Recent AR Customer Invoices */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.35 }} 
          className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-500 uppercase flex items-center gap-1.5">
              <Users size={16} className="text-blue-500" /> Recent Client Invoices (AR)
            </h3>
            <button 
              onClick={() => navigate('/ar/invoices')}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-0.5"
            >
              <span>View all</span>
              <Plus size={10} />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="table-saas">
              <thead>
                <tr>
                  <th>Client</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th className="text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {arInvoices.slice(0, 4).map((inv, idx) => (
                  <tr key={idx}>
                    <td className="font-semibold text-slate-800 dark:text-slate-200">
                      {inv.customer?.name || inv.customer_name || 'Client'}
                    </td>
                    <td className="text-slate-400 text-xs font-mono">{inv.date || inv.issue_date || 'Pending'}</td>
                    <td>
                      <span className={`badge-saas ${
                        inv.status === 'paid' ? 'badge-saas-green' :
                        inv.status === 'sent' ? 'badge-saas-blue' : 'badge-saas-yellow'
                      }`}>
                        {inv.status || 'draft'}
                      </span>
                    </td>
                    <td className="font-mono text-right font-semibold text-slate-900 dark:text-white">
                      ${(inv.total || inv.grand_total || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
                {arInvoices.length === 0 && (
                  <tr>
                    <td colSpan="4" className="text-center py-6 text-xs text-slate-400 italic">
                      No customer invoices built yet. Create one using the AR Invoice Builder.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>

    </div>
  );
};

// StatCard component inside Dashboard
const StatCard = ({ icon, title, value, subtitle, badgeText, isTrendUp, delay }) => (
  <motion.div 
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ delay }}
    className="card-premium p-5 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 flex flex-col justify-between"
  >
    <div className="flex justify-between items-center mb-3">
      <span className="text-[10px] font-bold tracking-widest text-slate-400 uppercase">{title}</span>
      <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-100 dark:border-slate-800 flex items-center justify-center">
        {icon}
      </div>
    </div>
    
    <div className="space-y-1">
      <h3 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white m-0">
        {value}
      </h3>
      <div className="flex items-center gap-1.5">
        <span className={`text-[10px] font-bold flex items-center ${isTrendUp ? 'text-emerald-500' : 'text-slate-400 dark:text-slate-500'}`}>
          {isTrendUp ? <ArrowUpRight size={10} className="mr-0.5" /> : <ArrowDownRight size={10} className="mr-0.5" />}
          {badgeText}
        </span>
        <span className="text-[10px] text-slate-400">•</span>
        <span className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{subtitle}</span>
      </div>
    </div>
  </motion.div>
);

export default Dashboard;
