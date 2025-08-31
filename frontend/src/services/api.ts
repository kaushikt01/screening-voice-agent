const API_BASE_URL = 'http://localhost:8000/api';



export interface QuestionResponse {
  id: number;
  question_text: string;
  audio_url: string;
}



export interface DashboardData {
  total_sessions: number;
  total_answers: number;
  recent_sessions: Array<{
    session_id: string;
    created_at: string | null;
    answer_count: number;
  }>;
  question_stats: Array<{
    question: string;
    answer_count: number;
  }>;
  avg_answer_length: number;
}



export interface CallAnalytics {
  question_id: number;
  response_time: number;
  answer_duration: number;
  audio_quality: number;
  confidence: number;
  hesitation: boolean;
  completed: boolean;
  timestamp: Date | string;
}

export interface CallAnalyticsSubmission {
  session_id: string;
  analytics: CallAnalytics[];
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    // Build headers conditionally to avoid triggering CORS preflight on GET
    const headers: HeadersInit = {
      Accept: 'application/json',
      ...(options?.headers || {}),
    };

    // Only set Content-Type for non-FormData bodies
    if (options?.body && !(options.body instanceof FormData)) {
      (headers as any)['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit',
      headers,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    return this.request('/health');
  }

  async getIntroductionAudio(): Promise<{ audio_url: string }> {
    return this.request('/introduction');
  }

  async startSession(): Promise<{ session_id: string; total_questions: number }> {
    return this.request('/start-session', { method: 'POST' });
  }

  async getQuestions(): Promise<{ questions: Array<{ id: number; question: string }> }> {
    return this.request('/questions');
  }

  async getNextQuestion(index: number, sessionId: string): Promise<QuestionResponse> {
    return this.request(`/next-question?index=${index}&session_id=${sessionId}`);
  }

  async submitAnswer(sessionId: string, questionId: number, audioFile: File): Promise<{
    success: boolean;
    answer_text: string;
    question_id: number;
  }> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('question_id', questionId.toString());
    formData.append('audio_file', audioFile);

    const response = await fetch(`${API_BASE_URL}/submit-answer`, {
      method: 'POST',
      body: formData,
      mode: 'cors',
      credentials: 'omit',
    });

    if (!response.ok) {
      throw new Error(`Submit answer failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }



  async getDashboardData(): Promise<DashboardData> {
    return this.request('/dashboard');
  }



  async saveCallAnalytics(sessionId: string, analytics: CallAnalytics[]): Promise<{ success: boolean; message: string }> {
    const submission: CallAnalyticsSubmission = {
      session_id: sessionId,
      analytics: analytics.map(a => ({
        ...a,
        timestamp: typeof a.timestamp === 'string' ? a.timestamp : a.timestamp.toISOString()
      }))
    };
    
    return this.request('/save-call-analytics', {
      method: 'POST',
      body: JSON.stringify(submission),
    });
  }
}

export const apiService = new ApiService();
