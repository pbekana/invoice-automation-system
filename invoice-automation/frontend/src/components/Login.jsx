import React, { useState } from 'react';
import { loginUser } from '../services/api';
import { FileText, Lock, Mail, AlertCircle, Eye, EyeOff, ArrowRight, ShieldCheck, Zap, Sparkles } from 'lucide-react';

const Login = ({ onLoginSuccess, onGoToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginUser(email, password);
      onLoginSuccess();
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200">
      
      {/* Left side: Premium SaaS branding panel */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-slate-900 overflow-hidden flex-col justify-between p-12 text-white">
        
        {/* Subtle decorative background gradients/shapes */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.15),transparent_50%)]" />
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl" />
        
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 opacity-5 bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:24px_24px]" />

        {/* Logo and Brand Name */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="p-2.5 bg-blue-600 rounded-lg shadow-lg shadow-blue-500/20 flex items-center justify-center">
            <FileText className="text-white" size={24} />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white">BillOrbit</span>
            <span className="ml-1.5 text-[9px] bg-blue-500/20 text-blue-400 font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">Enterprise</span>
          </div>
        </div>

        {/* Value Proposition / Testimonials */}
        <div className="relative z-10 max-w-md my-auto space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-extrabold tracking-tight leading-tight text-white">
              The Finance Operating System for Modern Teams.
            </h1>
            <p className="text-slate-400 text-base leading-relaxed">
              Automate accounts payable, streamline accounts receivable, and match invoices instantly with AI-driven categorization and matching rules.
            </p>
          </div>

          {/* Bullet highlights */}
          <div className="space-y-3.5">
            <div className="flex items-center gap-3 text-sm text-slate-300">
              <div className="p-1 bg-slate-800 rounded-md text-blue-400">
                <Sparkles size={16} />
              </div>
              <span>AI-Powered invoice text extraction (OCR)</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-300">
              <div className="p-1 bg-slate-800 rounded-md text-blue-400">
                <Zap size={16} />
              </div>
              <span>Automated AR invoicing and tracking workflow</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-300">
              <div className="p-1 bg-slate-800 rounded-md text-blue-400">
                <ShieldCheck size={16} />
              </div>
              <span>Secure approval rule matrix and audit trails</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 text-xs text-slate-500 flex justify-between">
          <span>&copy; {new Date().getFullYear()} BillOrbit Inc.</span>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Privacy & Terms</span>
        </div>
      </div>

      {/* Right side: Login form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 sm:p-12 md:p-16">
        <div className="w-full max-w-md space-y-8 animate-fade-in-up">
          
          {/* Header */}
          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Sign In
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Enter your email and password to access your dashboard
            </p>
          </div>

          {/* Form container */}
          <div className="bg-white dark:bg-slate-900/50 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            
            {error && (
              <div className="flex items-start gap-2.5 p-3.5 mb-6 text-sm text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 rounded-xl">
                <AlertCircle className="shrink-0 mt-0.5" size={16} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              
              {/* Email Address */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <Mail size={18} />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field pl-10"
                    placeholder="name@company.com"
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Password
                  </label>
                  <button 
                    type="button" 
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-medium"
                    onClick={() => alert("Password reset is managed by the system administrator.")}
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <Lock size={18} />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pl-10 pr-10"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-2.5 shadow-md shadow-blue-500/10 mt-6"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Signing in...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <span>Sign In</span>
                    <ArrowRight size={16} />
                  </div>
                )}
              </button>
            </form>
          </div>

          {/* Go to Register Link */}
          <div className="text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Don't have an account?{' '}
              <button 
                onClick={onGoToRegister} 
                type="button" 
                className="text-blue-600 dark:text-blue-400 hover:underline font-semibold transition-colors"
              >
                Create an account
              </button>
            </p>
          </div>

        </div>
      </div>

    </div>
  );
};

export default Login;
