import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({ baseURL: API_BASE_URL });

// ─── Auth interceptors ────────────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      original.url !== '/api/auth/login' &&
      original.url !== '/api/auth/register'
    ) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        const res = await axios.post(`${API_BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken });
        const { access_token } = res.data;
        localStorage.setItem('access_token', access_token);
        original.headers.Authorization = `Bearer ${access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const loginUser = async (email, password) => {
  const res = await api.post('/api/auth/login', { email, password });
  const { access_token, refresh_token, user } = res.data;
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  localStorage.setItem('user', JSON.stringify(user));
  return res.data;
};

export const registerUser = async (userData) => {
  const res = await api.post('/api/auth/register', userData);
  return res.data;
};

export const logoutUser = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

// ─── AP (Accounts Payable / legacy) ──────────────────────────────────────────
export const uploadInvoice = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data;
};
export const getInvoices = async () => { const res = await api.get('/invoices'); return res.data; };
export const getDashboardData = async () => { const res = await api.get('/dashboard'); return res.data; };
export const sendMessage = async (message) => { const res = await api.post('/chat', { message }); return res.data; };
export const getVendors = async (params = {}) => { const res = await api.get('/api/vendors', { params }); return res.data; };
export const getPendingApprovals = async () => { const res = await api.get('/api/invoices/pending-approvals'); return res.data; };
export const approveInvoice = async (id, comments = '') => { const res = await api.post(`/api/invoices/${id}/approve`, { comments }); return res.data; };
export const rejectInvoice = async (id, reason) => { const res = await api.post(`/api/invoices/${id}/reject`, { reason }); return res.data; };
export const submitInvoice = async (id) => { const res = await api.post(`/api/invoices/${id}/submit`); return res.data; };

// ─── Customers ────────────────────────────────────────────────────────────────
export const getCustomers = async (params = {}) => { const res = await api.get('/api/customers', { params }); return res.data; };
export const getCustomer = async (id) => { const res = await api.get(`/api/customers/${id}`); return res.data; };
export const createCustomer = async (data) => { const res = await api.post('/api/customers', data); return res.data; };
export const updateCustomer = async (id, data) => { const res = await api.patch(`/api/customers/${id}`, data); return res.data; };
export const deleteCustomer = async (id) => { const res = await api.delete(`/api/customers/${id}`); return res.data; };

// ─── Products ─────────────────────────────────────────────────────────────────
export const getProducts = async (params = {}) => { const res = await api.get('/api/products', { params }); return res.data; };
export const getProduct = async (id) => { const res = await api.get(`/api/products/${id}`); return res.data; };
export const createProduct = async (data) => { const res = await api.post('/api/products', data); return res.data; };
export const updateProduct = async (id, data) => { const res = await api.patch(`/api/products/${id}`, data); return res.data; };
export const deleteProduct = async (id) => { const res = await api.delete(`/api/products/${id}`); return res.data; };

// ─── Company ──────────────────────────────────────────────────────────────────
export const getCompany = async () => { const res = await api.get('/api/company'); return res.data; };
export const saveCompany = async (data) => { const res = await api.put('/api/company', data); return res.data; };

// ─── AR Invoices ──────────────────────────────────────────────────────────────
export const getARInvoices = async (params = {}) => { const res = await api.get('/api/ar/invoices', { params }); return res.data; };
export const getARInvoice = async (id) => { const res = await api.get(`/api/ar/invoices/${id}`); return res.data; };
export const createARInvoice = async (data) => { const res = await api.post('/api/ar/invoices', data); return res.data; };
export const updateARInvoice = async (id, data) => { const res = await api.patch(`/api/ar/invoices/${id}`, data); return res.data; };
export const sendARInvoice = async (id) => { const res = await api.post(`/api/ar/invoices/${id}/send`); return res.data; };
export const markARInvoicePaid = async (id, data = {}) => { const res = await api.post(`/api/ar/invoices/${id}/paid`, data); return res.data; };

export default api;
