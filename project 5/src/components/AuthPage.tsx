import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ConnectionTest from './ConnectionTest';
import {
  Brain,
  Loader2,
  Store,
  User,
  Mail,
  Lock,
  ArrowLeft,
} from 'lucide-react';

const AuthPage: React.FC = () => {
  const location = useLocation();
  const isSignup = location.pathname === '/signup';
  const navigate = useNavigate();
  const { login, signup, error: authError, clearError, isAuthenticated, loading: authLoading } = useAuth();

  // Redirect if already authenticated (but only after auth context is initialized)
  React.useEffect(() => {
    if (!authLoading && isAuthenticated) {
      console.log('✅ User already authenticated, redirecting to dashboard');
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const [formData, setFormData] = useState({
    name: '',
    storeName: '',
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);

  // isSubmitting combines local loading state and auth context loading state
  const isSubmitting = isLoading || authLoading;
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    clearError();

    console.log('🔄 Form submission started:', {
      isSignup,
      email: formData.email,
      storeName: formData.storeName,
    });
    try {
      let success = false;
      if (isSignup) {
        success = await signup(
          formData.name,
          formData.storeName,
          formData.email,
          formData.password
        );
      } else {
        success = await login(formData.email, formData.password);
      }

      if (success) {
        console.log('✅ Authentication successful, redirecting to dashboard');
        navigate('/dashboard');
      } else {
        console.log('❌ Authentication failed');
      }
    } catch (err) {
      console.error('❌ Form submission error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <ConnectionTest />

        <div className="text-center">
          <div className="flex items-center justify-center mb-6">
            <div className="w-12 h-12 bg-teal-500 rounded-2xl flex items-center justify-center">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <span className="ml-2 text-3xl font-bold text-slate-900">
              RetailIQ
            </span>
          </div>
          <h2 className="text-3xl font-bold text-slate-900">
            {isSignup ? 'Create your account' : 'Sign in to your account'}
          </h2>
          <p className="mt-2 text-slate-600">
            {isSignup
              ? 'Start transforming your retail operations'
              : 'Access your analytics dashboard'}
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {isSignup && (
              <>
                <div>
                  <label htmlFor="name" className="sr-only">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                    <input
                      id="name"
                      name="name"
                      type="text"
                      required
                      value={formData.name}
                      onChange={handleChange}
                      className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                      placeholder="Full Name"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="storeName" className="sr-only">
                    Store Name
                  </label>
                  <div className="relative">
                    <Store className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                    <input
                      id="storeName"
                      name="storeName"
                      type="text"
                      required
                      value={formData.storeName}
                      onChange={handleChange}
                      className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                      placeholder="Store Name"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="Email address"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={isSignup ? 'new-password' : 'current-password'}
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg text-slate-900 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="Password"
                />
              </div>
            </div>

            {authError && (
              <div className="text-red-600 text-sm text-center bg-red-50 p-3 rounded-lg border border-red-200">
                {authError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-teal-500 hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 hover:shadow-lg"
            >
              {isSubmitting ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : isSignup ? (
                'Create Account'
              ) : (
                'Sign In'
              )}
            </button>

            <div className="text-center">
              <span className="text-gray-400">
                {isSignup
                  ? 'Already have an account?'
                  : "Don't have an account?"}
              </span>{' '}
              <Link
                to={isSignup ? '/login' : '/signup'}
                className="text-teal-600 hover:text-teal-500 font-medium transition-all hover:scale-105"
              >
                {isSignup ? 'Sign in' : 'Sign up'}
              </Link>
            </div>

            <div className="text-center">
              <Link
                to="/"
                className="inline-flex items-center text-slate-600 hover:text-teal-600 font-medium transition-all hover:scale-105"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to home
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
