import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Mic,
  MicOff,
  Send,
  X,
  Trash2,
  Volume2,
  VolumeX,
  AlertCircle,
  Loader2,
  ArrowRight,
  Globe,
  Check,
  Calendar,
  FileText,
  Compass,
} from 'lucide-react';

import type { NavTab, FarmerProfile } from '../../types';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  sendChatMessageApi,
  getChatHistoryApi,
  clearChatHistoryApi,
  type ChatMessageApiResponse,
  type ChatAction,
} from '../../services/api';
import {
  createSpeechPlaybackController,
  createSpeechRecognizer,
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
} from '../../utils/speech';

interface GlobalChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  time: string;
  provider?: string;
  isRealAI?: boolean;
  action?: ChatAction | null;
  error?: boolean;
}

interface GlobalChatWidgetProps {
  currentTab: NavTab;
  onNavigate: (tab: NavTab, bookingId?: string) => void;
  farmer?: FarmerProfile;
}

export const GlobalChatWidget: React.FC<GlobalChatWidgetProps> = ({
  currentTab,
  onNavigate,
  farmer,
}) => {
  const { language: appLang, toggleLanguage } = useLanguage();
  const { user, token, isAuthenticated } = useAuth();

  // Widget state
  const [isOpen, setIsOpen] = useState(false);

  // Assistant language state (matches app or toggled)
  const [chatLang, setChatLang] = useState<'en' | 'ta'>(appLang === 'ta' ? 'ta' : 'en');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<GlobalChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  // Audio & TTS
  const speechControllerRef = useRef(createSpeechPlaybackController());
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);

  // Voice STT
  const [isListening, setIsListening] = useState(false);
  const [sttSupported] = useState(isSpeechRecognitionSupported());
  const recognizerRef = useRef<any>(null);
  const [micDeniedNotice, setMicDeniedNotice] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Synchronize language when app language changes
  useEffect(() => {
    setChatLang(appLang === 'ta' ? 'ta' : 'en');
  }, [appLang]);

  // Initial welcome message
  const getInitialWelcome = (lang: 'en' | 'ta'): GlobalChatMessage => ({
    id: 'welcome-global',
    sender: 'ai',
    text:
      lang === 'ta'
        ? `வணக்கம் ${user?.name || farmer?.name || 'விவசாயி'}! நான் உங்கள் 'அக்ரிபாரத் AI' உதவியாளர். வானிலை அறிக்கை, கொள்முதல் முன்பதிவு, டிஜிட்டல் ரசீதுகள் அல்லது விவசாய ஆலோசனைகள் குறித்து என்னிடம் கேளுங்கள்.`
        : `Vanakkam ${user?.name || farmer?.name || 'Farmer'}! I am your AgriBharat AI Assistant. Ask me to open weather, check your procurement slot, explain your bill, or answer any crop question.`,
    time: 'Just now',
    provider: 'AGRIBHARAT_AI',
    isRealAI: false,
  });

  // Load chat history once authenticated
  useEffect(() => {
    let isMounted = true;
    async function loadHistory() {
      if (!token) {
        if (isMounted) setMessages([getInitialWelcome(chatLang)]);
        return;
      }
      try {
        const res = await getChatHistoryApi(token);
        if (isMounted) {
          if (res && res.messages && res.messages.length > 0) {
            const loaded: GlobalChatMessage[] = [];
            for (const m of res.messages.slice(-15)) {
              loaded.push({
                id: `u-${m.id}`,
                sender: 'user',
                text: m.userMessage,
                time: m.timestamp || 'Earlier',
              });
              loaded.push({
                id: `a-${m.id}`,
                sender: 'ai',
                text: m.assistantReply,
                time: m.timestamp || 'Earlier',
                provider: m.provider,
                isRealAI: m.isRealAI,
              });
            }
            setMessages(loaded);
            if (res.messages[res.messages.length - 1].conversationId) {
              setConversationId(res.messages[res.messages.length - 1].conversationId);
            }
          } else {
            setMessages([getInitialWelcome(chatLang)]);
          }
        }
      } catch {
        if (isMounted) setMessages([getInitialWelcome(chatLang)]);
      }
    }
    loadHistory();
    return () => {
      isMounted = false;
    };
  }, [token]);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  // Handle Speech Recognition (Microphone)
  const toggleListening = () => {
    setMicDeniedNotice(null);
    if (!sttSupported) {
      setMicDeniedNotice(
        chatLang === 'ta'
          ? 'உங்கள் உலாவியில் குரல் அறிதல் ஆதரிக்கப்படவில்லை. நீங்கள் தட்டச்சு செய்யலாம்.'
          : 'Speech recognition is not supported in this browser. You can type your request.'
      );
      return;
    }

    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
      return;
    }

    // Stop TTS if speaking
    stopSpeaking();

    const recognizer = createSpeechRecognizer(
      chatLang,
      (transcript, isFinal) => {
        setInput(transcript);
        if (isFinal) {
          setIsListening(false);
        }
      },
      (errText) => {
        setIsListening(false);
        setMicDeniedNotice(errText);
      },
      () => {
        setIsListening(false);
      }
    );

    if (recognizer) {
      recognizerRef.current = recognizer;
      recognizer.start();
      setIsListening(true);
    } else {
      setMicDeniedNotice(
        chatLang === 'ta'
          ? 'மைக்ரோஃபோன் அணுகல் அனுமதிக்கப்படவில்லை.'
          : 'Microphone permission was not granted.'
      );
    }
  };

  // Text-To-Speech Playback
  const handleSpeak = (text: string, msgId: string) => {
    if (!isSpeechSynthesisSupported()) return;

    if (isSpeaking && speakingMsgId === msgId) {
      stopSpeaking();
      return;
    }

    stopSpeaking();
    setIsSpeaking(true);
    setSpeakingMsgId(msgId);

    speechControllerRef.current.speak(
      text,
      chatLang,
      () => {
        setIsSpeaking(true);
      },
      () => {
        setIsSpeaking(false);
        setSpeakingMsgId(null);
      },
      (err) => {
        setIsSpeaking(false);
        setSpeakingMsgId(null);
        setErrorNotice(err);
      }
    );
  };

  const stopSpeaking = () => {
    speechControllerRef.current.stop();
    setIsSpeaking(false);
    setSpeakingMsgId(null);
  };

  // Send message
  const handleSend = async (messageText?: string, confirmedActionPayload?: Record<string, any>) => {
    const textToSend = (messageText !== undefined ? messageText : input).trim();
    if (!textToSend && !confirmedActionPayload) return;

    // Stop speaking and listening
    stopSpeaking();
    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
    }

    const userMsgId = `u-${Date.now()}`;
    const userMsg: GlobalChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: textToSend || (confirmedActionPayload ? 'Confirmed requested action' : ''),
      time: 'Just now',
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!messageText) setInput('');
    setIsLoading(true);
    setErrorNotice(null);

    try {
      const payload = {
        message: textToSend || 'Confirm action',
        language: chatLang,
        conversationId: conversationId || undefined,
        confirmedAction: confirmedActionPayload,
      };

      const res: ChatMessageApiResponse = await sendChatMessageApi(payload, token);

      if (res.conversationId) {
        setConversationId(res.conversationId);
      }

      const aiMsgId = `a-${res.id || Date.now()}`;
      const aiMsg: GlobalChatMessage = {
        id: aiMsgId,
        sender: 'ai',
        text: res.reply,
        time: res.timestamp || 'Just now',
        provider: res.provider,
        isRealAI: res.isRealAI,
        action: res.action,
      };

      setMessages((prev) => [...prev, aiMsg]);

      // Automatically execute navigation if returned from backend
      if (res.action && res.action.actionType === 'NAVIGATE' && res.action.targetTab) {
        const target = res.action.targetTab as NavTab;
        if (target !== currentTab) {
          setTimeout(() => {
            onNavigate(target);
          }, 350);
        }
      }

      // Handle language toggle request
      if (res.action && res.action.actionName === 'TOGGLE_LANGUAGE') {
        const nextLang = chatLang === 'en' ? 'ta' : 'en';
        setChatLang(nextLang);
        toggleLanguage();
      }

      // If user had voice input active or explicitly toggled voice, play speech
      // (Optional gentle speech response)
    } catch (err: any) {
      const errorMsg: GlobalChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text:
          err.message ||
          (chatLang === 'ta'
            ? 'மன்னிக்கவும், சேவையகத்துடன் தொடர்பு கொள்ள முடியவில்லை.'
            : 'Sorry, could not connect to server. Please try again.'),
        time: 'Just now',
        error: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear Chat History
  const handleClearHistory = async () => {
    if (!window.confirm(chatLang === 'ta' ? 'அரட்டை வரலாற்றை அழிக்கவா?' : 'Clear conversation history?')) {
      return;
    }
    stopSpeaking();
    if (token) {
      try {
        await clearChatHistoryApi(token);
      } catch {
        // Fallback local clear
      }
    }
    setMessages([getInitialWelcome(chatLang)]);
  };

  // Action Button Click Handlers
  const handleActionExecute = (action: ChatAction) => {
    if (action.actionType === 'NAVIGATE' && action.targetTab) {
      onNavigate(action.targetTab as NavTab);
    } else if (action.actionType === 'REQUEST_CONFIRMATION' && action.confirmedActionPayload) {
      handleSend('Yes, confirm', action.confirmedActionPayload);
    }
  };

  // If user is unauthenticated, do not render global floating widget
  if (!isAuthenticated) return null;

  return (
    <>
      {/* 1. FLOATING ASSISTANT TRIGGER BUTTON */}
      {!isOpen && (
        <button
          id="global-ai-trigger-button"
          onClick={() => {
            setIsOpen(true);
          }}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold rounded-full shadow-xl shadow-emerald-700/25 transition-all duration-200 transform hover:scale-105 group border border-emerald-400/30"
          title={chatLang === 'ta' ? 'அக்ரிபாரத் AI உதவியாளர்' : 'AgriBharat AI Assistant'}
        >
          <div className="relative">
            <Bot className="w-5 h-5 transition-transform group-hover:rotate-12" />
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-300"></span>
            </span>
          </div>
          <span className="text-xs tracking-wide hidden sm:inline">
            {chatLang === 'ta' ? 'AI உதவியாளர்' : 'AI Assistant'}
          </span>
          <span className="flex items-center gap-1 text-[10px] bg-emerald-900/30 px-1.5 py-0.5 rounded-full border border-emerald-400/20 text-emerald-100">
            <Mic className="w-2.5 h-2.5" />
            <span>Voice</span>
          </span>
        </button>
      )}

      {/* 2. RESPONSIVE FLOATING CHAT PANEL */}
      {isOpen && (
        <div
          id="global-ai-chat-panel"
          className="fixed inset-x-0 bottom-0 sm:inset-auto sm:bottom-6 sm:right-6 z-50 w-full sm:w-[400px] md:w-[420px] max-h-[88vh] sm:max-h-[640px] h-[580px] bg-white/95 backdrop-blur-md rounded-t-2xl sm:rounded-2xl shadow-2xl border border-emerald-100/90 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200"
        >
          {/* A. HEADER */}
          <div className="bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-700 text-white p-3.5 px-4 flex items-center justify-between shadow-xs select-none">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white/15 flex items-center justify-center border border-white/20">
                <Bot className="w-4 h-4 text-emerald-100" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-xs font-bold tracking-tight">AgriBharat</h3>
                  <span className="text-[9px] bg-emerald-900/40 text-emerald-200 px-1.5 py-0.2 rounded-full border border-emerald-400/20 font-medium">
                    Global Voice & Actions
                  </span>
                </div>
                <p className="text-[10px] text-emerald-100/80">
                  {user?.name ? `${user.name} (${user.role})` : 'Active Assistant'}
                </p>
              </div>
            </div>

            {/* Header Controls */}
            <div className="flex items-center gap-1">
              {/* Language Switcher */}
              <button
                type="button"
                onClick={() => {
                  const next = chatLang === 'en' ? 'ta' : 'en';
                  setChatLang(next);
                  toggleLanguage();
                }}
                className="px-2 py-1 text-[11px] font-semibold bg-white/10 hover:bg-white/20 rounded-lg transition-colors flex items-center gap-1 text-emerald-100"
                title="Toggle Language"
              >
                <Globe className="w-3 h-3" />
                <span>{chatLang === 'ta' ? 'தமிழ்' : 'EN'}</span>
              </button>

              {/* Stop Speaking if TTS active */}
              {isSpeaking && (
                <button
                  type="button"
                  onClick={stopSpeaking}
                  className="p-1.5 text-amber-200 bg-amber-900/30 hover:bg-amber-800/40 rounded-lg transition-colors"
                  title="Stop Speaking"
                >
                  <VolumeX className="w-3.5 h-3.5" />
                </button>
              )}

              {/* Clear Chat */}
              <button
                type="button"
                onClick={handleClearHistory}
                className="p-1.5 text-emerald-100/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                title="Clear Chat"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>

              {/* Minimize / Close */}
              <button
                type="button"
                onClick={() => {
                  stopSpeaking();
                  setIsOpen(false);
                }}
                className="p-1.5 text-emerald-100/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* B. NOTICE / PERMISSION WARNING */}
          {errorNotice && (
            <div className="bg-red-50 border-b border-red-100 p-2 px-3 text-[11px] text-red-800 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                <span>{errorNotice}</span>
              </div>
              <button
                type="button"
                onClick={() => setErrorNotice(null)}
                className="text-red-600 hover:text-red-900 ml-2"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {micDeniedNotice && (
            <div className="bg-amber-50 border-b border-amber-100 p-2 px-3 text-[11px] text-amber-800 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                <span>{micDeniedNotice}</span>
              </div>
              <button
                type="button"
                onClick={() => setMicDeniedNotice(null)}
                className="text-amber-600 hover:text-amber-900 ml-2"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* C. MESSAGES SCROLL AREA */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5 bg-slate-50/60 text-xs">
            {messages.map((m) => {
              const isUser = m.sender === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-3 shadow-xs leading-relaxed ${
                      isUser
                        ? 'bg-emerald-600 text-white rounded-br-xs'
                        : m.error
                        ? 'bg-red-50 text-red-800 border border-red-200 rounded-bl-xs'
                        : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.text}</p>

                    {/* STRUCTURED ACTION CARD (IF RETURNED) */}
                    {m.action && !isUser && (
                      <div className="mt-2.5 pt-2 border-t border-slate-100 space-y-2">
                        {/* 1. Navigation Button */}
                        {m.action.actionType === 'NAVIGATE' && m.action.targetTab && (
                          <button
                            type="button"
                            onClick={() => handleActionExecute(m.action!)}
                            className="w-full flex items-center justify-between gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200/80 rounded-xl font-medium transition-colors text-[11px]"
                          >
                            <span className="flex items-center gap-1.5">
                              <Compass className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Go to {m.action.targetTab.toUpperCase()}</span>
                            </span>
                            <ArrowRight className="w-3 h-3 text-emerald-600" />
                          </button>
                        )}

                        {/* 2. Data Card (Slot, Bill, Weather) */}
                        {m.action.actionType === 'SHOW_DATA' && m.action.data && (
                          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/70 text-[11px] space-y-1 text-slate-700">
                            {m.action.actionName === 'GET_NEXT_SLOT' && (
                              <div>
                                <div className="font-semibold text-emerald-800 flex items-center gap-1">
                                  <Calendar className="w-3 h-3 text-emerald-600" />
                                  <span>Token #{m.action.data.tokenNumber || 'Confirmed'}</span>
                                </div>
                                <div className="text-[10px] text-slate-500 mt-0.5">
                                  {m.action.data.mandiName} • {m.action.data.slotDate} ({m.action.data.timeWindow})
                                </div>
                              </div>
                            )}

                            {m.action.actionName === 'GET_LATEST_BILL' && (
                              <div>
                                <div className="font-semibold text-emerald-800 flex items-center gap-1">
                                  <FileText className="w-3 h-3 text-emerald-600" />
                                  <span>Bill #{m.action.data.billNumber}</span>
                                </div>
                                <div className="text-[10px] text-slate-500 mt-0.5">
                                  Net Payable: ₹{Number(m.action.data.netAmount || 0).toLocaleString()} • DBT: {m.action.data.paymentStatus || 'PENDING'}
                                </div>
                              </div>
                            )}

                            {m.action.targetTab && (
                              <button
                                type="button"
                                onClick={() => handleActionExecute(m.action!)}
                                className="mt-1 text-[10px] text-emerald-700 font-medium hover:underline flex items-center gap-0.5"
                              >
                                <span>View in {m.action.targetTab}</span>
                                <ArrowRight className="w-2.5 h-2.5" />
                              </button>
                            )}
                          </div>
                        )}

                        {/* 3. Action Confirmation Buttons */}
                        {m.action.actionType === 'REQUEST_CONFIRMATION' && m.action.confirmedActionPayload && (
                          <div className="bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-200/80 space-y-2">
                            <p className="text-[11px] font-semibold text-emerald-900">
                              {m.action.confirmationPrompt || 'Please confirm this action:'}
                            </p>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => handleActionExecute(m.action!)}
                                className="flex-1 py-1.5 px-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-[11px] font-medium transition-colors flex items-center justify-center gap-1 shadow-xs"
                              >
                                <Check className="w-3 h-3" />
                                <span>{chatLang === 'ta' ? 'ஆம், உறுதிசெய்' : 'Yes, Confirm'}</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  setMessages((prev) => [
                                    ...prev,
                                    {
                                      id: `c-${Date.now()}`,
                                      sender: 'ai',
                                      text: chatLang === 'ta' ? 'முன்பதிவு நடவடிக்கை ரத்து செய்யப்பட்டது.' : 'Action cancelled by user.',
                                      time: 'Just now',
                                    },
                                  ]);
                                }}
                                className="py-1.5 px-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-[11px] font-medium transition-colors"
                              >
                                {chatLang === 'ta' ? 'வேண்டாம்' : 'Cancel'}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Metadata & Audio controls */}
                  <div className="flex items-center gap-1.5 mt-1 px-1 text-[10px] text-slate-400">
                    <span>{m.time}</span>
                    {!isUser && m.provider && (
                      <>
                        <span>•</span>
                        <span className="text-emerald-700 font-medium">
                          {m.provider.includes('Google Gemini')
                            ? 'Google Gemini'
                            : m.provider.includes('APP_ENGINE')
                            ? 'App Engine'
                            : 'TNAU Fallback'}
                        </span>
                      </>
                    )}
                    {!isUser && !m.error && (
                      <button
                        type="button"
                        onClick={() => handleSpeak(m.text, m.id)}
                        className={`hover:text-emerald-700 p-0.5 rounded transition-colors ${
                          speakingMsgId === m.id ? 'text-emerald-600 font-bold' : ''
                        }`}
                        title="Read aloud"
                      >
                        {speakingMsgId === m.id ? (
                          <VolumeX className="w-3 h-3" />
                        ) : (
                          <Volume2 className="w-3 h-3" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 text-slate-500 text-xs py-2 px-3 bg-white rounded-2xl w-fit border border-slate-200 shadow-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
                <span>{chatLang === 'ta' ? 'செயலாக்குகிறது...' : 'Thinking & resolving action...'}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* D. LIVE SPEECH PREVIEW (WHEN LISTENING) */}
          {isListening && (
            <div className="bg-emerald-50/90 border-t border-emerald-200/80 px-3 py-1.5 text-[11px] text-emerald-800 flex items-center justify-between animate-pulse">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                <span>Listening ({chatLang === 'ta' ? 'தமிழ்' : 'English'})... Speak now</span>
              </div>
              <button
                type="button"
                onClick={toggleListening}
                className="text-[10px] text-red-600 hover:text-red-800 font-medium ml-2"
              >
                Stop
              </button>
            </div>
          )}

          {/* E. INPUT BAR */}
          <div className="p-2.5 px-3 bg-white border-t border-slate-200/80 flex items-center gap-2">
            {/* Mic Button */}
            <button
              type="button"
              onClick={toggleListening}
              className={`p-2 rounded-xl transition-all ${
                isListening
                  ? 'bg-red-500 text-white animate-bounce shadow-md shadow-red-500/30'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
              title={isListening ? 'Stop Listening' : 'Speak (Microphone)'}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            {/* Text Input */}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                chatLang === 'ta'
                  ? 'கேள்வி கேளுங்கள் அல்லது "வானிலை திற"...'
                  : 'Ask question or e.g. "Open weather"...'
              }
              className="flex-1 text-xs py-2 px-3 bg-slate-100/80 focus:bg-white border border-transparent focus:border-emerald-500 rounded-xl outline-hidden transition-all text-slate-800 placeholder:text-slate-400"
              disabled={isLoading}
            />

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="p-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white rounded-xl shadow-xs transition-colors shrink-0"
              title="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
