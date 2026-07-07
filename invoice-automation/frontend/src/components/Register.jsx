import React, { useState } from 'react';
import { registerUser } from '../services/api';
import { FileText, Lock, Mail, User, AlertCircle, Shield, Briefcase, ArrowLeft, ArrowRight, Eye, EyeOff } from 'lucide-react';

const Register = ({ onRegisterSuccess, onGoToLogin }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [department, setDepartment] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await registerUser({ name, email, password, department, roles: ['submitter'] });
      // Call success callback
      onRegisterSuccess(email, password);
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please make sure the email is unique.');
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

        {/* Value Proposition */}
        <div className="relative z-10 max-w-md my-auto space-y-8">
          <div className="space-y-4">
            <h1 className="text-4xl font-extrabold tracking-tight leading-tight text-white">
              Start Automating Your Finance Workflows.
            </h1>
            <p className="text-slate-400 text-base leading-relaxed">
              Create an account in seconds to start importing invoices, processing files with OCR, setting up dynamic approval chains, and tracking custom client accounts.
            </p>
          </div>

          <div className="p-6 bg-slate-800/40 border border-slate-700/50 rounded-2xl backdrop-blur-sm">
            <p className="text-slate-300 italic text-sm">
              "Integrating BillOrbit into our accounting workflow saved us over 15 hours a week in manual entry. The AI categorization accuracy was surprisingly high!"
            </p>
            <div className="mt-4 flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold text-white">
                JD
              </div>
              <div>
                <p className="text-xs font-semibold text-white">John Doe</p>
                <p className="text-[10px] text-slate-400">Head of Finance, TechCorp</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 text-xs text-slate-500 flex justify-between">
          <span>&copy; {new Date().getFullYear()} BillOrbit Inc.</span>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Privacy & Terms</span>
        </div>
      </div>

      {/* Right side: Register form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 sm:p-12 md:p-16 overflow-y-auto">
        <div className="w-full max-w-md space-y-8 animate-fade-in-up py-8">
          
          {/* Header */}
          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Create your account
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              Let's set up your team account to automate billing & payments
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

            <form onSubmit={handleSubmit} className="space-y-4">
              
              {/* Full Name */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <User size={18} />
                  </div>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input-field pl-10"
                    placeholder="Jane Doe"
                    required
                  />
                </div>
              </div>

              {/* Email Address */}
              <div className="space-y-1">
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
                    placeholder="jane@company.com"
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <Lock size={18} />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pl-10 pr-10"
                    placeholder="Min. 8 characters"
                    minLength={8}
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

              {/* Department */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Department
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <Briefcase size={18} />
                  </div>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="input-field pl-10"
                    placeholder="Finance, Procurement, Operations..."
                  />
                </div>
              </div>

              {/* Security Banner / Info */}
              <div className="flex items-center gap-2 p-3 bg-slate-50 dark:bg-slate-900 rounded-xl text-slate-500 dark:text-slate-400 text-xs border border-slate-100 dark:border-slate-800">
                <Shield size={16} className="text-blue-500 shrink-0" />
                <span>Your account defaults to a submitter role for security.</span>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-2.5 shadow-md shadow-blue-500/10 mt-4"
              >
                {loading ? (
                  <div className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Creating account...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1">
                    <span>Create Account</span>
                    <ArrowRight size={16} />
                  </div>
                )}
              </button>
            </form>
          </div>

          {/* Go to Login Link */}
          <div className="text-center">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{' '}
              <button 
                onClick={onGoToLogin} 
                type="button" 
                className="text-blue-600 dark:text-blue-400 hover:underline font-semibold transition-colors"
              >
                Sign In
              </button>
            </p>
          </div>

        </div>
      </div>

    </div>
  );
};

export default Register;
