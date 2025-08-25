import React, { useState } from 'react';
import { Wifi, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../utils/api';

interface TestResult {
  name: string;
  status: 'success' | 'failed';
  details: string;
  url: string;
}

interface TestResults {
  timestamp: string;
  tests: TestResult[];
}

const ConnectionTest: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const runConnectionTest = async () => {
    setIsLoading(true);
    const results: TestResults = {
      timestamp: new Date().toISOString(),
      tests: [],
    };

    // Test 1: Direct URL access (test backend root)
    try {
      console.log('🔍 Testing direct URL access...');
      const backendRoot = API_BASE_URL.replace('/api', ''); // Remove /api for root test
      const response = await fetch(backendRoot, {
        method: 'GET',
        mode: 'cors',
      });
      const data = await response.json();
      results.tests.push({
        name: 'Direct URL Access',
        status: response.ok ? 'success' : 'failed',
        details: `Status: ${response.status} ${response.statusText}, Message: ${data.message || 'No message'}`,
        url: backendRoot,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      results.tests.push({
        name: 'Direct URL Access',
        status: 'failed',
        details: errorMessage,
        url: API_BASE_URL.replace('/api', ''),
      });
    }

    // Test 2: Health endpoint
    try {
      console.log('🔍 Testing health endpoint...');
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const data = await response.json();
      results.tests.push({
        name: 'Health Endpoint',
        status: response.ok ? 'success' : 'failed',
        details: `Status: ${response.status}, Data: ${JSON.stringify(data)}`,
        url: `${API_BASE_URL}/api/health`,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      results.tests.push({
        name: 'Health Endpoint',
        status: 'failed',
        details: errorMessage,
        url: `${API_BASE_URL}/health`,
      });
    }

    // Test 3: CORS preflight
    try {
      console.log('🔍 Testing CORS preflight...');
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'OPTIONS',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type',
        },
      });
      results.tests.push({
        name: 'CORS Preflight',
        status: response.ok ? 'success' : 'failed',
        details: `Status: ${response.status}, Headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`,
        url: `${API_BASE_URL}/api/auth/signup`,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      results.tests.push({
        name: 'CORS Preflight',
        status: 'failed',
        details: errorMessage,
        url: `${API_BASE_URL}/api/auth/signup`,
      });
    }

    // Test 4: Signup endpoint test
    try {
      console.log('🔍 Testing signup endpoint...');
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'testpass123',
          store_name: 'Test Store',
        }),
      });
      const data = await response.text();
      results.tests.push({
        name: 'Signup Endpoint Test',
        status: response.status < 500 ? 'success' : 'failed',
        details: `Status: ${response.status}, Response: ${data.substring(0, 200)}...`,
        url: `${API_BASE_URL}/api/auth/signup`,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      results.tests.push({
        name: 'Signup Endpoint Test',
        status: 'failed',
        details: errorMessage,
        url: `${API_BASE_URL}/api/auth/signup`,
      });
    }

    setTestResults(results);
    setIsLoading(false);
  };

  return (
    <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-8">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold flex items-center">
          <div className="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center mr-2">
            <Wifi className="h-4 w-4 text-blue-600" />
          </div>
          Connection Diagnostics
        </h3>
        <button
          onClick={runConnectionTest}
          disabled={isLoading}
          className="flex items-center space-x-2 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-all disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Wifi className="h-4 w-4" />
          )}
          <span>Run Tests</span>
        </button>
      </div>

      {testResults && (
        <div className="space-y-4">
          <div className="text-sm text-gray-600 mb-4">
            Test run at: {new Date(testResults.timestamp).toLocaleString()}
          </div>

          {testResults.tests.map((test: TestResult, index: number) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {test.status === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <span className="font-semibold">{test.name}</span>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    test.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {test.status}
                </span>
              </div>
              <div className="text-sm text-gray-600 mb-2">
                <strong>URL:</strong> {test.url}
              </div>
              <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                {test.details}
              </div>
            </div>
          ))}
        </div>
      )}

      {!testResults && !isLoading && (
        <div className="text-center py-8 text-gray-500">
          Click "Run Tests" to diagnose connection issues with your backend
        </div>
      )}
    </div>
  );
};

export default ConnectionTest;
