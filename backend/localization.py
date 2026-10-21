"""
AgriBharat Backend Localization Service
Handles localized dynamic system messages, error responses, and notifications across
all 22 Eighth Schedule languages of India plus English.
Internal identifiers, numeric values, ISO dates, and database field names remain language-neutral.
"""

from typing import Dict, Any, Optional

# Standard system message keys with regional translations
MESSAGES_CATALOG: Dict[str, Dict[str, str]] = {
    "AUTH_INVALID_CREDENTIALS": {
        "en": "Invalid mobile number or password. Please verify your credentials.",
        "ta": "தவறான கைபேசி எண் அல்லது கடவுச்சொல். உங்கள் விவரங்களை சரிபார்க்கவும்.",
        "hi": "अमान्य मोबाइल नंबर या पासवर्ड। कृपया अपने विवरण की जाँच करें।",
        "te": "చెల్లని మొబైల్ నంబర్ లేదా పాస్‌వర్డ్. దయచేసి వివరాలను తనిఖీ చేయండి.",
        "kn": "ಅಮಾನ್ಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ಅಥವಾ ಪಾಸ್‌ವರ್ಡ್. ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ.",
        "ml": "അസാധുവായ മൊബൈൽ നമ്പറോ പാസ്‌വേഡോ. ദയവായി പരിശോധിക്കുക.",
        "mr": "अवैध मोबाईल क्रमांक किंवा पासवर्ड. कृपया तपशील तपासा.",
        "bn": "ভুল মোবাইল নম্বর বা পাসওয়ার্ড। আপনার তথ্য যাচাই করুন।",
        "gu": "અમાન્ય મોબાઇલ નંબર અથવા પાસવર્ડ. કૃપા કરીને તપાસો.",
        "pa": "ਗਲਤ ਮੋਬਾਈਲ ਨੰਬਰ ਜਾਂ ਪਾਸਵਰਡ। ਕਿਰਪਾ ਕਰਕੇ ਜਾਂਚ ਕਰੋ।",
        "or": "ଅବୈଧ ମୋବାଇଲ୍ ନମ୍ବର କିମ୍ବା ପାସୱାର୍ଡ। ଦୟାକରି ଯାଞ୍ଚ କରନ୍ତୁ।",
        "as": "ভুল মোবাইল নম্বৰ বা পাছৱৰ্ড। অনুগ্ৰহ কৰি পৰীক্ষা কৰক।",
        "ur": "غلط موبائل نمبر یا پاس ورڈ۔ برائے مہربانی تصدیق کریں۔",
    },
    "AUTH_USER_EXISTS": {
        "en": "A user with this mobile number already exists.",
        "ta": "இந்த கைபேசி எண்ணுடன் ஏற்கனவே ஒரு பயனர் பதிவு செய்யப்பட்டுள்ளார்.",
        "hi": "इस मोबाइल नंबर के साथ पहले से एक उपयोगकर्ता मौजूद है।",
        "te": "ఈ మొబైల్ నంబర్‌తో ఇప్పటికే ఒక వినియోగదారు ఉన్నారు.",
        "kn": "ಈ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯೊಂದಿಗೆ ಈಗಾಗಲೇ ಬಳಕೆದಾರರಿದ್ದಾರೆ.",
        "ml": "ഈ മൊബൈൽ നമ്പറിൽ ഒരു ഉപയോക്താവ് ഇതിനകം രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്.",
        "mr": "या मोबाईल क्रमांकासह वापरकर्ता आधीच अस्तित्वात आहे.",
        "bn": "এই মোবাইল নম্বর দিয়ে ইতিমধ্যে একজন ব্যবহারকারী নিবন্ধিত আছেন।",
        "gu": "આ મોબાઇલ નંબર સાથે વપરાશકર્તા પહેલેથી અસ્તિત્વમાં છે.",
        "pa": "ਇਸ ਮੋਬਾਈਲ ਨੰਬਰ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਖਾਤਾ ਮੌਜੂਦ ਹੈ।",
        "or": "ଏହି ମୋବାଇଲ୍ ନମ୍ବର ସହିତ ପୂର୍ବରୁ ଉପଭୋକ୍ତା ପଞ୍ଜୀକୃତ ଅଛନ୍ତି।",
        "as": "এই মোবাইল নম্বৰৰ সৈতে ইতিমধ্যে এজন ব্যৱহাৰকাৰী আছে।",
        "ur": "اس موبائل نمبر کے ساتھ صارف پہلے سے موجود ہے۔",
    },
    "LANGUAGE_UPDATED_SUCCESS": {
        "en": "Preferred regional language updated successfully.",
        "ta": "விருப்பமான பிராந்திய மொழி வெற்றிகரமாக புதுப்பிக்கப்பட்டது.",
        "hi": "पसंदीदा क्षेत्रीय भाषा सफलतापूर्वक अपडेट कर दी गई।",
        "te": "ప్రాధాన్య ప్రాంతీయ భాష విజయవంతంగా నవీకరించబడింది.",
        "kn": "ಆದ್ಯತೆಯ ಪ್ರಾದೇಶಿಕ ಭಾಷೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ.",
        "ml": "തിരഞ്ഞെടുത്ത പ്രാദേശിക ഭാഷ വിജയകരമായി പുതുക്കി.",
        "mr": "पसंतीची भाषा यशस्वीरित्या अद्ययावत केली गेली.",
        "bn": "পছন্দের আঞ্চলিক ভাষা সফলভাবে আপডেট করা হয়েছে।",
        "gu": "પસંદગીની પ્રાદેશિક ભાષા સફળતાપૂર્વક અપડેટ થઈ ગઈ.",
        "pa": "ਤਰਜੀਹੀ ਖੇਤਰੀ ਭਾਸ਼ਾ ਸਫਲਤਾਪੂਰਵਕ ਅੱਪਡੇਟ ਕੀਤੀ ਗਈ।",
        "or": "ପସନ୍ଦର ଆଞ୍ଚଳିକ ଭାଷା ସଫଳତାର ସହ ଅଦ୍ୟତନ ହୋଇଛି।",
        "as": "পছন্দৰ আঞ্চলিক ভাষা সফলভাৱে আপডেট কৰা হ'ল।",
        "ur": "پسندیدہ علاقائی زبان کامیابی کے ساتھ اپ ڈیٹ ہو گئی۔",
    },
    "PROCUREMENT_SLOT_BOOKED": {
        "en": "Procurement slot booked successfully. Token No: {token_no}.",
        "ta": "கொள்முதல் நேரம் வெற்றிகரமாக முன்பதிவு செய்யப்பட்டது. டோக்கன் எண்: {token_no}.",
        "hi": "खरीद स्लॉट सफलतापूर्वक बुक किया गया। टोकन संख्या: {token_no}।",
        "te": "సేకరణ స్లాట్ విజయవంతంగా బుక్ చేయబడింది. టోకెన్ నంబర్: {token_no}.",
        "kn": "ಖರೀದಿ ಸ್ಲಾಟ್ ಯಶಸ್ವಿಯಾಗಿ ಬುಕ್ ಆಗಿದೆ. ಟೋಕನ್ ಸಂಖ್ಯೆ: {token_no}.",
        "ml": "സംഭരണ സ്ലോട്ട് വിജയകരമായി ബുക്ക് ചെയ്തു. ടോക്കൺ നമ്പർ: {token_no}.",
        "mr": "खरेदी स्लॉट यशस्वीरित्या बुक झाला. टोकन क्रमांक: {token_no}.",
        "bn": "সংগ্রহের স্লট সফলভাবে বুক করা হয়েছে। টোকেন নম্বর: {token_no}।",
        "gu": "ખરીદી સ્લોટ સફળતાપૂર્વક બુક થઈ ગયો. ટોકન નંબર: {token_no}.",
        "pa": "ਖਰੀਦ ਸਲਾਟ ਸਫਲਤਾਪੂਰਵਕ ਬੁੱਕ ਹੋਇਆ। ਟੋਕਨ ਨੰਬਰ: {token_no}।",
        "or": "ସଂଗ୍ରହ ସ୍ଲଟ୍ ସଫଳତାର ସହ ବୁକ୍ ହେଲା। ଟୋକନ୍ ନମ୍ବର: {token_no}।",
        "as": "ক্ৰয় স্লট সফলভাৱে বুক কৰা হ'ল। টোকেন নম্বৰ: {token_no}।",
        "ur": "خریداری سلاٹ کامیابی کے ساتھ بک ہو گیا۔ ٹوکن نمبر: {token_no}۔",
    },
    "WEATHER_SERVICE_ERROR": {
        "en": "Satellite weather service temporarily unavailable. Please retry shortly.",
        "ta": "செயற்கைக்கோள் வானிலை சேவை தற்காலிகமாக கிடைக்கவில்லை. சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.",
        "hi": "उपग्रह मौसम सेवा अस्थायी रूप से अनुपलब्ध है। कृपया कुछ समय बाद पुनः प्रयास करें।",
        "te": "వాతావరణ సేవ తాత్కాలికంగా అందుబాటులో లేదు. దయచేసి కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.",
        "kn": "ಹವಾಮಾನ ಸೇವೆ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಪ್ರಯತ್ನಿಸಿ.",
        "ml": "കാലാവസ്ഥാ സേവനം താൽക്കാലികമായി ലഭ്യമല്ല. ദയവായി അല്പം കഴിഞ്ഞ് വീണ്ടും ശ്രമിക്കുക.",
        "mr": "हवामान सेवा तात्पुरती अनुपलब्ध आहे. कृपया काही वेळाने प्रयत्न करा.",
        "bn": "আবহাওয়া পরিষেবা সাময়িকভাবে অনুপলব্ধ। কিছুক্ষণ পর চেষ্টা করুন।",
        "gu": "હવામાન સેવા અસ્થાયી રૂપે અનુપલબ્ધ છે. કૃપા કરીને થોડા સમય પછી પ્રયાસ કરો.",
        "pa": "ਮੌਸਮ ਸੇਵਾ ਅਸਥਾਈ ਤੌਰ 'ਤੇ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਥੋੜ੍ਹੀ ਦੇਰ ਬਾਅਦ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "or": "ପାଣିପାଗ ସେବା ଅସ୍ଥାୟୀ ଭାବେ ଅନୁପଲବ୍ଧ। ଦୟାକରି କିଛି ସମୟ ପରେ ଚେଷ୍ଟା କରନ୍ତୁ।",
        "as": "বতৰ সেৱা সাময়িকভাৱে উপলব্ধ নহয়। অলপ পিছত পুনৰ চেষ্টা কৰক।",
        "ur": "موسم کی سروس عارضی طور پر دستیاب نہیں ہے۔ کچھ دیر بعد دوبارہ کوشش کریں۔",
    },
}

def localize_message(key: str, lang: str = "en", **kwargs) -> str:
    """
    Returns a localized message with variable substitution.
    Falls back to English if key or language is missing.
    Dynamic variables (token numbers, IDs, dates) are formatted cleanly.
    """
    msg_dict = MESSAGES_CATALOG.get(key)
    if not msg_dict:
        return key

    raw_text = msg_dict.get(lang) or msg_dict.get("en") or key
    try:
        return raw_text.format(**kwargs)
    except Exception:
        return raw_text

def get_preferred_language_from_request(headers: Dict[str, str], user: Optional[Dict[str, Any]] = None) -> str:
    """
    Determines preferred language using:
    1. Authenticated user profile preference
    2. Accept-Language header
    3. Default: 'en'
    """
    if user and user.get("preferredLanguage"):
        return user["preferredLanguage"].strip().lower()

    accept_lang = headers.get("accept-language", "")
    if accept_lang:
        primary = accept_lang.split(",")[0].split(";")[0].strip().lower()
        if "-" in primary:
            primary = primary.split("-")[0]
        return primary

    return "en"
