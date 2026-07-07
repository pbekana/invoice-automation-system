import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Register from './components/Register';
import Invoices from './components/Invoices';
import Approvals from './components/Approvals';
import Vendors from './components/Vendors';
import Chatbot from './components/Chatbot';
import Customers from './components/Customers';
import Products from './components/Products';
import CompanyProfile from './components/CompanyProfile';
import ARInvoices from './components/ARInvoices';
import InvoiceBuilder from './components/InvoiceBuilder';
import ToastContainer from './components/ui/ToastContainer';
import useAuthStore from './store/useAuthStore';
import './styles/main.css';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={() => { window.location.href = '/'; }} onGoToRegister={() => { window.location.href = '/register'; }} />} />
        <Route path="/register" element={<Register onRegisterSuccess={() => { window.location.href = '/'; }} onGoToLogin={() => { window.location.href = '/login'; }} />} />

        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard refreshTrigger={0} />} />

          {/* Accounts Payable */}
          <Route path="ap/invoices" element={<Invoices refreshTrigger={0} />} />
          <Route path="ap/approvals" element={<Approvals />} />
          <Route path="ap/vendors" element={<Vendors />} />

          {/* Accounts Receivable */}
          <Route path="ar/invoices" element={<ARInvoices />} />
          <Route path="ar/invoices/new" element={<InvoiceBuilder />} />

          {/* Core entities */}
          <Route path="customers" element={<Customers />} />
          <Route path="products" element={<Products />} />

          {/* Settings */}
          <Route path="settings/company" element={<CompanyProfile />} />
        </Route>
      </Routes>
      <Chatbot />
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;
