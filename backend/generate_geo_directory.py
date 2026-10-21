"""
Script to generate the authoritative India Geographic Directory dataset.
Source: Local Government Directory (LGD), Ministry of Panchayati Raj, Government of India
& Open Government Data (OGD) Platform India (data.gov.in).
"""

import json
import os
import re

def slugify(text: str) -> str:
    # Lowercase, replace non-alphanumeric with underscore, strip leading/trailing underscores
    s = re.sub(r'[^a-zA-Z0-9]+', '_', text.lower()).strip('_')
    return s

DIRECTORY_METADATA = {
    "source": "Local Government Directory (LGD), Ministry of Panchayati Raj, Government of India & Census Administrative Atlas",
    "sourceUrl": "https://lgd.gov.in",
    "license": "Government Open Data License - India (GODL)",
    "version": "2026.1",
    "lastUpdated": "2026-03-01",
    "country": {
        "code": "IN",
        "iso3": "IND",
        "name": "India",
        "name_local": {
            "hi": "भारत",
            "ta": "இந்தியா",
            "te": "భారతదేశం",
            "kn": "ಭಾರತ",
            "ml": "ഭാരതം",
            "mr": "भारत",
            "gu": "ભારત",
            "bn": "ভারত",
            "pa": "ਭਾਰਤ"
        }
    },
    "totalStates": 28,
    "totalUnionTerritories": 8,
    "totalRegions": 36,
    "boundaryNotes": "Includes post-2020 administrative reorganizations (Ladakh and Jammu & Kashmir UTs, merged Dadra and Nagar Haveli and Daman and Diu UT, and newly gazetted districts across AP, MP, Chhattisgarh, Punjab, Rajasthan, etc.)."
}

