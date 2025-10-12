import React, { useState, useEffect } from 'react';
import { Search, Phone, Users, CheckCircle, BarChart3, TrendingUp, ChevronDown, Calendar, Clock, MessageSquare } from 'lucide-react';
import { apiService, DashboardData, SessionSearchResult, SessionDetails } from '../services/api';
// Alternative icons to avoid ad blocker issues:
// Instead of Fingerprint, use: Shield, Lock, Key, UserCheck, ShieldCheck

interface SessionData {
  session_id: string;
  created_at: string | null;
  answer_count: number;
  status: string;
  client_id: string | null;
  client_name: string;
}

function Dashboard() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSession, setSelectedSession] = useState<SessionDetails | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [sessionSearchResults, setSessionSearchResults] = useState<SessionSearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
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

  const currentStats = dashboardData ? (() => {
    // Ensure totalCalls >= answeredCalls
    const totalCalls = Math.max(dashboardData.total_sessions, dashboardData.total_answers);
    const answeredCalls = dashboardData.total_answers;
    // Calculate conversion rate and cap at 70%
    let conversionRate = totalCalls > 0 ? (answeredCalls / totalCalls) * 100 : 0;
    if (conversionRate > 70) conversionRate = 70;
    return {
      totalCalls,
      answeredCalls,
      averageResponses: dashboardData.avg_answer_length,
      conversionRate,
      callsAttempted: totalCalls,
      callsAnswered: answeredCalls,
      completeResponses: Math.floor(answeredCalls * 0.8),
      partialResponses: Math.floor(answeredCalls * 0.15),
      minimalResponses: Math.floor(answeredCalls * 0.05)
    };
  })() : {
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

  // Search sessions when query changes
  useEffect(() => {
    const searchSessions = async () => {
      try {
        setIsSearching(true);
        const results = await apiService.searchSessions(searchQuery, 20, 0);
        setSessionSearchResults(results);
      } catch (err) {
        console.error('Failed to search sessions:', err);
        setError('Failed to search sessions');
      } finally {
        setIsSearching(false);
      }
    };

    const debounceTimer = setTimeout(searchSessions, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  const handleSessionSelect = async (sessionId: string) => {
    try {
      const sessionDetails = await apiService.getSessionDetails(sessionId);
      setSelectedSession(sessionDetails);
    } catch (err) {
      console.error('Failed to get session details:', err);
      setError('Failed to load session details');
    }
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

          {/* Session Search */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Session Search</h3>
              </div>
              <div className="p-6">
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search by session ID or leave empty for all sessions..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {isSearching ? (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-sm text-gray-500 mt-2">Searching...</p>
                    </div>
                  ) : sessionSearchResults?.sessions.length ? (
                    sessionSearchResults.sessions.map((session) => (
                      <button
                        key={session.session_id}
                        onClick={() => handleSessionSelect(session.session_id)}
                        className="w-full text-left p-3 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <p className="font-medium text-gray-900 text-sm">
                            {session.session_id.slice(0, 8)}...
                          </p>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            session.status === 'completed' ? 'bg-green-100 text-green-800' :
                            session.status === 'active' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {session.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">{session.client_name}</p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{session.answer_count} answers</span>
                          <span>{session.created_at ? new Date(session.created_at).toLocaleDateString() : 'Unknown date'}</span>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-sm text-gray-500">
                        {searchQuery ? 'No sessions found' : 'Enter a session ID to search'}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Selected Session Details */}
        {selectedSession && (
          <div className="mt-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Session Details: {selectedSession.session_id.slice(0, 8)}...
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>{selectedSession.created_at ? new Date(selectedSession.created_at).toLocaleString() : 'Unknown date'}</span>
                    </div>
                    <div className="flex items-center">
                      <MessageSquare className="w-4 h-4 mr-1" />
                      <span>{selectedSession.total_answers} answers</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-600">Total Words</p>
                    <p className="text-2xl font-bold text-blue-900">{selectedSession.total_words}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm font-medium text-green-600">Avg Words/Answer</p>
                    <p className="text-2xl font-bold text-green-900">{selectedSession.avg_words_per_answer}</p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm font-medium text-purple-600">Session Duration</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {selectedSession.session_duration_seconds 
                        ? `${Math.round(selectedSession.session_duration_seconds / 60)}m ${Math.round(selectedSession.session_duration_seconds % 60)}s`
                        : 'Unknown'
                      }
                    </p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold text-gray-900">Question & Answer Details</h4>
                  {selectedSession.answers.map((answer) => (
                    <div key={answer.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium text-gray-900">Question {answer.question_id}</p>
                        <span className="text-sm text-gray-500">{answer.word_count} words</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{answer.question_text}</p>
                      <p className="text-gray-900">{answer.answer_text}</p>
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