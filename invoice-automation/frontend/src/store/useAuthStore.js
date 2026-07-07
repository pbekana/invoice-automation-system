import { create } from 'zustand';

const useAuthStore = create((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  token: localStorage.getItem('access_token'),
  user: null, // Could fetch and store user details later
  setAuth: (token, user = null) => {
    if (token) {
      localStorage.setItem('access_token', token);
      set({ isAuthenticated: true, token, user });
    } else {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ isAuthenticated: false, token: null, user: null });
    }
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ isAuthenticated: false, token: null, user: null });
  }
}));

export default useAuthStore;