RAW_DATA = [
    # ---------------- 28 STATES ----------------
    {
        "code": "IN-AP",
        "name": "Andhra Pradesh",
        "type": "state",
        "name_local": {"te": "ఆంధ్రప్రదేశ్", "hi": "आंध्र प्रदेश", "ta": "ஆந்திரப் பிரதேசம்"},
        "taluk_label": "Mandal",
        "districts": [
            "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla",
            "Chittoor", "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur",
            "Kakinada", "Krishna", "Kurnool", "Nandyal", "N.T.R.", "Palnadu",
            "Parvathipuram Manyam", "Prakasam", "S.P.S. Nellore", "Sri Sathya Sai",
            "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Y.S.R. Kadapa"
        ]
    },
    {
        "code": "IN-AR",
        "name": "Arunachal Pradesh",
        "type": "state",
        "name_local": {"hi": "अरुणाचल प्रदेश", "ta": "அருணாச்சலப் பிரதேசம்"},
        "taluk_label": "Circle / Sub-Division",
        "districts": [
            "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang",
            "Itanagar Capital Complex", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada",
            "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri",
            "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang",
            "Tawang", "Tirap", "Upper Dibang Valley", "Upper Siang", "Upper Subansiri",
            "West Kameng", "West Siang"
        ]
    },
    {
        "code": "IN-AS",
        "name": "Assam",
        "type": "state",
        "name_local": {"bn": "আসাম", "hi": "असम", "ta": "அசாம்"},
        "taluk_label": "Circle / Block",
        "districts": [
            "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo",
            "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao",
            "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup",
            "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur",
            "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur",
            "South Salmara-Mankachar", "Tamulpur", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Bajali"
        ]
    },
    {
        "code": "IN-BR",
        "name": "Bihar",
        "type": "state",
        "name_local": {"hi": "बिहार", "ta": "பீகார்"},
        "taluk_label": "Block / Anchal",
        "districts": [
            "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur",
            "Bhojpur", "Buxar", "Darbhanga", "East Champaran (Motihari)", "Gaya",
            "Gopalganj", "Jamui", "Jehanabad", "Kaimur (Bhabua)", "Katihar",
            "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani",
            "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia",
            "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar",
            "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"
        ]
    },
    {
        "code": "IN-CT",
        "name": "Chhattisgarh",
        "type": "state",
        "name_local": {"hi": "छत्तीसगढ़", "ta": "சத்தீஸ்கர்"},
        "taluk_label": "Tehsil / Block",
        "districts": [
            "Balod", "Baloda Bazar-Bhatapara", "Balrampur-Ramanujganj", "Bastar",
            "Bemetara", "Bijapur", "Bilaspur", "Dantewada (South Bastar)", "Dhamtari",
            "Durg", "Gariaband", "Gaurela-Pendra-Marwahi", "Janjgir-Champa", "Jashpur",
            "Kabirdham (Kawardha)", "Kanker (North Bastar)", "Khairagarh-Chhuikhadan-Gandai",
            "Kondagaon", "Korba", "Koriya", "Mahasamund", "Manendragarh-Chirmiri-Bharatpur",
            "Mohla-Manpur-Ambagarh Chowki", "Mungeli", "Narayanpur", "Raigarh",
            "Raipur", "Rajnandgaon", "Sarangarh-Bilaigarh", "Sakti", "Sukma",
            "Surajpur", "Surguja"
        ]
    },
    {
        "code": "IN-GA",
        "name": "Goa",
        "type": "state",
        "name_local": {"mr": "गोवा", "hi": "गोवा", "ta": "கோவா"},
        "taluk_label": "Taluka",
        "districts": [
            "North Goa", "South Goa"
        ]
    },
    {
        "code": "IN-GJ",
        "name": "Gujarat",
        "type": "state",
        "name_local": {"gu": "ગુજરાત", "hi": "गुजरात", "ta": "குஜராத்"},
        "taluk_label": "Taluka",
        "districts": [
            "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch",
            "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhumi Dwarka",
            "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch",
            "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal",
            "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar",
            "Tapi", "Vadodara", "Valsad"
        ]
    },
    {
        "code": "IN-HR",
        "name": "Haryana",
        "type": "state",
        "name_local": {"hi": "हरियाणा", "ta": "ஹரியானா"},
        "taluk_label": "Tehsil",
        "districts": [
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram",
            "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra",
            "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari",
            "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
        ]
    },
    {
        "code": "IN-HP",
        "name": "Himachal Pradesh",
        "type": "state",
        "name_local": {"hi": "हिमाचल प्रदेश", "ta": "இமாச்சலப் பிரதேசம்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu",
            "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"
        ]
    },
    {
        "code": "IN-JH",
        "name": "Jharkhand",
        "type": "state",
        "name_local": {"hi": "झारखंड", "ta": "ஜார்க்கண்ட்"},
        "taluk_label": "Block / Anchal",
        "districts": [
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum",
            "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara",
            "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu",
            "Ramgarh", "Ranchi", "Sahibganj", "Saraikela Kharsawan", "Simdega",
            "West Singhbhum"
        ]
    },
    {
        "code": "IN-KA",
        "name": "Karnataka",
        "type": "state",
        "name_local": {"kn": "ಕರ್ನಾಟಕ", "hi": "कर्नाटक", "ta": "கர்நாடகா"},
        "taluk_label": "Taluk",
        "districts": [
            "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
            "Bidar", "Chamarajanagara", "Chikkaballapura", "Chikkamagaluru", "Chitradurga",
            "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan",
            "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya",
            "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi",
            "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
        ]
    },
    {
        "code": "IN-KL",
        "name": "Kerala",
        "type": "state",
        "name_local": {"ml": "കേരളം", "hi": "केरल", "ta": "கேரளா"},
        "taluk_label": "Taluk",
        "districts": [
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam",
            "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta",
            "Thiruvananthapuram", "Thrissur", "Wayanad"
        ]
    },
    {
        "code": "IN-MP",
        "name": "Madhya Pradesh",
        "type": "state",
        "name_local": {"hi": "मध्य प्रदेश", "ta": "மத்தியப் பிரதேசம்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani",
            "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara",
            "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior",
            "Harda", "Hoshangabad (Narmadapuram)", "Indore", "Jabalpur", "Jhabua",
            "Katni", "Khandwa", "Khargone", "Maihar", "Mandla", "Mandsaur",
            "Mauganj", "Morena", "Narsinghpur", "Neemuch", "Niwari", "Panna",
            "Pandhurna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar",
            "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur",
            "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria",
            "Vidisha"
        ]
    },
    {
        "code": "IN-MH",
        "name": "Maharashtra",
        "type": "state",
        "name_local": {"mr": "महाराष्ट्र", "hi": "महाराष्ट्र", "ta": "மகாராஷ்டிரா"},
        "taluk_label": "Taluka",
        "districts": [
            "Ahmednagar (Ahilyanagar)", "Akola", "Amravati", "Chhatrapati Sambhajinagar (Aurangabad)",
            "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli",
            "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur",
            "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar",
            "Nashik", "Osmanabad (Dharashiv)", "Palghar", "Parbhani", "Pune",
            "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur",
            "Thane", "Wardha", "Washim", "Yavatmal"
        ]
    },
    {
        "code": "IN-MN",
        "name": "Manipur",
        "type": "state",
        "name_local": {"hi": "मणिपुर", "ta": "மணிப்பூர்"},
        "taluk_label": "Sub-Division",
        "districts": [
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West",
            "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl",
            "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"
        ]
    },
    {
        "code": "IN-ML",
        "name": "Meghalaya",
        "type": "state",
        "name_local": {"hi": "मेघालय", "ta": "மேகாலயா"},
        "taluk_label": "C&RD Block",
        "districts": [
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills",
            "Eastern West Khasi Hills", "North Garo Hills", "Ri-Bhoi", "South Garo Hills",
            "South West Garo Hills", "South West Khasi Hills", "West Garo Hills",
            "West Jaintia Hills", "West Khasi Hills"
        ]
    },
    {
        "code": "IN-MZ",
        "name": "Mizoram",
        "type": "state",
        "name_local": {"hi": "मिज़ोरम", "ta": "மிசோரம்"},
        "taluk_label": "Sub-Division / R.D. Block",
        "districts": [
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai",
            "Lunglei", "Mamit", "Saitual", "Serchhip", "Siaha"
        ]
    },
    {
        "code": "IN-NL",
        "name": "Nagaland",
        "type": "state",
        "name_local": {"hi": "नागालैंड", "ta": "நாகாலாந்து"},
        "taluk_label": "Circle / Sub-Division",
        "districts": [
            "Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung",
            "Mon", "Niuland", "Noklak", "Peren", "Phek", "Shamator",
            "Tseminyu", "Tuensang", "Wokha", "Zunheboto"
        ]
    },
    {
        "code": "IN-OR",
        "name": "Odisha",
        "type": "state",
        "name_local": {"hi": "ओडिशा", "ta": "ஒடிசா"},
        "taluk_label": "Tahasil / Block",
        "districts": [
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
            "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
            "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara",
            "Kendujhar (Keonjhar)", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
            "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur",
            "Subarnapur (Sonepur)", "Sundargarh"
        ]
    },
    {
        "code": "IN-PB",
        "name": "Punjab",
        "type": "state",
        "name_local": {"pa": "ਪੰਜਾਬ", "hi": "पंजाब", "ta": "பஞ்சாப்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
            "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
            "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga", "Muktsar",
            "Pathankot", "Patiala", "Rupnagar", "Sahibzada Ajit Singh Nagar (Mohali)",
            "Sangrur", "Shahid Bhagat Singh Nagar (Nawanshahr)", "Tarn Taran"
        ]
    },
    {
        "code": "IN-RJ",
        "name": "Rajasthan",
        "type": "state",
        "name_local": {"hi": "राजस्थान", "ta": "ராஜஸ்தான்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Ajmer", "Alwar", "Anupgarh", "Balotra", "Banswara", "Baran", "Barmer",
            "Beawar", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh",
            "Churu", "Dausa", "Deeg", "Dholpur", "Didwana-Kuchaman", "Dudu",
            "Dungarpur", "Ganganagar", "Gangapur City", "Hanumangarh", "Hindaun",
            "Jaipur", "Jaipur Rural", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu",
            "Jodhpur", "Jodhpur Rural", "Karauli", "Kekri", "Khairthal-Tijara",
            "Kota", "Kotputli-Behror", "Nagaur", "Neem Ka Thana", "Pali", "Phalodi",
            "Pratapgarh", "Rajsamand", "Salumbar", "Sanchore", "Sawai Madhopur",
            "Shahpura", "Sikar", "Sirohi", "Tonk", "Udaipur"
        ]
    },
    {
        "code": "IN-SK",
        "name": "Sikkim",
        "type": "state",
        "name_local": {"hi": "सिक्किम", "ta": "சிக்கிம்"},
        "taluk_label": "Sub-Division",
        "districts": [
            "Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"
        ]
    },
    {
        "code": "IN-TN",
        "name": "Tamil Nadu",
        "type": "state",
        "name_local": {"ta": "தமிழ்நாடு", "hi": "तमिलनाडु", "te": "తమిళనాడు"},
        "taluk_label": "Taluk",
        "districts": [
            "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
            "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
            "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
            "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
            "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
            "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
            "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
            "Vellore", "Viluppuram", "Virudhunagar"
        ]
    },
    {
        "code": "IN-TG",
        "name": "Telangana",
        "type": "state",
        "name_local": {"te": "తెలంగాణ", "hi": "तेलंगाना", "ta": "தெலங்கானா"},
        "taluk_label": "Mandal",
        "districts": [
            "Adilabad", "Bhadradri Kothagudem", "Hanamkonda", "Hyderabad", "Jagtial",
            "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy",
            "Karimnagar", "Khammam", "Kumuram Bheem Asifabad", "Mahabubabad",
            "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu",
            "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad",
            "Peddapalli", "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", "Siddipet",
            "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
        ]
    },
    {
        "code": "IN-TR",
        "name": "Tripura",
        "type": "state",
        "name_local": {"bn": "ত্রিপুরা", "hi": "त्रिपुरा", "ta": "திரிபுரா"},
        "taluk_label": "Sub-Division",
        "districts": [
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala",
            "South Tripura", "Unakoti", "West Tripura"
        ]
    },
    {
        "code": "IN-UP",
        "name": "Uttar Pradesh",
        "type": "state",
        "name_local": {"hi": "उत्तर प्रदेश", "ta": "உத்தரப் பிரதேசம்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya",
            "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur",
            "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor",
            "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
            "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar",
            "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur",
            "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj",
            "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri",
            "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri",
            "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar",
            "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur",
            "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli",
            "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur",
            "Unnao", "Varanasi"
        ]
    },
    {
        "code": "IN-UT",
        "name": "Uttarakhand",
        "type": "state",
        "name_local": {"hi": "उत्तराखंड", "ta": "உத்தரகண்ட்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar",
            "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal",
            "Udham Singh Nagar", "Uttarkashi"
        ]
    },
    {
        "code": "IN-WB",
        "name": "West Bengal",
        "type": "state",
        "name_local": {"bn": "পশ্চিমবঙ্গ", "hi": "पश्चिम बंगाल", "ta": "மேற்கு வங்காளம்"},
        "taluk_label": "Sub-Division / Block",
        "districts": [
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
            "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong",
            "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
            "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur",
            "Purulia", "South 24 Parganas", "Uttar Dinajpur"
        ]
    },

    # ---------------- 8 UNION TERRITORIES ----------------
    {
        "code": "IN-AN",
        "name": "Andaman and Nicobar Islands",
        "type": "union_territory",
        "name_local": {"hi": "अंडमान और निकोबार द्वीप समूह", "ta": "அந்தமான் நிக்கோபார் தீவுகள்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Nicobar", "North and Middle Andaman", "South Andaman"
        ]
    },
    {
        "code": "IN-CH",
        "name": "Chandigarh",
        "type": "union_territory",
        "name_local": {"pa": "ਚੰਡੀਗੜ੍ਹ", "hi": "चंडीगढ़", "ta": "சண்டிகர்"},
        "taluk_label": "Circle",
        "districts": [
            "Chandigarh"
        ]
    },
    {
        "code": "IN-DH",
        "name": "Dadra and Nagar Haveli and Daman and Diu",
        "type": "union_territory",
        "name_local": {"gu": "દાદરા અને નગર હવેલી અને દમણ અને દીવ", "hi": "दादरा और नगर हवेली एवं दमन और दीव", "ta": "தாத்ரா மற்றும் நகர் ஹவேலி மற்றும் தாமன் மற்றும் தியூ"},
        "taluk_label": "Taluka",
        "districts": [
            "Dadra and Nagar Haveli", "Daman", "Diu"
        ]
    },
    {
        "code": "IN-DL",
        "name": "Delhi",
        "type": "union_territory",
        "name_local": {"hi": "दिल्ली", "ta": "தில்லி"},
        "taluk_label": "Tehsil",
        "districts": [
            "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi",
            "North West Delhi", "Shahdara", "South Delhi", "South East Delhi",
            "South West Delhi", "West Delhi"
        ]
    },
    {
        "code": "IN-JK",
        "name": "Jammu and Kashmir",
        "type": "union_territory",
        "name_local": {"hi": "जम्मू और कश्मीर", "ta": "ஜம்மு காஷ்மீர்"},
        "taluk_label": "Tehsil",
        "districts": [
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal",
            "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch",
            "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian",
            "Srinagar", "Udhampur"
        ]
    },
    {
        "code": "IN-LA",
        "name": "Ladakh",
        "type": "union_territory",
        "name_local": {"hi": "लद्दाख", "ta": "லடாக்"},
        "taluk_label": "Sub-Division",
        "districts": [
            "Kargil", "Leh (Ladakh)"
        ]
    },
    {
        "code": "IN-LD",
        "name": "Lakshadweep",
        "type": "union_territory",
        "name_local": {"ml": "ലക്ഷദ്വീപ്", "hi": "लक्षद्वीप", "ta": "லட்சத்தீவு"},
        "taluk_label": "Sub-Division",
        "districts": [
            "Lakshadweep"
        ]
    },
    {
        "code": "IN-PY",
        "name": "Puducherry",
        "type": "union_territory",
        "name_local": {"ta": "புதுச்சேரி", "hi": "पुदुच्चेरी", "fr": "Pondichéry"},
        "taluk_label": "Taluk",
        "districts": [
            "Karaikal", "Mahe", "Puducherry", "Yanam"
        ]
    }
]

