import React, { useState, useEffect } from 'react';
import { Search, Phone, Users, CheckCircle, BarChart3, TrendingUp, ChevronDown, Calendar, Shield, Lock } from 'lucide-react';
import { apiService, DashboardData } from '../services/api';
// Alternative icons to avoid ad blocker issues:
// Instead of Fingerprint, use: Shield, Lock, Key, UserCheck, ShieldCheck

interface ClientData {
  id: string;
  name: string;
  callDate: string;
  responses: Record<string, string>;
}

function Dashboard() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClient, setSelectedClient] = useState<ClientData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        const data = await apiService.getDashboardData();
        setDashboardData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const currentStats = dashboardData ? {
    totalCalls: dashboardData.total_sessions,
    answeredCalls: dashboardData.total_answers,
    averageResponses: dashboardData.avg_answer_length,
    conversionRate: dashboardData.total_sessions > 0 ? (dashboardData.total_answers / dashboardData.total_sessions) * 100 : 0,
    callsAttempted: dashboardData.total_sessions,
    callsAnswered: dashboardData.total_answers,
    completeResponses: Math.floor(dashboardData.total_answers * 0.8),
    partialResponses: Math.floor(dashboardData.total_answers * 0.15),
    minimalResponses: Math.floor(dashboardData.total_answers * 0.05)
  } : {
    totalCalls: 0,
    answeredCalls: 0,
    averageResponses: 0,
    conversionRate: 0,
    callsAttempted: 0,
    callsAnswered: 0,
    completeResponses: 0,
    partialResponses: 0,
    minimalResponses: 0
  };

  const periodLabels = {
    today: 'Today',
    weekly: 'This Week',
    monthly: 'This Month'
  };

  // Mock client data for now - in a real app this would come from the API
  const mockClientData: ClientData[] = [
    {
      id: 'CL001',
      name: 'TechCorp Solutions',
      callDate: '2025-01-15',
      responses: {
        'What is your company size?': '50-100 employees',
        'What industry are you in?': 'Technology',
        'What is your annual revenue?': '$5M-$10M',
        'Do you currently use CRM software?': 'Yes, Salesforce',
        'What are your main pain points?': 'Integration issues',
        'What is your budget range?': '$10,000-$25,000',
        'When are you looking to implement?': 'Within 3 months',
        'Who makes the purchasing decisions?': 'CTO and VP Sales',
        'Have you evaluated other solutions?': 'Yes, HubSpot and Pipedrive',
        'What features are most important?': 'Automation and analytics'
      }
    },
    {
      id: 'CL002',
      name: 'Healthcare Plus',
      callDate: '2025-01-13',
      responses: {
        'What is your company size?': '100+ employees',
        'What industry are you in?': 'Healthcare',
        'What is your annual revenue?': '$10M+',
        'Do you currently use CRM software?': 'Yes, custom solution',
        'What are your main pain points?': 'System integration and compliance',
        'What is your budget range?': '$25,000+',
        'When are you looking to implement?': 'Within 1 month',
        'Who makes the purchasing decisions?': 'CTO and Compliance Officer',
        'Have you evaluated other solutions?': 'Yes, several enterprise solutions',
        'What features are most important?': 'HIPAA compliance and security'
      }
    }
  ];

  const filteredClients = mockClientData.filter(client => 
    client.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    client.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleClientSelect = (client: ClientData) => {
    setSelectedClient(client);
  };

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
    setIsDropdownOpen(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Call Analysis Dashboard</h1>
              <p className="text-gray-600">Monitor and analyze your automated call performance</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center space-x-2 bg-white border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <Calendar className="w-4 h-4" />
                  <span>{periodLabels[selectedPeriod as keyof typeof periodLabels]}</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
                
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                    <div className="py-1">
                      {Object.entries(periodLabels).map(([key, label]) => (
                        <button
                          key={key}
                          onClick={() => handlePeriodChange(key)}
                          className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Phone className="w-5 h-5 text-blue-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900">{currentStats.totalCalls.toLocaleString()}</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                <span className="text-green-600 font-medium">+12.5%</span>
                <span className="text-gray-500 ml-1">from last period</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Answered Calls</p>
                <p className="text-2xl font-bold text-gray-900">{currentStats.answeredCalls.toLocaleString()}</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                <span className="text-green-600 font-medium">+8.2%</span>
                <span className="text-gray-500 ml-1">from last period</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg. Responses</p>
                <p className="text-2xl font-bold text-gray-900">{currentStats.averageResponses.toFixed(1)}</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                <span className="text-green-600 font-medium">+5.3%</span>
                <span className="text-gray-500 ml-1">from last period</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-orange-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{currentStats.conversionRate.toFixed(1)}%</p>
              </div>
            </div>
            <div className="mt-4">
              <div className="flex items-center text-sm">
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                <span className="text-green-600 font-medium">+2.1%</span>
                <span className="text-gray-500 ml-1">from last period</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Calls */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Recent Calls</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {dashboardData?.recent_sessions.slice(0, 5).map((session) => (
                    <div key={session.session_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Phone className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Session {session.session_id.slice(0, 8)}...</p>
                          <p className="text-sm text-gray-500">
                            {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'Unknown date'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{session.answer_count} responses</p>
                        <p className="text-sm text-gray-500">Completed</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Client Search */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Client Search</h3>
              </div>
              <div className="p-6">
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search clients..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {filteredClients.map((client) => (
                    <button
                      key={client.id}
                      onClick={() => handleClientSelect(client)}
                      className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <p className="font-medium text-gray-900">{client.name}</p>
                      <p className="text-sm text-gray-500">{client.callDate}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Selected Client Details */}
        {selectedClient && (
          <div className="mt-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Client Details: {selectedClient.name}</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(selectedClient.responses).map(([question, answer]) => (
                    <div key={question} className="p-4 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-900 mb-2">{question}</p>
                      <p className="text-gray-600">{answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;