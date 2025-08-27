import React, { useState, useEffect } from 'react';
import { BarChart3, Clock, Mic, TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { apiService, SessionAnalytics } from '../services/api';

interface AnalyticsData {
  totalCalls: number;
  averageResponseTime: number;
  averageAnswerDuration: number;
  hesitationRate: number;
  completionRate: number;
  questionDifficulty: Array<{
    question: string;
    difficulty: number; // 0-100, higher = harder
    dropOffRate: number;
  }>;
}

function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setIsLoading(true);
      // For now, we'll use mock data since the analytics endpoint needs to be enhanced
      const mockAnalytics: AnalyticsData = {
        totalCalls: 47,
        averageResponseTime: 2800, // milliseconds
        averageAnswerDuration: 4500, // milliseconds
        hesitationRate: 23.4, // percentage
        completionRate: 78.9, // percentage
        questionDifficulty: [
          { question: "What is your company size?", difficulty: 15, dropOffRate: 5.2 },
          { question: "What industry are you in?", difficulty: 12, dropOffRate: 3.1 },
          { question: "What is your annual revenue?", difficulty: 45, dropOffRate: 12.8 },
          { question: "Do you currently use CRM software?", difficulty: 25, dropOffRate: 8.4 },
          { question: "What are your main pain points?", difficulty: 65, dropOffRate: 18.2 },
          { question: "What is your budget range?", difficulty: 55, dropOffRate: 15.6 },
          { question: "When are you looking to implement?", difficulty: 35, dropOffRate: 10.3 },
          { question: "Who makes the purchasing decisions?", difficulty: 75, dropOffRate: 22.1 },
          { question: "Have you evaluated other solutions?", difficulty: 40, dropOffRate: 11.7 },
          { question: "What features are most important?", difficulty: 30, dropOffRate: 9.8 }
        ]
      };
      
      setAnalytics(mockAnalytics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    return `${seconds}s`;
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty < 30) return 'text-green-600';
    if (difficulty < 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty < 30) return 'Easy';
    if (difficulty < 60) return 'Medium';
    return 'Hard';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
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
            onClick={loadAnalytics}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Call Analytics Dashboard</h1>
              <p className="text-gray-600">Voice call performance and user behavior insights</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.totalCalls.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-5 h-5 text-green-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                <p className="text-2xl font-bold text-gray-900">{formatTime(analytics.averageResponseTime)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Mic className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Answer Duration</p>
                <p className="text-2xl font-bold text-gray-900">{formatTime(analytics.averageAnswerDuration)}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.completionRate}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Question Difficulty Analysis */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Question Difficulty Analysis</h3>
            <p className="text-sm text-gray-600">Track which questions are easy or hard for users to answer</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {analytics.questionDifficulty.map((question, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-1">{question.question}</p>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className={`font-medium ${getDifficultyColor(question.difficulty)}`}>
                        {getDifficultyLabel(question.difficulty)} ({question.difficulty}/100)
                      </span>
                      <span className="text-gray-500">Drop-off: {question.dropOffRate}%</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {question.difficulty < 30 && <CheckCircle className="w-5 h-5 text-green-500" />}
                    {question.difficulty >= 30 && question.difficulty < 60 && <AlertTriangle className="w-5 h-5 text-yellow-500" />}
                    {question.difficulty >= 60 && <XCircle className="w-5 h-5 text-red-500" />}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Hesitation Analysis */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">User Behavior Insights</h3>
            <p className="text-sm text-gray-600">Understanding user hesitation and engagement patterns</p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-2">Hesitation Rate</h4>
                <p className="text-3xl font-bold text-blue-600">{analytics.hesitationRate}%</p>
                <p className="text-sm text-blue-700 mt-1">
                  Users hesitate before answering {analytics.hesitationRate}% of questions
                </p>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-semibold text-green-900 mb-2">Completion Rate</h4>
                <p className="text-3xl font-bold text-green-600">{analytics.completionRate}%</p>
                <p className="text-sm text-green-700 mt-1">
                  {analytics.completionRate}% of users complete all questions
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
            <p className="text-sm text-gray-600">Based on analytics data</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">High Drop-off Questions</p>
                  <p className="text-sm text-gray-600">
                    Questions about "purchasing decisions" and "pain points" have the highest drop-off rates. 
                    Consider simplifying these questions or providing more context.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">Response Time Optimization</p>
                  <p className="text-sm text-gray-600">
                    Average response time is {formatTime(analytics.averageResponseTime)}. 
                    Consider adding brief pauses between questions to give users time to think.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">Easy Questions</p>
                  <p className="text-sm text-gray-600">
                    Questions about company size and industry are easiest for users. 
                    Consider using these as warm-up questions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