def build_dataset():
    states_list = []
    total_districts = 0

    for item in RAW_DATA:
        s_code = item["code"]
        s_id = slugify(item["name"])
        districts_processed = []

        for d_name in item["districts"]:
            d_id = slugify(d_name)
            districts_processed.append({
                "id": d_id,
                "code": f"{s_code}-{d_id[:4].upper()}",
                "name": d_name,
                "name_local": {},
                "stateCode": s_code,
                "stateId": s_id,
                "stateName": item["name"]
            })
            total_districts += 1

        states_list.append({
            "code": s_code,
            "id": s_id,
            "name": item["name"],
            "type": item["type"],
            "name_local": item.get("name_local", {}),
            "talukLabel": item.get("taluk_label", "Taluk / Village"),
            "districtCount": len(districts_processed),
            "districts": districts_processed
        })

    dataset = dict(DIRECTORY_METADATA)
    dataset["totalDistricts"] = total_districts
    dataset["states"] = states_list

    out_path = os.path.join(os.path.dirname(__file__), "data", "india_geographic_directory.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Generated {out_path}")
    print(f"Total States: {len([s for s in states_list if s['type'] == 'state'])}")
    print(f"Total Union Territories: {len([s for s in states_list if s['type'] == 'union_territory'])}")
    print(f"Total Regions: {len(states_list)}")
    print(f"Total Districts: {total_districts}")

if __name__ == "__main__":
    build_dataset()
