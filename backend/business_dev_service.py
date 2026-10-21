"""
BUSINESS DEVELOPMENT SERVICE (AGRI ENTREPRENEURSHIP & VALUE-ADDED PRODUCTS)
Namma Vivasayi AI Platform

This service provides:
1. Agri Entrepreneurship matching engine, enterprise blueprints, startup/opex costing,
   and 8-step business planning wizard persistence.
2. Value-Added Products catalog organized by raw material and processing method,
   with authoritative university/institute references (TNAU PHTC, NIFTEM-T, CFTRI, TCRS).
3. Precision costing & profitability calculator with entered or sourced yield loss,
   processing waste, and byproduct revenue recovery.
4. Non-guarantee disclaimers and links to official training, incubation, and government schemes.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database import get_farmer_business_plans_collection
from models import (
    BilingualText,
    BusinessIdeaItem,
    BusinessIdeaMatchRequest,
    BusinessIdeaMatchResponse,
    BusinessPlanWizardData,
    BusinessPlanCalculationResult,
    BusinessPlanModel,
    BusinessPlanCreateRequest,
    BusinessPlanUpdateRequest,
    BusinessPlanCalculationRequest,
    ValueAdditionProductBlueprint,
    ValueAdditionCalculationRequest,
    ValueAdditionCalculationResponse,
)

logger = logging.getLogger("business_dev_service")

# ----------------------------------------------------------------------------
# VERIFIED AGRI-ENTREPRENEURSHIP BLUEPRINTS (TNAU DABD / EDII-TN / ACABC)
# ----------------------------------------------------------------------------

ENTREPRENEURSHIP_BLUEPRINTS: List[Dict[str, Any]] = [
    {
        "ideaId": "bio_inputs_lab",
        "title": {
            "en": "Village Organic Bio-Inputs & Microbial Production Lab",
            "ta": "கிராமப்புற இயற்கை உரம் மற்றும் நுண்ணுயிர் உற்பத்தி கூடம்"
        },
        "category": "Organic Inputs & Bio-fertilizers",
        "budgetRangeMin": 50000.0,
        "budgetRangeMax": 250000.0,
        "matchingInterests": ["organic_inputs", "sustainable_farming", "soil_health"],
        "matchingSkills": ["farming_experience", "technical_operations"],
        "recommendedProduce": ["Cow Dung / Urine", "Crop Residues", "Neem Seed", "Paddy Straw"],
        "recommendedDistricts": ["Salem", "Erode", "Coimbatore", "Thanjavur", "Dindigul", "All"],
        "suitabilitySummary": {
            "en": "Ideal for progressive farmers with livestock access. Produce Trichoderma viride, Pseudomonas fluorescens, Panchagavya, and enriched vermicompost for neighbouring farms.",
            "ta": "கால்நடை வளர்க்கும் விவசாயிகளுக்கு சிறந்தது. ட்ரைக்கோடெர்மா, சூடோமோனாஸ், பஞ்சகவ்யா மற்றும் மண்புழு உரம் தயாரித்து உள்ளூர் விவசாயிகளுக்கு விற்பனை செய்யலாம்."
        },
        "estimatedStartupCapex": {
            "Autoclave & Laminar Airflow (Mini)": 65000.0,
            "HDPE Fermentation Drums (10 x 200L)": 18000.0,
            "Shade Net Fermentation Shed (300 sq.ft)": 35000.0,
            "Sealing Machine & Packaging Tools": 12000.0,
            "Initial Mother Cultures & Glassware": 15000.0,
            "Udyam MSME & FCO Licensing Consultation": 5000.0
        },
        "estimatedMonthlyOpex": {
            "Mother Culture Media & Nutrient Agar": 6000.0,
            "Cow Dung, Urine & Organic Raw Base": 12000.0,
            "Packaging Bottles, Pouches & Custom Labels": 8000.0,
            "Part-time Skilled Assistant Labour": 10000.0,
            "Electricity & Clean Water Utilities": 3500.0,
            "Local Delivery & Promotion": 3000.0
        },
        "typicalBreakevenMonths": "6 - 9 months",
        "targetCustomers": [
            {"en": "Organic certified and natural farmers within 20 km radius", "ta": "20 கி.மீ சுற்றளவிலுள்ள இயற்கை விவசாயிகள்"},
            {"en": "Local Farmer Producer Organisations (FPOs) bulk procurement", "ta": "உள்ளூர் உழவர் உற்பத்தியாளர் நிறுவனங்கள் (FPO)"},
            {"en": "Horticulture nursery owners and urban terrace gardeners", "ta": "தோட்டக்கலை நர்சரிகள் மற்றும் மாடித் தோட்ட ஆர்வலர்கள்"}
        ],
        "requiredSkillsAndEquipment": [
            {"en": "Aseptic handling and culture sub-culturing (KVK training)", "ta": "நுண்ணுயிர் வளர்ப்பு மற்றும் பாதுகாப்பு முறை பயிற்சி (KVK)"},
            {"en": "Autoclave, pH meter, weighing balance, airtight HDPE drums", "ta": "ஆட்டோகிளேவ், pH மீட்டர், எடை இயந்திரம், HDPE டிரம்கள்"}
        ],
        "officialResources": [
            {
                "title": "TNAU Directorate of Agri-Business Development (DABD) Incubation",
                "department": "Tamil Nadu Agricultural University, Coimbatore",
                "phone": "+91-422-6611310",
                "email": "business@tnau.ac.in",
                "link": "https://agritech.tnau.ac.in/dabd/",
                "eligibilityNote": "Open to TN agri graduates, diploma holders, and rural farm youth."
            },
            {
                "title": "Agri-Clinics and Agri-Business Centres (ACABC) Scheme",
                "department": "MANAGE / Ministry of Agriculture & Farmers Welfare, GoI",
                "phone": "1800-425-1999",
                "email": "acabc@manage.gov.in",
                "link": "https://www.agriclinics.net/",
                "eligibilityNote": "Provides 36% composite subsidy (44% for women/SC/ST) on bankable projects up to ₹20 Lakhs."
            }
        ],
        "statutoryRequirements": [
            {"en": "Udyam MSME Registration (Free online at udyamregistration.gov.in)", "ta": "உத்யம் MSME பதிவு (இலவச ஆன்லைன் பதிவு)"},
            {"en": "Fertilizer Control Order (FCO) Commercial Bio-fertilizer License from Dept of Agriculture", "ta": "வேளாண்மை துறையிடமிருந்து உரக் கட்டுப்பாட்டு ஆணை (FCO) உரிமம்"},
            {"en": "Pollution Control Board Green Category White Certificate / Consent to Establish", "ta": "மாசு கட்டுப்பாட்டு வாரிய பசுமை சான்றிதழ்"}
        ]
    },
    {
        "ideaId": "custom_hiring_centre",
        "title": {
            "en": "Village Farm Machinery Custom Hiring Centre (CHC)",
            "ta": "கிராமப்புற பண்ணை இயந்திரங்கள் வாடகை சேவை மையம்"
        },
        "category": "Farm Mechanisation & Custom Hiring",
        "budgetRangeMin": 300000.0,
        "budgetRangeMax": 1500000.0,
        "matchingInterests": ["machinery_rental", "mechanisation", "service_enterprise"],
        "matchingSkills": ["mechanical", "technical_operations"],
        "recommendedProduce": ["Paddy", "Groundnut", "Sugarcane", "Millets", "Cotton", "All"],
        "recommendedDistricts": ["Salem", "Villupuram", "Thanjavur", "Tiruvarur", "Madurai", "All"],
        "suitabilitySummary": {
            "en": "Provide hourly/daily tractor attachments, power weeders, brush cutters, and drone spraying to smallholders facing rural farm labour shortages.",
            "ta": "வேளாண் தொழிலாளர் பற்றாக்குறை உள்ள பகுதிகளில் டிராக்டர் உபகரணங்கள், பவர் வீடர் மற்றும் ட்ரோன் தெளிப்பான் வாடகை மையம்."
        },
        "estimatedStartupCapex": {
            "Power Tiller / Mini Tractor (15-24 HP)": 380000.0,
            "Rotavator & Disc Plough Implements": 110000.0,
            "Self-Propelled Power Weeder (7 HP)": 55000.0,
            "Battery / Petrol Backpack Sprayers (4 units)": 24000.0,
            "Agri Drone (Optional leased / subsidy model)": 450000.0,
            "Implement Storage Shed & Tools": 60000.0
        },
        "estimatedMonthlyOpex": {
            "Diesel / Fuel Consumption": 25000.0,
            "Machine Operators Wages (2 operators)": 28000.0,
            "Routine Maintenance, Lubricants & Spares": 8500.0,
            "Equipment Insurance & Road Tax": 4500.0,
            "Booking Mobile App & Local Marketing": 2000.0
        },
        "typicalBreakevenMonths": "14 - 18 months",
        "targetCustomers": [
            {"en": "Small and marginal farmers (< 2 acres) unable to purchase heavy tractors", "ta": "சொந்தமாக டிராக்டர் வாங்க இயலாத சிறு-குறு விவசாயிகள்"},
            {"en": "Neighbouring village clusters during peak sowing and harvest windows", "ta": "விதைப்பு மற்றும் அறுவடை காலத்தில் பக்கத்து கிராம விவசாயிகள்"}
        ],
        "requiredSkillsAndEquipment": [
            {"en": "Tractor driving license, machinery servicing, implement hitching", "ta": "டிராக்டர் ஓட்டுநர் உரிமம் மற்றும் பராமரிப்பு பயிற்சி"},
            {"en": "Agricultural Machinery Testing Centre certified equipment", "ta": "மத்திய அரசின் அங்கீகரிக்கப்பட்ட பண்ணை இயந்திரங்கள்"}
        ],
        "officialResources": [
            {
                "title": "Sub-Mission on Agricultural Mechanization (SMAM) - CHC Subsidy",
                "department": "Agricultural Engineering Department (AED), Government of Tamil Nadu",
                "phone": "+91-44-29530188",
                "email": "aed@tn.gov.in",
                "link": "https://agriengineering.tn.gov.in/",
                "eligibilityNote": "40% to 50% capital subsidy for establishing Custom Hiring Centres in rural blocks."
            },
            {
                "title": "Agriculture Infrastructure Fund (AIF)",
                "department": "Ministry of Agriculture & Farmers Welfare, GoI",
                "phone": "011-23381012",
                "email": "aif-support@gov.in",
                "link": "https://agriinfra.dac.gov.in/",
                "eligibilityNote": "3% interest subvention on term loans up to ₹2 Crores for farm machinery hubs."
            }
        ],
        "statutoryRequirements": [
            {"en": "Commercial Vehicle Fitness & Comprehensive Machinery Insurance", "ta": "வாகன தகுதி சான்றிதழ் மற்றும் இயந்திர காப்பீடு"},
            {"en": "RTO Registration for road travel implements", "ta": "சாலைப் போக்குவரத்து RTO பதிவு"},
            {"en": "DGCA Remote Pilot Certificate if offering Drone spraying services", "ta": "ட்ரோன் தெளிப்பிற்கு DGCA பைலட் சான்றிதழ்"}
        ]
    },
    {
        "ideaId": "solar_dehydration_unit",
        "title": {
            "en": "Solar Dehydration & Farm Produce Processing Unit",
            "ta": "சூரிய கூடார உலர்த்தி மற்றும் மதிப்புக் கூட்டல் மையம்"
        },
        "category": "Horticulture Preservation & Drying",
        "budgetRangeMin": 80000.0,
        "budgetRangeMax": 400000.0,
        "matchingInterests": ["solar_drying", "value_addition", "horticulture"],
        "matchingSkills": ["farming_experience", "packaging", "marketing_sales"],
        "recommendedProduce": ["Tomato", "Banana", "Moringa", "Chillies", "Tapioca", "Turmeric"],
        "recommendedDistricts": ["Salem", "Dharmapuri", "Theni", "Dindigul", "Tiruppur", "All"],
        "suitabilitySummary": {
            "en": "Protect against tomato and vegetable price crashes by converting surplus crops into sun-protected dehydrated flakes, moringa powder, and dried fruit crisps.",
            "ta": "தக்காளி, முருங்கை, வாழை போன்ற விளைபொருட்களின் விலை வீழ்ச்சியைத் தடுத்து உலர்த்தி நீண்ட நாள் சந்தைப்படுத்துதல்."
        },
        "estimatedStartupCapex": {
            "Polyhouse Solar Tunnel Dryer (400 sq.ft, 100 kg batch)": 140000.0,
            "Stainless Steel SS304 Trays (50 units)": 35000.0,
            "Vegetable Slicer & Blanching Vessel (Food Grade)": 28000.0,
            "Moisture Meter (Grain & Veg probe)": 8500.0,
            "Continuous Nitrogen Flushing Band Sealer": 32000.0,
            "FSSAI Registration & Food Testing Kit": 6500.0
        },
        "estimatedMonthlyOpex": {
            "Fresh Farm Produce Sourcing (Seasonal surplus)": 20000.0,
            "Food-Grade Foil Pouch Packaging & Silica Pouches": 7500.0,
            "Sanitation, Citric Acid Blanching & Potable Water": 3000.0,
            "Manual Sorting & Slicing Labour": 12000.0,
            "Electricity & Solar Fan Battery Maintenance": 2500.0,
            "Courier & Distribution Logistics": 5000.0
        },
        "typicalBreakevenMonths": "8 - 12 months",
        "targetCustomers": [
            {"en": "Instant food mix manufacturers, spice blenders and bakeries", "ta": "மசாலா நிறுவனங்கள் மற்றும் உடனடி உணவு உற்பத்தியாளர்கள்"},
            {"en": "Health food stores, supermarket chains and direct consumers", "ta": "இயற்கை அங்காடி மற்றும் சூப்பர் மார்க்கெட் சங்கிலிகள்"},
            {"en": "Export aggregators for moringa powder and dry chillies", "ta": "முருங்கை இலை மற்றும் காய்ந்த மிளகாய் ஏற்றுமதியாளர்கள்"}
        ],
        "requiredSkillsAndEquipment": [
            {"en": "Blanching temperature control, hygienic tray loading, moisture measurement", "ta": "பிளான்சிங் வெப்பநிலை கட்டுப்பாடு மற்றும் சுகாதாரமான உலர்த்தல் முறை"},
            {"en": "Solar tunnel dryer, SS304 slicer, band sealer", "ta": "சூரிய உலர்த்தி கூடம், காய்கறி நறுக்கும் இயந்திரம், பேக்கிங் சீலர்"}
        ],
        "officialResources": [
            {
                "title": "TNAU Post Harvest Technology Centre (PHTC)",
                "department": "Agricultural Engineering College & Research Institute, Coimbatore",
                "phone": "+91-422-6611268",
                "email": "phtc@tnau.ac.in",
                "link": "https://agritech.tnau.ac.in/post_harvest/pht_index.html",
                "eligibilityNote": "Conducts monthly 2-day hands-on solar drying & dehydration entrepreneurship training."
            },
            {
                "title": "PM Formalisation of Micro food processing Enterprises (PMFME)",
                "department": "Ministry of Food Processing Industries, GoI / TNSFAC",
                "phone": "+91-44-22253744",
                "email": "pmfme.tn@gov.in",
                "link": "https://pmfme.mofpi.gov.in/",
                "eligibilityNote": "35% credit-linked capital subsidy up to ₹10 Lakhs for individual agri-food processing."
            }
        ],
        "statutoryRequirements": [
            {"en": "FSSAI Food Safety Basic Registration (Form A) / State License (Form B)", "ta": "FSSAI உணவு பாதுகாப்பு பதிவு / மாநில உரிமம்"},
            {"en": "Pesticide residue and microbial limit water testing report from NABL lab", "ta": "NABL ஆய்வகத்தின் குடிநீர் பரிசோதனை அறிக்கை"},
            {"en": "Nutrition facts and shelf-life declaration on retail pouches", "ta": "பாக்கெட்டுகளில் ஊட்டச்சத்து மற்றும் காலாவதி தேதி அச்சிடுதல்"}
        ]
    },
    {
        "ideaId": "mini_cattle_feed_mill",
        "title": {
            "en": "Village Cattle Feed & Mineral Mixture Compounding Mill",
            "ta": "கிராமப்புற மாட்டுத் தீவனம் மற்றும் தாது உப்பு கலவை ஆலை"
        },
        "category": "Animal Husbandry & Feed Compounding",
        "budgetRangeMin": 150000.0,
        "budgetRangeMax": 600000.0,
        "matchingInterests": ["cattle_feed", "dairy_support", "value_addition"],
        "matchingSkills": ["farming_experience", "technical_operations"],
        "recommendedProduce": ["Maize", "Groundnut Cake", "Paddy Straw / Bran", "Cottonseed"],
        "recommendedDistricts": ["Salem", "Erode", "Namakkal", "Dindigul", "Vellore", "All"],
        "suitabilitySummary": {
            "en": "Utilise farm byproducts (maize, groundnut cake, bran) to produce balanced dairy concentrate mash and mineral blocks for local milk producers.",
            "ta": "சோளம், கடலை புண்ணாக்கு, தவிடு கொண்டு சமச்சீர் அடர் தீவனம் மற்றும் தாது உப்பு கட்டிகள் தயாரித்தல்."
        },
        "estimatedStartupCapex": {
            "Feed Pulverizer & Hammer Mill (5 HP)": 65000.0,
            "Ribbon Batch Mixer (200 kg capacity)": 75000.0,
            "Bag Stitching Machine & Platform Scale": 18000.0,
            "Storage Shed Concrete Flooring (400 sq.ft)": 50000.0,
            "Working Capital for Raw Ingredients (Maize, Salt, Calcite)": 80000.0
        },
        "estimatedMonthlyOpex": {
            "Maize, Broken Rice & Pulses Husk": 65000.0,
            "Oil Cakes (Groundnut, Cottonseed, Soya)": 55000.0,
            "Mineral Mixture Premix, Calcite & Salt": 12000.0,
            "Woven HDPE Bags (50 kg capacity)": 8000.0,
            "Mill Operator & Loading Labour": 18000.0,
            "Electricity (Three-Phase)": 6500.0
        },
        "typicalBreakevenMonths": "9 - 14 months",
        "targetCustomers": [
            {"en": "Local dairy farmers and Aavin primary milk cooperative society members", "ta": "உள்ளூர் கறவை மாடு வளர்ப்போர் மற்றும் ஆவின் பால் உற்பத்தியாளர்கள்"},
            {"en": "Commercial goat and sheep fattening farms in the taluk", "ta": "வட்டார ஆடு வளர்ப்பு பண்ணையாளர்கள்"}
        ],
        "requiredSkillsAndEquipment": [
            {"en": "Feed formulation balancing (CP % and TDN %), moisture checking", "ta": "தீவன ஊட்டச்சத்து விகிதம் கணக்கீடு மற்றும் ஈரப்பதம் சரிபார்த்தல்"},
            {"en": "Hammer mill, ribbon mixer, heavy-duty bag closer", "ta": "அரைவை இயந்திரம், மிக்சர், பை தைக்கும் இயந்திரம்"}
        ],
        "officialResources": [
            {
                "title": "TANUVAS Feed Technology & Nutrition Division",
                "department": "Tamil Nadu Veterinary and Animal Sciences University, Chennai",
                "phone": "+91-44-25551586",
                "email": "dirres@tanuvas.org.in",
                "link": "https://tanuvas.ac.in/",
                "eligibilityNote": "Offers feed formulation short courses and feed testing analytical services."
            },
            {
                "title": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
                "department": "Department of Animal Husbandry & Dairying, GoI",
                "phone": "011-23384501",
                "email": "ahidf-dadf@gov.in",
                "link": "https://ahidf.udyamimitra.in/",
                "eligibilityNote": "3% interest subvention for establishing animal feed manufacturing plants."
            }
        ],
        "statutoryRequirements": [
            {"en": "BIS Specification IS 2052: Compound Cattle Feeds Compliance", "ta": "BIS IS 2052 மாட்டுத் தீவன தர வழிகாட்டுதல்"},
            {"en": "Commercial Local Body Trade License & Electricity Board 3-Phase Sanction", "ta": "உள்ளாட்சி தொழில் உரிமம் மற்றும் 3-பேஸ் மின் இணைப்பு"}
        ]
    },
    {
        "ideaId": "horti_seedling_nursery",
        "title": {
            "en": "Pro-tray Vegetable Seedling Nursery & Shade Net Enterprise",
            "ta": "நிழல்வலை குடில் காய்கறி நாற்றங்கால் தொழில்"
        },
        "category": "Horticultural Nursery & Planting Material",
        "budgetRangeMin": 100000.0,
        "budgetRangeMax": 450000.0,
        "matchingInterests": ["nursery", "horticulture", "organic_inputs"],
        "matchingSkills": ["farming_experience", "technical_operations", "marketing_sales"],
        "recommendedProduce": ["Tomato", "Chilli", "Brinjal", "Cabbage", "Watermelon"],
        "recommendedDistricts": ["Salem", "Krishnagiri", "Dharmapuri", "Coimbatore", "Theni", "All"],
        "suitabilitySummary": {
            "en": "Raise healthy, viral-disease-free hybrid vegetable seedlings in pro-trays with sterilized coco peat for supply to commercial vegetable growers.",
            "ta": "கொக்கோபீட் ஊடகத்தில் பூச்சி மற்றும் வைரஸ் நோய் தாக்காத தரமான காய்கறி நாற்றுகளை உற்பத்தி செய்து விவசாயிகளுக்கு வழங்குதல்."
        },
        "estimatedStartupCapex": {
            "Naturally Ventilated Shade Net House (500 sq.m, 50% shade)": 165000.0,
            "Micro-Sprinkler / Fogger Irrigation with Booster Pump": 35000.0,
            "Germination Chamber Setup": 25000.0,
            "Pro-trays (98-cell, 2,000 trays)": 28000.0,
            "Working Capital for Coco Peat & Hybrid Seeds": 45000.0
        },
        "estimatedMonthlyOpex": {
            "Certified Hybrid Seeds (Tomato, Chilli, Brinjal)": 30000.0,
            "Washed & Low-EC Coco Peat Blocks": 12000.0,
            "Fungicide drench & Bio-fertilizer consumables": 5000.0,
            "Nursery Care & Tray Filling Labour": 16000.0,
            "Water & Electricity": 3000.0,
            "Transportation Crates & Delivery Fuel": 6000.0
        },
        "typicalBreakevenMonths": "6 - 10 months",
        "targetCustomers": [
            {"en": "Commercial vegetable growers within 35 km radius", "ta": "35 கி.மீ சுற்றளவிலுள்ள காய்கறி பயிரிடும் விவசாயிகள்"},
            {"en": "Farmer Producer Companies undertaking cluster horticulture planting", "ta": "தோட்டக்கலை பயிரிடும் உழவர் உற்பத்தியாளர் நிறுவனங்கள்"}
        ],
        "requiredSkillsAndEquipment": [
            {"en": "Pro-tray sowing precision, hardening techniques, micro-irrigation scheduling", "ta": "ப்ரோ-ட்ரே விதைப்பு முறை, நாற்று கடினப்படுத்துதல் மற்றும் நுண்ணீர் பாசனம்"},
            {"en": "50% shade net structure, misting nozzles, seed seeding trays", "ta": "50% நிழல்வலை குடில், மூடுபனி தெளிப்பான், விதை தட்டுகள்"}
        ],
        "officialResources": [
            {
                "title": "Mission for Integrated Development of Horticulture (MIDH)",
                "department": "Department of Horticulture and Plantation Crops, Tamil Nadu",
                "phone": "+91-44-28414602",
                "email": "horticulture@tn.gov.in",
                "link": "https://tnhorticulture.tn.gov.in/",
                "eligibilityNote": "50% subsidy for setting up hi-tech shade net nurseries up to prescribed unit costs."
            },
            {
                "title": "Horticultural College and Research Institute (HC&RI) Periyakulam",
                "department": "TNAU, Theni District",
                "phone": "+91-4546-231726",
                "email": "deanhortpkm@tnau.ac.in",
                "link": "https://agritech.tnau.ac.in/",
                "eligibilityNote": "Provides nursery certification training and seed source verification."
            }
        ],
        "statutoryRequirements": [
            {"en": "State Horticulture Nursery Registration under Seeds Act / Nursery Rules", "ta": "மாநில தோட்டக்கலை நாற்றங்கால் பதிவு"},
            {"en": "Source declaration invoice for hybrid certified parent seed lots", "ta": "அங்கீகரிக்கப்பட்ட விதை நிறுவன ரசீது"}
        ]
    }
]

# ----------------------------------------------------------------------------
# VERIFIED VALUE-ADDED PRODUCT BLUEPRINTS (TNAU PHTC / NIFTEM-T / CFTRI / TCRS)
# ----------------------------------------------------------------------------

VALUE_ADDED_PRODUCT_BLUEPRINTS: List[Dict[str, Any]] = [
    {
        "productId": "tomato_puree",
        "productName": {
            "en": "Thermal Concentrated Tomato Puree & Sauce",
            "ta": "வெப்ப பதப்படுத்தப்பட்ட தக்காளி கூழ் மற்றும் சாஸ்"
        },
        "rawMaterial": "Tomato",
        "processingMethod": "Thermal Processing, Pulping & Hot-Fill Bottling",
        "processingMethodCategory": "thermal_processing",
        "fssaiCategory": "FSSAI Category 4.0: Fruit and Vegetable Products",
        "rawMaterialToFinishedRatio": 0.62,  # 100 kg fresh ripe tomato yields 62 kg puree (38% moisture/skin loss)
        "typicalByproducts": [
            {
                "name": "Tomato Pomace (Skin & Seeds)",
                "yieldRatio": 0.12,
                "typicalValuePerKg": 4.5,
                "purpose": "Sold as high-lycopene animal feed supplement"
            }
        ],
        "shelfLifeAndStorage": {
            "en": "9 months unopened at ambient temperature (25°C-30°C). Refrigerate after opening.",
            "ta": "திறக்காத நிலையில் 9 மாதங்கள் (25°C-30°C). திறந்த பிறகு குளிர்சாதனப் பெட்டியில் வைக்கவும்."
        },
        "storageTemperature": "Ambient dry store (25°C - 30°C)",
        "requiredEquipment": [
            {
                "machineName": "Fruit Washer & Inspection Conveyor (SS304)",
                "capacity": "250 kg/hr",
                "approxCostInr": 45000.0,
                "purpose": "Remove dirt and cull bruised/unripe fruit"
            },
            {
                "machineName": "Tomato Pulper with Dual Mesh Sieve (SS304)",
                "capacity": "150 kg/hr",
                "approxCostInr": 68000.0,
                "purpose": "Extract smooth pulp separating skin and seeds"
            },
            {
                "machineName": "Steam Jacketed Tilting Boiling Pan (100 Litres)",
                "capacity": "100 L batch",
                "approxCostInr": 85000.0,
                "purpose": "Thermal concentration to 9-12° Brix and pasteurisation"
            },
            {
                "machineName": "Semi-Automatic Crown Corking / Lug Capping Machine",
                "capacity": "300 bottles/hr",
                "approxCostInr": 28000.0,
                "purpose": "Airtight hot-fill sealing of glass bottles"
            }
        ],
        "ingredientsAndRecipe": [
            {
                "ingredientName": "Fresh Ripe Firm Tomatoes (High TSS > 4.5° Brix)",
                "proportionPercentage": 96.5,
                "purpose": "Primary fruit base",
                "foodGradeGrade": "Sound Farm Gate Produce"
            },
            {
                "ingredientName": "Common Edible Iodised Salt",
                "proportionPercentage": 1.8,
                "purpose": "Flavor and ionic preservation",
                "foodGradeGrade": "FSSAI Compliant Food Grade"
            },
            {
                "ingredientName": "Citric Acid (Monohydrate)",
                "proportionPercentage": 0.2,
                "purpose": "pH adjustment to < 4.2 to inhibit Clostridium botulinum",
                "foodGradeGrade": "INS 330 Pure Food Grade"
            },
            {
                "ingredientName": "Refined Cane Sugar (for Sauce formulation)",
                "proportionPercentage": 1.5,
                "purpose": "Brix balance and palatability",
                "foodGradeGrade": "FSSAI Grade"
            }
        ],
        "standardOperatingProcedure": [
            {
                "stepNumber": 1,
                "stepTitle": "Sorting and Chlorinated Washing",
                "details": "Wash firm red ripe tomatoes in 50 ppm chlorinated potable water. Discard diseased or fungal-attacked fruits.",
                "hygieneStandard": "Clean rubber gloves and aprons; chlorinated potable wash tank.",
                "criticalControlPoint": "Remove all split fruits to avoid mold count exceeding 40%."
            },
            {
                "stepNumber": 2,
                "stepTitle": "Hot Break & Mechanical Pulping",
                "details": "Chop tomatoes and heat rapidly to 85°C for 3 minutes (Hot Break) to inactivate pectolytic enzymes. Pass through pulper with 0.8 mm sieve.",
                "hygieneStandard": "SS304 contact surfaces pre-sanitized with hot water.",
                "criticalControlPoint": "Rapid heat break maintains viscous natural body."
            },
            {
                "stepNumber": 3,
                "stepTitle": "Concentration & Brix Verification",
                "details": "Simmer pulp in steam jacketed pan until refractometer reading reaches 9.0° to 12.0° Brix. Add salt and citric acid.",
                "hygieneStandard": "Closed pan boiling; calibrate optical handheld refractometer.",
                "criticalControlPoint": "Ensure final product pH is strictly below 4.2."
            },
            {
                "stepNumber": 4,
                "stepTitle": "Hot Filling, Capping & Thermal Inversion",
                "details": "Fill into pre-sterilized glass bottles at minimum 85°C. Cap immediately with lug caps and invert bottle for 3 minutes to sterilize lid.",
                "hygieneStandard": "Bottles dry-heat sterilized at 110°C for 20 minutes prior to fill.",
                "criticalControlPoint": "Filling temperature must not drop below 85°C."
            },
            {
                "stepNumber": 5,
                "stepTitle": "Cooling & Tamper-Evident Labeling",
                "details": "Cool bottles gradually in air to avoid thermal shock breakage. Apply shrink sleeves, batch date, and FSSAI license number.",
                "hygieneStandard": "Dry dust-free packaging area.",
                "criticalControlPoint": "Inspect vacuum button seal on caps."
            }
        ],
        "foodSafetyAndHygiene": [
            {
                "en": "Strict adherence to FSSAI Schedule 4 (General Sanitary and Hygienic Requirements)",
                "ta": "FSSAI அட்டவணை 4 உணவு சுகாதார விதிமுறைகளை கண்டிப்பாக பின்பற்றுதல்"
            },
            {
                "en": "Ensure final product pH stays strictly <= 4.2 to prevent microbial spore germination",
                "ta": "நுண்ணுயிர் பெருக்கத்தை தடுக்க அமிலத்தன்மை (pH) 4.2 க்கும் குறைவாக இருப்பதை உறுதிசெய்தல்"
            },
            {
                "en": "Potable water tested according to IS 10500 standards for food processing",
                "ta": "IS 10500 தரத்திற்கு இணையான தூய குடிநீரை மட்டுமே பயன்படுத்துதல்"
            }
        ],
        "packagingGuidance": {
            "en": "500g / 1kg wide-mouth glass bottles with lug caps, or retort pouch (multi-layer laminate) with induction seal.",
            "ta": "500 கிராம் அல்லது 1 கிலோ கண்ணாடி பாட்டில்கள் அல்லது பல அடுக்கு உணவுப் பைகள் (Retort Pouches)."
        },
        "authoritativeReference": {
            "institute": "TNAU Post Harvest Technology Centre, Coimbatore",
            "document": "Package of Practices for Processing of Tomatoes into Puree, Paste and Ketchup (PHTC-Hort-03)",
            "verificationUrl": "https://agritech.tnau.ac.in/post_harvest/pht_tomato.html"
        },
        "potentialSalesChannels": [
            "Local Pizza, Bakery & Fast-Food Outlets",
            "College Hostels & Hospital Canteens",
            "Uzhavar Sandhai Direct Farmer Stalls",
            "Namma Vivasayi Direct Marketplace",
            "Organic & Natural Food Grocery Stores"
        ],
        "trainingProviders": [
            {
                "institute": "TNAU Post Harvest Technology Centre (PHTC)",
                "location": "AEC&RI, Coimbatore",
                "contact": "+91-422-6611268",
                "email": "phtc@tnau.ac.in",
                "courseName": "Hands-on Processing & Preservation of Fruits & Vegetables"
            },
            {
                "institute": "Krishi Vigyan Kendra (KVK) Sandhiyur",
                "location": "Sandhiyur, Salem District",
                "contact": "+91-427-2422550",
                "email": "kvksalem@tnau.ac.in",
                "courseName": "Farm Women Food Processing & Value Addition Training"
            }
        ]
    },
    {
        "productId": "groundnut_cold_pressed_oil",
        "productName": {
            "en": "Cold-Pressed Groundnut Oil (Mara Chekku Ennai)",
            "ta": "மரச்செக்கு கடலை எண்ணெய் மற்றும் கடலை புண்ணாக்கு"
        },
        "rawMaterial": "Groundnut",
        "processingMethod": "Wood Cold-Press Rotary Expeller Extraction & Gravity Settling",
        "processingMethodCategory": "cold_extraction",
        "fssaiCategory": "FSSAI Category 2.0: Fats, Oils and Fat Emulsions",
        "rawMaterialToFinishedRatio": 0.42,  # 100 kg dry groundnut kernels yield 42 Litres virgin oil (42% oil recovery)
        "typicalByproducts": [
            {
                "name": "De-oiled Groundnut Cake (Kadalai Pinnakku)",
                "yieldRatio": 0.56,  # 56 kg cake per 100 kg kernels
                "typicalValuePerKg": 36.0,
                "purpose": "High-protein cattle and poultry feed ingredient"
            }
        ],
        "shelfLifeAndStorage": {
            "en": "6 months in opaque containers stored in cool, dark place away from direct sunlight.",
            "ta": "குளிர்ந்த, இருண்ட இடத்தில் சேமித்தால் 6 மாதங்கள் வரை தரம் மாறாது."
        },
        "storageTemperature": "Dry dark room below 28°C",
        "requiredEquipment": [
            {
                "machineName": "Traditional Mara Chekku (Vagai Wood Drum Rotary Press, 15 kg batch)",
                "capacity": "15 kg / 45 min",
                "approxCostInr": 185000.0,
                "purpose": "Slow friction extraction keeping temperature strictly below 45°C"
            },
            {
                "machineName": "Groundnut Kernel Decorticator & Cleaner",
                "capacity": "200 kg/hr",
                "approxCostInr": 48000.0,
                "purpose": "Pod deshelling and dust/stone screening"
            },
            {
                "machineName": "SS304 Gravity Settling Tanks with Decanter Taps",
                "capacity": "2 x 200 Litres",
                "approxCostInr": 35000.0,
                "purpose": "Natural clarification without chemical bleaching or refining"
            },
            {
                "machineName": "Volumetric Liquid Piston Filling & Induction Sealer",
                "capacity": "250 bottles/hr",
                "approxCostInr": 42000.0,
                "purpose": "Precision filling into tin cans and PET bottles"
            }
        ],
        "ingredientsAndRecipe": [
            {
                "ingredientName": "Sun-dried Sound Groundnut Kernels (Moisture < 7%)",
                "proportionPercentage": 98.0,
                "purpose": "Clean, aflatoxin-screened kernels",
                "foodGradeGrade": "Bold Grade A Kernels"
            },
            {
                "ingredientName": "Pure Organic Palm Jaggery (Karupatti)",
                "proportionPercentage": 2.0,
                "purpose": "Traditional extraction binding agent and mild sweetness aroma",
                "foodGradeGrade": "Pure Organic Jaggery"
            }
        ],
        "standardOperatingProcedure": [
            {
                "stepNumber": 1,
                "stepTitle": "Raw Material Inspection & Aflatoxin Check",
                "details": "Inspect shelled kernels under UV light / visual inspection. Discard broken, shrivelled, or green moldy kernels.",
                "hygieneStandard": "Ensure kernels are dried to <= 7% moisture to prevent Aspergillus flavus fungal growth.",
                "criticalControlPoint": "Aflatoxin B1 level must test below 15 ppb as per FSSAI."
            },
            {
                "stepNumber": 2,
                "stepTitle": "Chekku Charging & Slow Pressing",
                "details": "Load 15 kg cleaned kernels into Vagai wood mortar. Add 300g palm jaggery. Run rotary pestle at 16-20 RPM for 40 minutes.",
                "hygieneStandard": "Clean wooden barrel between batches; no mineral grease on machine shafts.",
                "criticalControlPoint": "Oil temperature during pressing must never exceed 45°C to preserve natural tocopherols."
            },
            {
                "stepNumber": 3,
                "stepTitle": "Cake Discharge & Press Cake Stacking",
                "details": "Remove pressed firm groundnut cake (Pinnakku). Break into uniform pieces and bag in breathable gunny bags.",
                "hygieneStandard": "Clean stainless steel scoops; keep cake away from ground moisture.",
                "criticalControlPoint": "Store cake in aerated racks to prevent dampness."
            },
            {
                "stepNumber": 4,
                "stepTitle": "Natural Gravity Sedimentation",
                "details": "Transfer raw oil into SS304 settling tanks. Allow 48 hours for natural plant fibers and micro-solids to settle to the bottom cone.",
                "hygieneStandard": "Airtight SS tank lid with fine air breather mesh.",
                "criticalControlPoint": "Zero artificial filter aids, chemical neutralizers, or bleaches."
            },
            {
                "stepNumber": 5,
                "stepTitle": "Bottling & Packaging",
                "details": "Decant clear aromatic golden oil into food-grade opaque HDPE tins or amber PET bottles. Apply induction heat seal.",
                "hygieneStandard": "Automated nozzle filling; wipe exterior cleanly.",
                "criticalControlPoint": "Hermetic seal prevents rancidity and photo-oxidation."
            }
        ],
        "foodSafetyAndHygiene": [
            {
                "en": "FSSAI Regulation: Free Fatty Acid (as oleic acid) must not exceed 3.0%",
                "ta": "FSSAI விதிமுறை: கொழுப்பு அமில அளவு (Free Fatty Acid) 3.0%க்குள் இருக்க வேண்டும்"
            },
            {
                "en": "Peroxide Value must remain below 10 meq/kg of oil",
                "ta": "பெராக்சைடு மதிப்பு 10 meq/kg க்குள் இருக்க வேண்டும்"
            },
            {
                "en": "Total absence of argemone oil, mineral oil or synthetic additives",
                "ta": "எந்தவித செயற்கை நிறமி அல்லது கலப்பட எண்ணெய்களும் சேர்க்கக்கூடாது"
            }
        ],
        "packagingGuidance": {
            "en": "Food-grade food-lacquered tin containers (1L, 5L) or UV-protected PET bottles with tamper-evident induction cap.",
            "ta": "உணவுத் தரம் வாய்ந்த தகர டின்கள் (1L, 5L) அல்லது புற ஊதா கதிர் தடுப்பு PET பாட்டில்கள்."
        },
        "authoritativeReference": {
            "institute": "National Institute of Food Technology, Entrepreneurship and Management (NIFTEM-T), Thanjavur",
            "document": "SOP for Cold-Pressed Virgin Groundnut Oil Processing & Quality Evaluation (NIFTEM-T-ED-14)",
            "verificationUrl": "https://niftem-t.ac.in/"
        },
        "potentialSalesChannels": [
            "Direct Sale to Regular Urban Households (Subscription Model)",
            "Local Dairy & Farm Gate Sales",
            "Heritage & Organic Specialty Retailers",
            "Namma Vivasayi Direct Marketplace",
            "Export Aggregators for Cold-Pressed Edible Oils"
        ],
        "trainingProviders": [
            {
                "institute": "NIFTEM-Thanjavur (formerly IIFPT)",
                "location": "Pudukkottai Road, Thanjavur",
                "contact": "+91-4362-228155",
                "email": "director@iifpt.edu.in",
                "courseName": "Entrepreneurship Development on Cold-Pressed Edible Oil Processing"
            },
            {
                "institute": "TNAU Oilseeds Research Station (ORS)",
                "location": "Tindivanam, Villupuram District",
                "contact": "+91-4147-250293",
                "email": "arstvm@tnau.ac.in",
                "courseName": "Quality Groundnut Seed Production & Processing"
            }
        ]
    },
    {
        "productId": "tapioca_crisps",
        "productName": {
            "en": "Dehydrated Tapioca Wafers & Roasted Chips",
            "ta": "மரவள்ளிக்கிழங்கு சிப்ஸ் மற்றும் உலர்ந்த அப்பள வத்தல்"
        },
        "rawMaterial": "Tapioca",
        "processingMethod": "Washing, Peeling, Uniform Slicing, Blanching & Solar Dehydration",
        "processingMethodCategory": "dehydration_drying",
        "fssaiCategory": "FSSAI Category 4.0: Fruit and Vegetable Products",
        "rawMaterialToFinishedRatio": 0.35,  # 100 kg raw tapioca tubers yield 35 kg dried wafers (65% peel + moisture loss)
        "typicalByproducts": [
            {
                "name": "Tapioca Peels & Fiber Residue",
                "yieldRatio": 0.18,
                "typicalValuePerKg": 2.5,
                "purpose": "Livestock fodder or composting biomass"
            }
        ],
        "shelfLifeAndStorage": {
            "en": "12 months in moisture-barrier hermetic poly pouches stored in cool, dry conditions.",
            "ta": "ஈரப்பதம் படாத பாக்கெட்டுகளில் 12 மாதங்கள் வரை கெடாமல் இருக்கும்."
        },
        "storageTemperature": "Dry ambient storage (< 30°C)",
        "requiredEquipment": [
            {
                "machineName": "Abrasive Tapioca Peeling & Washing Machine (SS304)",
                "capacity": "200 kg/hr",
                "approxCostInr": 55000.0,
                "purpose": "Rapid mechanical peel removal reducing manual labour"
            },
            {
                "machineName": "Adjustable Thickness Rotary Tuber Slicer",
                "capacity": "150 kg/hr",
                "approxCostInr": 32000.0,
                "purpose": "Precision 1.2 mm - 1.5 mm wafer slicing"
            },
            {
                "machineName": "Blanching Tank with LPG / Steam Immersion Burner",
                "capacity": "100 Litres",
                "approxCostInr": 28000.0,
                "purpose": "Enzyme deactivation and starch gelatinisation"
            },
            {
                "machineName": "Polyhouse Solar Tunnel Dryer (400 sq.ft)",
                "capacity": "150 kg wet batch",
                "approxCostInr": 135000.0,
                "purpose": "Hygienic dust-free solar drying down to < 8% moisture"
            }
        ],
        "ingredientsAndRecipe": [
            {
                "ingredientName": "Fresh Tapioca Tubers (TCRS varieties: Yethapur-1 or Mulluvadi)",
                "proportionPercentage": 97.5,
                "purpose": "High-starch firm tuber base",
                "foodGradeGrade": "Sound Freshly Harvested Tubers"
            },
            {
                "ingredientName": "Edible Rock Salt",
                "proportionPercentage": 2.0,
                "purpose": "Brining and taste",
                "foodGradeGrade": "FSSAI Food Grade Salt"
            },
            {
                "ingredientName": "Sodium Metabisulphite (Permitted Class II Preservative)",
                "proportionPercentage": 0.05,
                "purpose": "Prevent enzymatic browning and maintain crisp white color",
                "foodGradeGrade": "FSSAI INS 223 Permitted Limit (< 50 ppm residual)"
            },
            {
                "ingredientName": "Organic Red Chilli Powder / Black Pepper (Optional Sprinkling)",
                "proportionPercentage": 0.45,
                "purpose": "Flavoring for ready-to-eat variant",
                "foodGradeGrade": "Pure Spice Powder"
            }
        ],
        "standardOperatingProcedure": [
            {
                "stepNumber": 1,
                "stepTitle": "Harvest Conditioning & Trimming",
                "details": "Process tapioca within 48 hours of harvest to avoid vascular streaking deterioration. Wash mud thoroughly in running water.",
                "hygieneStandard": "Chlorinated water soak (30 ppm) to remove root microbes.",
                "criticalControlPoint": "Discard tubers showing blue/black vascular streaks."
            },
            {
                "stepNumber": 2,
                "stepTitle": "Peeling and Precision Slicing",
                "details": "Peel outer brown periderm and pink cortical layer cleanly. Slice tubers immediately into 1.2 to 1.5 mm thick uniform round discs.",
                "hygieneStandard": "Food-grade SS slicer blades; keep slices submerged in water to avoid oxidation.",
                "criticalControlPoint": "Uniform slice thickness is mandatory for even dehydration."
            },
            {
                "stepNumber": 3,
                "stepTitle": "Blanching in Salted Brine",
                "details": "Blanch slices in boiling water containing 2% salt and 0.05% potassium metabisulphite at 95°C for 2.5 minutes until translucent.",
                "hygieneStandard": "Temperature monitored via digital probe.",
                "criticalControlPoint": "Complete gelatinization without turning slices mushy."
            },
            {
                "stepNumber": 4,
                "stepTitle": "Solar Tunnel Drying",
                "details": "Spread blanched wafers in single layer on SS304 drying trays inside the solar tunnel dryer. Dry until moisture content drops below 8%.",
                "hygieneStandard": "UV-stabilized polyhouse prevents dust, insects, and bird droppings.",
                "criticalControlPoint": "Moisture must be <= 8.0% to ensure snap crispiness and zero fungal risk."
            },
            {
                "stepNumber": 5,
                "stepTitle": "Nitrogen-Flushed Pouch Sealing",
                "details": "Pack cooled wafers in multi-layer metalized polyester (BOPP/Met PET/Poly) pouches with nitrogen flush.",
                "hygieneStandard": "Hermetic band sealing at 180°C.",
                "criticalControlPoint": "Zero pinhole leaks; shelf life depends on moisture barrier."
            }
        ],
        "foodSafetyAndHygiene": [
            {
                "en": "Hydrocyanic acid (HCN) naturally occurring in cassava must be reduced to safe levels (< 10 ppm) via peeling and blanching",
                "ta": "மரவள்ளியில் உள்ள சயனைடு நச்சுத்தன்மையை நீக்க தோலை முழுமையாக நீக்கி கொதிநீரில் வேகவைத்தல் கட்டாயம்"
            },
            {
                "en": "Zero artificial food colors (Tartrazine or Sunset Yellow) in pure dried wafers",
                "ta": "செயற்கை வண்ணங்கள் எதுவும் சேர்க்கக்கூடாது"
            }
        ],
        "packagingGuidance": {
            "en": "250g, 500g, and 1kg heat-sealed metalized pouches with oxygen scavenger or nitrogen flushing.",
            "ta": "250 கிராம், 500 கிராம் அல்லது 1 கிலோ நைட்ரஜன் நிரப்பப்பட்ட மாய்ஸ்சர் தடுப்பு உணவுப் பைகள்."
        },
        "authoritativeReference": {
            "institute": "Tapioca and Castor Research Station (TCRS) Yethapur",
            "document": "Post-Harvest Processing and Value Addition in Cassava Tubers (TCRS-TNAU-Pub-07)",
            "verificationUrl": "https://agritech.tnau.ac.in/expert_system/tapioca/post_harvest.html"
        },
        "potentialSalesChannels": [
            "Salem Sago & Starch Merchant Aggregators",
            "Direct Deep-Frying Snack Manufacturers",
            "Supermarket Chains (Fry-at-Home Wafers Section)",
            "Uzhavar Sandhai & Local Village Weekly Shandy",
            "Namma Vivasayi Marketplace"
        ],
        "trainingProviders": [
            {
                "institute": "Tapioca and Castor Research Station (TCRS) Yethapur",
                "location": "Yethapur, P.G. Palayam, Salem District",
                "contact": "+91-4282-293526",
                "email": "aratcrs@tnau.ac.in",
                "courseName": "Value Addition & Processing Technologies in Cassava"
            },
            {
                "institute": "TNAU Post Harvest Technology Centre",
                "location": "Coimbatore",
                "contact": "+91-422-6611268",
                "email": "phtc@tnau.ac.in",
                "courseName": "Solar Tunnel Drying & Dehydration Enterprise Course"
            }
        ]
    },
    {
        "productId": "turmeric_cured_powder",
        "productName": {
            "en": "Steam-Cured & Micronized Salem Turmeric Powder",
            "ta": "நீராவி பதப்படுத்தப்பட்ட சேலம் விரலி மஞ்சள் தூள்"
        },
        "rawMaterial": "Turmeric",
        "processingMethod": "Boiling/Steam Curing, Sun Drying, Polishing & Pulverization",
        "processingMethodCategory": "milling_pulverizing",
        "fssaiCategory": "FSSAI Category 12.0: Salts, Spices, Soups, Sauces and Salads",
        "rawMaterialToFinishedRatio": 0.22,  # 100 kg fresh wet rhizomes yield 22 kg cured polished dry powder (78% moisture/curing loss)
        "typicalByproducts": [
            {
                "name": "Turmeric Root Polishing Dust / Small Bits",
                "yieldRatio": 0.04,
                "typicalValuePerKg": 25.0,
                "purpose": "Sold to dye extractors or low-grade incense compounding"
            }
        ],
        "shelfLifeAndStorage": {
            "en": "18 months when stored in airtight amber containers protected from UV light and humidity.",
            "ta": "சூரிய ஒளி படாமல் காற்றுப்புகாத பாக்கெட்டுகளில் 18 மாதங்கள் வரை சேமிக்கலாம்."
        },
        "storageTemperature": "Dry dark warehouse (20°C - 28°C)",
        "requiredEquipment": [
            {
                "machineName": "TNAU Improved Turmeric Steam Boiling Boiler (Perforated drums)",
                "capacity": "300 kg / batch",
                "approxCostInr": 65000.0,
                "purpose": "Uniform steam curing without color burning and conserving fuel"
            },
            {
                "machineName": "Power-Operated Turmeric Mechanical Polishing Drum",
                "capacity": "250 kg/hr",
                "approxCostInr": 45000.0,
                "purpose": "Remove outer rough skin and polish rhizomes to bright golden hue"
            },
            {
                "machineName": "SS304 Water-Cooled Impact Pulverizer with Cyclone Separator",
                "capacity": "80 kg/hr",
                "approxCostInr": 95000.0,
                "purpose": "Fine milling to 80-100 mesh without burning volatile curcumin oils"
            },
            {
                "machineName": "Semi-Automatic Auger Powder Filling Machine",
                "capacity": "350 pouches/hr",
                "approxCostInr": 58000.0,
                "purpose": "Accurate dust-free filling into printed stand-up zipper pouches"
            }
        ],
        "ingredientsAndRecipe": [
            {
                "ingredientName": "High Curcumin Raw Salem Turmeric Rhizomes (Curcumin > 3.8%)",
                "proportionPercentage": 100.0,
                "purpose": "Pure single-origin unadulterated spice",
                "foodGradeGrade": "Salem Local / PTS-10 Variety"
            }
        ],
        "standardOperatingProcedure": [
            {
                "stepNumber": 1,
                "stepTitle": "Cleaning and Rhizome Sorting",
                "details": "Separate mother rhizomes from finger rhizomes. Soak in water to wash away red gravel soil adhering to root crevices.",
                "hygieneStandard": "Wash with potable agricultural water.",
                "criticalControlPoint": "Finger rhizomes cured separately for superior market grade."
            },
            {
                "stepNumber": 2,
                "stepTitle": "TNAU Steam Curing",
                "details": "Place clean fingers in perforated metal drum inside steam cooker. Steam until fingers turn soft to thumb pressure and froth disappears (approx 45-60 min).",
                "hygieneStandard": "Closed boiler steam vessel.",
                "criticalControlPoint": "Over-boiling darkens colour; under-boiling leaves white chalky core."
            },
            {
                "stepNumber": 3,
                "stepTitle": "Drying and Mechanical Polishing",
                "details": "Spread cured rhizomes in thin layer (5 cm) on clean tarpaulin or drying yard for 10-14 days until moisture drops to 8-10%. Run through polishing drum for 25 minutes.",
                "hygieneStandard": "Clean raised platform away from farm livestock.",
                "criticalControlPoint": "Polishing exposes bright yellow inner core."
            },
            {
                "stepNumber": 4,
                "stepTitle": "Cold Micro-Pulverization",
                "details": "Milled in water-jacketed impact pulverizer to maintain chamber temperature <= 50°C. Sieve through 100-mesh nylon screen.",
                "hygieneStandard": "Food-grade stainless steel chamber with magnetic separator for metal bits.",
                "criticalControlPoint": "Cold milling preserves essential turmerone volatile oils and curcumin."
            },
            {
                "stepNumber": 5,
                "stepTitle": "Packaging in Light-Barrier Pouches",
                "details": "Pack into aluminum foil stand-up zipper pouches. Heat seal and inspect tare weight.",
                "hygieneStandard": "Clean dry room; operators wear masks to avoid spice inhalation.",
                "criticalControlPoint": "Foil barrier prevents curcumin photodegradation from sunlight."
            }
        ],
        "foodSafetyAndHygiene": [
            {
                "en": "FSSAI Specification: Curcumin content must be minimum 3.0% by mass",
                "ta": "FSSAI தரம்: குர்குமின் அளவு குறைந்தது 3.0% இருக்க வேண்டும்"
            },
            {
                "en": "Strict zero tolerance for lead chromate or Sudan red dye adulteration",
                "ta": "லெட் குரோமேட் போன்ற நச்சு வண்ணங்கள் கலக்கக்கூடாது"
            },
            {
                "en": "Total ash content must not exceed 9.0% by mass",
                "ta": "மொத்த சாம்பல் சத்து 9.0%க்கு மிகாமல் இருக்க வேண்டும்"
            }
        ],
        "packagingGuidance": {
            "en": "100g, 250g, 500g, 1kg multi-layer metalized PET/Alu-foil barrier standup pouches with re-closable zipper.",
            "ta": "100 கிராம் முதல் 1 கிலோ வரை காற்று மற்றும் ஒளி புகாத ஜிப்பர் பைகள்."
        },
        "authoritativeReference": {
            "institute": "TNAU Department of Spices & Plantation Crops & Salem Turmeric Cluster",
            "document": "Scientific Curing and Processing of Salem Turmeric for Export Grade Quality (TNAU-Hort-Spices-09)",
            "verificationUrl": "https://agritech.tnau.ac.in/horticulture/horti_spices_turmeric.html"
        },
        "potentialSalesChannels": [
            "Salem & Erode Regulated Market Turmeric Auctions",
            "Ayurvedic and Siddha Medicine Manufacturers",
            "Direct Retail to Households via Namma Vivasayi Marketplace",
            "Export Aggregators for Organic Curcumin Spices",
            "Local Supermarkets and Departmental Outlets"
        ],
        "trainingProviders": [
            {
                "institute": "TNAU Department of Spices & Plantation Crops",
                "location": "Horticultural College, Coimbatore",
                "contact": "+91-422-6611279",
                "email": "spices@tnau.ac.in",
                "courseName": "Commercial Processing & Export Quality Production in Turmeric"
            },
            {
                "institute": "Indian Institute of Spices Research (ICAR-IISR)",
                "location": "Kozhikode / Regional Centre",
                "contact": "+91-495-2731410",
                "email": "director.spices@icar.gov.in",
                "courseName": "Advanced Spice Processing & Curcumin Extraction Techniques"
            }
        ]
    },
    {
        "productId": "millet_flour_mix",
        "productName": {
            "en": "Ready-to-Cook Multigrain Millet Flour & Health Mix",
            "ta": "பாரம்பரிய சிறுதானிய சத்து மாவு மற்றும் இட்லி/தோசை கலவை"
        },
        "rawMaterial": "Millets",
        "processingMethod": "Grading, Roasting, Milling, Sieving & Vacuum Packaging",
        "processingMethodCategory": "milling_pulverizing",
        "fssaiCategory": "FSSAI Category 6.0: Cereals and Cereal Products",
        "rawMaterialToFinishedRatio": 0.88,  # 100 kg raw millets yield 88 kg finished health mix flour (12% bran/chaff loss)
        "typicalByproducts": [
            {
                "name": "Millet Husk and Fine Bran Screenings",
                "yieldRatio": 0.12,
                "typicalValuePerKg": 8.0,
                "purpose": "Nutritious fiber feed supplement for cattle and goats"
            }
        ],
        "shelfLifeAndStorage": {
            "en": "6 months in airtight nitrogen-flushed laminated packs stored in a cool, dry place.",
            "ta": "நைட்ரஜன் நிரப்பப்பட்ட காற்றுப்புகாத பைகளில் 6 மாதங்கள் வரை கெடாமல் இருக்கும்."
        },
        "storageTemperature": "Dry ambient room (< 28°C)",
        "requiredEquipment": [
            {
                "machineName": "Rotary Grain Destoner & Aspirator",
                "capacity": "250 kg/hr",
                "approxCostInr": 55000.0,
                "purpose": "Remove stones, mud balls, and hollow seeds"
            },
            {
                "machineName": "Continuous Electric / LPG Roaster Drum (SS304)",
                "capacity": "50 kg/hr",
                "approxCostInr": 68000.0,
                "purpose": "Controlled dry roasting to develop nutty aroma and digest starch"
            },
            {
                "machineName": "SS304 Heavy-Duty Flour Mill / Pin Mill with Dust Collector",
                "capacity": "60 kg/hr",
                "approxCostInr": 72000.0,
                "purpose": "Ultra-fine pulverizing of tough small millet grains"
            },
            {
                "machineName": "Continuous Band Sealer with Nitrogen Flushing Unit",
                "capacity": "400 pouches/hr",
                "approxCostInr": 35000.0,
                "purpose": "Inert gas packaging preventing fat rancidity"
            }
        ],
        "ingredientsAndRecipe": [
            {
                "ingredientName": "Finger Millet / Ragi (Eleusine coracana)",
                "proportionPercentage": 35.0,
                "purpose": "Rich calcium and dietary fiber foundation",
                "foodGradeGrade": "Cleaned Farm Gate Grain"
            },
            {
                "ingredientName": "Pearl Millet / Kambu (Pennisetum glaucum)",
                "proportionPercentage": 20.0,
                "purpose": "Iron and energetic body warmth",
                "foodGradeGrade": "Cleaned Grain"
            },
            {
                "ingredientName": "Foxtail Millet / Thinai (Setaria italica)",
                "proportionPercentage": 15.0,
                "purpose": "Low glycemic index and B-vitamins",
                "foodGradeGrade": "Dehulled Grain"
            },
            {
                "ingredientName": "Roasted Bengal Gram (Pottukadalai)",
                "proportionPercentage": 15.0,
                "purpose": "Digestible plant protein complement",
                "foodGradeGrade": "Food Grade Legume"
            },
            {
                "ingredientName": "Cardamom & Dry Ginger (Sukku & Elachi)",
                "proportionPercentage": 2.0,
                "purpose": "Digestive aroma and traditional taste",
                "foodGradeGrade": "Cleaned Natural Spices"
            },
            {
                "ingredientName": "Almonds and Cashews (Crushed)",
                "proportionPercentage": 13.0,
                "purpose": "Premium nutritional density and healthy fats",
                "foodGradeGrade": "Food Grade Nuts"
            }
        ],
        "standardOperatingProcedure": [
            {
                "stepNumber": 1,
                "stepTitle": "Pre-Cleaning & Destoning",
                "details": "Pass small millets through multi-deck destoner to remove sand and clay balls. Wash and dry under gentle shade if dust is heavy.",
                "hygieneStandard": "Zero grit policy; magnetic trap for metal contaminants.",
                "criticalControlPoint": "Zero grit or stones in final flour."
            },
            {
                "stepNumber": 2,
                "stepTitle": "Controlled Roasting",
                "details": "Roast each grain individually at 110°C to 125°C for 8-12 minutes until pleasant nutty aroma is released without burning.",
                "hygieneStandard": "Clean SS drum roaster; digital temperature monitoring.",
                "criticalControlPoint": "Inactivates lipase enzymes that cause millet flour bitterness."
            },
            {
                "stepNumber": 3,
                "stepTitle": "Cooling and Ingredient Blending",
                "details": "Cool roasted grains on stainless steel tables. Weigh accurately according to recipe ratio and mix thoroughly.",
                "hygieneStandard": "Clean SS paddle blender.",
                "criticalControlPoint": "Uniform ingredient distribution throughout the batch."
            },
            {
                "stepNumber": 4,
                "stepTitle": "Milling and Vibro-Sieving",
                "details": "Grind through pin mill. Sieve through 60-mesh vibro-sifter to ensure silky, clump-free consistency.",
                "hygieneStandard": "Clean cloth filter bags on cyclone collector.",
                "criticalControlPoint": "Fineness of grind ensures smooth porridge preparation."
            },
            {
                "stepNumber": 5,
                "stepTitle": "Nitrogen Flushed Packaging",
                "details": "Fill into aluminum barrier stand-up pouches with nitrogen gas flushing to protect delicate millet fats from oxidation.",
                "hygieneStandard": "Automated weighing balance; clean packaging zone.",
                "criticalControlPoint": "Residual oxygen below 2% ensures 6 months rancidity-free shelf life."
            }
        ],
        "foodSafetyAndHygiene": [
            {
                "en": "Moisture content of flour must not exceed 10.0% by mass",
                "ta": "மாவின் ஈரப்பதம் 10.0%க்கு மிகாமல் இருப்பதை உறுதி செய்தல்"
            },
            {
                "en": "Gluten-free equipment dedicated line to avoid wheat cross-contamination",
                "ta": "கோதுமை மாவு கலப்படம் இல்லாத தனித்துவமான அரைவை இயந்திரம்"
            },
            {
                "en": "Periodic testing for uric acid and insect fragments under FSSAI rules",
                "ta": "FSSAI விதிமுறைப்படி பூச்சி அல்லது தூசு இல்லாத சுத்தமான மாவு"
            }
        ],
        "packagingGuidance": {
            "en": "500g and 1kg matte-finish multi-layer stand-up zipper pouches with transparent window and nitrogen flushing.",
            "ta": "500 கிராம் அல்லது 1 கிலோ நைட்ரஜன் நிரப்பப்பட்ட மாய்ஸ்சர் தடுப்பு ஜிப்பர் பைகள்."
        },
        "authoritativeReference": {
            "institute": "National Institute of Food Technology, Entrepreneurship and Management (NIFTEM-T)",
            "document": "Technology for Production of Value-Added Products from Millets (NIFTEM-T-Millet-01)",
            "verificationUrl": "https://niftem-t.ac.in/"
        },
        "potentialSalesChannels": [
            "Direct Subscriptions to Health-Conscious Urban Families",
            "Organic Groceries and Wellness Stores",
            "Namma Vivasayi Direct Marketplace",
            "School and Hospital Dietary Programs",
            "Local Supermarket Chains and Uzhavar Sandhai"
        ],
        "trainingProviders": [
            {
                "institute": "NIFTEM-Thanjavur Millet Incubation Centre",
                "location": "Pudukkottai Road, Thanjavur",
                "contact": "+91-4362-228155",
                "email": "incubation@iifpt.edu.in",
                "courseName": "Commercial Processing & Formulation of Millet Value-Added Foods"
            },
            {
                "institute": "Centre of Excellence in Millets, Athiyandal",
                "location": "Tiruvannamalai District (TNAU)",
                "contact": "+91-4176-254221",
                "email": "cemathiyandal@tnau.ac.in",
                "courseName": "Small Millets Production, Processing & Business Opportunities"
            }
        ]
    }
]

# ----------------------------------------------------------------------------
# CORE BUSINESS LOGIC & CALCULATION ENGINES
# ----------------------------------------------------------------------------

def match_business_ideas(request: BusinessIdeaMatchRequest) -> BusinessIdeaMatchResponse:
    """
    Evaluates farmer inputs (interests, skills, location, budget, available produce)
    against verified agricultural enterprise blueprints to compute suitability scores and itemized matches.
    """
    matched: List[BusinessIdeaItem] = []
    farmer_budget = request.investmentBudget
    user_interests = set(i.lower() for i in request.interests)
    user_skills = set(s.lower() for s in request.skills)
    user_produce = set(p.lower() for p in request.availableProduce)
    user_district = request.locationDistrict.strip()

    for bp in ENTREPRENEURSHIP_BLUEPRINTS:
        score = 40  # base starting score for verified viable template
        match_reasons_en = []
        match_reasons_ta = []

        # 1. Budget Fit Check
        min_b = bp.get("budgetRangeMin", 50000.0)
        max_b = bp.get("budgetRangeMax", 500000.0)
        if farmer_budget >= min_b and farmer_budget <= max_b * 1.5:
            score += 20
            match_reasons_en.append(f"Budget of ₹{farmer_budget:,.0f} aligns with template setup requirements (₹{min_b:,.0f} - ₹{max_b:,.0f}).")
            match_reasons_ta.append(f"உங்களின் ₹{farmer_budget:,.0f} முதலீடு இந்த தொழிலுக்கு உகந்தது.")
        elif farmer_budget < min_b:
            # Score penalty if severely underfunded, but remind them of subsidy/AIF
            deficit = min_b - farmer_budget
            score = max(10, score - 15)
            match_reasons_en.append(f"Starting capex requires approx ₹{min_b:,.0f}. Government subsidy schemes (PMFME/ACABC) can assist with ₹{deficit:,.0f} deficit.")
            match_reasons_ta.append(f"தொடக்க முதலீட்டிற்கு ₹{min_b:,.0f} தேவைப்படுகிறது; அரசு மானிய திட்டங்கள் மூலம் மீத தொகையை பெறலாம்.")
        else:
            score += 10
            match_reasons_en.append(f"Comfortable investment headroom to invest in advanced automation.")
            match_reasons_ta.append(f"உங்களிடம் கூடுதல் முதலீடு இருப்பதால் நவீன இயந்திரங்களை வாங்கலாம்.")

        # 2. Interests Overlap
        bp_interests = set(i.lower() for i in bp.get("matchingInterests", []))
        common_interests = user_interests.intersection(bp_interests)
        if common_interests:
            score += 20
            match_reasons_en.append(f"Matches your stated interests in {', '.join(common_interests)}.")
            match_reasons_ta.append(f"உங்கள் விருப்பங்களுடன் ({', '.join(common_interests)}) பொருந்துகிறது.")

        # 3. Skills Overlap
        bp_skills = set(s.lower() for s in bp.get("matchingSkills", []))
        common_skills = user_skills.intersection(bp_skills)
        if common_skills:
            score += 15
            match_reasons_en.append(f"Your capabilities in {', '.join(common_skills)} will reduce external hiring costs.")
            match_reasons_ta.append(f"உங்கள் பணி அனுபவம் நிர்வாக செலவை குறைக்கும்.")

        # 4. Available Produce Synergies
        bp_produce = [p.lower() for p in bp.get("recommendedProduce", [])]
        matched_produce = []
        for p in user_produce:
            for rec in bp_produce:
                if p in rec or rec in p or rec == "all":
                    matched_produce.append(p)
                    break
        if matched_produce:
            score += 15
            match_reasons_en.append(f"Directly utilizes your existing farm produce: {', '.join(set(matched_produce)).title()}.")
            match_reasons_ta.append(f"உங்கள் பண்ணை விளைபொருட்களை ({', '.join(set(matched_produce)).title()}) நேரடியாக பயன்படுத்தலாம்.")

        # 5. District Cluster Priority
        recommended_districts = bp.get("recommendedDistricts", ["All"])
        if user_district in recommended_districts or "All" in recommended_districts:
            score += 5
            match_reasons_en.append(f"Strong regional presence & established farm ecosystem in {user_district}.")
            match_reasons_ta.append(f"{user_district} மாவட்டத்தில் இந்த தொழிலுக்கு நல்ல சந்தை வாய்ப்பு உள்ளது.")

        final_score = min(98, max(25, score))

        reasons = []
        for i in range(len(match_reasons_en)):
            reasons.append(BilingualText(en=match_reasons_en[i], ta=match_reasons_ta[i]))

        matched.append(
            BusinessIdeaItem(
                ideaId=bp["ideaId"],
                title=BilingualText(en=bp["title"]["en"], ta=bp["title"]["ta"]),
                category=bp["category"],
                matchScore=final_score,
                matchReasons=reasons,
                suitabilitySummary=BilingualText(en=bp["suitabilitySummary"]["en"], ta=bp["suitabilitySummary"]["ta"]),
                estimatedStartupCapex=bp["estimatedStartupCapex"],
                estimatedMonthlyOpex=bp["estimatedMonthlyOpex"],
                typicalBreakevenMonths=bp["typicalBreakevenMonths"],
                targetCustomers=[BilingualText(en=c["en"], ta=c["ta"]) for c in bp["targetCustomers"]],
                requiredSkillsAndEquipment=[BilingualText(en=e["en"], ta=e["ta"]) for e in bp["requiredSkillsAndEquipment"]],
                officialResources=bp["officialResources"],
                statutoryRequirements=[BilingualText(en=r["en"], ta=r["ta"]) for r in bp["statutoryRequirements"]],
                nonGuaranteeDisclaimer="Startup costs and timelines are indicative estimates based on TNAU DABD and EDII-TN benchmarks. No loan approval, subsidy sanction, or profit is guaranteed."
            )
        )

    # Sort descending by match score
    matched.sort(key=lambda x: x.matchScore, reverse=True)

    summary_ctx = {
        "locationDistrict": request.locationDistrict,
        "investmentBudget": request.investmentBudget,
        "availableProduce": request.availableProduce,
        "topRecommendation": matched[0].title.en if matched else None
    }

    return BusinessIdeaMatchResponse(
        matchedIdeas=matched,
        farmerContextSummary=summary_ctx,
        disclaimer="Matched enterprise proposals are educational templates for planning. Real enterprise viability depends on local market demand, raw material prices, and operational execution."
    )


def calculate_business_plan_finances(
    equipment_items: List[Dict[str, Any]],
    raw_material_inputs: List[Dict[str, Any]],
    operating_costs: Dict[str, float],
    pricing_strategy: Dict[str, Any]
) -> BusinessPlanCalculationResult:
    """
    Computes total startup capex, monthly operating expenses, gross monthly revenue,
    breakeven units, and breakeven payback timeline with itemized assumptions.
    """
    # 1. Total Startup Capex
    total_capex = 0.0
    for item in equipment_items:
        qty = float(item.get("quantity", 1.0) or 1.0)
        cost = float(item.get("unitCost", 0.0) or item.get("totalCost", 0.0) or 0.0)
        total_capex += qty * cost

    # 2. Total Monthly Opex
    raw_materials_monthly = 0.0
    for rm in raw_material_inputs:
        qty = float(rm.get("monthlyQuantity", 0.0) or 0.0)
        cost = float(rm.get("unitCost", 0.0) or 0.0)
        raw_materials_monthly += qty * cost

    other_opex = 0.0
    for k, v in operating_costs.items():
        other_opex += float(v or 0.0)

    total_monthly_opex = raw_materials_monthly + other_opex

    # 3. Monthly Revenue
    unit_selling_price = float(pricing_strategy.get("targetSellingPrice", 0.0) or 0.0)
    monthly_sales_units = float(pricing_strategy.get("expectedMonthlySalesUnits", 0.0) or 0.0)
    monthly_gross_revenue = unit_selling_price * monthly_sales_units

    # 4. Net Operating Surplus
    monthly_net_surplus = monthly_gross_revenue - total_monthly_opex

    # 5. Breakeven Volume & Months
    # Breakeven volume = Fixed opex / (Price per unit - Variable cost per unit)
    # Here, assume raw materials + packaging are variable (~60% of opex), rest fixed (~40%)
    fixed_opex = other_opex * 0.7  # labour, rent, electricity, maintenance
    variable_opex_per_unit = (raw_materials_monthly + (other_opex * 0.3)) / max(1.0, monthly_sales_units)
    contribution_margin = unit_selling_price - variable_opex_per_unit

    if contribution_margin > 0.0:
        breakeven_units = round(fixed_opex / contribution_margin, 1)
    else:
        breakeven_units = 0.0

    if monthly_net_surplus > 0.0 and total_capex > 0.0:
        breakeven_months = round(total_capex / monthly_net_surplus, 1)
    else:
        breakeven_months = 0.0

    assumptions = [
        f"Startup Capital Expenditure (Capex): ₹{total_capex:,.2f} based on {len(equipment_items)} itemized equipment lines.",
        f"Raw Material Monthly Inputs: ₹{raw_materials_monthly:,.2f} based on {len(raw_material_inputs)} ingredient lines.",
        f"Other Operating Monthly Expenses (Opex): ₹{other_opex:,.2f} (labour, electricity, logistics, packaging).",
        f"Unit Economics: Target selling price ₹{unit_selling_price:,.2f} against variable cost approx ₹{variable_opex_per_unit:,.2f}/unit.",
        f"Projected Monthly Volume: {monthly_sales_units:,.0f} units yielding estimated monthly gross revenue of ₹{monthly_gross_revenue:,.2f}."
    ]

    if monthly_net_surplus <= 0:
        assumptions.append("Caution: Current projected sales volume does not cover monthly operating expenses. Revise selling price or volume.")

    return BusinessPlanCalculationResult(
        totalStartupCapex=round(total_capex, 2),
        totalMonthlyOpex=round(total_monthly_opex, 2),
        monthlyGrossRevenue=round(monthly_gross_revenue, 2),
        monthlyNetOperatingSurplus=round(monthly_net_surplus, 2),
        breakevenMonthlyUnits=breakeven_units,
        breakevenMonths=breakeven_months,
        itemizedAssumptions=assumptions,
        disclaimer="Estimates reflect user-entered figures and institutional benchmarks. Profit and sales volumes are never guaranteed."
    )


# ----------------------------------------------------------------------------
# FARMER BUSINESS PLANS CRUD OPERATIONS
# ----------------------------------------------------------------------------

async def create_farmer_business_plan(farmer_user: Dict[str, Any], req: BusinessPlanCreateRequest) -> BusinessPlanModel:
    """Creates and persists an 8-step business plan in MongoDB."""
    col = get_farmer_business_plans_collection()
    plan_id = f"plan_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Calculate financial projections
    calc = calculate_business_plan_finances(
        equipment_items=req.wizardData.equipmentAndInfrastructure,
        raw_material_inputs=req.wizardData.rawMaterialInputs,
        operating_costs=req.wizardData.operatingCosts,
        pricing_strategy=req.wizardData.pricingStrategy
    )

    # Link relevant schemes based on ideaId
    linked_schemes = [
        {
            "name": "PM Formalisation of Micro food processing Enterprises (PMFME)",
            "link": "https://pmfme.mofpi.gov.in/",
            "subsidyType": "35% credit-linked capital subsidy up to ₹10 Lakhs"
        },
        {
            "name": "Agriculture Infrastructure Fund (AIF)",
            "link": "https://agriinfra.dac.gov.in/",
            "subsidyType": "3% interest subvention for post-harvest management projects"
        },
        {
            "name": "Udyam MSME Zero Cost Registration",
            "link": "https://udyamregistration.gov.in/",
            "subsidyType": "Statutory recognition & priority sector lending benefits"
        }
    ]

    doc = {
        "planId": plan_id,
        "farmerId": str(farmer_user.get("_id") or farmer_user.get("id") or "farmer_demo"),
        "farmerName": farmer_user.get("name", "Farmer"),
        "businessName": req.businessName,
        "ideaId": req.ideaId,
        "wizardData": req.wizardData.model_dump(),
        "financialCalculations": calc.model_dump(),
        "linkedSchemes": linked_schemes,
        "status": "draft",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    if col is not None:
        await col.insert_one(doc)

    logger.info(f"Created farmer business plan {plan_id} for farmer {farmer_user.get('name')}")
    return BusinessPlanModel(**doc)


async def get_farmer_business_plans(farmer_id: str) -> List[BusinessPlanModel]:
    """Retrieves all business plans for a specific farmer."""
    col = get_farmer_business_plans_collection()
    if col is None:
        return []
    cursor = col.find({"farmerId": str(farmer_id)}).sort("createdAt", -1)
    plans = []
    async for doc in cursor:
        doc.pop("_id", None)
        plans.append(BusinessPlanModel(**doc))
    return plans


async def get_farmer_business_plan_by_id(plan_id: str, farmer_id: Optional[str] = None) -> Optional[BusinessPlanModel]:
    """Retrieves a single business plan by planId with optional farmer ownership check."""
    col = get_farmer_business_plans_collection()
    if col is None:
        return None
    query: Dict[str, Any] = {"planId": plan_id}
    if farmer_id:
        query["farmerId"] = str(farmer_id)
    doc = await col.find_one(query)
    if not doc:
        return None
    doc.pop("_id", None)
    return BusinessPlanModel(**doc)


async def update_farmer_business_plan(plan_id: str, farmer_id: str, req: BusinessPlanUpdateRequest) -> Optional[BusinessPlanModel]:
    """Updates an existing business plan, re-running financial calculations if wizard data changed."""
    col = get_farmer_business_plans_collection()
    if col is None:
        return None

    existing = await col.find_one({"planId": plan_id, "farmerId": str(farmer_id)})
    if not existing:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    updates: Dict[str, Any] = {"updatedAt": now_iso}

    if req.businessName is not None:
        updates["businessName"] = req.businessName
    if req.status is not None:
        updates["status"] = req.status

    if req.wizardData is not None:
        updates["wizardData"] = req.wizardData.model_dump()
        calc = calculate_business_plan_finances(
            equipment_items=req.wizardData.equipmentAndInfrastructure,
            raw_material_inputs=req.wizardData.rawMaterialInputs,
            operating_costs=req.wizardData.operatingCosts,
            pricing_strategy=req.wizardData.pricingStrategy
        )
        updates["financialCalculations"] = calc.model_dump()

    await col.update_one({"planId": plan_id}, {"$set": updates})
    updated_doc = await col.find_one({"planId": plan_id})
    if updated_doc:
        updated_doc.pop("_id", None)
        return BusinessPlanModel(**updated_doc)
    return None


async def delete_farmer_business_plan(plan_id: str, farmer_id: str) -> bool:
    """Deletes a business plan with ownership verification."""
    col = get_farmer_business_plans_collection()
    if col is None:
        return False
    result = await col.delete_one({"planId": plan_id, "farmerId": str(farmer_id)})
    return result.deleted_count > 0


# ----------------------------------------------------------------------------
# VALUE-ADDED PRODUCTS CATALOG & COSTING ENGINE
# ----------------------------------------------------------------------------

def get_value_addition_products(raw_material: Optional[str] = None, method_category: Optional[str] = None) -> List[ValueAdditionProductBlueprint]:
    """
    Returns verified value-added product blueprints, filterable by raw material and processing method.
    """
    results: List[ValueAdditionProductBlueprint] = []
    for item in VALUE_ADDED_PRODUCT_BLUEPRINTS:
        if raw_material and raw_material.lower() not in item["rawMaterial"].lower():
            continue
        if method_category and method_category.lower() != item["processingMethodCategory"].lower():
            continue
        results.append(
            ValueAdditionProductBlueprint(
                productId=item["productId"],
                productName=BilingualText(en=item["productName"]["en"], ta=item["productName"]["ta"]),
                rawMaterial=item["rawMaterial"],
                processingMethod=item["processingMethod"],
                processingMethodCategory=item["processingMethodCategory"],
                fssaiCategory=item["fssaiCategory"],
                rawMaterialToFinishedRatio=item["rawMaterialToFinishedRatio"],
                typicalByproducts=item.get("typicalByproducts", []),
                shelfLifeAndStorage=BilingualText(en=item["shelfLifeAndStorage"]["en"], ta=item["shelfLifeAndStorage"]["ta"]),
                storageTemperature=item["storageTemperature"],
                requiredEquipment=item.get("requiredEquipment", []),
                ingredientsAndRecipe=item.get("ingredientsAndRecipe", []),
                standardOperatingProcedure=item.get("standardOperatingProcedure", []),
                foodSafetyAndHygiene=[BilingualText(en=h["en"], ta=h["ta"]) for h in item.get("foodSafetyAndHygiene", [])],
                packagingGuidance=BilingualText(en=item["packagingGuidance"]["en"], ta=item["packagingGuidance"]["ta"]),
                authoritativeReference=item.get("authoritativeReference", {}),
                potentialSalesChannels=item.get("potentialSalesChannels", []),
                trainingProviders=item.get("trainingProviders", [])
            )
        )
    return results


def get_value_addition_product_by_id(product_id: str) -> Optional[ValueAdditionProductBlueprint]:
    """Returns single product blueprint by productId."""
    for item in VALUE_ADDED_PRODUCT_BLUEPRINTS:
        if item["productId"] == product_id:
            return ValueAdditionProductBlueprint(
                productId=item["productId"],
                productName=BilingualText(en=item["productName"]["en"], ta=item["productName"]["ta"]),
                rawMaterial=item["rawMaterial"],
                processingMethod=item["processingMethod"],
                processingMethodCategory=item["processingMethodCategory"],
                fssaiCategory=item["fssaiCategory"],
                rawMaterialToFinishedRatio=item["rawMaterialToFinishedRatio"],
                typicalByproducts=item.get("typicalByproducts", []),
                shelfLifeAndStorage=BilingualText(en=item["shelfLifeAndStorage"]["en"], ta=item["shelfLifeAndStorage"]["ta"]),
                storageTemperature=item["storageTemperature"],
                requiredEquipment=item.get("requiredEquipment", []),
                ingredientsAndRecipe=item.get("ingredientsAndRecipe", []),
                standardOperatingProcedure=item.get("standardOperatingProcedure", []),
                foodSafetyAndHygiene=[BilingualText(en=h["en"], ta=h["ta"]) for h in item.get("foodSafetyAndHygiene", [])],
                packagingGuidance=BilingualText(en=item["packagingGuidance"]["en"], ta=item["packagingGuidance"]["ta"]),
                authoritativeReference=item.get("authoritativeReference", {}),
                potentialSalesChannels=item.get("potentialSalesChannels", []),
                trainingProviders=item.get("trainingProviders", [])
            )
    return None


def calculate_value_addition_profitability(req: ValueAdditionCalculationRequest) -> ValueAdditionCalculationResponse:
    """
    Computes precise product costing, yield recovery, processing loss, byproduct income,
    and unit profit margins using verified institutional conversion rates.
    """
    bp = get_value_addition_product_by_id(req.productId)
    if not bp:
        raise ValueError(f"Value addition blueprint '{req.productId}' not found in registry.")

    # 1. Yield & Waste Loss Determination
    standard_ratio = bp.rawMaterialToFinishedRatio
    if req.yieldLossPercentage is not None and req.yieldLossPercentage >= 0:
        effective_yield_ratio = max(0.05, 1.0 - (req.yieldLossPercentage / 100.0))
        effective_yield_percent = round(effective_yield_ratio * 100.0, 1)
        yield_loss_kg = round(req.rawMaterialQuantityKg * (req.yieldLossPercentage / 100.0), 2)
    else:
        effective_yield_ratio = standard_ratio
        effective_yield_percent = round(standard_ratio * 100.0, 1)
        yield_loss_kg = round(req.rawMaterialQuantityKg * (1.0 - standard_ratio), 2)

    finished_quantity = round(req.rawMaterialQuantityKg * effective_yield_ratio, 2)
    unit_size = req.finishedUnitSize if req.finishedUnitSize > 0 else 1.0
    units_count = int(finished_quantity / unit_size)

    # 2. Byproduct Yield & Revenue
    byproduct_qty = 0.0
    byproduct_revenue = 0.0
    if req.includeByproductRecovery and bp.typicalByproducts:
        first_bp = bp.typicalByproducts[0]
        bp_ratio = float(first_bp.get("yieldRatio", 0.0) or 0.0)
        default_val = float(first_bp.get("typicalValuePerKg", 0.0) or 0.0)
        price_per_kg = req.byproductSellingPricePerKg if req.byproductSellingPricePerKg is not None else default_val
        byproduct_qty = round(req.rawMaterialQuantityKg * bp_ratio, 2)
        byproduct_revenue = round(byproduct_qty * price_per_kg, 2)

    # 3. Itemized Expenses
    raw_material_expense = round(req.rawMaterialQuantityKg * req.rawMaterialCostPerKg, 2)
    processing_expense = round(req.processingCostPerKgOrBatch, 2)
    packaging_expense = round(units_count * req.packagingCostPerFinishedUnit, 2)
    labour_expense = round(req.labourCostTotal, 2)
    transport_expense = round(req.transportAndMarketingCost, 2)

    total_expense = round(
        raw_material_expense + processing_expense + packaging_expense + labour_expense + transport_expense,
        2
    )

    # 4. Revenue & Profitability
    finished_revenue = round(units_count * req.expectedSellingPricePerFinishedUnit, 2)
    total_gross_revenue = round(finished_revenue + byproduct_revenue, 2)
    gross_profit = round(total_gross_revenue - total_expense, 2)

    margin_percent = round((gross_profit / total_gross_revenue) * 100.0, 2) if total_gross_revenue > 0 else 0.0

    net_expense_after_byproduct = max(0.0, total_expense - byproduct_revenue)
    cost_per_unit = round(net_expense_after_byproduct / max(1, units_count), 2)
    net_profit_per_unit = round(req.expectedSellingPricePerFinishedUnit - cost_per_unit, 2)
    breakeven_selling_price = cost_per_unit

    assumptions = [
        f"Raw Material: {req.rawMaterialQuantityKg:,.1f} kg @ ₹{req.rawMaterialCostPerKg:,.2f}/kg = ₹{raw_material_expense:,.2f}.",
        f"Yield Recovery: {effective_yield_percent}% yield produces {finished_quantity:,.1f} finished units ({yield_loss_kg:,.1f} kg processing/moisture reduction).",
        f"Packaging: {units_count} units ({unit_size} kg/L pack) @ ₹{req.packagingCostPerFinishedUnit:,.2f} packaging cost/unit.",
        f"Byproduct Recovery: {byproduct_qty:,.1f} kg byproducts recovered yielding ₹{byproduct_revenue:,.2f} offset.",
        f"Total Cost of Production: ₹{total_expense:,.2f} yielding net unit production cost of ₹{cost_per_unit:,.2f}."
    ]

    return ValueAdditionCalculationResponse(
        productId=bp.productId,
        productName=bp.productName,
        rawMaterialQuantityKg=req.rawMaterialQuantityKg,
        effectiveYieldPercent=effective_yield_percent,
        yieldLossQuantityKg=yield_loss_kg,
        finishedProductQuantity=finished_quantity,
        finishedUnitsCount=units_count,
        unitSize=unit_size,
        byproductQuantityKg=byproduct_qty,
        byproductRevenue=byproduct_revenue,
        totalExpenses={
            "rawMaterial": raw_material_expense,
            "processing": processing_expense,
            "packaging": packaging_expense,
            "labour": labour_expense,
            "transport": transport_expense,
            "total": total_expense
        },
        finishedProductRevenue=finished_revenue,
        totalGrossRevenue=total_gross_revenue,
        estimatedGrossProfit=gross_profit,
        estimatedProfitMarginPercent=margin_percent,
        costPerFinishedUnit=cost_per_unit,
        netProfitPerFinishedUnit=net_profit_per_unit,
        breakevenSellingPricePerUnit=breakeven_selling_price,
        itemizedAssumptions=assumptions,
        authoritativeReference=bp.authoritativeReference,
        disclaimer="Yield ratios and processing steps cite official university and institute guidelines. Real farm gate profitability varies with raw material moisture, fuel efficiency, and market price realization."
    )
