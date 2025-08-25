import React, { useState, useEffect } from 'react';
import { Plus, Camera, Settings, Trash2, TestTube, CheckCircle, AlertCircle, Play, Square, Activity } from 'lucide-react';
import { cameraAPI } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';

interface Camera {
  id: number;
  name: string;
  rtsp_url: string;
  location: string;
  status: string;
  features: CameraFeature[];
  detection_active?: boolean;
  enabled_features?: string[];
}

interface CameraFeature {
  id: number;
  feature_type: string;
  enabled: boolean;
  coordinates?: any;
  settings?: any;
}

interface FeatureType {
  name: string;
  description: string;
  requires_coordinates: boolean;
  coordinate_type: string | null;
}

interface FeatureTypes {
  [key: string]: FeatureType;
}

const CameraSetup: React.FC = () => {
  const { user } = useAuth();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [featureTypes, setFeatureTypes] = useState<FeatureTypes>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [loading, setLoading] = useState(true);

  // Form states
  const [newCamera, setNewCamera] = useState({
    name: '',
    rtsp_url: '',
    location: ''
  });

  useEffect(() => {
    loadCameras();
    loadFeatureTypes();
  }, []);

  const loadCameras = async () => {
    try {
      const [camerasResponse, statusResponse] = await Promise.all([
        cameraAPI.getCameras(),
        cameraAPI.getDetectionStatus()
      ]);

      // Handle cameras response - our backend returns array directly
      const camerasData = Array.isArray(camerasResponse.data) ? camerasResponse.data : [];
        
      // Merge with detection status
      if (statusResponse.data.success && Array.isArray(statusResponse.data.cameras)) {
        const statusData = statusResponse.data.cameras;
        
        const enrichedCameras = camerasData.map((camera: Camera) => {
          const status = statusData.find((s: any) => s.camera_id === camera.id);
          return {
            ...camera,
            detection_active: status?.detection_active || false,
            enabled_features: status?.enabled_features || []
          };
        });
        
        setCameras(enrichedCameras);
      } else {
        setCameras(camerasData);
      }
    } catch (error) {
      console.error('Failed to load cameras:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFeatureTypes = async () => {
    try {
      const response = await cameraAPI.getFeatureTypes();
      if (response.data.success) {
        setFeatureTypes(response.data.feature_types);
      }
    } catch (error) {
      console.error('Failed to load feature types:', error);
    }
  };

  const addCamera = async () => {
    if (!newCamera.name || !newCamera.rtsp_url) {
      alert('Please fill in required fields');
      return;
    }

    try {
      const response = await cameraAPI.addCamera(newCamera);
      if (response.data.success) {
        setNewCamera({ name: '', rtsp_url: '', location: '' });
        setShowAddForm(false);
        loadCameras();
      } else {
        alert(response.data.error || 'Failed to add camera');
      }
    } catch (error) {
      console.error('Failed to add camera:', error);
      alert('Failed to add camera');
    }
  };

  const updateCameraFeatures = async (camera: Camera, features: any) => {
    try {
      const response = await cameraAPI.updateCameraFeatures(camera.id, features);
      if (response.data.success) {
        loadCameras();
        alert('Features updated successfully!');
      } else {
        alert(response.data.error || 'Failed to update features');
      }
    } catch (error) {
      console.error('Failed to update features:', error);
      alert('Failed to update features');
    }
  };

  const deleteCamera = async (cameraId: number) => {
    if (!confirm('Are you sure you want to delete this camera?')) return;

    try {
      const response = await cameraAPI.deleteCamera(cameraId);
      if (response.data.success) {
        loadCameras();
      } else {
        alert(response.data.error || 'Failed to delete camera');
      }
    } catch (error) {
      console.error('Failed to delete camera:', error);
      alert('Failed to delete camera');
    }
  };

  const testConnection = async (camera: Camera) => {
    try {
      const response = await cameraAPI.testConnection(camera.id);
      if (response.data.success) {
        alert('Connection test successful!');
      } else {
        alert(response.data.error || 'Connection test failed');
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed');
    }
  };

  const startDetection = async (camera: Camera) => {
    if (!user?.storeId) {
      alert('User has no associated store.');
      return;
    }
    try {
      const response = await cameraAPI.startDetection(user.storeId, camera.id);
      if (response.data.success) {
        loadCameras(); // Refresh to update detection status
        alert('Detection started successfully!');
      } else {
        alert(response.data.error || 'Failed to start detection');
      }
    } catch (error) {
      console.error('Failed to start detection:', error);
      alert('Failed to start detection');
    }
  };

  const stopDetection = async (camera: Camera) => {
    if (!user?.storeId) {
      alert('User has no associated store.');
      return;
    }
    try {
      const response = await cameraAPI.stopDetection(user.storeId, camera.id);
      if (response.data.success) {
        loadCameras(); // Refresh to update detection status
        alert('Detection stopped successfully!');
      } else {
        alert(response.data.error || 'Failed to stop detection');
      }
    } catch (error) {
      console.error('Failed to stop detection:', error);
      alert('Failed to stop detection');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Camera Management</h1>
          <p className="text-gray-600 mt-2">Configure your RTSP cameras and detection features</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700 flex items-center space-x-2"
        >
          <Plus className="w-5 h-5" />
          <span>Add Camera</span>
        </button>
      </div>

      {/* Add Camera Form */}
      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Add New Camera</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Camera Name *
              </label>
              <input
                type="text"
                value={newCamera.name}
                onChange={(e) => setNewCamera({ ...newCamera, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="e.g., Entrance Camera 1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <input
                type="text"
                value={newCamera.location}
                onChange={(e) => setNewCamera({ ...newCamera, location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="e.g., Main Entrance"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                RTSP URL *
              </label>
              <input
                type="text"
                value={newCamera.rtsp_url}
                onChange={(e) => setNewCamera({ ...newCamera, rtsp_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="rtsp://username:password@camera-ip:554/stream"
              />
              <p className="text-sm text-gray-500 mt-1">
                Supports RTSP, HTTP, or HTTPS URLs
              </p>
            </div>
          </div>
          <div className="flex justify-end space-x-3 mt-4">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={addCamera}
              className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700"
            >
              Add Camera
            </button>
          </div>
        </div>
      )}

      {/* Camera List */}
      {cameras.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Camera className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No cameras configured</h3>
          <p className="text-gray-600 mb-4">Add your first camera to start monitoring</p>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-teal-600 text-white px-4 py-2 rounded-lg hover:bg-teal-700"
          >
            Add Camera
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {cameras.map((camera) => (
            <CameraCard
              key={camera.id}
              camera={camera}
              featureTypes={featureTypes}
              onEdit={setSelectedCamera}
              onDelete={deleteCamera}
              onTest={testConnection}
              onUpdateFeatures={updateCameraFeatures}
              onStartDetection={startDetection}
              onStopDetection={stopDetection}
            />
          ))}
        </div>
      )}

      {/* Feature Configuration Modal */}
      {selectedCamera && (
        <FeatureConfigModal
          camera={selectedCamera}
          featureTypes={featureTypes}
          onClose={() => setSelectedCamera(null)}
          onSave={updateCameraFeatures}
        />
      )}
    </div>
  );
};

// Camera Card Component
const CameraCard: React.FC<{
  camera: Camera;
  featureTypes: FeatureTypes;
  onEdit: (camera: Camera) => void;
  onDelete: (id: number) => void;
  onTest: (camera: Camera) => void;
  onUpdateFeatures: (camera: Camera, features: any) => void;
  onStartDetection: (camera: Camera) => void;
  onStopDetection: (camera: Camera) => void;
}> = ({ camera, featureTypes, onEdit, onDelete, onTest, onStartDetection, onStopDetection }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const enabledFeatures = camera.features?.filter(f => f.enabled) || [];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{camera.name}</h3>
          {camera.location && (
            <p className="text-sm text-gray-600">{camera.location}</p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(camera.status)}
          <span className="text-sm capitalize text-gray-600">{camera.status}</span>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-500 break-all">{camera.rtsp_url}</p>
      </div>

      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Enabled Features:</h4>
        {enabledFeatures.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {enabledFeatures.map((feature) => (
              <span
                key={feature.id}
                className="px-2 py-1 bg-teal-100 text-teal-800 text-xs rounded-full"
              >
                {featureTypes[feature.feature_type]?.name || feature.feature_type}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No features enabled</p>
        )}
      </div>

      {/* Detection Status */}
      <div className="mb-4 p-3 rounded-lg bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium">Detection:</span>
            <span className={`text-sm ${camera.detection_active ? 'text-green-600' : 'text-gray-500'}`}>
              {camera.detection_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          {enabledFeatures.length > 0 && (
            <div className="flex space-x-2">
              {camera.detection_active ? (
                <button
                  onClick={() => onStopDetection(camera)}
                  className="flex items-center space-x-1 px-3 py-1 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                >
                  <Square className="w-3 h-3" />
                  <span>Stop</span>
                </button>
              ) : (
                <button
                  onClick={() => onStartDetection(camera)}
                  className="flex items-center space-x-1 px-3 py-1 text-xs bg-green-100 text-green-700 rounded-md hover:bg-green-200"
                >
                  <Play className="w-3 h-3" />
                  <span>Start</span>
                </button>
              )}
            </div>
          )}
        </div>
        {enabledFeatures.length === 0 && (
          <p className="text-xs text-orange-600 mt-1">
            Configure features first to enable detection
          </p>
        )}
      </div>

      <div className="flex justify-between space-x-2">
        <div className="flex space-x-2">
          <button
            onClick={() => onTest(camera)}
            className="flex items-center space-x-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
          >
            <TestTube className="w-4 h-4" />
            <span>Test</span>
          </button>
          <button
            onClick={() => onEdit(camera)}
            className="flex items-center space-x-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            <Settings className="w-4 h-4" />
            <span>Configure</span>
          </button>
        </div>
        <button
          onClick={() => onDelete(camera.id)}
          className="flex items-center space-x-1 px-3 py-2 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200"
        >
          <Trash2 className="w-4 h-4" />
          <span>Delete</span>
        </button>
      </div>
    </div>
  );
};

// Feature Configuration Modal Component
const FeatureConfigModal: React.FC<{
  camera: Camera;
  featureTypes: FeatureTypes;
  onClose: () => void;
  onSave: (camera: Camera, features: any) => void;
}> = ({ camera, featureTypes, onClose, onSave }) => {
  const [features, setFeatures] = useState<any>({});

  useEffect(() => {
    // Initialize features state from camera data
    const initialFeatures: any = {};
    
    Object.keys(featureTypes).forEach(featureType => {
      const existingFeature = camera.features?.find(f => f.feature_type === featureType);
      initialFeatures[featureType] = {
        enabled: existingFeature?.enabled || false,
        coordinates: existingFeature?.coordinates || null,
        settings: existingFeature?.settings || {}
      };
    });
    
    setFeatures(initialFeatures);
  }, [camera, featureTypes]);

  const toggleFeature = (featureType: string, enabled: boolean) => {
    setFeatures((prev: any) => ({
      ...prev,
      [featureType]: {
        ...prev[featureType],
        enabled
      }
    }));
  };

  const handleSave = () => {
    onSave(camera, features);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Configure Features - {camera.name}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {Object.entries(featureTypes).map(([featureType, featureInfo]) => (
            <div key={featureType} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="font-medium text-gray-900">{featureInfo.name}</h4>
                  <p className="text-sm text-gray-600">{featureInfo.description}</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={features[featureType]?.enabled || false}
                    onChange={(e) => toggleFeature(featureType, e.target.checked)}
                    className="rounded border-gray-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span className="ml-2 text-sm">Enable</span>
                </label>
              </div>
              
              {featureInfo.requires_coordinates && features[featureType]?.enabled && (
                <div className="mt-3 p-3 bg-yellow-50 rounded-md">
                  <p className="text-sm text-yellow-800">
                    <strong>Coordinate mapping required:</strong> This feature needs you to define {featureInfo.coordinate_type} coordinates on your camera feed. This will be configured after saving.
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default CameraSetup;