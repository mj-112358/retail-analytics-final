import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();

  console.log('🛡️ ProtectedRoute check:', { isAuthenticated, loading, hasUser: !!user });

  // Show loading spinner while auth context is initializing
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500 mx-auto mb-4" />
          <p className="text-slate-600">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // Only redirect if auth is fully initialized and user is not authenticated
  if (!loading && !isAuthenticated) {
    console.log('🚫 Redirecting to login - not authenticated');
    return <Navigate to="/login" replace />;
  }

  // User is authenticated, render protected content
  console.log('✅ Rendering protected content');
  return <>{children}</>;
};

export default ProtectedRoute;
