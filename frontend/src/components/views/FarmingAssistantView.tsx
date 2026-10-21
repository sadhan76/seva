import React, { useState, useEffect, useRef } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  Volume2,
  Pause,
  Play,
  Square,
  Mic,
  MicOff,
  Trash2,
  AlertCircle,
  Loader2,
  HelpCircle,
  Globe,
} from 'lucide-react';

import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import {
  sendChatMessageApi,
  getChatHistoryApi,
  clearChatHistoryApi,
  getChatStatusApi,
  type ChatMessageApiResponse,
  type ChatStatusApiResponse,
} from '../../services/api';
import {
  createSpeechPlaybackController,
  createSpeechRecognizer,
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
} from '../../utils/speech';
import type { ChatMessage, Language } from '../../types';
import { getLocaleMetadata } from '../../i18n/localeRegistry';
import { REGIONAL_LANGUAGE_OPTIONS } from '../../i18n/translations';

export const FarmingAssistantView: React.FC = () => {
  const { language: appLanguage } = useLanguage();
  const { user, token } = useAuth();

  // Assistant language state (supports all 23 languages, defaults to active app language)
  const [chatLang, setChatLang] = useState<Language>(() => appLanguage);

  useEffect(() => {
    setChatLang(appLanguage);
  }, [appLanguage]);

  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [geminiStatus, setGeminiStatus] = useState<ChatStatusApiResponse | null>(null);

  // Speech Synthesis (TTS) State
  const speechControllerRef = useRef(createSpeechPlaybackController());
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const [isSpeechPaused, setIsSpeechPaused] = useState(false);
  const [ttsSupported] = useState(isSpeechSynthesisSupported());

  // Speech Recognition (STT) State
  const [isListening, setIsListening] = useState(false);
  const [sttSupported] = useState(isSpeechRecognitionSupported());
  const [micError, setMicError] = useState<string | null>(null);
  const recognizerRef = useRef<any>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial welcome message supporting all 23 regional languages
  const getWelcomeMessage = (lang: Language): ChatMessage => {
    const meta = getLocaleMetadata(lang);
    let welcomeText = `Hello ${user?.name || 'Farmer'}! I am your AgriBharat AI Agricultural Assistant. Ask me anything about crop nutrition, real-time weather, foliar spray advisories, AWD irrigation, plant symptoms, or your mandi procurement bookings.`;
    if (lang === 'ta') {
      welcomeText = `வணக்கம் ${user?.name || 'விவசாயி'}! நான் உங்கள் 'அகிரிபாரத்' செயற்கை நுண்ணறிவு உதவியாளர். உங்கள் பயிர் சாகுபடி, நேரலை வானிலை, உரம், நீர் பாசனம், நோய் அறிகுறிகள் அல்லது நெல் கொள்முதல் டோக்கன் குறித்து எதையும் தமிழில் கேட்கலாம்.`;
    } else if (lang === 'hi') {
      welcomeText = `नमस्ते ${user?.name || 'किसान मित्र'}! मैं आपका एग्रीभारत एआई कृषि सहायक हूँ। अपनी फसल पोषण, मौसम पूर्वानुमान, छिड़काव सलाह, जल प्रबंधन, फसल रोग अथवा मंडी खरीद स्लॉट के बारे में कुछ भी पूछें।`;
    } else if (lang === 'te') {
      welcomeText = `నమస్కారం ${user?.name || 'రైతు మిత్రమా'}! నేను మీ అగ్రిభారత్ AI వ్యవసాయ సహాయకుడిని. పంట పోషణ, వాతావరణ సూచన, ఎరువులు, నీటిపారుదల మరియు మార్కెట్ సేకరణ గురించి ఏదైనా అడగండి.`;
    } else if (lang === 'kn') {
      welcomeText = `ನಮಸ್ಕಾರ ${user?.name || 'ರೈತ ಮಿತ್ರರೆ'}! ನಾನು ನಿಮ್ಮ ಅಗ್ರಿಭಾರತ್ AI ಕೃಷಿ ಸಹಾಯಕ. ಬೆಳೆ ಪೋಷಣೆ, ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ, ರಸಗೊಬ್ಬರ ಮತ್ತು ಮಂಡಿ ಖರೀದಿ ಬಗ್ಗೆ ನೀವು ಕೇಳಬಹುದು.`;
    } else if (lang === 'ml') {
      welcomeText = `നമസ്കാരം ${user?.name || 'കർഷക സുഹൃത്തേ'}! ഞാൻ നിങ്ങളുടെ അഗ്രിഭారത് AI കാർഷിക സഹായിയാണ്. വിള പരിപാലനം, കാലാവസ്ഥ, ജലസേചനം, മാണ്ഡി സംഭരണം എന്നിവയെക്കുറിച്ച് ചോദിക്കാം.`;
    } else if (lang === 'mr') {
      welcomeText = `नमस्कार ${user?.name || 'शेतकरी मित्र'}! मी आपला अॅग्रीभारत AI कृषी सल्लागार आहे. पीक पोषण, हवामान अंदाज, फवारणी, सिंचन आणि मंडी खरेदीबाबत विचारा.`;
    } else if (lang === 'bn') {
      welcomeText = `নমস্কার ${user?.name || 'কৃষক বন্ধু'}! আমি আপনার অ্যাগ্রিভারত এআই কৃষি সহকারী। ফসলের পুষ্টি, আবহাওয়ার পূর্বাভাস, স্প্রে পরামর্শ ও মান্ডি সংগ্রহ সম্পর্কে যে কোনো প্রশ্ন করতে পারেন।`;
    } else if (lang === 'gu') {
      welcomeText = `નમસ્તે ${user?.name || 'ખેડૂત મિત્ર'}! હું તમારો એગ્રીભારત AI કૃષિ સહાયક છું. પાક પોષણ, હવામાન, ખાતર, સિંચાઈ અને મંડી ખરીદી વિશે પૂછી શકો છો.`;
    } else if (lang === 'pa') {
      welcomeText = `ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ${user?.name || 'ਕਿਸਾਨ ਵੀਰੋ'}! ਮੈਂ ਤੁਹਾਡਾ ਐਗਰੀਭਾਰਤ AI ਖੇਤੀ ਸਹਾਇਕ ਹਾਂ। ਫ਼ਸਲ ਪੋਸ਼ਣ, ਮੌਸਮ ਦੀ ਭਵਿੱਖਬਾਣੀ, ਖਾਦਾਂ ਅਤੇ ਮੰਡੀ ਖਰੀਦ ਬਾਰੇ ਕੁਝ ਵੀ ਪੁੱਛੋ।`;
    } else if (lang === 'or') {
      welcomeText = `ନମସ୍କାର ${user?.name || 'କୃଷକ ଭାଇ'}! ମୁଁ ଆପଣଙ୍କ ଏଗ୍ରିଭାରତ AI କୃଷି ସହାୟକ। ଫସଲ ପୋଷଣ, ପାଣିପାଗ, ଜଳସେଚନ ଓ ମଣ୍ଡି ସଂଗ୍ରହ ବିଷୟରେ ପଚାରନ୍ତୁ।`;
    } else if (lang === 'as') {
      welcomeText = `নমস্কাৰ ${user?.name || 'কৃষক বন্ধু'}! মই আপোনাৰ এগ্ৰীভাৰত এআই কৃষি সহায়ক। শস্য পুষ্টি, বতৰৰ পূৰ্বাভাস, সাৰ আৰু মণ্ডী ক্ৰয় সম্পৰ্কে সোধক।`;
    } else if (lang === 'ur') {
      welcomeText = `خوش آمدید ${user?.name || 'کسان دوست'}! میں آپ کا ایگری بھارت اے آئی زرعی معاون ہوں۔ فصل کی دیکھ بھال، موسم، کھاد، اسمارٹ آبپاشی یا منڈی خریداری کے بارے میں اردو میں پوچھیں۔`;
    } else {
      welcomeText = `Welcome ${user?.name || 'Farmer'}! I am your AgriBharat AI Agricultural Assistant in ${meta.name} (${meta.nativeName}). Ask me anything about your farm, weather, fertilizer schedules, or mandi slots.`;
    }

    return {
      id: 'welcome-0',
      sender: 'ai',
      text: welcomeText,
      time: 'Just now',
      language: lang,
      isRealAI: false,
      provider: 'RULE_BASED_LOCAL',
      providerNotice:
        'Notice: Grounded in agricultural university agronomy reference data and live satellite weather.',
    };
  };

  // Load chat history from backend if authenticated
  const loadChatHistory = async () => {
    if (!token) {
      setMessages([getWelcomeMessage(chatLang)]);
      return;
    }

    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await getChatHistoryApi(token);
      if (res && res.messages && res.messages.length > 0) {
        const loaded: ChatMessage[] = [];
        res.messages.forEach((m) => {
          loaded.push({
            id: `u-${m.id}`,
            sender: 'user',
            text: m.userMessage,
            time: m.timestamp || 'Previous session',
            language: m.language,
          });
          loaded.push({
            id: `ai-${m.id}`,
            sender: 'ai',
            text: m.assistantReply,
            time: m.timestamp || 'Previous session',
            language: m.language,
            provider: m.provider,
            isRealAI: m.isRealAI,
            providerNotice: (m as any).providerNotice,
            followUpQuestion: m.followUpQuestion,
          });
        });
        setMessages(loaded);
        if (res.messages[0]?.conversationId) {
          setConversationId(res.messages[0].conversationId);
        }
      } else {
        setMessages([getWelcomeMessage(chatLang)]);
      }
    } catch (err: any) {
      console.warn('Could not load chat history:', err);
      setMessages([getWelcomeMessage(chatLang)]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check backend AI assistant status on load
    getChatStatusApi()
      .then((status) => {
        setGeminiStatus(status);
      })
      .catch((err) => {
        console.warn('Could not fetch chat status:', err);
      });
  }, []);

  useEffect(() => {
    loadChatHistory();
    // Cleanup any active speech on unmount
    return () => {
      speechControllerRef.current.stop();
      if (recognizerRef.current) {
        recognizerRef.current.stop();
      }
    };
  }, [token]);

  // Handle language switch
  const handleLanguageToggle = (lang: Language) => {
    setChatLang(lang);
    speechControllerRef.current.stop();
    setSpeakingMessageId(null);
    if (messages.length <= 1) {
      setMessages([getWelcomeMessage(lang)]);
    }
  };

  // Quick suggestions
  const promptSuggestions =
    chatLang === 'ta'
      ? [
          'இன்றைய வானிலை மற்றும் மருந்து தெளிக்க உகந்த நேரமா?',
          'தூர்கட்டும் பருவத்தில் எந்த உரம் இட வேண்டும்?',
          'என் கொள்முதல் டோக்கன் மற்றும் வரிசை நிலை என்ன?',
          'காய்ச்சலும் பாய்ச்சலும் (AWD) பாசனம் செய்வது எப்படி?',
          'இலையில் பழுப்பு நிற புள்ளிகள் உள்ளன - இது என்ன நோய்?',
        ]
      : chatLang === 'hi'
      ? [
          'आज का मौसम देखकर बताएं, क्या कीटनाशक छिड़काव का सही समय है?',
          'कल्ले फूटने (टिलरिंग) की अवस्था में कौन सा उर्वरक डालना चाहिए?',
          'मेरी मंडी खरीद टोकन व स्लॉट की वर्तमान स्थिति क्या है?',
          'कम पानी में धान की वैज्ञानिक सिंचाई (AWD) कैसे करें?',
          'पत्तियों पर भूरे धब्बे दिखाई दे रहे हैं - यह कौन सा रोग है?',
        ]
      : chatLang === 'te'
      ? [
          'నేటి వాతావరణం ప్రకారం మందు పిచికారీ చేయడానికి సరైన సమయమా?',
          'పిలకల దశలో వరికి ఏ ఎరువులు వేయాలి?',
          'నా మార్కెట్ సేకరణ టోకెన్ మరియు స్లాట్ స్థితి ఏమిటి?',
          'తక్కువ నీటితో ఆరుతడి (AWD) వరి సాగు ఎలా చేయాలి?',
          'ఆకులపై గోధుమ రంగు మచ్చలు ఉన్నాయి - ఇది ఏ తెగులు?',
        ]
      : chatLang === 'ur'
      ? [
          'کیا آج کا موسم دیکھ کر اسپرے کرنا محفوظ ہے؟',
          'شاخیں نکلنے کے مرحلے پر دھان کو کون سی کھاد ڈالنی چاہیے؟',
          'میری منڈی خریداری ٹوکن کی موجودہ حیثیت کیا ہے؟',
          'کم پانی میں اسمارٹ آبپاشی (AWD) کیسے کریں؟',
          'پتوں پر بھورے دھبے ہیں - یہ کون سی بیماری ہے؟',
        ]
      : [
          'Is foliar spraying safe according to today’s weather?',
          'What is the recommended fertilizer for tillering stage paddy?',
          'What is the status of my mandi procurement booking?',
          'How does Alternate Wetting & Drying (AWD) save water?',
          'Brown spindle shaped spots on paddy leaf - is it blast?',
        ];

  // Send message
  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    // Stop speaking if playing
    speechControllerRef.current.stop();
    setSpeakingMessageId(null);

    const userMsgId = `usr-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: 'user',
      text: query,
      time: 'Just now',
      language: chatLang,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response: ChatMessageApiResponse = await sendChatMessageApi(
        {
          message: query,
          language: chatLang,
          conversationId: conversationId || undefined,
          includeFarmContext: true,
        },
        token
      );

      if (response.conversationId) {
        setConversationId(response.conversationId);
      }

      const aiMsg: ChatMessage = {
        id: response.id || `ai-${Date.now()}`,
        sender: 'ai',
        text: response.reply,
        time: response.timestamp || 'Just now',
        language: response.language,
        provider: response.provider,
        isRealAI: response.isRealAI,
        providerNotice: response.providerNotice,
        followUpQuestion: response.followUpQuestion,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setErrorMsg(
        err.message ||
          (chatLang === 'ta'
            ? 'பதில் பெறுவதில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.'
            : 'Failed to retrieve response. Please check your connection and retry.')
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Text to Speech playback controls
  const handlePlayTTS = (msg: ChatMessage) => {
    if (speakingMessageId === msg.id && !isSpeechPaused) {
      // Pause
      speechControllerRef.current.pause();
      setIsSpeechPaused(true);
      return;
    }

    if (speakingMessageId === msg.id && isSpeechPaused) {
      // Resume
      speechControllerRef.current.resume();
      setIsSpeechPaused(false);
      return;
    }

    // Play new message
    speechControllerRef.current.stop();
    setSpeakingMessageId(msg.id);
    setIsSpeechPaused(false);

    speechControllerRef.current.speak(
      msg.text,
      msg.language || chatLang,
      () => {
        setSpeakingMessageId(msg.id);
        setIsSpeechPaused(false);
      },
      () => {
        setSpeakingMessageId(null);
        setIsSpeechPaused(false);
      },
      (errorText) => {
        setSpeakingMessageId(null);
        setIsSpeechPaused(false);
        console.warn('TTS Warning:', errorText);
      }
    );
  };

  const handleStopTTS = () => {
    speechControllerRef.current.stop();
    setSpeakingMessageId(null);
    setIsSpeechPaused(false);
  };

  // Speech to Text (Microphone)
  const toggleSpeechRecognition = () => {
    if (!sttSupported) {
      setMicError(
        chatLang === 'ta'
          ? 'உங்கள் உலாவியில் குரல் அறிதல் ஆதரிக்கப்படவில்லை (Google Chrome / Edge பரிந்துரைக்கப்படுகிறது).'
          : 'Speech recognition is not supported in this browser. Please use Chrome or Edge.'
      );
      return;
    }

    if (isListening) {
      recognizerRef.current?.stop();
      setIsListening(false);
      return;
    }

    setMicError(null);
    const recognizer = createSpeechRecognizer(
      chatLang,
      (transcribedText, isFinal) => {
        setInput(transcribedText);
        if (isFinal) {
          setIsListening(false);
        }
      },
      (errText) => {
        setMicError(errText);
        setIsListening(false);
      },
      () => {
        setIsListening(false);
      }
    );

    if (recognizer) {
      recognizerRef.current = recognizer;
      recognizer.start();
      setIsListening(true);
    }
  };

  // Clear chat history
  const handleClearHistory = async () => {
    if (
      !window.confirm(
        chatLang === 'ta'
          ? 'உரையாடல் வரலாற்றை அழிக்க விரும்புகிறீர்களா?'
          : 'Clear all conversation history with the assistant?'
      )
    )
      return;

    speechControllerRef.current.stop();
    setSpeakingMessageId(null);

    if (token) {
      try {
        await clearChatHistoryApi(token);
      } catch (e) {
        console.warn('Error clearing backend history:', e);
      }
    }
    setMessages([getWelcomeMessage(chatLang)]);
  };

  const latestAiMsg = [...messages].reverse().find((m) => m.sender === 'ai' && m.provider);
  const isGeminiLiveResponse = Boolean(latestAiMsg && latestAiMsg.isRealAI);

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] max-w-4xl mx-auto rounded-3xl bg-white border border-slate-200 shadow-xl overflow-hidden">
      {/* Top Header */}
      <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-emerald-50 via-teal-50 to-white flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-emerald-700 text-white flex items-center justify-center shadow-md shadow-emerald-700/20">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-black text-slate-900 text-sm sm:text-base">
                {chatLang === 'ta'
                  ? 'அக்ரிபாரத் AI உதவியாளர்'
                  : 'AgriBharat AI Agronomist'}
              </h2>
              {/* Honest provider badge */}
              {isGeminiLiveResponse ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 shadow-xs">
                  <Sparkles className="w-3 h-3 text-emerald-600 animate-pulse" />
                  Google Gemini Live
                </span>
              ) : geminiStatus?.geminiConfigured ? (
                <span
                  className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1"
                  title={latestAiMsg?.providerNotice || 'Operating in rule-based fallback mode'}
                >
                  <Sparkles className="w-3 h-3 text-amber-700" />
                  Fallback: TNAU Agronomic Engine
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-amber-700" />
                  Rule-Based Engine (Demo)
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              {chatLang === 'ta'
                ? 'தமிழ்நாடு வேளாண்மை & மண்டி கொள்முதல் நுண்ணறிவு'
                : 'Verified TNAU agronomic advisory, live weather & mandi bookings'}
            </p>
          </div>
        </div>

        {/* Language selector & actions */}
        <div className="flex items-center gap-2">
          {/* Language Toggle */}
          {/* Language Selector Dropdown */}
          <div className="flex items-center bg-slate-100 px-2 py-1 rounded-xl border border-slate-200 text-xs font-semibold">
            <Globe className="w-3.5 h-3.5 text-emerald-700 mr-1.5 shrink-0" />
            <select
              value={chatLang}
              onChange={(e) => handleLanguageToggle(e.target.value as Language)}
              className="bg-transparent text-slate-800 text-xs font-bold focus:outline-hidden cursor-pointer"
              title="Select Assistant Language / மொழி தேர்வு"
            >
              {REGIONAL_LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.code} value={opt.code}>
                  {opt.nativeName} ({opt.name})
                </option>
              ))}
            </select>
          </div>

          {/* Clear history */}
          <button
            onClick={handleClearHistory}
            title={chatLang === 'ta' ? 'வரலாற்றை அழி' : 'Clear Chat'}
            className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Dynamic Context Strip */}
      <div className="px-4 py-2 bg-emerald-900 text-emerald-100 text-[11px] font-medium flex items-center justify-between gap-2 overflow-x-auto">
        <div className="flex items-center gap-2 shrink-0">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>
            <strong>{chatLang === 'ta' ? 'இணைக்கப்பட்ட சுயவிவரம்:' : 'Grounded Farm Context:'}</strong>
          </span>
          <span className="bg-emerald-800/80 px-2 py-0.5 rounded text-[10px] font-mono">
            {user?.district || 'Thanjavur'}{user?.village ? ` (${user.village})` : ''} • {user?.primaryCrop || 'Samba Paddy'} • {user?.totalLandAcres ? `${user.totalLandAcres} Acres` : '3.5 Acres'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-emerald-200/80 shrink-0">
          <span>🛡️ {chatLang === 'ta' ? 'தனிப்பட்ட தரவுப் பாதுகாப்பு' : 'Strict Farmer Privacy'}</span>
        </div>
      </div>

      {/* Mic or General Warning alert */}
      {micError && (
        <div className="p-3 bg-rose-50 border-b border-rose-200 text-rose-800 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{micError}</span>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
        {messages.map((m) => {
          const isAi = m.sender === 'ai';
          const isPlayingThis = speakingMessageId === m.id;

          return (
            <div
              key={m.id}
              className={`flex ${isAi ? 'justify-start' : 'justify-end'}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed space-y-2 ${
                  isAi
                    ? 'bg-white text-slate-800 border border-slate-200 shadow-sm rounded-bl-xs'
                    : 'bg-emerald-700 text-white rounded-br-xs shadow-md shadow-emerald-700/10'
                }`}
              >
                {/* AI Sender Tag */}
                {isAi && (
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-1">
                    <span className="font-bold text-emerald-800 text-[11px] flex items-center gap-1">
                      <Bot className="w-3.5 h-3.5" />
                      AgriBharat AI
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {m.time}
                    </span>
                  </div>
                )}

                {/* Message Body */}
                <div className="whitespace-pre-wrap">{m.text}</div>

                {/* Provider transparency notice */}
                {isAi && m.id !== 'welcome-msg' && m.providerNotice && (
                  <div className="text-[10px] text-slate-500 bg-slate-50 border border-slate-200 rounded-lg p-2 mt-1.5 leading-relaxed">
                    <span className="font-semibold text-slate-700">
                      {m.isRealAI ? '🤖 Google Gemini:' : 'ℹ️ Mode:'}
                    </span>{' '}
                    {m.providerNotice}
                  </div>
                )}

                {/* Follow-up question highlight */}
                {isAi && m.followUpQuestion && (
                  <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-semibold flex items-start gap-1.5 mt-2">
                    <HelpCircle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                    <span>{m.followUpQuestion}</span>
                  </div>
                )}

                {/* AI Action Toolbar (Listen Button & Controls) */}
                {isAi && (
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                    <div className="flex items-center gap-1.5">
                      {/* TASK 3: Listen Button (TTS) with Play / Pause / Stop */}
                      {ttsSupported ? (
                        <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg p-0.5">
                          <button
                            onClick={() => handlePlayTTS(m)}
                            className="px-2 py-1 rounded hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 font-bold text-[11px] flex items-center gap-1 transition-colors"
                          >
                            {isPlayingThis ? (
                              isSpeechPaused ? (
                                <>
                                  <Play className="w-3 h-3 text-emerald-700 fill-emerald-700" />
                                  <span>{chatLang === 'ta' ? 'தொடர' : 'Resume'}</span>
                                </>
                              ) : (
                                <>
                                  <Pause className="w-3 h-3 text-amber-700 fill-amber-700" />
                                  <span>{chatLang === 'ta' ? 'நிறுத்து' : 'Pause'}</span>
                                </>
                              )
                            ) : (
                              <>
                                <Volume2 className="w-3.5 h-3.5 text-emerald-700" />
                                <span>{chatLang === 'ta' ? 'கேளுங்கள்' : 'Listen'}</span>
                              </>
                            )}
                          </button>

                          {isPlayingThis && (
                            <button
                              onClick={handleStopTTS}
                              title="Stop Audio"
                              className="p-1 rounded hover:bg-rose-50 text-rose-600"
                            >
                              <Square className="w-3 h-3 fill-rose-600" />
                            </button>
                          )}
                        </div>
                      ) : (
                        <span className="text-[10px] text-slate-400">
                          Audio speech unavailable
                        </span>
                      )}
                    </div>

                    <span className="text-[10px] text-slate-400 italic">
                      {m.provider === 'RULE_BASED_LOCAL'
                        ? 'TNAU Verified Rules'
                        : m.provider}
                    </span>
                  </div>
                )}

                {/* User Message Timestamp */}
                {!isAi && (
                  <span className="text-[10px] text-emerald-100 block text-right">
                    {m.time}
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {/* Typing Loading Indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl p-4 text-xs text-slate-500 flex items-center gap-2 shadow-xs">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-700" />
              <span>
                {chatLang === 'ta'
                  ? 'பதில் தயாரிக்கப்படுகிறது (வானிலை & பண்ணை தரவு சரிபார்க்கப்படுகிறது)...'
                  : 'Analyzing farming context, weather & agronomic guidance...'}
              </span>
            </div>
          </div>
        )}

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-300 text-rose-800 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-4 py-2 bg-white border-t border-slate-100 flex items-center gap-2 overflow-x-auto">
        <span className="text-[11px] font-bold text-slate-400 shrink-0 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-emerald-600" />
          {chatLang === 'ta' ? 'பரிந்துரைகள்:' : 'Suggestions:'}
        </span>
        {promptSuggestions.map((sug, i) => (
          <button
            key={i}
            onClick={() => handleSend(sug)}
            className="text-xs text-slate-700 hover:text-emerald-800 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-300 border border-slate-200 rounded-xl px-3 py-1 transition-all shrink-0 text-left font-medium"
          >
            {sug}
          </button>
        ))}
      </div>

      {/* Input bar with Mic (STT) and Send */}
      <div className="p-3 sm:p-4 bg-white border-t border-slate-200 space-y-2">
        {/* Listening Indicator with Transcript Preview */}
        {isListening && (
          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
              <span className="font-bold">
                {chatLang === 'ta'
                  ? 'குரலைக் கேட்கிறது... (தமிழில் பேசவும்):'
                  : 'Listening... (Speak clearly into microphone):'}
              </span>
            </div>
            <button
              onClick={toggleSpeechRecognition}
              className="text-[11px] font-bold text-rose-700 underline"
            >
              Done / Stop
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          {/* TASK 4: Microphone button (Speech-to-text) */}
          <button
            type="button"
            onClick={toggleSpeechRecognition}
            title={
              isListening
                ? 'Stop listening'
                : chatLang === 'ta'
                ? 'குரல் மூலம் பேச (தமிழ்)'
                : 'Speak query via microphone'
            }
            className={`p-3 rounded-2xl border transition-all ${
              isListening
                ? 'bg-rose-600 text-white border-rose-700 shadow-md animate-pulse ring-2 ring-rose-400'
                : 'bg-slate-50 hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 border-slate-200'
            }`}
          >
            {isListening ? (
              <MicOff className="w-5 h-5 text-white" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={
              isListening
                ? chatLang === 'ta'
                  ? 'உங்கள் குரல் இங்கு தட்டச்சு செய்யப்படுகிறது...'
                  : 'Transcribing your speech in real time...'
                : chatLang === 'ta'
                ? 'பயிர் சாகுபடி, வானிலை, உரம், கொள்முதல் பற்றி கேளுங்கள்...'
                : 'Ask anything about crops, soil, pests, weather, or procurement...'
            }
            className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
          />

          {/* Send Button */}
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="p-3 bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white rounded-2xl shadow-md shadow-emerald-700/20 transition-all flex items-center justify-center shrink-0"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Small Notice at Bottom */}
        <div className="flex items-center justify-between text-[10px] text-slate-400 px-1">
          <span>
            {chatLang === 'ta'
              ? '🗣️ பேச்சு அறிதல் மற்றும் ஒலிவாசிப்பு வசதியுடன் கூடியது'
              : '🗣️ Supports Tamil & English speech recognition and audio playback'}
          </span>
          <span className="hidden sm:inline">
            Government of Tamil Nadu Agriculture Reference Catalog
          </span>
        </div>
      </div>
    </div>
  );
};
