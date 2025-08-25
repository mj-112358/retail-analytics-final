import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Camera,
  Brain,
  BarChart3,
  Users,
  Shield,
  Eye,
  MapPin,
  Clock,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Play,
  Target,
  Timer,
  Activity,
  MousePointer,
  Zap,
  Mail,
  Phone,
  MapPin as LocationIcon,
  Twitter,
  Linkedin,
  Github,
  ChevronRight,
} from 'lucide-react';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);

  // Redirect if already authenticated (but only after auth context is initialized)
  useEffect(() => {
    if (!loading && isAuthenticated) {
      console.log('✅ User authenticated, redirecting from home to dashboard');
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);
  const [demoData, setDemoData] = useState({
    zoneA: {
      visitors: 12,
      engagement: 85,
      suggestion: 'High dwell, low purchase — Suggest promo',
    },
    snacks: { touchRate: 30, trend: 'up', message: 'Touch rate up 30%' },
    queue: {
      waitTime: 5.2,
      status: 'alert',
      message: 'Queue over 5 mins — Alert triggered',
    },
  });

  const features = [
    {
      icon: Brain,
      title: 'GPT-Powered Suggestions',
      description:
        'AI analyzes patterns and provides actionable recommendations',
    },
    {
      icon: Users,
      title: 'Footfall by Hour',
      description: 'Track customer flow patterns throughout the day',
    },
    {
      icon: MousePointer,
      title: 'Product Interactions',
      description: 'See which products customers touch and engage with',
    },
    {
      icon: Shield,
      title: 'Theft Alerts',
      description: 'Real-time notifications for suspicious activities',
    },
    {
      icon: Timer,
      title: 'Queue Time Monitoring',
      description: 'Optimize checkout flow and reduce wait times',
    },
    {
      icon: TrendingUp,
      title: 'Festival Spike Detection',
      description: 'Identify and prepare for peak traffic periods',
    },
    {
      icon: MapPin,
      title: 'Heatmaps & Zone Dwell Time',
      description: 'Visualize customer movement and popular areas',
    },
    {
      icon: BarChart3,
      title: 'Advanced Analytics',
      description: 'Deep insights into customer behavior patterns',
    },
  ];

  const steps = [
    {
      number: '01',
      title: 'Connect Existing CCTV',
      description:
        'Simply integrate your current camera system with our AI platform',
      icon: Camera,
    },
    {
      number: '02',
      title: 'AI Analyzes Footage',
      description:
        'Our advanced computer vision processes video feeds in real-time',
      icon: Brain,
    },
    {
      number: '03',
      title: 'Insights + Alerts via Dashboard',
      description:
        'Receive actionable insights and real-time alerts on your dashboard',
      icon: BarChart3,
    },
  ];

  const founders = [
    {
      name: 'Aashi Goyal',
      role: 'Founder & CEO',
      description: 'AI & Machine Learning Expert',
      avatar: 'AG',
    },
    {
      name: 'Hershel Goyal',
      role: 'Creative & Product Lead',
      description: 'UX Design & Product Strategy',
      avatar: 'HG',
    },
    {
      name: 'Mrityunjay Gupta',
      role: 'AI & Tech Lead',
      description: 'Computer Vision & Backend Systems',
      avatar: 'MG',
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setDemoData((prev) => ({
        zoneA: {
          ...prev.zoneA,
          visitors: Math.floor(Math.random() * 20) + 10,
          engagement: Math.floor(Math.random() * 30) + 70,
        },
        snacks: {
          ...prev.snacks,
          touchRate: Math.floor(Math.random() * 50) + 20,
        },
        queue: {
          ...prev.queue,
          waitTime: Math.random() * 8 + 2,
        },
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Hero Section */}
      <section
        id="hero"
        className="relative min-h-screen flex items-center justify-center"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Text Content */}
            <div className="text-center lg:text-left">
              <div className="mb-8 flex justify-center lg:justify-start">
                <div className="w-16 h-16 bg-teal-500 rounded-2xl flex items-center justify-center">
                  <Brain className="h-8 w-8 text-white" />
                </div>
              </div>

              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 text-slate-900 tracking-tight">
                Make Your Store Smarter.
              </h1>
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-8 text-slate-900 tracking-tight">
                Just Plug In.
              </h2>

              <p className="text-xl md:text-2xl text-slate-600 mb-12 max-w-3xl mx-auto lg:mx-0 leading-relaxed">
                AI-powered CCTV analytics for real-world retail problems.
                Transform your existing cameras into intelligent business
                insights.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mb-16">
                <Link
                  to="/signup"
                  className="group bg-teal-500 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-teal-600 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl hover:-translate-y-1"
                >
                  Get Started
                  <ChevronRight className="inline-block ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <button className="group border-2 border-gray-300 text-slate-700 px-8 py-4 rounded-xl text-lg font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all flex items-center justify-center space-x-2 hover:scale-105 hover:shadow-lg hover:-translate-y-1">
                  <Play className="h-5 w-5" />
                  <span>See Demo</span>
                </button>
              </div>
            </div>

            {/* Right Column - CCTV Camera Visual */}
            <div className="relative lg:block hidden">
              <div className="relative">
                {/* Main CCTV Image Container */}
                <div className="relative bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl p-8 shadow-2xl">
                  <img
                    src="https://images.pexels.com/photos/264636/pexels-photo-264636.jpeg?auto=compress&cs=tinysrgb&w=800"
                    alt="Security camera monitoring busy retail store with customers shopping"
                    className="w-full h-80 object-cover rounded-2xl shadow-lg"
                  />

                  {/* AI Analysis Overlay */}
                  <div className="absolute top-12 right-12 bg-white/95 backdrop-blur-sm p-4 rounded-xl shadow-lg border border-gray-200 max-w-xs">
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="w-3 h-3 bg-teal-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-semibold text-slate-900">
                        AI Analysis Active
                      </span>
                    </div>
                    <div className="space-y-1 text-xs text-slate-600">
                      <div className="flex justify-between">
                        <span>Customers detected:</span>
                        <span className="font-semibold text-blue-700">12</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Zone activity:</span>
                        <span className="font-semibold text-teal-600">
                          High
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Queue status:</span>
                        <span className="font-semibold text-amber-600">
                          Normal
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Detection Points */}
                  <div className="absolute top-32 left-16 w-4 h-4 bg-blue-700 rounded-full animate-ping"></div>
                  <div className="absolute top-32 left-16 w-4 h-4 bg-blue-700 rounded-full"></div>

                  <div className="absolute bottom-32 right-20 w-4 h-4 bg-teal-500 rounded-full animate-ping"></div>
                  <div className="absolute bottom-32 right-20 w-4 h-4 bg-teal-500 rounded-full"></div>
                </div>

                {/* Floating Analytics Cards */}
                <div className="absolute -bottom-6 -left-6 bg-white p-4 rounded-xl shadow-lg border border-gray-200">
                  <div className="flex items-center space-x-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-teal-600" />
                    <span className="text-sm font-semibold text-slate-900">
                      Footfall Today
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-blue-700">247</div>
                  <div className="text-xs text-teal-600">
                    ↑ 12% vs yesterday
                  </div>
                </div>

                <div className="absolute -top-6 -right-6 bg-white p-4 rounded-xl shadow-lg border border-gray-200">
                  <div className="flex items-center space-x-2 mb-1">
                    <Brain className="h-4 w-4 text-blue-700" />
                    <span className="text-sm font-semibold text-slate-900">
                      AI Insights
                    </span>
                  </div>
                  <div className="text-2xl font-bold text-blue-700">8</div>
                  <div className="text-xs text-blue-700">
                    New recommendations
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section
        id="problems"
        className="py-24 bg-white relative overflow-hidden"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-2xl mb-6">
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">
              The Problems We Solve
            </h2>
            <p className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed">
              Modern retail faces critical challenges that traditional systems
              can't address.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {/* Problem 1 */}
            <div className="group">
              <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-orange-300 transition-all hover:shadow-lg h-full hover:-translate-y-2">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                    <Users className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="text-2xl font-bold text-orange-600">
                    Customer Expectations
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900">
                  Have Fundamentally Changed
                </h3>
                <p className="text-slate-600 mb-4">
                  People expect fast checkout, smooth layouts, and personalized
                  experiences. Delays make them walk out — and they won't come
                  back.
                </p>
                <div className="flex items-center text-orange-600 text-sm font-semibold">
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  <span>
                    73% of customers abandon stores due to poor experience
                  </span>
                </div>
              </div>
            </div>

            {/* Problem 2 */}
            <div className="group">
              <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-amber-300 transition-all hover:shadow-lg h-full hover:-translate-y-2">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                    <Camera className="h-6 w-6 text-amber-600" />
                  </div>
                  <div className="text-2xl font-bold text-amber-600">
                    CCTV is Everywhere
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900">
                  But Massively Underused
                </h3>
                <p className="text-slate-600 mb-4">
                  99% of footage in stores is never analyzed. It just sits idle,
                  while valuable insights about customer behavior go unnoticed.
                </p>
                <div className="flex items-center text-amber-600 text-sm font-semibold">
                  <Eye className="h-4 w-4 mr-2" />
                  <span>$2.3B worth of unused retail data annually</span>
                </div>
              </div>
            </div>

            {/* Problem 3 */}
            <div className="group">
              <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-blue-400 transition-all hover:shadow-lg h-full hover:-translate-y-2">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                    <Brain className="h-6 w-6 text-blue-700" />
                  </div>
                  <div className="text-2xl font-bold text-blue-700">
                    AI is Finally
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900">
                  Affordable & Accessible
                </h3>
                <p className="text-slate-600 mb-4">
                  Tools like YOLOv8, Roboflow, and cloud AI now allow small
                  stores to access big-brand-level tech without expensive new
                  hardware.
                </p>
                <div className="flex items-center text-blue-700 text-sm font-semibold">
                  <Zap className="h-4 w-4 mr-2" />
                  <span>90% cost reduction in AI deployment since 2020</span>
                </div>
              </div>
            </div>

            {/* Problem 4 */}
            <div className="group">
              <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-teal-300 transition-all hover:shadow-lg h-full hover:-translate-y-2">
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center mr-4 group-hover:scale-110 transition-transform">
                    <Target className="h-6 w-6 text-teal-600" />
                  </div>
                  <div className="text-2xl font-bold text-teal-600">
                    Post-COVID Reality
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900">
                  Every Decision Matters
                </h3>
                <p className="text-slate-600 mb-4">
                  Footfall is unpredictable. Layouts and staffing must adapt
                  quickly. Data isn't a luxury anymore — it's survival.
                </p>
                <div className="flex items-center text-teal-600 text-sm font-semibold">
                  <Activity className="h-4 w-4 mr-2" />
                  <span>
                    40% of retailers who don't adapt will close by 2026
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="solution" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">
              Our Solution
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Transform your existing CCTV infrastructure into a powerful retail
              intelligence system
            </p>
          </div>

          {/* Solution Steps */}
          <div className="relative mb-16">
            <div className="grid md:grid-cols-3 gap-8">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className={`relative transition-all duration-1000 ${
                    currentStep === index
                      ? 'scale-105 z-10'
                      : 'scale-95 opacity-70'
                  }`}
                >
                  <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-teal-300 transition-all hover:shadow-lg h-full hover:-translate-y-2">
                    <div className="flex items-center justify-between mb-6">
                      <div className="text-6xl font-bold text-teal-500">
                        {step.number}
                      </div>
                      <step.icon
                        className={`h-12 w-12 ${
                          currentStep === index
                            ? 'text-teal-500'
                            : 'text-gray-400'
                        } transition-colors`}
                      />
                    </div>
                    <h3 className="text-2xl font-bold mb-4 text-slate-900">
                      {step.title}
                    </h3>
                    <p className="text-slate-600 text-lg">{step.description}</p>
                  </div>

                  {index < steps.length - 1 && (
                    <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2 z-20">
                      <ArrowRight className="h-8 w-8 text-teal-500" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">
              Powerful Features
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Everything you need to transform your retail operations with
              AI-powered insights
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="group">
                <div className="bg-white p-6 rounded-2xl border border-gray-200 hover:border-gray-300 transition-all hover:shadow-lg h-full">
                  <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <feature.icon className="h-6 w-6 text-teal-600" />
                  </div>
                  <h3 className="text-lg font-bold mb-3 text-slate-900">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 text-sm">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">
              See It In Action
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Real-time insights from your store, powered by AI
            </p>
          </div>

          <div className="bg-white p-8 rounded-3xl border border-gray-200 shadow-lg">
            <h3 className="text-2xl font-bold mb-8 text-center text-slate-900">
              Live Store Analytics
            </h3>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-teal-300 transition-all group">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-blue-700">
                    Zone A - Electronics
                  </h4>
                  <div className="w-3 h-3 bg-teal-500 rounded-full animate-pulse"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Visitors:</span>
                    <span className="font-bold text-blue-700">
                      {demoData.zoneA.visitors}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Engagement:</span>
                    <span className="font-bold text-teal-600">
                      {demoData.zoneA.engagement}%
                    </span>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <p className="text-sm text-amber-700">
                    💡 {demoData.zoneA.suggestion}
                  </p>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-teal-300 transition-all group">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-teal-600">Snacks Section</h4>
                  <TrendingUp className="w-5 h-5 text-teal-600 group-hover:scale-110 transition-transform" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Touch Rate:</span>
                    <span className="font-bold text-teal-600">
                      ↑{demoData.snacks.touchRate}%
                    </span>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-teal-50 rounded-lg border border-teal-200">
                  <p className="text-sm text-teal-700">
                    📈 {demoData.snacks.message}
                  </p>
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-orange-300 transition-all group">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-orange-600">Checkout Queue</h4>
                  <AlertTriangle className="w-5 h-5 text-orange-600 group-hover:scale-110 transition-transform animate-pulse" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Wait Time:</span>
                    <span className="font-bold text-orange-600">
                      {demoData.queue.waitTime.toFixed(1)} mins
                    </span>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-sm text-orange-700">
                    ⚠️ {demoData.queue.message}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section id="team" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 tracking-tight">
              Meet Our Team
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Passionate innovators dedicated to revolutionizing retail with AI
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {founders.map((founder, index) => (
              <div key={index} className="group text-center">
                <div className="bg-white p-8 rounded-2xl border border-gray-200 hover:border-teal-300 transition-all hover:shadow-lg mb-6 hover:-translate-y-2">
                  <div className="w-24 h-24 bg-teal-100 rounded-full mx-auto flex items-center justify-center text-2xl font-bold text-teal-600 group-hover:scale-110 transition-transform mb-6">
                    {founder.avatar}
                  </div>
                  <h3 className="text-2xl font-bold mb-2 text-slate-900">
                    {founder.name}
                  </h3>
                  <p className="text-teal-600 font-semibold mb-4">
                    {founder.role}
                  </p>
                  <p className="text-slate-600">{founder.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="footer" className="bg-slate-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-2 mb-6">
                <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center">
                  <Brain className="h-5 w-5 text-white" />
                </div>
                <span className="text-2xl font-bold text-white">RetailIQ</span>
              </div>
              <p className="text-gray-400 mb-6 max-w-md">
                Transform your retail operations with AI-powered CCTV analytics.
                Get insights, reduce theft, and boost sales.
              </p>
              <div className="flex space-x-4">
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Twitter className="h-6 w-6" />
                </a>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Linkedin className="h-6 w-6" />
                </a>
                <a
                  href="#"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Github className="h-6 w-6" />
                </a>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h4 className="text-white font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2">
                <li>
                  <Link
                    to="/"
                    className="text-gray-400 hover:text-teal-400 transition-colors"
                  >
                    Home
                  </Link>
                </li>
                <li>
                  <Link
                    to="/signup"
                    className="text-gray-400 hover:text-teal-400 transition-colors"
                  >
                    Get Started
                  </Link>
                </li>
                <li>
                  <Link
                    to="/login"
                    className="text-gray-400 hover:text-teal-400 transition-colors"
                  >
                    Login
                  </Link>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-teal-400 transition-colors"
                  >
                    Pricing
                  </a>
                </li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="text-white font-semibold mb-4">Contact</h4>
              <ul className="space-y-2">
                <li className="flex items-center space-x-2 text-gray-400">
                  <Mail className="h-4 w-4" />
                  <span>hello@retailiq.ai</span>
                </li>
                <li className="flex items-center space-x-2 text-gray-400">
                  <Phone className="h-4 w-4" />
                  <span>+1 (555) 123-4567</span>
                </li>
                <li className="flex items-center space-x-2 text-gray-400">
                  <LocationIcon className="h-4 w-4" />
                  <span>San Francisco, CA</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">
              © 2024 RetailIQ. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a
                href="#"
                className="text-gray-400 hover:text-teal-400 text-sm transition-colors"
              >
                Terms of Service
              </a>
              <a
                href="#"
                className="text-gray-400 hover:text-teal-400 text-sm transition-colors"
              >
                Privacy Policy
              </a>
              <a
                href="#"
                className="text-gray-400 hover:text-teal-400 text-sm transition-colors"
              >
                Cookie Policy
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
