import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Phone, PhoneOff, Mic, MicOff, Volume2, VolumeX, Circle, Loader2 } from 'lucide-react';
import { apiService, QuestionResponse } from '../services/api';

// Mock TTS function for fallback messages (in a real app, this would call the backend TTS API)
const generate_conversational_voice = (text: string, filename: string, style: string): string => {
  // For now, return a placeholder - in a real implementation, this would call the backend TTS API
  console.log(`[DEBUG] Would generate TTS for: "${text}" with filename: ${filename}, style: ${style}`);
  return `/static/audio/${filename}`;
};

const mockClientInfo = {
  name: "Sarah Johnson",
  company: "ADP",
  phone: "+1 (555) 123-4567",
  avatar: "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=150&h=150&fit=crop"
};

interface CallAnalytics {
  question_id: number;
  response_time: number; // Time from question start to answer start
  answer_duration: number; // Duration of voice recording
  audio_quality: number; // Audio clarity score (0-100)
  confidence: number; // Confidence score from speech recognition
  hesitation: boolean; // Whether user hesitated before answering
  completed: boolean; // Whether question was completed
  timestamp: Date;
}

function CallInterface() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [callStatus, setCallStatus] = useState<'idle' | 'calling' | 'connected' | 'agent-speaking' | 'listening' | 'processing' | 'ended'>('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerOn] = useState(true);
  const [callDuration, setCallDuration] = useState(0);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [sessionId, setSessionId] = useState<string | null>(() => {
    // Initialize from localStorage immediately to prevent null values
    const saved = localStorage.getItem('callSessionId');
    console.log('[DEBUG] Initializing sessionId from localStorage:', saved);
    return saved || null;
  });
  
  // Add a ref to track the current sessionId to avoid stale closures
  const sessionIdRef = useRef<string | null>(sessionId);
  
  // Update ref whenever sessionId changes
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);
  const [questions, setQuestions] = useState<QuestionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<CallAnalytics[]>([]);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState<Date | null>(null);
  const [recordingStartTime, setRecordingStartTime] = useState<Date | null>(null);
  const [isConversationStarted, setIsConversationStarted] = useState(false);
  const [autoAdvanceTimer, setAutoAdvanceTimer] = useState<number | null>(null);
  const [totalQuestions, setTotalQuestions] = useState<number>(0);
  const [isSilenceDetected, setIsSilenceDetected] = useState(false);
  const [fallbackMessage, setFallbackMessage] = useState<string | null>(null);
  
  // Add refs to track current state values to avoid stale closures
  const totalQuestionsRef = useRef<number>(totalQuestions);
  const questionsRef = useRef<QuestionResponse[]>(questions);
  
  // Update refs whenever state changes
  useEffect(() => {
    totalQuestionsRef.current = totalQuestions;
  }, [totalQuestions]);
  
  useEffect(() => {
    questionsRef.current = questions;
  }, [questions]);

  // Refs for voice recording
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Audio analysis for auto-stop on silence
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceIntervalRef = useRef<number | null>(null);
  const speakingRef = useRef<boolean>(false);
  const silenceStartRef = useRef<number | null>(null);
  
  // Ref to track current question (always up-to-date)
  const currentQuestionRef = useRef<number>(0);
  
  // Ref to track answered questions to prevent duplicates
  const answeredQuestionsRef = useRef<Set<number>>(new Set());
  
  // Flag to prevent multiple simultaneous nextQuestion calls
  const isProcessingNextQuestionRef = useRef<boolean>(false);

  // Recording guardrails
  const NO_SPEECH_TIMEOUT_MS = 6000; // if user doesn't speak at all
  const MAX_LISTEN_DURATION_MS = 20000; // hard cap per question
  const ANSWER_WINDOW_MS = 7000; // static 7s answer window for testing
  const answerWindowTimeoutRef = useRef<number | null>(null);

  // Sync audio mute/volume with UI state
  useEffect(() => {
    if (currentAudio) {
      const shouldMute = isMuted || !isSpeakerOn;
      currentAudio.muted = shouldMute;
      currentAudio.volume = shouldMute ? 0 : 1;
    }
  }, [isMuted, isSpeakerOn, currentAudio]);

  // Track state changes for debugging
  useEffect(() => {
    console.log(`[DEBUG] State changed - sessionId: ${sessionId}, totalQuestions: ${totalQuestions}, questions.length: ${questions.length}, currentQuestion: ${currentQuestion}`);
    
    // Update the ref whenever currentQuestion changes
    currentQuestionRef.current = currentQuestion;
    
    // Persist critical state to localStorage
    if (sessionId) {
      localStorage.setItem('callSessionId', sessionId);
      console.log(`[DEBUG] Saved sessionId to localStorage: ${sessionId}`);
    }
    if (totalQuestions > 0) {
      localStorage.setItem('callTotalQuestions', totalQuestions.toString());
    }
    if (questions.length > 0) {
      localStorage.setItem('callQuestions', JSON.stringify(questions));
    }
    // Save current question progress
    localStorage.setItem('callCurrentQuestion', currentQuestion.toString());
  }, [sessionId, totalQuestions, questions.length, currentQuestion]);

  // State restoration flag to prevent race conditions
  const [isStateRestoring, setIsStateRestoring] = useState(false);
  
  // Function to validate and refresh session if needed
  const validateSession = async (): Promise<boolean> => {
    if (!sessionId) {
      console.log('[DEBUG] No session ID found, starting new session');
      try {
        const session = await apiService.startSession();
        setSessionId(session.session_id);
        setTotalQuestions(session.total_questions);
        localStorage.setItem('callSessionId', session.session_id);
        localStorage.setItem('callTotalQuestions', session.total_questions.toString());
        return true;
      } catch (err) {
        console.error('[ERROR] Failed to start new session:', err);
        setError('Failed to start session. Please refresh the page.');
        return false;
      }
    }
    return true;
  };
  
  // Function to ensure session is properly initialized
  const ensureSessionInitialized = async (): Promise<boolean> => {
    console.log('[DEBUG] Ensuring session is initialized...');
    
    // Check if we have all required state
    const currentSessionId = sessionIdRef.current;
    const currentTotalQuestions = totalQuestionsRef.current;
    const currentQuestions = questionsRef.current;
    
    if (currentSessionId && currentTotalQuestions > 0 && currentQuestions.length > 0) {
      console.log('[DEBUG] Session already initialized');
      return true;
    }
    
    // Try to restore from localStorage first
    const savedSessionId = localStorage.getItem('callSessionId');
    const savedTotalQuestions = localStorage.getItem('callTotalQuestions');
    const savedQuestions = localStorage.getItem('callQuestions');
    
    if (savedSessionId && savedTotalQuestions && savedQuestions) {
      console.log('[DEBUG] Restoring session from localStorage...');
      try {
        const parsedQuestions = JSON.parse(savedQuestions);
        const parsedTotalQuestions = parseInt(savedTotalQuestions);
        
        setSessionId(savedSessionId);
        setTotalQuestions(parsedTotalQuestions);
        setQuestions(parsedQuestions);
        
        // Wait a bit for state to update
        await new Promise(resolve => setTimeout(resolve, 100));
        
        console.log('[DEBUG] Session restored from localStorage');
        return true;
      } catch (err) {
        console.error('[ERROR] Failed to restore session from localStorage:', err);
      }
    }
    
    // If restoration failed, start a new session
    console.log('[DEBUG] Starting new session...');
    try {
      const session = await apiService.startSession();
      setSessionId(session.session_id);
      setTotalQuestions(session.total_questions);
      
      // Load questions
      const questionsData = await apiService.getQuestions();
      const questionPromises = questionsData.questions.map((_, index) => 
        apiService.getNextQuestion(index, session.session_id)
      );
      const loadedQuestions = await Promise.all(questionPromises);
      setQuestions(loadedQuestions);
      
      // Save to localStorage
      localStorage.setItem('callSessionId', session.session_id);
      localStorage.setItem('callTotalQuestions', session.total_questions.toString());
      localStorage.setItem('callQuestions', JSON.stringify(loadedQuestions));
      
      console.log('[DEBUG] New session started successfully');
      return true;
    } catch (err) {
      console.error('[ERROR] Failed to start new session:', err);
      setError('Failed to initialize session. Please refresh the page.');
      return false;
    }
  };

  // Restore state from localStorage on component mount
  useEffect(() => {
    console.log('[DEBUG] Component mount - restoring state from localStorage');
    const savedSessionId = localStorage.getItem('callSessionId');
    const savedTotalQuestions = localStorage.getItem('callTotalQuestions');
    const savedQuestions = localStorage.getItem('callQuestions');
    const savedCurrentQuestion = localStorage.getItem('callCurrentQuestion');
    
    console.log('[DEBUG] Saved state found:', {
      sessionId: savedSessionId ? 'exists' : 'missing',
      totalQuestions: savedTotalQuestions,
      questions: savedQuestions ? 'exists' : 'missing',
      currentQuestion: savedCurrentQuestion
    });
    
    if (savedSessionId && !sessionId) {
      console.log('[DEBUG] Restoring session ID from localStorage:', savedSessionId);
      setSessionId(savedSessionId);
    }
    
    if (savedTotalQuestions && totalQuestions === 0) {
      console.log('[DEBUG] Restoring total questions from localStorage:', savedTotalQuestions);
      setTotalQuestions(parseInt(savedTotalQuestions));
    }
    
    if (savedQuestions && questions.length === 0) {
      console.log('[DEBUG] Restoring questions from localStorage:', savedQuestions);
      try {
        const parsedQuestions = JSON.parse(savedQuestions);
        setQuestions(parsedQuestions);
      } catch (err) {
        console.error('[ERROR] Failed to parse saved questions:', err);
      }
    }
    
    // Validate session ID exists in localStorage
    if (!savedSessionId && sessionId) {
      console.log('[DEBUG] Session ID exists in state but not in localStorage, saving it');
      localStorage.setItem('callSessionId', sessionId);
    }
    
    if (savedCurrentQuestion && currentQuestion === 0) {
      console.log('[DEBUG] Restoring current question from localStorage:', savedCurrentQuestion);
      const questionIndex = parseInt(savedCurrentQuestion);
      setCurrentQuestion(questionIndex);
      currentQuestionRef.current = questionIndex;
    }
    
    // Validate session on mount
    if (savedSessionId) {
      console.log('[DEBUG] Validating existing session on mount');
      validateSession().then(isValid => {
        if (!isValid) {
          console.log('[DEBUG] Session validation failed on mount, clearing localStorage');
          localStorage.removeItem('callSessionId');
          localStorage.removeItem('callTotalQuestions');
          localStorage.removeItem('callQuestions');
          localStorage.removeItem('callCurrentQuestion');
        }
      });
    }
  }, []); // Only run on mount

  // Additional state restoration after initial values are set
  useEffect(() => {
    if (sessionId && totalQuestions > 0 && questions.length > 0) {
      const savedCurrentQuestion = localStorage.getItem('callCurrentQuestion');
      if (savedCurrentQuestion && currentQuestion === 0) {
        const questionIndex = parseInt(savedCurrentQuestion);
        if (questionIndex < totalQuestions) {
          console.log(`[DEBUG] Restoring current question to ${questionIndex} after state initialization`);
          setCurrentQuestion(questionIndex);
          currentQuestionRef.current = questionIndex;
        }
      }
    }
  }, [sessionId, totalQuestions, questions.length]);

  // Prevent state restoration from interfering with active question flow
  useEffect(() => {
    // Only restore state if we're not actively in a question flow
    if (callStatus === 'idle' || callStatus === 'calling') {
      const savedCurrentQuestion = localStorage.getItem('callCurrentQuestion');
      if (savedCurrentQuestion && currentQuestion === 0) {
        const questionIndex = parseInt(savedCurrentQuestion);
        if (questionIndex < totalQuestions) {
          console.log(`[DEBUG] Restoring current question to ${questionIndex} during idle state`);
          setCurrentQuestion(questionIndex);
          currentQuestionRef.current = questionIndex;
        }
      }
    }
  }, [callStatus, totalQuestions, currentQuestion]);

  // Monitor state restoration and retry recording if needed
  useEffect(() => {
    // If we just restored state and we're supposed to be recording, retry
    if (sessionId && totalQuestions > 0 && questions.length > 0 && callStatus === 'connected') {
      console.log('[DEBUG] State restored, checking if we should retry recording...');
      // Check if we were in the middle of a question
      if (currentQuestion < totalQuestions) {
        console.log('[DEBUG] State restored during question flow, continuing...');
        // We're good to continue
      }
    }
  }, [sessionId, totalQuestions, questions.length, callStatus]);

  // Reset state restoration flag when all state is properly loaded
  useEffect(() => {
    if (sessionId && totalQuestions > 0 && questions.length > 0 && isStateRestoring) {
      console.log('[DEBUG] All state restored, resetting restoration flag');
      setIsStateRestoring(false);
    }
  }, [sessionId, totalQuestions, questions.length, isStateRestoring]);

  // Debug currentQuestion changes
  useEffect(() => {
    console.log(`[DEBUG] currentQuestion changed to: ${currentQuestion}`);
    console.log(`[DEBUG] currentQuestionRef.current is now: ${currentQuestionRef.current}`);
    
    // Log the call stack to see what triggered this change
    console.trace(`[DEBUG] currentQuestion state change triggered by:`);
  }, [currentQuestion]);

  // Cleanup state restoration flag on unmount
  useEffect(() => {
    return () => {
      setIsStateRestoring(false);
    };
  }, []);

  // Validate state consistency and reset if needed
  const validateAndResetState = () => {
    console.log(`[DEBUG] Validating state consistency...`);
    console.log(`[DEBUG] Current state: currentQuestion=${currentQuestion}, ref=${currentQuestionRef.current}, totalQuestions=${totalQuestions}, questions.length=${questions.length}`);
    
    // TEMPORARILY DISABLED TO PREVENT INFINITE LOOPS
    // This function was causing infinite loops and has been disabled
    console.log(`[DEBUG] Validation temporarily disabled to prevent infinite loops`);
    return false;
    
    // Use ref as source of truth for validation
    const currentQuestionValue = currentQuestionRef.current;
    
    // Check for state inconsistencies
    if (currentQuestionValue >= totalQuestions && totalQuestions > 0) {
      console.log(`[DEBUG] State inconsistency detected: currentQuestion (${currentQuestionValue}) >= totalQuestions (${totalQuestions})`);
      console.log(`[DEBUG] Resetting currentQuestion to 0`);
      setCurrentQuestion(0);
      currentQuestionRef.current = 0;
      return true;
    }
    
    if (currentQuestionValue < 0) {
      console.log(`[DEBUG] State inconsistency detected: currentQuestion (${currentQuestionValue}) < 0`);
      console.log(`[DEBUG] Resetting currentQuestion to 0`);
      setCurrentQuestion(0);
      currentQuestionRef.current = 0;
      return true;
    }
    
    // Check if state and ref are out of sync - but don't retry if we're already in the process of syncing
    if (currentQuestion !== currentQuestionValue) {
      console.log(`[DEBUG] State/Ref mismatch detected: state=${currentQuestion}, ref=${currentQuestionValue}`);
      console.log(`[DEBUG] Syncing state to ref value`);
      setCurrentQuestion(currentQuestionValue);
      // Don't return true here to avoid infinite retry loop
      return false;
    }
    
    return false;
  };

  // Timer for call duration
  useEffect(() => {
    let interval: number;
    if (callStatus === 'connected' || callStatus === 'agent-speaking' || callStatus === 'listening' || callStatus === 'processing') {
      interval = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [callStatus]);

  // Auto-advance timer for natural conversation flow
  useEffect(() => {
    // Disabled: We'll advance based on silence detection after user stops speaking
    if (autoAdvanceTimer) {
      clearTimeout(autoAdvanceTimer);
      setAutoAdvanceTimer(null);
    }
    return () => {
      if (autoAdvanceTimer) {
        clearTimeout(autoAdvanceTimer);
      }
    };
  }, [isConversationStarted, callStatus, isRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Start voice recording
  const startRecording = async () => {
    console.log('[DEBUG] startRecording called');
    
    // Prevent multiple simultaneous recording attempts
    if (isRecording) {
      console.log(`[DEBUG] Already recording, skipping duplicate startRecording call`);
      return;
    }
    
    // Prevent race conditions during state restoration
    if (isStateRestoring) {
      console.log('[DEBUG] State restoration in progress, skipping startRecording call');
      return;
    }
    
    // Ensure session is properly initialized before recording
    const sessionInitialized = await ensureSessionInitialized();
    if (!sessionInitialized) {
      console.error('[ERROR] Failed to initialize session, cannot start recording');
      return;
    }
    
    // Get current state from refs
    const currentSessionId = sessionIdRef.current;
    const currentTotalQuestions = totalQuestionsRef.current;
    const currentQuestions = questionsRef.current;
    
    if (!currentSessionId || currentTotalQuestions === 0 || currentQuestions.length === 0) {
      console.error(`[ERROR] Session initialization failed - missing state: sessionId=${currentSessionId}, totalQuestions=${currentTotalQuestions}, questions.length=${currentQuestions.length}`);
      return;
    }
    
    // Proceed with recording
    console.log('[DEBUG] Starting recording with initialized session');
    startRecordingWithState(currentSessionId, currentTotalQuestions, currentQuestions);
  };

  // Helper function to start recording with explicit state values
  const startRecordingWithState = async (sessionId: string, totalQuestions: number, questions: QuestionResponse[]) => {
    console.log(`[DEBUG] startRecordingWithState called with sessionId: ${sessionId}, totalQuestions: ${totalQuestions}, questions.length: ${questions.length}`);
    
    // Final validation
    if (!sessionId || totalQuestions === 0 || questions.length === 0) {
      console.error(`[ERROR] startRecordingWithState validation failed: sessionId=${sessionId}, totalQuestions=${totalQuestions}, questions.length=${questions.length}`);
      return;
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      // Setup WebAudio context and analyser
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const audioContext = audioContextRef.current;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyserRef.current = analyser;
      source.connect(analyser);

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        console.log('[DEBUG] MediaRecorder onstop event fired');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processVoiceResponse(audioBlob);
      };

      // Add a fallback in case onstop doesn't fire
      mediaRecorder.onerror = (event) => {
        console.error('[ERROR] MediaRecorder error:', event);
        // Process whatever audio we have and advance
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          processVoiceResponse(audioBlob);
        } else {
          setTimeout(() => {
            nextQuestion();
          }, 1000);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingStartTime(new Date());
      setCallStatus('listening');

      // Clear auto-advance timer when user starts speaking
      if (autoAdvanceTimer) {
        clearTimeout(autoAdvanceTimer);
        setAutoAdvanceTimer(null);
      }

      // Start silence detection
      startSilenceDetection();
      
      // Set a maximum recording time as fallback
      if (answerWindowTimeoutRef.current) {
        clearTimeout(answerWindowTimeoutRef.current);
      }
      answerWindowTimeoutRef.current = window.setTimeout(() => {
        console.log('[DEBUG] Maximum recording time reached, stopping recording');
        stopRecording();
      }, MAX_LISTEN_DURATION_MS);

      // Safety timeout: ensure next question comes even if all else fails
      setTimeout(() => {
        if (isRecording) {
          console.log('[DEBUG] Safety timeout: forcing next question');
          stopRecording();
          setTimeout(() => {
            nextQuestion();
          }, 1000);
        }
      }, MAX_LISTEN_DURATION_MS + 5000); // 5 seconds after max recording time
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to access microphone');
    }
  };

  // Start silence detection
  const startSilenceDetection = () => {
    if (silenceIntervalRef.current) {
      clearInterval(silenceIntervalRef.current);
    }

    silenceIntervalRef.current = window.setInterval(() => {
      if (!analyserRef.current || !isRecording) return;

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      // Calculate average volume
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      const threshold = 10; // Adjust this threshold as needed
      
      if (average < threshold) {
        // Silence detected
        if (!silenceStartRef.current) {
          silenceStartRef.current = Date.now();
          setIsSilenceDetected(true);
        } else if (Date.now() - silenceStartRef.current > 2000) { // 2 seconds of silence
          console.log('[DEBUG] 2 seconds of silence detected, stopping recording');
          stopRecording();
        }
      } else {
        // Sound detected, reset silence timer
        silenceStartRef.current = null;
        setIsSilenceDetected(false);
      }
    }, 100); // Check every 100ms
  };

  // Stop voice recording
  const stopRecording = () => {
    console.log('[DEBUG] stopRecording called');
    
    if (mediaRecorderRef.current && isRecording) {
      console.log('[DEBUG] Stopping media recorder');
      
      // Check if media recorder is actually recording
      if (mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      } else {
        console.log('[DEBUG] Media recorder not in recording state, processing chunks directly');
        // If media recorder isn't recording, process the chunks directly
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          processVoiceResponse(audioBlob);
        } else {
          console.log('[DEBUG] No audio chunks to process');
          // Don't advance automatically - let the user try again
        }
      }
      
      setIsRecording(false);
      setCallStatus('processing');

      // Stop analyser loop
      if (silenceIntervalRef.current) {
        clearInterval(silenceIntervalRef.current);
        silenceIntervalRef.current = null;
        console.log('[DEBUG] Cleared silence interval');
      }
      
      // Clear maximum recording timeout
      if (answerWindowTimeoutRef.current) {
        clearTimeout(answerWindowTimeoutRef.current);
        answerWindowTimeoutRef.current = null;
        console.log('[DEBUG] Cleared answer window timeout');
      }

      // Close audio tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        console.log('[DEBUG] Stopped audio tracks');
      }
      
      // Reset recording state
      setRecordingStartTime(null);
      setQuestionStartTime(null);
      silenceStartRef.current = null;
      setIsSilenceDetected(false);
      
      console.log('[DEBUG] Recording stopped successfully');
    } else {
      console.log('[DEBUG] stopRecording called but not recording or no media recorder');
      // Don't advance automatically - let the user try again
    }
  };

  // Process voice response
  const processVoiceResponse = async (audioBlob: Blob) => {
    // Use ref to get the most current question value (avoids closure issues)
    const currentQuestionValue = currentQuestionRef.current;
    console.log(`[DEBUG] processVoiceResponse called with sessionId: ${sessionId}, currentQuestion: ${currentQuestionValue}, totalQuestions: ${totalQuestions}`);
    console.log(`[DEBUG] State vs Ref comparison - state: ${currentQuestion}, ref: ${currentQuestionValue}`);
    
    // Get sessionId from multiple sources to handle race conditions
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = localStorage.getItem('callSessionId');
      console.log(`[DEBUG] Retrieved sessionId from localStorage: ${currentSessionId}`);
    }
    if (!currentSessionId) {
      currentSessionId = sessionIdRef.current;
      console.log(`[DEBUG] Retrieved sessionId from ref: ${currentSessionId}`);
    }
    
    if (!currentSessionId) {
      console.log('[DEBUG] No session ID available from any source, cannot process response');
      setError('Session ID is missing. Please refresh the page and try again.');
      return;
    }
    
    // Ensure we have valid question and total questions data
    if (currentQuestionValue < 0 || totalQuestions === 0) {
      console.log(`[DEBUG] Invalid question state: currentQuestion=${currentQuestionValue}, totalQuestions=${totalQuestions}`);
      setError('Question state is invalid. Please refresh the page and try again.');
      return;
    }

    try {
      setIsLoading(true);
      
      // Check if we have actual audio data
      if (audioBlob.size === 0) {
        console.log('[DEBUG] Empty audio blob, cannot process response');
        return;
      }
      
      const audioFile = new File([audioBlob], 'response.wav', { type: 'audio/wav' });
      
      // Fix: Use the correct question ID (currentQuestionValue + 1 maps to question IDs 1, 2, 3...)
      const questionId = currentQuestionValue + 1;
      console.log(`[DEBUG] Submitting answer for question ${questionId} (index ${currentQuestionValue})`);
      
      // Use ref to track answered questions and prevent duplicates
      if (answeredQuestionsRef.current.has(currentQuestionValue)) {
        console.log(`[DEBUG] Question ${questionId} (index ${currentQuestionValue}) already answered, skipping`);
        return;
      }
      
      // Mark this question as answered immediately to prevent race conditions
      answeredQuestionsRef.current.add(currentQuestionValue);
      
      // Validate session before submitting
      const sessionValid = await validateSession();
      if (!sessionValid) {
        console.error('[ERROR] Session validation failed, cannot submit answer');
        return;
      }
      
      // Update the sessionId state if it was retrieved from localStorage or ref
      if (currentSessionId !== sessionId) {
        console.log(`[DEBUG] Updating sessionId state from ${sessionId} to ${currentSessionId}`);
        setSessionId(currentSessionId);
        sessionIdRef.current = currentSessionId;
      }
      
      const response = await apiService.submitAnswer(currentSessionId, questionId, audioFile);
      
      // Check if validation failed
      if (response.validation_failed) {
        console.log(`[DEBUG] Answer validation failed for question ${questionId}: "${response.fallback_message}"`);
        console.log(`[DEBUG] Original answer: "${response.original_answer}"`);
        
        // Play fallback message
        await playFallbackMessage(response.fallback_message || "I didn't understand your response. Please try again.");
        
        // Don't advance to next question - let user try again
        return;
      }
      
      // Calculate analytics
      const responseTime = questionStartTime ? new Date().getTime() - questionStartTime.getTime() : 0;
      const answerDuration = recordingStartTime ? new Date().getTime() - recordingStartTime.getTime() : 0;
      
      const analyticsEntry: CallAnalytics = {
        question_id: questionId,
        response_time: responseTime,
        answer_duration: answerDuration,
        audio_quality: calculateAudioQuality(audioBlob),
        confidence: 0.8, // Placeholder - could be enhanced with actual confidence scoring
        hesitation: responseTime > 3000, // Hesitation if response time > 3 seconds
        completed: true,
        timestamp: new Date()
      };

      setAnalytics(prev => [...prev, analyticsEntry]);
      setResponses(prev => ({ ...prev, [currentQuestionValue]: response.answer_text }));
      
      console.log(`[DEBUG] Answer processed successfully for question ${questionId}: "${response.answer_text}"`);
      
      // Auto-advance to next question after a short delay
      setTimeout(() => {
        nextQuestion();
      }, 1500);
      
    } catch (err) {
      console.error('Error processing voice response:', err);
      setError(err instanceof Error ? err.message : 'Failed to process response');
      // Don't auto-advance on error - let the user try again
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate audio quality (simplified)
  const calculateAudioQuality = (audioBlob: Blob): number => {
    // This is a simplified calculation - in a real app, you'd analyze audio characteristics
    const size = audioBlob.size;
    const duration = 3; // Assuming 3 seconds average
    const bitrate = (size * 8) / duration;
    
    // Normalize to 0-100 scale
    return Math.min(100, Math.max(0, (bitrate / 64000) * 100));
  };

  // Verify audio file accessibility and content type
  const verifyAudioFile = async (audioUrl: string): Promise<boolean> => {
    try {
      const response = await fetch(audioUrl, { method: 'HEAD' });
      if (!response.ok) {
        console.error('Audio file not accessible:', audioUrl, response.status);
        return false;
      }
      
      const contentType = response.headers.get('content-type');
      console.log('Audio file content type:', contentType);
      
      if (!contentType || !contentType.startsWith('audio/')) {
        console.error('Invalid audio content type:', contentType);
        return false;
      }
      
      const contentLength = response.headers.get('content-length');
      console.log('Audio file size:', contentLength, 'bytes');
      
      return true;
    } catch (err) {
      console.error('Error verifying audio file:', err);
      return false;
    }
  };

  // Preload and verify audio file
  const preloadAudio = async (audioUrl: string): Promise<HTMLAudioElement> => {
    return new Promise((resolve, reject) => {
      const audio = new Audio(audioUrl);
      
      audio.addEventListener('canplaythrough', () => {
        console.log('Audio preloaded successfully:', audioUrl);
        resolve(audio);
      });
      
      audio.addEventListener('error', (e) => {
        console.error('Audio preload failed:', audioUrl, e);
        reject(new Error(`Failed to preload audio: ${audioUrl}`));
      });
      
      // Set a timeout for preloading
      setTimeout(() => {
        reject(new Error('Audio preload timeout'));
      }, 10000); // 10 second timeout
      
      audio.load();
    });
  };

  // Play agent's question audio
  const playQuestionAudio = async (question: QuestionResponse) => {
    console.log(`[DEBUG] playQuestionAudio called with question:`, question);
    console.log(`[DEBUG] Current state in playQuestionAudio - sessionId: ${sessionId}, totalQuestions: ${totalQuestions}, questions.length: ${questions.length}`);
    
    // Prevent playing the same question multiple times
    if (callStatus === 'agent-speaking') {
      console.log(`[DEBUG] Already playing audio, skipping duplicate call to playQuestionAudio`);
      return;
    }
    
    try {
      setCallStatus('agent-speaking');
      
      // Stop any current audio
      if (currentAudio) {
        try { 
          currentAudio.pause(); 
          currentAudio.currentTime = 0;
        } catch {}
      }
      
      // Fix audio path - ensure it works with backend-generated files
      if (!question.audio_url) {
        console.error('Missing question audio URL');
        setCallStatus('connected');
        setQuestionStartTime(new Date());
        return;
      }
      let audioUrl = question.audio_url.startsWith('http') 
        ? question.audio_url 
        : `http://localhost:8000${question.audio_url}`;
      
      // Add cache-busting only for static audio assets
      if (audioUrl.includes('/static/audio/')) {
        audioUrl += `?t=${Date.now()}`;
      }
      
      console.log(`[DEBUG] Playing audio from: ${audioUrl}`);
      
      // Verify the audio file before playing
      const isAudioValid = await verifyAudioFile(audioUrl);
      if (!isAudioValid) {
        console.error('Audio file verification failed, cannot play');
        setCallStatus('connected');
        setQuestionStartTime(new Date());
        return;
      }
      
      // Preload the audio to ensure we get the correct file
      const audio = await preloadAudio(audioUrl);
      // Apply mute/volume state
      const shouldMute = isMuted || !isSpeakerOn;
      audio.muted = shouldMute;
      audio.volume = shouldMute ? 0 : 1;
      setCurrentAudio(audio);
      
      // Capture current state values to avoid closure issues
      const currentSessionId = sessionId;
      const currentTotalQuestions = totalQuestions;
      const currentQuestions = questions;
      
      audio.onended = () => {
        console.log(`[DEBUG] Audio finished playing for question ${question.id}, switching to listening mode`);
        console.log(`[DEBUG] State check before starting recording - sessionId: ${currentSessionId}, totalQuestions: ${currentTotalQuestions}, questions.length: ${currentQuestions.length}`);
        setCallStatus('connected');
        setQuestionStartTime(new Date());
        
        // Check if we need to restore state from localStorage
        if (!currentSessionId || currentTotalQuestions === 0 || currentQuestions.length === 0) {
          console.log('[DEBUG] State appears to be lost, attempting to restore from localStorage...');
          const savedSessionId = localStorage.getItem('callSessionId');
          const savedTotalQuestions = localStorage.getItem('callTotalQuestions');
          const savedQuestions = localStorage.getItem('callQuestions');
          const savedCurrentQuestion = localStorage.getItem('callCurrentQuestion');
          
          if (savedSessionId && savedTotalQuestions && savedQuestions) {
            console.log('[DEBUG] Restoring state from localStorage...');
            setSessionId(savedSessionId);
            setTotalQuestions(parseInt(savedTotalQuestions));
            try {
              const parsedQuestions = JSON.parse(savedQuestions);
              setQuestions(parsedQuestions);
              if (savedCurrentQuestion) {
                const questionIndex = parseInt(savedCurrentQuestion);
                setCurrentQuestion(questionIndex);
                currentQuestionRef.current = questionIndex;
              }
              console.log('[DEBUG] State restored, now starting recording...');
              startRecording();
            } catch (err) {
              console.error('[ERROR] Failed to parse saved questions:', err);
            }
          } else {
            console.error('[ERROR] No saved state found in localStorage');
          }
        } else {
          // Auto-start recording when agent finishes asking
          startRecording();
        }
      };
      
      audio.onerror = (e) => {
        console.error('Error playing audio:', e);
        console.log(`[DEBUG] Audio error, state check - sessionId: ${currentSessionId}, totalQuestions: ${currentTotalQuestions}, questions.length: ${currentQuestions.length}`);
        setCallStatus('connected');
        setQuestionStartTime(new Date());
        // Auto-start recording even if audio fails
        startRecording();
      };
      
      await audio.play();
    } catch (err) {
      console.error('Error playing audio:', err);
      setCallStatus('connected');
      setQuestionStartTime(new Date());
      // Auto-start recording even if audio fails
      startRecording();
    }
  };

  // Play fallback message when validation fails
  const playFallbackMessage = async (message: string) => {
    try {
      setCallStatus('agent-speaking');
      setFallbackMessage(message);
      
      // Stop any current audio
      if (currentAudio) {
        try { currentAudio.pause(); } catch {}
      }
      
      // Generate fallback audio using backend TTS API
      console.log('Generating fallback audio for:', message);
      
      try {
        // Call backend TTS API to generate audio
        const response = await fetch('http://localhost:8000/api/generate-fallback-audio', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: message,
            style: 'friendly'
          })
        });
        
        if (response.ok) {
          const audioData = await response.json();
          const audioUrl = audioData.audio_url;
          
          if (audioUrl) {
            // Fix audio path
            let fullAudioUrl = audioUrl.startsWith('http') 
              ? audioUrl 
              : `http://localhost:8000${audioUrl}`;
            
            console.log('Playing fallback audio from:', fullAudioUrl);
            
            // Preload and play the audio
            const audio = await preloadAudio(fullAudioUrl);
            const shouldMute = isMuted || !isSpeakerOn;
            audio.muted = shouldMute;
            audio.volume = shouldMute ? 0 : 1;
            setCurrentAudio(audio);
            
            audio.onended = () => {
              console.log('Fallback audio finished, returning to question');
              setFallbackMessage(null);
              setCallStatus('connected');
              setQuestionStartTime(new Date());
              // Auto-start recording after fallback message
              startRecording();
            };
            
            audio.onerror = (e) => {
              console.error('Fallback audio error:', e);
              setFallbackMessage(null);
              setCallStatus('connected');
              setQuestionStartTime(new Date());
              // Auto-start recording even if audio fails
              startRecording();
            };
            
            await audio.play();
            return; // Successfully played audio
          }
        }
      } catch (audioError) {
        console.error('Failed to generate fallback audio:', audioError);
      }
      
      // Fallback: if TTS fails, just show the message for 3 seconds
      console.log('Using fallback display-only mode');
      setTimeout(() => {
        console.log('Fallback message finished, returning to question');
        setFallbackMessage(null);
        setCallStatus('connected');
        setQuestionStartTime(new Date());
        // Auto-start recording after fallback message
        startRecording();
      }, 3000); // 3 second delay to show the message
      
    } catch (err) {
      console.error('Error playing fallback message:', err);
      setFallbackMessage(null);
      setCallStatus('connected');
      setQuestionStartTime(new Date());
      // Auto-start recording even if audio fails
      startRecording();
    }
  };

  // Play introduction message
  const playIntroduction = async (loadedQuestions: QuestionResponse[]) => {
    try {
      setCallStatus('agent-speaking');
      
      // Stop any current audio
      if (currentAudio) {
        try { currentAudio.pause(); } catch {}
      }
      
      // Get introduction audio from API
      const introData = await apiService.getIntroductionAudio();
      console.log('Introduction audio data:', introData);
      
      // Fix audio path for introduction
      if (!introData.audio_url) {
        console.error('Missing introduction audio URL');
        // Fallback: skip intro and go directly to questions
        setIsConversationStarted(true);
        if (loadedQuestions.length > 0) {
          playQuestionAudio(loadedQuestions[0]);
        }
        return;
      }
      let audioUrl = introData.audio_url.startsWith('http') 
        ? introData.audio_url 
        : `http://localhost:8000${introData.audio_url}`;
      
      // Add cache-busting only for static audio assets
      if (audioUrl.includes('/static/audio/')) {
        audioUrl += `?t=${Date.now()}`;
      }
      
      console.log('Playing introduction from:', audioUrl);
      
      // Verify the audio file before playing
      const isAudioValid = await verifyAudioFile(audioUrl);
      if (!isAudioValid) {
        console.error('Introduction audio file verification failed, cannot play');
        // Fallback: skip intro and go directly to questions
        setIsConversationStarted(true);
        if (loadedQuestions.length > 0) {
          playQuestionAudio(loadedQuestions[0]);
        }
        return;
      }
      
      // Preload the audio to ensure we get the correct file
      const audio = await preloadAudio(audioUrl);
      // Apply mute/volume state
      const shouldMute = isMuted || !isSpeakerOn;
      audio.muted = shouldMute;
      audio.volume = shouldMute ? 0 : 1;
      setCurrentAudio(audio);
      
      audio.onended = () => {
        console.log('Introduction finished, starting questions');
        console.log('Questions array at this point:', loadedQuestions);
        console.log('Questions length:', loadedQuestions.length);
        setIsConversationStarted(true);
        // Start with first question after introduction
        if (loadedQuestions.length > 0) {
          console.log('Playing first question:', loadedQuestions[0]);
          playQuestionAudio(loadedQuestions[0]);
        } else {
          console.error('No questions available to play!');
        }
      };
      
      audio.onerror = (e) => {
        console.error('Introduction audio error:', e);
        // Fallback: skip intro and go directly to questions
        setIsConversationStarted(true);
        if (loadedQuestions.length > 0) {
          playQuestionAudio(loadedQuestions[0]);
        }
      };
      
      await audio.play();
    } catch (err) {
      console.error('Error with introduction:', err);
      // Fallback: skip intro and go directly to questions
      setIsConversationStarted(true);
      if (loadedQuestions.length > 0) {
        playQuestionAudio(loadedQuestions[0]);
      }
    }
  };

  const startCall = async () => {
    console.log('[DEBUG] startCall called');
    setCallStatus('calling');
    setIsLoading(true);
    
    // Clear any previous call state from localStorage
    localStorage.removeItem('callSessionId');
    localStorage.removeItem('callTotalQuestions');
    localStorage.removeItem('callQuestions');
    localStorage.removeItem('callCurrentQuestion');
    
    // Reset current question to 0 for new call
    setCurrentQuestion(0);
    currentQuestionRef.current = 0;
    answeredQuestionsRef.current.clear();
    isProcessingNextQuestionRef.current = false;
    
    try {
      // Initialize session and load questions first
      console.log('[DEBUG] Starting session...');
      const session = await apiService.startSession();
      console.log('[DEBUG] Session started:', session);
      
      // Update both state and refs immediately to prevent race conditions
      setSessionId(session.session_id);
      sessionIdRef.current = session.session_id;
      setTotalQuestions(session.total_questions);
      totalQuestionsRef.current = session.total_questions;
      
      // Save to localStorage immediately
      localStorage.setItem('callSessionId', session.session_id);
      localStorage.setItem('callTotalQuestions', session.total_questions.toString());
      
      // Load all questions
      console.log('[DEBUG] Loading questions...');
      const questionsData = await apiService.getQuestions();
      console.log('[DEBUG] Questions data loaded:', questionsData);
      
      const questionPromises = questionsData.questions.map((_, index) => 
        apiService.getNextQuestion(index, session.session_id)
      );
      const loadedQuestions = await Promise.all(questionPromises);
      console.log('[DEBUG] Questions loaded:', loadedQuestions);
      setQuestions(loadedQuestions);
      questionsRef.current = loadedQuestions;
      
      // Save questions to localStorage
      localStorage.setItem('callQuestions', JSON.stringify(loadedQuestions));
      
      // Simulate call connection
      setTimeout(async () => {
        setCallStatus('connected');
        setIsLoading(false);
        
        console.log('[DEBUG] About to start introduction, questions count:', loadedQuestions.length);
        console.log('[DEBUG] Session ID at this point:', session.session_id);
        console.log('[DEBUG] Total questions at this point:', session.total_questions);
        
        // Ensure all state is properly synchronized
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Start with introduction only after questions are loaded
        await playIntroduction(loadedQuestions);
      }, 2000);
      
    } catch (err) {
      console.error('Failed to start call:', err);
      setError('Failed to start call');
      setCallStatus('ended');
      setIsLoading(false);
    }
  };

  const endCall = () => {
    console.log('[DEBUG] endCall called, clearing localStorage');
    setCallStatus('ended');
    
    // Clear localStorage
    localStorage.removeItem('callSessionId');
    localStorage.removeItem('callTotalQuestions');
    localStorage.removeItem('callQuestions');
    localStorage.removeItem('callCurrentQuestion');
    
    // Clear refs
    answeredQuestionsRef.current.clear();
    isProcessingNextQuestionRef.current = false;
    
    // Stop current audio
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }
    
    // Stop recording if active
    if (isRecording) {
      stopRecording();
    }
    
    // Clear auto-advance timer
    if (autoAdvanceTimer) {
      clearTimeout(autoAdvanceTimer);
    }
    
    // Save analytics
    saveCallAnalytics();
  };

    const nextQuestion = async () => {
    // Prevent multiple simultaneous calls
    if (isProcessingNextQuestionRef.current) {
      console.log(`[DEBUG] nextQuestion already in progress, skipping duplicate call`);
      return;
    }
    
    isProcessingNextQuestionRef.current = true;
    
    try {
      // Use ref as source of truth to avoid closure issues
      const currentQuestionValue = currentQuestionRef.current;
      console.log(`[DEBUG] nextQuestion called. currentQuestion=${currentQuestion}, ref=${currentQuestionValue}, questions.length=${questions.length}, totalQuestions=${totalQuestions}, sessionId=${sessionId}`);
      
      // Skip validation to prevent infinite loops - just proceed with the ref value
      const nextIndex = currentQuestionValue + 1;
      console.log(`[DEBUG] Next index: ${nextIndex}`);
      
      // Update the ref immediately for consistency
      currentQuestionRef.current = nextIndex;
      console.log(`[DEBUG] Updated currentQuestionRef.current to: ${nextIndex}`);
      
      // Check if we have more questions to ask
      if (nextIndex < totalQuestions) {
        console.log(`[DEBUG] Moving to next question: index ${nextIndex}`);
        
        // Update current question state using functional update to ensure we have the latest value
        setCurrentQuestion(prev => {
          console.log(`[DEBUG] setCurrentQuestion called with prev=${prev}, setting to ${nextIndex}`);
          return nextIndex;
        });
        
        // Use a small delay to ensure state update completes
        await new Promise(resolve => setTimeout(resolve, 100));
      
      // Check if we already have this question loaded
      if (questions[nextIndex]) {
        console.log(`[DEBUG] Playing preloaded question ${nextIndex}:`, questions[nextIndex]);
        await playQuestionAudio(questions[nextIndex]);
      } else {
        // Fetch the question on-demand
        try {
          console.log(`[DEBUG] Fetching question ${nextIndex} on-demand`);
          const newQuestion = await apiService.getNextQuestion(nextIndex, sessionId!);
          
          // Add the new question to our questions array
          setQuestions(prev => {
            const updated = [...prev];
            updated[nextIndex] = newQuestion;
            return updated;
          });
          
          console.log(`[DEBUG] Playing fetched question ${nextIndex}:`, newQuestion);
          await playQuestionAudio(newQuestion);
        } catch (error) {
          console.error(`[ERROR] Failed to fetch question ${nextIndex}:`, error);
          // Try to continue with the next question, but prevent infinite loops
          if (nextIndex < totalQuestions - 1) {
            setTimeout(() => {
              nextQuestion();
            }, 1000);
          } else {
            console.error('[ERROR] Failed to fetch question and reached end, ending call');
            endCall();
          }
        }
      }
    } else {
      // All questions completed
      console.log(`[DEBUG] All ${totalQuestions} questions completed. Ending call.`);
      endCall();
    }
    } catch (error) {
      console.error('[ERROR] Error in nextQuestion:', error);
      // Reset the flag to allow future calls
      isProcessingNextQuestionRef.current = false;
    } finally {
      // Always reset the flag when done
      isProcessingNextQuestionRef.current = false;
    }
  };

  // Removed manual skip control; auto-advance handles progression

  const saveCallAnalytics = async () => {
    if (!sessionId) return;
    
    try {
      await apiService.saveCallAnalytics(sessionId, analytics);
      console.log('Call Analytics saved successfully');
    } catch (err) {
      console.error('Failed to save analytics:', err);
    }
  };

  const handleRecordingToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (isLoading && !sessionId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4" />
          <p>Initializing call session...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <p className="text-red-400 mb-4">Error: {error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Call Status Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-2 bg-white/10 rounded-full px-6 py-2 backdrop-blur-sm">
            <div className={`w-3 h-3 rounded-full ${
              callStatus === 'connected' || callStatus === 'agent-speaking' || callStatus === 'listening' ? 'bg-green-400' : 
              callStatus === 'calling' ? 'bg-yellow-400' : 
              callStatus === 'processing' ? 'bg-blue-400' : 'bg-red-400'
            }`}></div>
            <span className="text-white font-medium">
              {callStatus === 'idle' && 'Ready to Call'}
              {callStatus === 'calling' && 'Connecting...'}
              {callStatus === 'connected' && `Connected - ${formatTime(callDuration)}`}
              {callStatus === 'agent-speaking' && 'Agent Speaking...'}
              {callStatus === 'listening' && 'Listening...'}
              {callStatus === 'processing' && 'Processing...'}
              {callStatus === 'ended' && 'Call Ended'}
            </span>
          </div>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Call Interface */}
          <div className="bg-white/5 rounded-3xl p-8 backdrop-blur-sm border border-white/10">
            {callStatus === 'idle' && (
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-6 bg-blue-600 rounded-full flex items-center justify-center">
                  <Phone className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">Start a Voice Call</h2>
                <p className="text-blue-200 mb-8">Begin your automated voice call session</p>
                <button
                  onClick={startCall}
                  className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-full font-semibold transition-colors"
                >
                  Start Call
                </button>
              </div>
            )}

            {callStatus === 'calling' && (
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-6 bg-yellow-600 rounded-full flex items-center justify-center animate-pulse">
                  <Phone className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">Connecting...</h2>
                <p className="text-blue-200">Establishing connection with agent</p>
              </div>
            )}

            {(callStatus === 'connected' || callStatus === 'agent-speaking' || callStatus === 'listening' || callStatus === 'processing') && (
              <div className="space-y-6">
                {/* Call Controls */}
                <div className="flex justify-center space-x-4">
                  <button
                    onClick={handleRecordingToggle}
                    disabled={callStatus === 'agent-speaking' || callStatus === 'processing'}
                    className={`p-4 rounded-full transition-colors ${
                      isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
                    } ${(callStatus === 'agent-speaking' || callStatus === 'processing') ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {isRecording ? <MicOff className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
                  </button>
                  
                  {isRecording && (
                    <button
                      onClick={stopRecording}
                      disabled={callStatus === 'processing'}
                      className={`p-4 rounded-full transition-colors ${
                        callStatus === 'processing' ? 'opacity-50 cursor-not-allowed' : 'bg-orange-600 hover:bg-orange-700'
                      }`}
                      title="Stop Recording"
                    >
                      <Circle className="w-6 h-6 text-white" />
                    </button>
                  )}
                  
                  <button
                    onClick={() => setIsMuted(!isMuted)}
                    className={`p-4 rounded-full transition-colors ${
                      isMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-600 hover:bg-gray-700'
                    }`}
                  >
                    {isMuted ? <VolumeX className="w-6 h-6 text-white" /> : <Volume2 className="w-6 h-6 text-white" />}
                  </button>
                  
                  <button
                    onClick={endCall}
                    className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-colors"
                  >
                    <PhoneOff className="w-6 h-6 text-white" />
                  </button>
                  
                  {/* Debug button */}
                  <button
                    onClick={() => {
                      console.log('[DEBUG] Manual state check:', {
                        currentQuestion,
                        totalQuestions,
                        questionsLength: questions.length,
                        sessionId,
                        callStatus
                      });
                      validateAndResetState();
                    }}
                    className="p-4 rounded-full bg-purple-600 hover:bg-purple-700 transition-colors"
                    title="Debug State"
                  >
                    <span className="text-white text-xs">DBG</span>
                  </button>
                </div>

                {/* Client Info */}
                <div className="text-center px-6 mb-8">
                  <div className="w-32 h-32 mx-auto mb-4 rounded-full overflow-hidden border-4 border-white/20">
                    <img 
                      src={mockClientInfo.avatar} 
                      alt={mockClientInfo.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <h3 className="text-xl font-semibold text-white">{mockClientInfo.name}</h3>
                  <p className="text-blue-200">{mockClientInfo.company}</p>
                  <p className="text-blue-300 text-sm">{mockClientInfo.phone}</p>
                </div>

                {/* Question Display */}
                {isConversationStarted && questions[currentQuestion] && (
                  <div className="px-6 mb-6 flex-1">
                    <div className="bg-white/10 rounded-2xl p-4 backdrop-blur-sm">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-blue-200">Question {currentQuestion + 1}/{questions.length}</span>
                        <span className="text-xs text-gray-400">(Index: {currentQuestion})</span>
                        {callStatus === 'listening' && (
                          <div className="flex items-center space-x-1">
                            <Circle className="w-2 h-2 text-red-400 fill-current animate-pulse" />
                            <span className="text-xs text-blue-200">Recording...</span>
                            {isSilenceDetected && (
                              <span className="text-xs text-orange-300 ml-2">
                                Silence detected...
                              </span>
                            )}
                            <span className="text-xs text-gray-300 ml-2">
                              Max: {Math.ceil(MAX_LISTEN_DURATION_MS / 1000)}s
                            </span>
                          </div>
                        )}
                        {callStatus === 'processing' && (
                          <div className="flex items-center space-x-1">
                            <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                            <span className="text-xs text-blue-200">Processing...</span>
                          </div>
                        )}
                        {fallbackMessage && (
                          <div className="flex items-center space-x-1">
                            <Circle className="w-2 h-2 text-orange-400 fill-current animate-pulse" />
                            <span className="text-xs text-orange-200">Agent speaking...</span>
                          </div>
                        )}
                      </div>
                      <p className="text-white font-medium mb-4">{questions[currentQuestion].question_text}</p>
                      
                      {/* Fallback Message Display */}
                      {fallbackMessage && (
                        <div className="bg-orange-500/20 border border-orange-400/30 rounded-lg p-3 mb-3">
                          <p className="text-orange-200 text-sm font-medium">Agent Response:</p>
                          <p className="text-orange-100">{fallbackMessage}</p>
                        </div>
                      )}
                      
                      {/* Response Display */}
                      {responses[currentQuestion] && (
                        <div className="bg-white/5 rounded-lg p-3 mb-3">
                          <p className="text-blue-200 text-sm">Your response:</p>
                          <p className="text-white">{responses[currentQuestion]}</p>
                        </div>
                      )}
                      
                      {/* No manual controls; recording is automatic */}
                    </div>
                  </div>
                )}

                {/* Progress */}
                {isConversationStarted && (
                  <div className="px-6">
                    <div className="bg-white/10 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
                      ></div>
                    </div>
                    <p className="text-center text-blue-200 mt-2">
                      {currentQuestion + 1} of {questions.length} questions completed
                    </p>
                    
                    {/* Debug Info */}
                    <div className="mt-4 p-3 bg-white/5 rounded-lg">
                      <p className="text-xs text-gray-400 text-center">Debug Info</p>
                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-300">
                        <div>Session ID: {sessionId?.substring(0, 8)}...</div>
                        <div>Total Questions: {totalQuestions}</div>
                        <div>Current Index: {currentQuestion}</div>
                        <div>Questions Loaded: {questions.length}</div>
                        <div>Call Status: {callStatus}</div>
                        <div>Recording: {isRecording ? 'Yes' : 'No'}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {callStatus === 'ended' && (
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-6 bg-gray-600 rounded-full flex items-center justify-center">
                  <PhoneOff className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">Call Completed</h2>
                <p className="text-blue-200 mb-4">Duration: {formatTime(callDuration)}</p>
                <p className="text-blue-200 mb-8">Thank you for your responses!</p>
                <button
                  onClick={() => window.location.reload()}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-full font-semibold transition-colors"
                >
                  Start New Call
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CallInterface;