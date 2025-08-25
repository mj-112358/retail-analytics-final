import React, { useState, useEffect } from 'react';
// import { useAuth } from '../contexts/AuthContext';
import { authAPI, cameraAPI, dashboardAPI } from '../utils/api';
import CameraSetup from './CameraSetup';
import {
  Users,
  Timer,
  Clock,
  TrendingUp,
  RefreshCw,
  MapPin,
  UserCheck,
  Users2,
  User,
} from 'lucide-react';

interface Insight {
  id: string;
  zone: string;
  time: string;
  feedback: string;
  type: 'warning' | 'success' | 'info';
  category: string;
}

interface DashboardMetrics {
  footfall_today: number;
  dwell_time_avg: number;
  queue_wait_time: number;
  peak_hour: string;
  unique_visitors: number;
  group_visitors: number;
  solo_visitors: number;
  shelf_interactions: number;
  zone_interactions: number;
}

interface ZoneData {
  zone: string;
  population: number;
  interactions: number;
  uniqueVisitors: number;
  dwellTime: number;
  avgDwellPerPerson: number;
}

const Dashboard: React.FC = () => {
  // const { user } = useAuth(); // user not currently used; retained for future store-specific filtering
  const [activeTab, setActiveTab] = useState<'analytics' | 'cameras'>('analytics');
  const [cameras, setCameras] = useState([]);
  // const [camerasLoaded, setCamerasLoaded] = useState(false); // unused
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    footfall_today: 0,
    dwell_time_avg: 0,
    queue_wait_time: 0,
    peak_hour: '',
    unique_visitors: 0,
    group_visitors: 0,
    solo_visitors: 0,
    shelf_interactions: 0,
    zone_interactions: 0,
  });

  const [insights, setInsights] = useState<Insight[]>([]);
  const [rawInsightObj, setRawInsightObj] = useState<any>(null);
  const [zoneData, setZoneData] = useState<ZoneData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  // const [selectedZone, setSelectedZone] = useState('all'); // zone filter not yet implemented
  // Promo / Festival controls
  const [promoEnabled, setPromoEnabled] = useState(false);
  const [festivalEnabled, setFestivalEnabled] = useState(false);
  const [promoName, setPromoName] = useState('');
  const [festivalName, setFestivalName] = useState('');
  const [promoStart, setPromoStart] = useState('');
  const [promoEnd, setPromoEnd] = useState('');
  const [festivalStart, setFestivalStart] = useState('');
  const [festivalEnd, setFestivalEnd] = useState('');
  const [lookbackMonths, setLookbackMonths] = useState(6);

  // Load cameras
  const loadCameras = async () => {
    try {
      const response = await cameraAPI.getCameras();
      if (response.status === 200) {
        setCameras(response.data);
      }
    } catch (error) {
      console.error('Error loading cameras:', error);
    }
  };

  // Verify user profile
  const verifyUserProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      if (response.status === 200) {
        console.log('✅ User profile verified:', response.data);
      }
    } catch (error) {
      console.error('❌ User profile verification failed:', error);
    }
  };

  // Load real dashboard data
  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Get real metrics from backend
      const metricsResponse = await dashboardAPI.getMetrics();

      if (metricsResponse.status === 200) {
        const metricsData = metricsResponse.data;
        
        // Update metrics with real data
        setMetrics({
          footfall_today: metricsData.footfall_today || 0,
          dwell_time_avg: metricsData.dwell_time_avg || 0,
          queue_wait_time: metricsData.queue_wait_time || 0,
          peak_hour: metricsData.peak_hour || 'N/A',
          unique_visitors: metricsData.unique_visitors || 0,
          group_visitors: metricsData.group_visitors || 0,
          solo_visitors: metricsData.solo_visitors || 0,
          shelf_interactions: metricsData.shelf_interactions || 0,
          zone_interactions: metricsData.zone_interactions || 0,
        });

        // Update zone data with real data
        const realZoneData = metricsData.zone_analytics || [];
        setZoneData(realZoneData.map((zone: any) => ({
          zone: zone.zone,
          population: zone.population || 0,
          interactions: zone.interactions || 0,
          uniqueVisitors: zone.unique_visitors || 0,
          dwellTime: zone.total_dwell_time || 0,
          avgDwellPerPerson: zone.avg_dwell_per_person || 0,
        })));
      } else {
        console.error('Failed to load dashboard metrics:', metricsResponse.status);
        // Fallback to empty data if API fails
        setMetrics({
          footfall_today: 0,
          dwell_time_avg: 0,
          queue_wait_time: 0,
          peak_hour: 'N/A',
          unique_visitors: 0,
          group_visitors: 0,
          solo_visitors: 0,
          shelf_interactions: 0,
          zone_interactions: 0,
        });
        setZoneData([]);
      }

      // Get real AI insights from backend
      const insightsResponse = await dashboardAPI.generateInsights({
        period_start: new Date(Date.now() - lookbackMonths * 30 * 24 * 60 * 60 * 1000).toISOString(),
        period_end: new Date().toISOString(),
        insight_type: 'comprehensive',
        include_promo: promoEnabled,
        promo_start: promoEnabled ? promoStart : undefined,
        promo_end: promoEnabled ? promoEnd : undefined
      });

      if (insightsResponse.status === 200 && insightsResponse.data) {
        const insightObj = insightsResponse.data;
        setRawInsightObj(insightObj);
        
        // Handle both insights and recommendations from backend
        const insights = insightObj.insights || '';
        const recommendations = insightObj.recommendations || [];
        
        const realInsights: Insight[] = [];
        
        // Add main insight if it exists
        if (insights) {
          realInsights.push({
            id: '1',
            zone: 'Store-wide',
            time: new Date().toLocaleTimeString(),
            feedback: insights,
            type: 'info',
            category: 'AI Insight'
          });
        }
        
        // Add recommendations
        recommendations.forEach((rec: string, index: number) => {
          realInsights.push({
            id: (index + 2).toString(),
            zone: 'Store-wide',
            time: new Date().toLocaleTimeString(),
            feedback: rec,
            type: 'success',
            category: 'Recommendation'
          });
        });
        
        setInsights(realInsights);
      } else {
        console.error('Failed to load insights:', insightsResponse.status);
        // Fallback to empty insights
        setInsights([]);
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Fallback to empty data on error
      setMetrics({
        footfall_today: 0,
        dwell_time_avg: 0,
        queue_wait_time: 0,
        peak_hour: 'N/A',
        unique_visitors: 0,
        group_visitors: 0,
        solo_visitors: 0,
        shelf_interactions: 0,
        zone_interactions: 0,
      });
      setZoneData([]);
      setInsights([]);
    }

    setIsLoading(false);
  };

  // Load data on component mount
  useEffect(() => {
    loadDashboardData();
    loadCameras();
    verifyUserProfile();
  }, []);

  // Refresh data
  const handleRefresh = () => {
    loadDashboardData();
  };

  // Format time in minutes and seconds
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Get insight icon
  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <TrendingUp className="w-4 h-4 text-orange-500" />;
      case 'success':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      default:
        return <TrendingUp className="w-4 h-4 text-blue-500" />;
    }
  };

  // Get category color
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'AI Insight':
        return 'bg-blue-100 text-blue-800';
      case 'Performance':
        return 'bg-green-100 text-green-800';
      case 'Warning':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('analytics')}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    activeTab === 'analytics'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Analytics
                </button>
                <button
                  onClick={() => setActiveTab('cameras')}
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    activeTab === 'cameras'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Camera Setup ({cameras.length})
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'analytics' ? (
          <div className="space-y-8">
            {/* Real Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Footfall Today */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Footfall Today</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.footfall_today}</p>
                  </div>
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </div>

              {/* Average Dwell Time */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Dwell Time</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatTime(metrics.dwell_time_avg)}
                    </p>
                  </div>
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Timer className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </div>

              {/* Queue Wait Time */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Queue Wait Time</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatTime(metrics.queue_wait_time)}
                    </p>
                  </div>
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Clock className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
              </div>

              {/* Peak Hour */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Peak Hour</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.peak_hour}</p>
                  </div>
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Visitor Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              {/* Unique Visitors */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Unique Visitors</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.unique_visitors}</p>
                  </div>
                  <div className="p-2 bg-indigo-100 rounded-lg">
                    <UserCheck className="w-6 h-6 text-indigo-600" />
                  </div>
                </div>
              </div>

              {/* Group Visitors */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Group Visitors</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.group_visitors}</p>
                  </div>
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Users2 className="w-6 h-6 text-green-600" />
                  </div>
                </div>
              </div>

              {/* Solo Visitors */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Solo Visitors</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.solo_visitors}</p>
                  </div>
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <User className="w-6 h-6 text-yellow-600" />
                  </div>
                </div>
              </div>

              {/* Shelf Interactions */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Shelf Interactions</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.shelf_interactions}</p>
                  </div>
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <MapPin className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </div>

              {/* Zone Interactions */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Zone Interactions</p>
                    <p className="text-2xl font-bold text-gray-900">{metrics.zone_interactions}</p>
                  </div>
                  <div className="p-2 bg-pink-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-pink-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Zone Analytics */}
            {zoneData.length > 0 && (
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Zone Analytics</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Zone
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Population
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Unique Visitors
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg Dwell Time
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {zoneData.map((zone, index) => (
                        <tr key={index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {zone.zone}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {zone.population}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {zone.uniqueVisitors}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatTime(zone.avgDwellPerPerson)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* AI Insights */}
            {insights.length > 0 && (
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">AI Insights</h3>
                  <div className="flex flex-wrap gap-4 items-center text-sm">
                    <div className="flex items-center space-x-1">
                      <input type="checkbox" checked={promoEnabled} onChange={e=>setPromoEnabled(e.target.checked)} />
                      <span>Promo</span>
                    </div>
                    {promoEnabled && (
                      <div className="flex flex-wrap gap-2">
                        <input placeholder="Name" className="border px-2 py-1 rounded" value={promoName} onChange={e=>setPromoName(e.target.value)} />
                        <input title="Promo start" type="date" className="border px-2 py-1 rounded" value={promoStart} onChange={e=>setPromoStart(e.target.value)} />
                        <input title="Promo end" type="date" className="border px-2 py-1 rounded" value={promoEnd} onChange={e=>setPromoEnd(e.target.value)} />
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <input type="checkbox" checked={festivalEnabled} onChange={e=>setFestivalEnabled(e.target.checked)} />
                      <span>Festival</span>
                    </div>
                    {festivalEnabled && (
                      <div className="flex flex-wrap gap-2">
                        <input placeholder="Name" className="border px-2 py-1 rounded" value={festivalName} onChange={e=>setFestivalName(e.target.value)} />
                        <input title="Festival start" type="date" className="border px-2 py-1 rounded" value={festivalStart} onChange={e=>setFestivalStart(e.target.value)} />
                        <input title="Festival end" type="date" className="border px-2 py-1 rounded" value={festivalEnd} onChange={e=>setFestivalEnd(e.target.value)} />
                      </div>
                    )}
                    <div className="flex items-center space-x-2">
                      <span>Lookback</span>
                      <input type="number" min={1} max={12} value={lookbackMonths} onChange={e=>setLookbackMonths(Number(e.target.value))} className="w-16 border px-2 py-1 rounded" />
                    </div>
                    <button onClick={handleRefresh} className="px-3 py-1 bg-teal-600 text-white rounded text-xs">Run</button>
                  </div>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {insights.map((insight) => (
                      <div key={insight.id} className="flex items-start space-x-3">
                        {getInsightIcon(insight.type)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCategoryColor(insight.category)}`}>
                              {insight.category}
                            </span>
                            <span className="text-sm text-gray-500">{insight.time}</span>
                          </div>
                          <p className="mt-1 text-sm text-gray-900">{insight.feedback}</p>
                        </div>
                      </div>
                    ))}
                    {rawInsightObj?.recommendations?.length > 0 && (
                      <div className="mt-6">
                        <h4 className="font-semibold mb-2">Recommendations</h4>
                        <ul className="list-disc ml-6 text-sm space-y-1">
                          {rawInsightObj.recommendations.map((r: string, i: number)=>(<li key={i}>{r}</li>))}
                        </ul>
                      </div>
                    )}
                    {promoEnabled && rawInsightObj?.promo_analysis && (
                      <div className="mt-6">
                        <h4 className="font-semibold mb-2">Promo Analysis</h4>
                        <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">{JSON.stringify(rawInsightObj.promo_analysis, null, 2)}</pre>
                      </div>
                    )}
                    {festivalEnabled && rawInsightObj?.festival_analysis && (
                      <div className="mt-6">
                        <h4 className="font-semibold mb-2">Festival Analysis</h4>
                        <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto">{JSON.stringify(rawInsightObj.festival_analysis, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* No Data Message */}
            {!isLoading && metrics.footfall_today === 0 && zoneData.length === 0 && (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Detection Data Yet</h3>
                <p className="text-gray-500 mb-4">
                  Start your cameras and begin detection to see real analytics data.
                </p>
                <button
                  onClick={() => setActiveTab('cameras')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Setup Cameras
                </button>
              </div>
            )}
          </div>
        ) : (
          <CameraSetup />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
