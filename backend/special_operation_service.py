"""
Special Operation — From First Step to First Sale Service.
Interactive guided farming journey for complete beginners.
Backed by verified TNAU, ICAR, and TN Agriculture Department agronomic references.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId

from database import get_special_operation_journeys_collection
from notifications import create_in_app_notification

logger = logging.getLogger("special_operation_service")

# ============================================================================
# VERIFIED AGRONOMIC KNOWLEDGE REPOSITORY
# ============================================================================

VERIFIED_CROPS_CATALOG: Dict[str, Dict[str, Any]] = {
    "tomato": {
        "cropId": "tomato",
        "cropName": {
            "en": "Commercial Hybrid Tomato",
            "ta": "வணிக தக்காளி சாகுபடி"
        },
        "varietySuggestions": ["Shivam (Seminis)", "US-440", "PKM-1", "CO-3", "Ananya"],
        "durationDays": 125,
        "waterNeedLevel": "medium",
        "waterNeedText": {
            "en": "Moderate root-zone moisture; critical during flowering & fruit set. Drip irrigation saves 40-45% water.",
            "ta": "பூக்கும் மற்றும் காய் பிடிக்கும் பருவத்தில் மிதமான தொடர் ஈரப்பதம் அவசியம். சொட்டுநீர்ப் பாசனம் 45% நீரைச் சேமிக்கும்."
        },
        "budgetEstimatePerAcre": "₹35,000 - ₹48,000",
        "suitabilityReason": {
            "en": "Well suited for Salem & surrounding districts with warm climate and well-drained sandy loam or red soil. Excellent cash flow with 8-10 pickings.",
            "ta": "சேலம் மற்றும் தமிழகத்தின் வெப்ப தட்பவெப்ப நிலைக்கும் செம்மண் பூமிக்கும் மிக உகந்தது. தொடர் அறுவடை மூலம் சீரான வருமானம் தரும்."
        },
        "tradeOffsAndRisks": [
            {
                "en": "Market Price Fluctuation: Open market prices vary widely (₹10/kg to ₹60/kg). Direct selling via Uzhavar Sandhai mitigates trader margin loss.",
                "ta": "சந்தை விலை மாறுபாடு: பொது சந்தையில் விலை கிலோவுக்கு ₹10 முதல் ₹60 வரை மாறலாம். உழவர் சந்தை மூலம் நேரடியாக விற்பது லாபத்தைப் பாதுகாக்கும்."
            },
            {
                "en": "Frequent Harvesting Labour: Fruits ripen quickly and must be picked every 3-4 days to prevent spoilage on plant.",
                "ta": "தொடர் ஆட்கள் தேவை: பழங்கள் பழுக்கத் தொடங்கியதும் 3-4 நாட்களுக்கு ஒருமுறை கண்டிப்பாக பறிக்க வேண்டும்."
            },
            {
                "en": "Pest & Disease Scouting: Susceptible to leaf miner, early blight, and fruit borer; requires weekly scouting and pheromone traps.",
                "ta": "பூச்சி கண்காணிப்பு: இலைப்புழு மற்றும் காய்ப்புழு தாக்குதலை வாரந்தோறும் இனக்கவர்ச்சி பொறி வைத்து கண்காணிக்க வேண்டும்."
            }
        ],
        "marketChannels": [
            "Salem Uzhavar Sandhais (11 centers in district, zero commission)",
            "Salem Market Committee e-NAM Mandi (Electronic bidding)",
            "AgriBharat Direct Farm Gate & WhatsApp Order-Requests",
            "Local Hotels, Hostels & Vegetable Aggregators"
        ],
        "verifiedReference": {
            "institution": "TNAU Horticultural College & Research Institute / DDH Salem",
            "sourceUrl": "https://agritech.tnau.ac.in/horticulture/horti_vegetables_tomato.html",
            "reviewDate": "2026-10-20"
        },
        "preparationChecklist": [
            {
                "id": "prep_soil_test",
                "titleEn": "Collect 8-point zigzag soil sample and test at KVK / Agri office (pH 6.0 - 7.0 optimal)",
                "titleTa": "நிலத்தில் 8 இடங்களில் மண் மாதிரி எடுத்து KVK அல்லது வேளாண் அலுவலகத்தில் பரிசோதனை செய்தல் (pH 6.0-7.0)",
                "criticalNoteEn": "Avoid heavy waterlogged spots. If pH is below 6.0, apply agricultural lime.",
                "criticalNoteTa": "நீர் தேங்கும் இடங்களை தவிர்க்கவும். அமிலத்தன்மை இருந்தால் சுண்ணாம்பு இட வேண்டும்."
            },
            {
                "id": "prep_ploughing",
                "titleEn": "Deep summer ploughing (25-30 cm) followed by 2 passes of rotavator for fine tilth",
                "titleTa": "கோடை உழவு (25-30 செ.மீ) செய்து பின்னர் 2 முறை ரோட்டோவேட்டர் மூலம் மண்ணை கட்டியில்லாமல் உழுதல்",
                "criticalNoteEn": "Fine loose tilth ensures easy root penetration and weed seed suppression.",
                "criticalNoteTa": "மண் பொலபொலப்பாக இருப்பது வேர்கள் ஆழமாக இறங்க உதவும்."
            },
            {
                "id": "prep_manure",
                "titleEn": "Apply 10 tonnes well-decomposed Farm Yard Manure (FYM) or 2 tonnes Vermicompost per acre",
                "titleTa": "ஏக்கருக்கு 10 டன் மக்கிய தொழு உரம் அல்லது 2 டன் மண்புழு உரம் இட்டு சமன் செய்தல்",
                "criticalNoteEn": "Never apply raw dung which breeds white grubs and root rot fungus.",
                "criticalNoteTa": "பச்சை சாணத்தை இடக்கூடாது; அது வேர்ப்புழு மற்றும் வேரழுகல் நோயை உருவாக்கும்."
            },
            {
                "id": "prep_beds_drip",
                "titleEn": "Form raised beds (90 cm width, 15 cm height) or ridges & furrows at 60 cm spacing with drip laterals",
                "titleTa": "90 செ.மீ அகல பாத்திகள் அல்லது 60 செ.மீ இடைவெளியில் பார் அமைத்து சொட்டுநீர்க் குழாய் பொருத்துதல்",
                "criticalNoteEn": "Raised beds prevent collar rot during heavy sudden showers.",
                "criticalNoteTa": "மேட்டுப்பாத்தி அமைப்பது திடீர் மழையின் போது வேரழுகல் வராமல் பாதுகாக்கும்."
            }
        ],
        "plantingGuide": {
            "materialType": "25 to 30-day-old sturdy pro-tray seedlings with 4-5 true leaves",
            "spacingText": "60 cm between rows × 45 cm between plants (approx. 14,000 seedlings/acre)",
            "plantingDepth": "Cover root-plug completely with soil; avoid burying the stem collar too deep",
            "bestTimeOfDay": "Late afternoon (3:30 PM to 5:30 PM) followed by immediate light irrigation",
            "diagram": "Row [ 60 cm ] Row | Plant -- 45 cm -- Plant (Staggered zigzag pattern)"
        },
        "growthStages": [
            {
                "stageNumber": 1,
                "stageName": "Nursery & Field Establishment",
                "stageNameTa": "நாற்று நடுதல் & வேர் ஊன்றுதல்",
                "daysRange": "Days 1 - 20",
                "durationDays": 20,
                "tasks": [
                    "Dip seedling root balls in Pseudomonas fluorescens (10g/L) before transplanting",
                    "Provide light daily irrigation for the first 5 days until new leaves appear",
                    "Replace any dead or wilted seedlings within the first 7 days (gap filling)"
                ],
                "waterAdvisory": "Keep root zone moist without waterlogging",
                "pestWatch": "Cutworms and seedling damping-off"
            },
            {
                "stageNumber": 2,
                "stageName": "Active Vegetative Growth & Staking",
                "stageNameTa": "வளர்ச்சிப் பருவம் & முட்டு கொடுத்தல்",
                "daysRange": "Days 21 - 45",
                "durationDays": 25,
                "tasks": [
                    "Manual weeding or light inter-cultivation at Day 25",
                    "Apply top-dressing fertilizer / bio-fertilizer cocktail around plant base",
                    "Erect bamboo stakes or twine support to keep heavy fruit-bearing branches off wet ground",
                    "Install yellow sticky traps (12/acre) to trap whiteflies and leaf miners"
                ],
                "waterAdvisory": "Irrigate once in 3 days in sandy loam; check soil moisture with finger probe",
                "pestWatch": "Leaf miner serpentine mines, whitefly, and early leaf spots"
            },
            {
                "stageNumber": 3,
                "stageName": "Flowering & Fruit Set",
                "stageNameTa": "பூக்கும் மற்றும் பிஞ்சு பிடிக்கும் பருவம்",
                "daysRange": "Days 46 - 75",
                "durationDays": 30,
                "tasks": [
                    "Spray Panchagavya 3% or micronutrient spray during peak flowering to prevent flower drop",
                    "Maintain steady soil moisture — water deficit at this stage causes flower and small fruit drop",
                    "Hang pheromone traps for Helicoverpa fruit borer (4-5 traps per acre)"
                ],
                "waterAdvisory": "CRITICAL WATER PERIOD: Do not allow soil to crack or dry out",
                "pestWatch": "Flower drop, fruit borer entry holes on young green fruits"
            },
            {
                "stageNumber": 4,
                "stageName": "Fruit Enlargement & Colour Breaker",
                "stageNameTa": "காய் பருத்தல் & நிறம் மாறுதல்",
                "daysRange": "Days 76 - 100",
                "durationDays": 25,
                "tasks": [
                    "Monitor for Blossom End Rot (black base on fruit due to calcium deficiency) — apply gypsum if needed",
                    "Prune diseased or touching-ground lower senescent leaves for better air circulation",
                    "Arrange clean plastic harvesting crates; avoid rough gunny bags that crush bottom fruit"
                ],
                "waterAdvisory": "Uniform regular irrigation; alternating dry-and-flooded soil causes fruit cracking",
                "pestWatch": "Fruit borer, pin rot, blossom end rot"
            },
            {
                "stageNumber": 5,
                "stageName": "Harvesting, Grading & Direct Marketing",
                "stageNameTa": "அறுவடை, தரம் பிரித்தல் & சந்தைப்படுத்தல்",
                "daysRange": "Days 101 - 125",
                "durationDays": 25,
                "tasks": [
                    "Harvest early morning (6:00 AM - 9:00 AM) when fruits are cool and firm",
                    "Pick at Breaker stage (pink star on blossom end) for distant mandi; firm red for local Uzhavar Sandhai",
                    "Grade into Grade A (uniform, clean, unblemished) and Grade B (slight marks)",
                    "Transport in ventilated crates stacked max 4 high to market"
                ],
                "waterAdvisory": "Light watering after each harvest to support remaining fruit flushes",
                "pestWatch": "Post-harvest fruit rot"
            }
        ],
        "maturityIndicators": [
            "Blossom end displays faint pink star coloration ('Breaker' stage) for distant transport",
            "Firm red ripe color with glossy taut skin for same-day direct sales",
            "Fruit separates cleanly from calyx with gentle upward thumb twist without tearing flesh"
        ],
        "harvestHandling": {
            "pickingTechnique": "Twist gently upward with calyx intact. Do not yank or drop into crates.",
            "shadeCooling": "Immediately move filled crates to tree shade or packing shed to remove field heat.",
            "gradingRules": "Grade A: Firm, uniform size, zero cracks or caterpillar punctures. Grade B: Minor skin scratches, slightly irregular shape. Culls: Soft rot or deep punctures (do not pack).",
            "packaging": "25 kg ventilated plastic crates with paper lining. Never use 50 kg gunny sacks."
        },
        "benchmarkCostBreakdownPerAcre": [
            {"category": "land_prep", "itemName": {"en": "Tractor Summer Ploughing, Rotavator & Bed Formation", "ta": "டிராக்டர் உழவு, ரோட்டோவேட்டர் & பாத்தி அமைத்தல்"}, "benchmarkRatePerAcre": 3800.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "seeds", "itemName": {"en": "Pro-tray Certified Hybrid Seedlings (14,000 seedlings)", "ta": "சான்றளிக்கப்பட்ட குழித்தட்டு நாற்றுகள் (14,000 நாற்றுகள்)"}, "benchmarkRatePerAcre": 7000.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "fertilizer", "itemName": {"en": "Decomposed FYM (10 tons) + Bio-fertilizers (Azospirillum/PSB)", "ta": "மக்கிய தொழு உரம் (10 டன்) + உயிர் உரங்கள்"}, "benchmarkRatePerAcre": 8500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "irrigation", "itemName": {"en": "Drip Maintenance, Electricity & Pumping Charges", "ta": "சொட்டுநீர்ப் பாசன பராமரிப்பு & மின்சாரம்"}, "benchmarkRatePerAcre": 2500.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "plant_protection", "itemName": {"en": "Pheromone & Yellow Sticky Traps, Neem Oil, Biocontrols", "ta": "இனக்கவர்ச்சி & ஒட்டும் பொறிகள், வேப்பெண்ணெய்"}, "benchmarkRatePerAcre": 3500.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "labour", "itemName": {"en": "Transplanting, Staking & Manual Weeding Labour", "ta": "நாற்று நடுதல், முட்டு கொடுத்தல் & களையெடுக்கும் கூலி"}, "benchmarkRatePerAcre": 6500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "harvesting", "itemName": {"en": "Sequential Picking & Field Grading Labour (8 pickings)", "ta": "தொடர் அறுவடை & தரம் பிரிக்கும் கூலி (8 அறுவடைகள்)"}, "benchmarkRatePerAcre": 6000.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "transport", "itemName": {"en": "Plastic Crates Rental & Local Tempo Transport to Mandi", "ta": "கூடை வாடகை & உள்ளூர் ஆட்டோ/டெம்போ வண்டி வாடகை"}, "benchmarkRatePerAcre": 3200.0, "defaultQty": 1.0, "unit": "lot"}
        ]
    },

    "groundnut": {
        "cropId": "groundnut",
        "cropName": {
            "en": "Rainfed / Irrigated Groundnut",
            "ta": "நிலக்கடலை சாகுபடி"
        },
        "varietySuggestions": ["VRI 8 (Dharani)", "TMV 13", "CO 7", "Kadiri-6"],
        "durationDays": 105,
        "waterNeedLevel": "low_medium",
        "waterNeedText": {
            "en": "Low-to-moderate water requirement (400-450 mm). 4-5 irrigations sufficient if irrigated; flourishes in monsoon rain.",
            "ta": "குறைந்த-மிதமான நீர் தேவை (400-450 மி.மீ). 4-5 பாசனங்கள் போதுமானது; பருவமழையிலும் நன்கு வளரும்."
        },
        "budgetEstimatePerAcre": "₹22,000 - ₹30,000",
        "suitabilityReason": {
            "en": "Ideal low-risk crop for red sandy loam soils in Salem & North Tamil Nadu. Enriches soil with atmospheric nitrogen and has dependable mandi demand.",
            "ta": "சேலம் மற்றும் தமிழகத்தின் செம்மண் நிலங்களுக்கு ஏற்ற குறைவான ஆபத்துள்ள பயிர். தழைச்சத்தை நிலைநிறுத்தி மண்வளத்தைக் கூட்டும்."
        },
        "tradeOffsAndRisks": [
            {
                "en": "Low Initial Risk & Guaranteed Oilseed Mandi Demand: Steady local market absorption by oil mills and wholesale traders.",
                "ta": "குறைவான ஆபத்து & நிலையான தேவை: செக்கு எண்ணெய் ஆலைகள் மற்றும் மண்டிகளில் எப்போதும் நிலையான விற்பனை வாய்ப்பு."
            },
            {
                "en": "Unseasonal Harvest Rain Hazard: Heavy rain during maturity causes subterranean pod sprouting and digging difficulties.",
                "ta": "அறுவடைக்கால மழை ஆபத்து: முதிர்ச்சிப் பருவத்தில் அதிக மழை பெய்தால் நிலக்கடலை மண்ணிலேயே முளைத்துவிடும் அபாயம் உள்ளது."
            },
            {
                "en": "Pod Borer & Tikka Leaf Spot: Requires seed treatment and timely sulfur dusting if leaf spot appears.",
                "ta": "டிக்கா இலைப்புள்ளி நோய்: விதை நேர்த்தி செய்தலும், நோய் தென்பட்டால் கந்தக தூவுதலும் அவசியம்."
            }
        ],
        "marketChannels": [
            "Salem Regulated Mandis (Commercial Oilseed e-Auctions)",
            "Direct Wood-Pressed Oil Units (Chekku)",
            "AgriBharat Direct Marketplace",
            "Local Seed Selection & Farming Cooperatives"
        ],
        "verifiedReference": {
            "institution": "TNAU Regional Research Station Vridhachalam / Tindivanam",
            "sourceUrl": "https://agritech.tnau.ac.in/agriculture/agri_oilseeds_groundnut.html",
            "reviewDate": "2026-10-20"
        },
        "preparationChecklist": [
            {
                "id": "prep_soil_drainage",
                "titleEn": "Ensure well-drained friable sandy loam soil with pH 6.0 to 7.5",
                "titleTa": "நல்ல வடிகால் வசதியுள்ள பொலபொலப்பான மணற்பாங்கான செம்மண் நிலத்தை உறுதி செய்தல் (pH 6.0-7.5)",
                "criticalNoteEn": "Hard compacted clay prevents peg penetration into the soil.",
                "criticalNoteTa": "கடினமான களிமண் நிலத்தில் விழுதுகள் (pegs) பூமிக்குள் இறங்க முடியாது."
            },
            {
                "id": "prep_seed_treatment",
                "titleEn": "Treat 55 kg kernel seeds with Trichoderma viride (4g/kg) and Rhizobium culture",
                "titleTa": "55 கிலோ பருப்பு விதைகளை டிரைக்கோடெர்மா விரிடி (4கி/கிலோ) மற்றும் ரைசோபியம் கொண்டு விதை நேர்த்தி செய்தல்",
                "criticalNoteEn": "Prevents collar rot and enhances root nodule nitrogen fixation by 30%.",
                "criticalNoteTa": "வேரழுகல் நோயைத் தடுத்து, வேர்முடிச்சுகளில் தழைச்சத்து சேர்வதை 30% அதிகரிக்கும்."
            },
            {
                "id": "prep_gypsum_application",
                "titleEn": "Procure Gypsum (200 kg/acre) to apply in 2 splits (basal & pegging stage)",
                "titleTa": "ஜிப்சம் (ஏக்கருக்கு 200 கிலோ) இரு தவணைகளாக இட தயார் செய்தல் (அடி உரம் & விழுது இறங்கும் பருவம்)",
                "criticalNoteEn": "Calcium in gypsum is mandatory for full pod shell development without hollow kernels ('pops').",
                "criticalNoteTa": "ஜிப்சத்தில் உள்ள கால்சியம் நிலக்கடலை சொத்தையாகாமல் பருப்பு திரட்சியாக வர மிக அவசியம்."
            }
        ],
        "plantingGuide": {
            "materialType": "Certified, plump kernels with intact seed coat (VRI 8 variety)",
            "spacingText": "30 cm between rows × 10 cm between plants (approx. 130,000 plants/acre)",
            "plantingDepth": "Sow at 4 to 5 cm depth. Sowing deeper than 5 cm causes poor seedling emergence",
            "bestTimeOfDay": "Morning or early evening in moist soil bed",
            "diagram": "Row [ 30 cm ] Row | Seed - 10 cm - Seed (Planted in shallow furrows)"
        },
        "growthStages": [
            {
                "stageNumber": 1,
                "stageName": "Germination & Seedling Emergence",
                "stageNameTa": "முளைத்தல் & நாற்றுப் பருவம்",
                "daysRange": "Days 1 - 20",
                "durationDays": 20,
                "tasks": [
                    "Sow in optimum moisture; seedlings emerge within 5 to 7 days",
                    "Conduct visual inspection for cutworms or patchy germination",
                    "Light weeding at Day 18 to remove competing early weeds"
                ],
                "waterAdvisory": "Initial moisture critical for uniform germination",
                "pestWatch": "Collar rot, subterranean grubs"
            },
            {
                "stageNumber": 2,
                "stageName": "Vegetative Growth & Branching",
                "stageNameTa": "வளர்ச்சி & கிளைப்பு பருவம்",
                "daysRange": "Days 21 - 40",
                "durationDays": 20,
                "tasks": [
                    "Hand hoeing and light inter-cultivation before flowering",
                    "Do NOT disturb soil once flowering starts to protect tender pegs",
                    "Broadcast 100 kg gypsum per acre around root zones"
                ],
                "waterAdvisory": "Irrigate at Day 25 and Day 38 if rain is absent",
                "pestWatch": "Leaf miner, thrips, aphids"
            },
            {
                "stageNumber": 3,
                "stageName": "Flowering & Peg Penetration",
                "stageNameTa": "பூத்தல் & விழுது இறங்குதல்",
                "daysRange": "Days 41 - 70",
                "durationDays": 30,
                "tasks": [
                    "CRITICAL: Keep top 5 cm soil moist and loose so pegs easily penetrate the ground",
                    "Apply remaining 100 kg gypsum per acre at Day 45 and lightly earth up",
                    "Spray neem oil 2% or biocontrol if Tikka leaf spot symptoms appear"
                ],
                "waterAdvisory": "HIGHEST WATER SENSITIVITY: Pegs cannot enter dry hard crust",
                "pestWatch": "Tikka leaf spot, Spodoptera caterpillar"
            },
            {
                "stageNumber": 4,
                "stageName": "Pod Filling & Shell Hardening",
                "stageNameTa": "காய் உருவாதல் & பருப்பு திரட்சி",
                "daysRange": "Days 71 - 95",
                "durationDays": 25,
                "tasks": [
                    "Ensure adequate soil moisture for plump kernel development",
                    "Monitor 5 random plants by gently digging to inspect pod maturity",
                    "Cease irrigation 7 to 10 days before intended harvest"
                ],
                "waterAdvisory": "Avoid over-irrigation which induces pod rot",
                "pestWatch": "Pod borer, rust"
            },
            {
                "stageNumber": 5,
                "stageName": "Maturity, Digging & Sun-Drying",
                "stageNameTa": "முதிர்ச்சி, அறுவடை & உலர்த்துதல்",
                "daysRange": "Days 96 - 105",
                "durationDays": 10,
                "tasks": [
                    "Harvest when 75-80% pods show dark inner shell coloration",
                    "Pull or tractor-dig vines in morning; strip pods cleanly",
                    "Sun-dry harvested pods on clean tarpaulin for 4-5 days to 8-9% moisture",
                    "Bag in clean gunny bags and store on wooden pallets off damp floor"
                ],
                "waterAdvisory": "Zero irrigation; harvest in dry soil conditions",
                "pestWatch": "Storage bruchid beetles, aflatoxin fungus"
            }
        ],
        "maturityIndicators": [
            "Older leaves turn yellowish and naturally shed off the vine",
            "Cracked open test pods reveal dark brown/black coloration on the inner shell wall",
            "Kernels fill the shell tightly with distinctive pinkish-red seed coat"
        ],
        "harvestHandling": {
            "pickingTechnique": "Use blade digger or manual pulling when soil has slight friability. Pods shouldn't break off underground.",
            "shadeCooling": "Dry pods on tarpaulins under open sun for 4-5 days until moisture drops below 9% (kernel rattles inside shell).",
            "gradingRules": "Grade A: Well-filled 2-seeded pods, clean shell, zero mold. Grade B: Small or single-seeded pods. Pops (empty shells): Discard.",
            "packaging": "Breathable jute gunny bags (40 kg). Store elevated on wooden pallets."
        },
        "benchmarkCostBreakdownPerAcre": [
            {"category": "land_prep", "itemName": {"en": "Ploughing, Disc Harrowing & Bed Preparation", "ta": "டிராக்டர் உழவு & பாத்தி அமைத்தல்"}, "benchmarkRatePerAcre": 3000.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "seeds", "itemName": {"en": "Certified VRI 8 Kernel Seeds (55 kg @ ₹90/kg)", "ta": "சான்றளிக்கப்பட்ட VRI 8 பருப்பு விதை (55 கிலோ)"}, "benchmarkRatePerAcre": 4950.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "fertilizer", "itemName": {"en": "Gypsum (200 kg) + Basal Manures & Bio-fertilizers", "ta": "ஜிப்சம் (200 கிலோ) + அடி உரம் & உயிர் உரங்கள்"}, "benchmarkRatePerAcre": 4500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "irrigation", "itemName": {"en": "Protective Irrigations / Fuel / Electricity Charges", "ta": "பாசனக் கட்டணம் & மின்சாரம்/எரிபொருள்"}, "benchmarkRatePerAcre": 2000.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "plant_protection", "itemName": {"en": "Seed Treatment, Neem Oil & Biocontrol Sprays", "ta": "விதை நேர்த்தி, வேப்பெண்ணெய் & உயிரியல் பாதுகாப்பு"}, "benchmarkRatePerAcre": 1800.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "labour", "itemName": {"en": "Sowing, First Weeding & Gypsum Application Labour", "ta": "விதைத்தல், முதல் களையெடுப்பு & ஜிப்சம் இடும் கூலி"}, "benchmarkRatePerAcre": 4200.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "harvesting", "itemName": {"en": "Pod Digging, Stripping & Sun-Drying Labour", "ta": "செடி பிடுங்குதல், காய் உதிர்த்தல் & உலர்த்தும் கூலி"}, "benchmarkRatePerAcre": 4500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "transport", "itemName": {"en": "Gunny Bags & Transport to Regulated Market", "ta": "சாக்குப்பைகள் & ஒழுங்குமுறை விற்பனைக் கூட வண்டி வாடகை"}, "benchmarkRatePerAcre": 1800.0, "defaultQty": 1.0, "unit": "lot"}
        ]
    },

    "paddy": {
        "cropId": "paddy",
        "cropName": {
            "en": "Delta & Wetland Samba Paddy",
            "ta": "சம்பா நெல் சாகுபடி"
        },
        "varietySuggestions": ["CR 1009 Sub 1", "CO 52", "BPT 5204 (Andhra Ponni)", "Mappillai Samba"],
        "durationDays": 150,
        "waterNeedLevel": "high",
        "waterNeedText": {
            "en": "High water requirement (1200 mm). Requires 2-5 cm standing water during tillering and panicle development.",
            "ta": "அதிக நீர் தேவை (1200 மி.மீ). தூர்கட்டும் மற்றும் கதிர் வரும் பருவத்தில் 2-5 செ.மீ நீர் தேங்க வேண்டும்."
        },
        "budgetEstimatePerAcre": "₹26,000 - ₹35,000",
        "suitabilityReason": {
            "en": "Standard staple crop for wetland canal and assured borewell regions across Tamil Nadu. Unmatched MSP security through direct purchase centers (DPC).",
            "ta": "தமிழகத்தின் பாசன வசதியுள்ள நன்செய் நிலங்களுக்கு ஏற்ற முதன்மைப் பயிர். அரசு நேரடி நெல் கொள்முதல் நிலையங்கள் மூலம் உத்தரவாத விலை கிடைக்கும்."
        },
        "tradeOffsAndRisks": [
            {
                "en": "Direct Government Purchase (MSP): Protected from private price collapse by selling directly at TNCSC DPCs.",
                "ta": "அரசு நேரடி கொள்முதல்: TNCSC கொள்முதல் நிலையங்கள் மூலம் அரசு நிர்ணயித்த ஆதார விலை (MSP) நேரடியாக வங்கி கணக்கில் கிடைக்கும்."
            },
            {
                "en": "High Water Dependence: High failure risk if canal water ceases early or borewell yield drops during booting stage.",
                "ta": "அதிக நீர் சார்பு: கதிர் வரும் பருவத்தில் நீர் பற்றாக்குறை ஏற்பட்டால் பதர் அதிகமாகி பெரும் இழப்பு ஏற்படும்."
            },
            {
                "en": "Stem Borer & Blast Disease: Requires monitoring for 'dead hearts' and blast lesions during humid weather.",
                "ta": "குருத்துப்பூச்சி & குலைநோய்: பனி மற்றும் ஈரப்பதமான காலங்களில் குருத்துப்பூச்சி மற்றும் குலைநோயை கண்காணிக்க வேண்டும்."
            }
        ],
        "marketChannels": [
            "TNCSC Direct Purchase Centre (DPC) Mandis (MSP Direct Bank Transfer)",
            "Private Modern Rice Mills (Direct Bulk Procurement)",
            "AgriBharat Direct Marketplace (Heritage / Organic Rice Buyers)"
        ],
        "verifiedReference": {
            "institution": "Tamil Nadu Rice Research Institute (TRRI) Aduthurai / TNAU",
            "sourceUrl": "https://agritech.tnau.ac.in/agriculture/agri_paddy_index.html",
            "reviewDate": "2026-10-20"
        },
        "preparationChecklist": [
            {
                "id": "prep_puddling",
                "titleEn": "Puddle field thoroughly with cage wheels (2-3 passes) to create impervious subsoil hardpan",
                "titleTa": "கேஜ்வீல் கொண்டு சேற்றுழவு (2-3 முறை) செய்து நீர் கசியாதவாறு நிலத்தை சேறாக்குதல்",
                "criticalNoteEn": "Puddling reduces water percolation loss by 60%.",
                "criticalNoteTa": "சேற்றுழவு செய்வதால் நீர் பூமிக்குள் வீணாக உறிஞ்சப்படுவது 60% குறையும்."
            },
            {
                "id": "prep_leveling",
                "titleEn": "Perfect wooden board levelling to maintain uniform 2 cm water layer across entire plot",
                "titleTa": "மரப்பலகை கொண்டு நிலத்தை மட்டப்படுத்துதல் (அனைத்து இடங்களிலும் சீரான 2 செ.மீ நீர் நிற்க வேண்டும்)",
                "criticalNoteEn": "Uneven plots lead to exposed dry patches with rampant weed growth.",
                "criticalNoteTa": "மேடு பள்ளம் இருந்தால் மேடான பகுதியில் களைகள் மண்டி நெல் பயிர் பாதிக்கப்படும்."
            },
            {
                "id": "prep_green_manure",
                "titleEn": "Incorporate in-situ Daincha or Sunnhemp (5 tons/acre) during puddling",
                "titleTa": "சேற்றுழவின் போது தக்கைப்பூண்டு அல்லது சணப்பை போன்ற பசுந்தாள் உரங்களை மடக்கி உழுதல்",
                "criticalNoteEn": "Supplies 25-30 kg natural nitrogen and improves microbial soil health.",
                "criticalNoteTa": "மண்ணிற்கு 25-30 கிலோ இயற்கை தழைச்சத்தை வழங்கி நுண்ணுயிர் பெருக்கத்தை தூண்டும்."
            }
        ],
        "plantingGuide": {
            "materialType": "21 to 25-day-old single or double healthy seedlings from mat or wet nursery",
            "spacingText": "20 cm between rows × 10 cm between hills (approx. 50 hills per square meter)",
            "plantingDepth": "Shallow transplanting (2 to 3 cm depth). Deep planting (>4 cm) severely inhibits tillering",
            "bestTimeOfDay": "Morning in standing water of 2 cm",
            "diagram": "Row [ 20 cm ] Row | Hill (2 seedlings) -- 10 cm -- Hill"
        },
        "growthStages": [
            {
                "stageNumber": 1,
                "stageName": "Nursery & Transplanting",
                "stageNameTa": "நாற்றங்கால் & நடவுப் பருவம்",
                "daysRange": "Days 1 - 25",
                "durationDays": 25,
                "tasks": [
                    "Raise raised-bed wet nursery; sow salt-water selected certified seeds",
                    "Transplant 22-day seedlings at shallow 2 cm depth (2-3 seedlings/hill)",
                    "Maintain thin film of water (1-2 cm) during first week for quick root anchoring"
                ],
                "waterAdvisory": "1-2 cm shallow water to avoid drowning seedlings",
                "pestWatch": "Thrips, snail damage"
            },
            {
                "stageNumber": 2,
                "stageName": "Active Tillering & Weed Management",
                "stageNameTa": "தூர்கட்டும் பருவம் & களை மேலாண்மை",
                "daysRange": "Days 26 - 55",
                "durationDays": 30,
                "tasks": [
                    "Run cono-weeder at Day 30 and Day 45 to bury weeds and aerate root zone",
                    "Apply first top-dressing of urea/neem-coated urea or Panchagavya",
                    "Adopt Alternate Wetting & Drying (AWD) to save 30% irrigation water"
                ],
                "waterAdvisory": "Allow surface water to disappear for 1 day before re-flooding (AWD)",
                "pestWatch": "Yellow stem borer (dead hearts), leaf folder"
            },
            {
                "stageNumber": 3,
                "stageName": "Panicle Initiation & Booting",
                "stageNameTa": "கதிர் உருவாகும் & கருவுறும் பருவம்",
                "daysRange": "Days 56 - 95",
                "durationDays": 40,
                "tasks": [
                    "CRITICAL: Maintain continuous 3-5 cm water layer from panicle initiation to flowering",
                    "Apply second top-dress of Potash (MOP) to ensure plump heavy grains",
                    "Scout for neck blast lesions and bacterial leaf blight"
                ],
                "waterAdvisory": "DO NOT ALLOW WATER STRESS: Moisture stress here creates white sterile panicles",
                "pestWatch": "Stem borer (white ears), brown planthopper (BPH) at base"
            },
            {
                "stageNumber": 4,
                "stageName": "Flowering & Grain Filling",
                "stageNameTa": "பூத்தல் & பால் பிடிக்கும் பருவம்",
                "daysRange": "Days 96 - 130",
                "durationDays": 35,
                "tasks": [
                    "Flowering occurs between 9:00 AM and 11:30 AM — do not spray chemicals during these hours",
                    "Grain transitions from milky stage to dough stage",
                    "Monitor for Gundhi bug which punctures soft milky grains"
                ],
                "waterAdvisory": "Maintain 2 cm water layer until dough stage",
                "pestWatch": "Gundhi bug, false smut"
            },
            {
                "stageNumber": 5,
                "stageName": "Ripening, Drainage & Combine Harvesting",
                "stageNameTa": "முதிர்ச்சி, வடி கட்டல் & அறுவடை",
                "daysRange": "Days 131 - 150",
                "durationDays": 20,
                "tasks": [
                    "Completely drain water from field 10 to 12 days before harvest to firm up ground",
                    "Harvest when 85% grains turn golden yellow and moisture reaches 18-20%",
                    "Thresh, winnow, and sun-dry on clean threshing floor to 14% moisture for DPC sale",
                    "Book online queue token on AgriBharat Mandi Procurement module!"
                ],
                "waterAdvisory": "Field must be dry to support combine harvester weight",
                "pestWatch": "Rodents, grain moisture spoilage"
            }
        ],
        "maturityIndicators": [
            "Over 85% of grains on the panicle have turned from greenish to bright golden yellow",
            "Base of the panicle turns yellow and bends gracefully under grain weight",
            "Grain kernel cracks cleanly when pressed firmly between fingernails without milky oozing"
        ],
        "harvestHandling": {
            "pickingTechnique": "Combine harvester or manual sickle cutting at 10 cm above ground level.",
            "shadeCooling": "Thresh immediately and spread grains on tarpaulin under sun to reach 14% moisture standard for DPC.",
            "gradingRules": "Fair Average Quality (FAQ) norms: Maximum 17% moisture, max 1% foreign matter, max 3% damaged/discolored grains.",
            "packaging": "Clean 40 kg or 50 kg gunny bags stenciled with farmer name/token."
        },
        "benchmarkCostBreakdownPerAcre": [
            {"category": "land_prep", "itemName": {"en": "Tractor Puddling with Cage Wheels & Levelling", "ta": "டிராக்டர் கேஜ்வீல் சேற்றுழவு & மட்டப்பலகை"}, "benchmarkRatePerAcre": 3800.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "seeds", "itemName": {"en": "Certified Samba Paddy Seeds (30 kg @ ₹45/kg)", "ta": "சான்றளிக்கப்பட்ட சம்பா நெல் விதை (30 கிலோ)"}, "benchmarkRatePerAcre": 1350.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "fertilizer", "itemName": {"en": "Daincha Green Manure + Basal NPK + Potash", "ta": "தக்கைப்பூண்டு + அடி உரம் + பொட்டாஷ்"}, "benchmarkRatePerAcre": 5200.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "irrigation", "itemName": {"en": "Canal Maintenance / Submersible Pumping Energy", "ta": "பாசன நீர் பராமரிப்பு & பம்பிங் செலவு"}, "benchmarkRatePerAcre": 2800.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "plant_protection", "itemName": {"en": "Biocontrol Agents, Neem Formulations & Traps", "ta": "உயிரியல் பூச்சிக்கட்டுப்பாடு & இனக்கவர்ச்சி பொறிகள்"}, "benchmarkRatePerAcre": 2200.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "labour", "itemName": {"en": "Nursery Upkeep, Transplanting & Cono-Weeding Labour", "ta": "நாற்றுப் பிடுங்குதல், நடவு & கோனோவீடர் கூலி"}, "benchmarkRatePerAcre": 5800.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "harvesting", "itemName": {"en": "Combine Harvester Machine Rental & Threshing", "ta": "அறுவடை இயந்திர வாடகை & களம் சேர்த்தல்"}, "benchmarkRatePerAcre": 3500.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "transport", "itemName": {"en": "Bags, Loading & Transport to TNCSC DPC Mandi", "ta": "சாக்குப்பை, ஏற்றுக்கூலி & கொள்முதல் நிலைய வண்டி வாடகை"}, "benchmarkRatePerAcre": 2200.0, "defaultQty": 1.0, "unit": "lot"}
        ]
    },

    "tapioca": {
        "cropId": "tapioca",
        "cropName": {
            "en": "Salem Industrial & Sago Tapioca",
            "ta": "சேலம் மரவள்ளிக்கிழங்கு சாகுபடி"
        },
        "varietySuggestions": ["Co (Tp) 4", "Co (Tp) 5", "Mulluvadi 1", "H-226"],
        "durationDays": 280,
        "waterNeedLevel": "low_medium",
        "waterNeedText": {
            "en": "Drought hardy once established. 10-12 light irrigations across entire 9-month lifecycle.",
            "ta": "வறட்சியைத் தாங்கக்கூடியது. 9 மாத காலத்திற்கு 10-12 மிதமான பாசனங்களே போதுமானது."
        },
        "budgetEstimatePerAcre": "₹32,000 - ₹44,000",
        "suitabilityReason": {
            "en": "Signature commercial crop of Salem District. Thrives in red sandy soils with direct institutional marketing via Sagoserve and 350+ local sago mills.",
            "ta": "சேலம் மாவட்டத்தின் பிரதான பணப்பயிர். செம்மண் பூமியில் செழித்து வளரும்; சாகோசர்வ் மற்றும் ஆலைகள் மூலம் உறுதியான விற்பனை உண்டு."
        },
        "tradeOffsAndRisks": [
            {
                "en": "Direct Industrial Demand (Sagoserve Linkage): Immediate bulk sale to starch extraction mills based on starch point testing.",
                "ta": "நேரடி தொழிற்துறை தேவை: சேலம் சாகோசர்வ் மற்றும் ஆலைகளில் கிழங்கின் மாவுச்சத்தின் அடிப்படையில் உடனடி கொள்முதல்."
            },
            {
                "en": "Long Gestation Period (9-10 Months): Capital and land remain committed for nearly an entire calendar year before cash realization.",
                "ta": "நீண்ட கால முதலீடு: அறுவடைக்கு 9 முதல் 10 மாதங்கள் ஆவதால் ஒரு முழு ஆண்டிற்கு நிலமும் மூலதனமும் முடங்கும்."
            },
            {
                "en": "Cassava Mosaic Virus & Red Mite: Transmitted by whitefly; requires virus-free stem setts and early vector control.",
                "ta": "தேமல் நோய் (மசைக் வைரஸ்) மற்றும் சிவப்பு சிலந்தி: வெள்ளை ஈக்களால் பரவும்; நோய் தாக்காத தரமான குச்சிகளை நடுவது மிக முக்கியம்."
            }
        ],
        "marketChannels": [
            "Salem Sagoserve Starch & Sago Industrial Mandis",
            "Local Tapioca Processing Mills (Attur, Yethapur, Rasipuram)",
            "Uzhavar Sandhai (Table Culinary Varieties)"
        ],
        "verifiedReference": {
            "institution": "TNAU Tapioca & Castor Research Station (TCRS) Yethapur, Salem",
            "sourceUrl": "https://tnau.ac.in/",
            "reviewDate": "2026-10-20"
        },
        "preparationChecklist": [
            {
                "id": "prep_deep_plough",
                "titleEn": "Deep ploughing (35 cm) to loosen soil sub-layer for unrestricted tuber expansion",
                "titleTa": "கிழங்கு தடையின்றி பருத்து வளர 35 செ.மீ ஆழ உழவு செய்து மண்ணை தளர்த்துதல்",
                "criticalNoteEn": "Hard compacted subsurface soils result in thin, stunted, pencil-like tubers.",
                "criticalNoteTa": "அடிமண் கடினமாக இருந்தால் கிழங்கு பருக்காமல் மெலிந்து போகும்."
            },
            {
                "id": "prep_ridges_furrows",
                "titleEn": "Form high ridges and furrows at 90 cm spacing for good drainage",
                "titleTa": "90 செ.மீ இடைவெளியில் உயரமான பார்கள் மற்றும் வாய்க்கால்கள் அமைத்தல்",
                "criticalNoteEn": "Tapioca tubers quickly rot if submerged in stagnant water for >48 hours.",
                "criticalNoteTa": "48 மணி நேரத்திற்கு மேல் நீர் தேங்கினால் கிழங்கு அழுகிவிடும்."
            },
            {
                "id": "prep_stem_setts",
                "titleEn": "Select 15 cm healthy stem cuttings ('setts') with 8-10 prominent buds from mosaic-free mother plants",
                "titleTa": "தேமல் நோய் தாக்காத 8-10 ஆரோக்கியமான மொட்டுகள் கொண்ட 15 செ.மீ தண்டு குச்சிகளை தேர்வு செய்தல்",
                "criticalNoteEn": "Never use thin immature top shoots or diseased woody stems.",
                "criticalNoteTa": "முதிராத நுனிக்குச்சிகளையோ, நோய் தாக்கிய தண்டுகளையோ நடவுக்கு பயன்படுத்தக் கூடாது."
            }
        ],
        "plantingGuide": {
            "materialType": "15 cm healthy mature setts with clean horizontal cut",
            "spacingText": "90 cm between ridges × 90 cm between plants (approx. 4,800 setts per acre)",
            "plantingDepth": "Insert vertically 5 cm into ridge crest with buds pointing upward. Avoid inverted planting",
            "bestTimeOfDay": "Morning or evening into irrigated moist ridge crests",
            "diagram": "Ridge [ 90 cm ] Ridge | Sett (Vertical 5 cm) -- 90 cm -- Sett"
        },
        "growthStages": [
            {
                "stageNumber": 1,
                "stageName": "Sprouting & Sett Establishment",
                "stageNameTa": "துளிர்த்தல் & வேரூன்றுதல்",
                "daysRange": "Days 1 - 30",
                "durationDays": 30,
                "tasks": [
                    "Dip stem setts in Carbendazim + Malathion solution before planting",
                    "Plant vertically on ridge crest; shoots sprout within 10-14 days",
                    "Replace any dead setts within 20 days (gap filling)"
                ],
                "waterAdvisory": "Initial irrigation at planting followed by life irrigation at Day 3",
                "pestWatch": "White grubs, termite damage to setts"
            },
            {
                "stageNumber": 2,
                "stageName": "Shoot Thinning & Vegetative Canopy",
                "stageNameTa": "துளிர் கழித்தல் & வளர்ச்சிப் பருவம்",
                "daysRange": "Days 31 - 90",
                "durationDays": 60,
                "tasks": [
                    "Retain only 2 vigorous shoots per plant at Day 45; remove extra tender shoots",
                    "First manual weeding and earth up ridges to support stem stability",
                    "Apply top dressing of Urea and Potash at Day 60"
                ],
                "waterAdvisory": "Light irrigation once in 10-12 days",
                "pestWatch": "Spiralling whitefly, mealybugs"
            },
            {
                "stageNumber": 3,
                "stageName": "Tuber Initiation & Expansion",
                "stageNameTa": "கிழங்கு உருவாதல் & பருத்தல் பருவம்",
                "daysRange": "Days 91 - 180",
                "durationDays": 90,
                "tasks": [
                    "CRITICAL: Roots transition into storage tubers — apply second dose of Potash for starch accumulation",
                    "Maintain soil loose around root zone; check ridges for cracks exposing tubers to sunlight",
                    "Spray neem oil if red spider mites appear during dry hot weather"
                ],
                "waterAdvisory": "Crucial watering phase: Alternate wet/dry cycles promote tuber swelling",
                "pestWatch": "Red spider mites, cassava mosaic virus symptoms"
            },
            {
                "stageNumber": 4,
                "stageName": "Starch Accumulation & Bulking",
                "stageNameTa": "மாவுச்சத்து சேருதல் பருவம்",
                "daysRange": "Days 181 - 250",
                "durationDays": 70,
                "tasks": [
                    "Starch content peaks; avoid heavy nitrogen fertilizer which promotes leafiness over tuber starch",
                    "Test 2 sample plants for tuber size and starch points (sample factory testing)",
                    "Maintain ridges weed-free"
                ],
                "waterAdvisory": "Reduce irrigation frequency to concentrate starch content",
                "pestWatch": "Tuber rot in waterlogged patches"
            },
            {
                "stageNumber": 5,
                "stageName": "Tuber Harvest & Sagoserve Delivery",
                "stageNameTa": "அறுவடை & சாகோசர்வ்/ஆலை விற்பனை",
                "daysRange": "Days 251 - 280",
                "durationDays": 30,
                "tasks": [
                    "Withhold water 15 days before harvest to maximize dry matter and ease pulling",
                    "Cut top stem at 30 cm height; pull stem manually or with tractor hook",
                    "Harvest early morning; deliver to starch factory or market within 24 hours (tapioca deteriorates quickly after harvest)",
                    "Save top mature healthy stems for next season planting material"
                ],
                "waterAdvisory": "Completely dry before harvest",
                "pestWatch": "Post-harvest physiological deterioration (blue vascular streaking after 48h)"
            }
        ],
        "maturityIndicators": [
            "Canopy naturally sheds 60-70% leaves, leaving bare woody stems with tuft at top",
            "Soil around plant base shows prominent radial cracks from expanding tuber girth",
            "Sample dug tuber snaps cleanly with crisp white flesh and milky high-starch sap"
        ],
        "harvestHandling": {
            "pickingTechnique": "Slash stems at 30 cm height. Pull upward using the remaining stem as lever.",
            "shadeCooling": "Deliver to factory/mandi within 24-36 hours. Tapioca rapidly loses starch and turns black inside after 48 hours.",
            "gradingRules": "High starch points (28-32 points measured by hydrometer test) command premium payment.",
            "packaging": "Open tractor trolley or tempo in bulk. No bagging required for factory delivery."
        },
        "benchmarkCostBreakdownPerAcre": [
            {"category": "land_prep", "itemName": {"en": "Deep Tractor Ploughing, Levelling & High Ridges Formation", "ta": "டிராக்டர் ஆழ உழவு & உயரமான பார்கள் அமைத்தல்"}, "benchmarkRatePerAcre": 4200.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "seeds", "itemName": {"en": "Certified Disease-Free Stem Cuttings (4,800 setts)", "ta": "சான்றளிக்கப்பட்ட ஆரோக்கியமான தண்டுக்குச்சிகள் (4,800)"}, "benchmarkRatePerAcre": 3800.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "fertilizer", "itemName": {"en": "FYM (8 tons) + NPK Fertilizers (High Potash for Starch)", "ta": "தொழு உரம் (8 டன்) + பொட்டாஷ் உரங்கள்"}, "benchmarkRatePerAcre": 7800.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "irrigation", "itemName": {"en": "10-12 Light Irrigations Across 9 Months (Energy & Labor)", "ta": "9 மாதங்களுக்கான 10-12 பாசன செலவு & மின்சாரம்"}, "benchmarkRatePerAcre": 3500.0, "defaultQty": 1.0, "unit": "acre"},
            {"category": "plant_protection", "itemName": {"en": "Sett Dip Treatment, Whitefly & Red Mite Protection", "ta": "குச்சி நேர்த்தி, வெள்ளை ஈ & சிவப்பு சிலந்தி கட்டுப்பாடு"}, "benchmarkRatePerAcre": 2500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "labour", "itemName": {"en": "Planting, Shoot Thinning, Earthing-Up & Weeding", "ta": "நடுதல், துளிர் கழித்தல் & பாருக்கு மண் அணைக்கும் கூலி"}, "benchmarkRatePerAcre": 5500.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "harvesting", "itemName": {"en": "Top Slashing, Tuber Pulling, Cleaning & Loading", "ta": "தண்டு வெட்டுதல், கிழங்கு பிடுங்குதல் & வண்டியில் ஏற்றுதல்"}, "benchmarkRatePerAcre": 6000.0, "defaultQty": 1.0, "unit": "lot"},
            {"category": "transport", "itemName": {"en": "Tractor Trolley Transport to Salem Sago Mill / Mandi", "ta": "சேலம் சாகோ ஆலைக்கு டிராக்டர் வண்டி வாடகை"}, "benchmarkRatePerAcre": 3500.0, "defaultQty": 1.0, "unit": "lot"}
        ]
    }
}


# ============================================================================
# SERVICE LOGIC & RECOMMENDATION MATCHING
# ============================================================================

def normalize_land_to_acres(area: float, unit: str) -> float:
    """Converts user land input to normalized acres."""
    u = (unit or "acres").lower().strip()
    if u in ["cent", "cents"]:
        return round(area * 0.01, 3)
    elif u in ["gunta", "guntas"]:
        return round(area * 0.025, 3)
    elif u in ["sq_ft", "sqft", "square_feet"]:
        return round(area / 43560.0, 3)
    return round(area * 1.0, 3)


def get_candidate_crops_for_profile(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Ranks verified candidate crops based on the beginner farmer's inputs.
    Gracefully handles 'unknown' inputs without penalizing valid crops.
    """
    water = profile.get("waterAvailability", "unknown")
    soil = profile.get("soilType", "unknown")
    budget = profile.get("budgetRange", "unknown")
    goal = profile.get("farmingGoal", "commercial_income")
    labour = profile.get("availableLabour", "unknown")
    district = profile.get("district", "Salem")

    recommendations: List[Dict[str, Any]] = []

    for crop_id, crop_info in VERIFIED_CROPS_CATALOG.items():
        score = 80  # Base suitability

        # Water compatibility
        if water == "ample_borewell":
            if crop_id in ["tomato", "paddy"]:
                score += 15
            elif crop_id in ["groundnut", "tapioca"]:
                score += 10
        elif water == "rainfed_only":
            if crop_id in ["groundnut"]:
                score += 15
            elif crop_id == "paddy":
                score -= 40  # Inadvisable for rainfed
            elif crop_id == "tomato":
                score -= 10
        elif water == "canal_seasonal":
            if crop_id in ["paddy", "groundnut", "tapioca"]:
                score += 12

        # Soil compatibility
        if soil in ["red_sandy_loam", "alluvial"]:
            if crop_id in ["tomato", "groundnut", "tapioca"]:
                score += 10
        elif soil == "clay_loam":
            if crop_id == "paddy":
                score += 15
            elif crop_id == "groundnut":
                score -= 10  # Peg penetration difficult in heavy clay

        # Budget matching
        if budget == "micro_under_15k":
            if crop_id in ["groundnut"]:
                score += 15
            elif crop_id == "tomato":
                score -= 15  # Higher input cost
        elif budget in ["medium_35k_75k", "flexible_above_75k"]:
            if crop_id in ["tomato", "tapioca"]:
                score += 10

        # Goal matching
        if goal == "commercial_income":
            if crop_id in ["tomato", "tapioca"]:
                score += 10
        elif goal == "low_risk_learning":
            if crop_id in ["groundnut"]:
                score += 15
            elif crop_id == "tomato":
                score -= 5

        # District booster (Salem specific specialties)
        if district.lower() == "salem":
            if crop_id in ["tapioca", "tomato"]:
                score += 8

        # Cap score between 30 and 98
        final_score = max(35, min(98, score))

        recommendations.append({
            "cropId": crop_id,
            "cropName": crop_info["cropName"],
            "varietySuggestions": crop_info["varietySuggestions"],
            "durationDays": crop_info["durationDays"],
            "suitabilityScore": final_score,
            "suitabilityReason": crop_info["suitabilityReason"],
            "waterNeedLevel": crop_info["waterNeedLevel"],
            "waterNeedText": crop_info["waterNeedText"],
            "budgetEstimatePerAcre": crop_info["budgetEstimatePerAcre"],
            "tradeOffsAndRisks": crop_info["tradeOffsAndRisks"],
            "marketChannels": crop_info["marketChannels"],
            "verifiedReference": crop_info["verifiedReference"]
        })

    # Sort descending by score
    recommendations.sort(key=lambda x: x["suitabilityScore"], reverse=True)
    return recommendations


def get_crop_agronomic_guide(crop_id: str) -> Optional[Dict[str, Any]]:
    """Returns complete agronomic guide, checklists, stages, and costs for a chosen crop."""
    cid = (crop_id or "").lower().strip()
    raw = VERIFIED_CROPS_CATALOG.get(cid)
    if not raw:
        return None

    guide = dict(raw)
    
    # 1. landPreparation
    prep_steps = []
    for item in raw.get("preparationChecklist", []):
        prep_steps.append({
            "id": item.get("id"),
            "title": {"en": item.get("titleEn", ""), "ta": item.get("titleTa", "")},
            "description": {"en": item.get("criticalNoteEn", ""), "ta": item.get("criticalNoteTa", "")},
            "kvkContactAlert": {"en": "Contact Salem KVK or Block Agricultural Officer if severe anomalies occur.", "ta": "கடுமையான பாதிப்பு இருப்பின் சேலம் KVK அல்லது வட்டார வேளாண் அலுவலரை அணுகவும்."} if "soil" in item.get("id", "") else None
        })
    guide["landPreparation"] = {"steps": prep_steps}

    # 2. plantingInstructions
    pg = raw.get("plantingGuide", {})
    guide["plantingInstructions"] = {
        "seedRatePerAcre": {"en": pg.get("materialType", "Standard rate"), "ta": pg.get("materialType", "நிலையான அளவு")},
        "spacing": {
            "rowToRowCm": 60 if cid in ("tomato", "tapioca") else 30,
            "plantToPlantCm": 45 if cid == "tomato" else (90 if cid == "tapioca" else 10),
            "diagramText": {"en": pg.get("diagram", ""), "ta": pg.get("spacingText", "")}
        },
        "plantingDepthCm": 2,
        "nurseryAndSowingMethod": {"en": pg.get("materialType", ""), "ta": pg.get("materialType", "")},
        "idealTimingOfDay": {"en": pg.get("bestTimeOfDay", "Late afternoon"), "ta": pg.get("bestTimeOfDay", "மாலை வேளை")}
    }

    # 3. cropCareStages
    stages_list = []
    for st in raw.get("growthStages", []):
        tasks = []
        for t in st.get("tasks", []):
            tasks.append({
                "category": "ipm" if "scout" in t.lower() or "watch" in t.lower() or "trap" in t.lower() else ("nutrients" if "fertil" in t.lower() or "manure" in t.lower() or "top-dress" in t.lower() else "irrigation"),
                "task": {"en": t, "ta": t},
                "criticality": "critical" if st.get("stageNumber") in (1, 3) else "high"
            })
        stages_list.append({
            "stageNumber": st.get("stageNumber"),
            "stageName": {"en": st.get("stageName", ""), "ta": st.get("stageNameTa", st.get("stageName", ""))},
            "durationDays": st.get("durationDays", 20),
            "tasks": tasks,
            "smartFeaturesPrompt": {
                "feature": "disease" if "pest" in st.get("pestWatch", "").lower() else "irrigation",
                "message": {"en": f"Scout alert: {st.get('pestWatch', '')}", "ta": f"கண்காணிப்பு: {st.get('pestWatch', '')}"}
            } if st.get("pestWatch") else None
        })
    guide["cropCareStages"] = stages_list

    # 4. harvestReadiness
    hg = raw.get("harvestGuide", {})
    guide["harvestReadiness"] = {
        "maturityIndicators": [{"en": m, "ta": m} for m in hg.get("maturitySigns", [])],
        "harvestingMethod": {"en": hg.get("harvestMethod", ""), "ta": hg.get("harvestMethod", "")},
        "postHarvestCare": [{"en": p, "ta": p} for p in hg.get("gradingAndPacking", [])],
        "gradingStandards": [
            {"grade": "Grade A", "description": {"en": "Uniform, mature, blemish-free", "ta": "சீரான, பழுத்த, காயமில்லாத முதல் தரம்"}},
            {"grade": "Grade B", "description": {"en": "Minor variance in size or curve", "ta": "சிறு அளவு மாறுபாடு கொண்ட இரண்டாம் தரம்"}},
            {"grade": "Cull / Processing", "description": {"en": "Overripe or blemished", "ta": "சாறு பிழிவதற்கு அல்லது உழவர் உரம்"}}
        ],
        "storageAdvisory": {"en": hg.get("storageAndShelfLife", ""), "ta": hg.get("storageAndShelfLife", "")},
        "safetyCaution": {"en": "Never apply chemical pesticide sprays within 7 days of harvest.", "ta": "அறுவடைக்கு 7 நாட்களுக்குள் எந்தவொரு பூச்சிக்கொல்லியும் தெளிக்கக் கூடாது."}
    }

    return guide


def calculate_crop_stage_timeline(crop_id: str, planting_date_str: Optional[str]) -> Dict[str, Any]:
    """
    Computes real calendar dates for every stage from the farmer's actual planting date.
    Calculates current day offset, active stage, and days remaining.
    """
    guide = get_crop_agronomic_guide(crop_id)
    if not guide:
        return {"error": f"Unknown crop: {crop_id}"}

    stages = guide.get("growthStages", [])
    total_duration = guide.get("durationDays", 120)

    if not planting_date_str:
        return {
            "hasPlantingDate": False,
            "totalDurationDays": total_duration,
            "stages": stages,
            "currentDay": 0,
            "currentStageNumber": 1,
            "percentComplete": 0
        }

    try:
        p_date = datetime.strptime(planting_date_str[:10], "%Y-%m-%d").date()
    except Exception:
        p_date = datetime.now(timezone.utc).date()

    today = datetime.now(timezone.utc).date()
    days_elapsed = (today - p_date).days
    current_day = max(1, days_elapsed + 1)
    percent_complete = min(100, max(0, int((current_day / total_duration) * 100)))

    calculated_stages: List[Dict[str, Any]] = []
    cumulative_days = 0
    active_stage_num = 1

    for stage in stages:
        stage_duration = stage.get("durationDays", 20)
        stage_start = p_date + timedelta(days=cumulative_days)
        stage_end = stage_start + timedelta(days=stage_duration - 1)
        cumulative_days += stage_duration

        is_active = stage_start <= today <= stage_end
        is_completed = today > stage_end
        is_upcoming = today < stage_start

        if is_active:
            active_stage_num = stage.get("stageNumber", 1)

        stage_copy = dict(stage)
        stage_copy["calculatedStartDate"] = stage_start.strftime("%Y-%m-%d")
        stage_copy["calculatedEndDate"] = stage_end.strftime("%Y-%m-%d")
        stage_copy["status"] = "completed" if is_completed else ("active" if is_active else "upcoming")
        calculated_stages.append(stage_copy)

    # If past total duration, active stage is last
    if days_elapsed >= total_duration:
        active_stage_num = len(stages)

    expected_harvest_date = p_date + timedelta(days=total_duration)

    return {
        "hasPlantingDate": True,
        "plantingDate": p_date.strftime("%Y-%m-%d"),
        "expectedHarvestDate": expected_harvest_date.strftime("%Y-%m-%d"),
        "totalDurationDays": total_duration,
        "daysElapsed": days_elapsed,
        "currentDay": current_day,
        "percentComplete": percent_complete,
        "currentStageNumber": active_stage_num,
        "currentActiveStageNumber": active_stage_num,
        "stages": calculated_stages
    }


def generate_default_cost_worksheet(crop_id: str, land_acres: float = 1.0) -> Dict[str, Any]:
    """Generates transparent, editable input-cost worksheet scaled to farmer's acreage."""
    guide = get_crop_agronomic_guide(crop_id)
    if not guide:
        return {"entries": [], "totalOperatingCost": 0.0, "costPerUnitArea": 0.0}

    benchmarks = guide.get("benchmarkCostBreakdownPerAcre", [])
    scale = max(0.1, land_acres)
    entries: List[Dict[str, Any]] = []
    total_cost = 0.0

    for b in benchmarks:
        scaled_rate = round(b.get("benchmarkRatePerAcre", 1000.0) * scale, 2)
        total_cost += scaled_rate
        entries.append({
            "category": b.get("category"),
            "itemName": b.get("itemName"),
            "benchmarkRatePerAcre": b.get("benchmarkRatePerAcre"),
            "userQuantity": scale,
            "userUnitPrice": b.get("benchmarkRatePerAcre"),
            "isUserEdited": False,
            "notes": f"Baseline institutional benchmark for {scale} acre(s)"
        })

    return {
        "entries": entries,
        "totalOperatingCost": round(total_cost, 2),
        "costPerUnitArea": round(total_cost / scale, 2),
        "disclaimer": "Estimates are illustrative guidelines based on TNAU Cost of Cultivation benchmarks. Profit is never guaranteed."
    }


# ============================================================================
# DATABASE PERSISTENCE & JOURNEY LIFECYCLE
# ============================================================================

async def get_or_create_journey(
    farmer_id: str,
    farmer_name: str,
    farmer_phone: str,
    initial_district: Optional[str] = "Salem"
) -> Dict[str, Any]:
    """
    Retrieves the farmer's active Special Operation journey from MongoDB.
    If none exists, initializes a fresh Step 1 journey.
    """
    col = get_special_operation_journeys_collection()
    if col is None:
        raise RuntimeError("Database unavailable.")

    existing = await col.find_one({"farmerId": farmer_id, "status": {"$in": ["in_progress", "paused", "completed"]}}, {"_id": 0})
    if existing:
        return existing

    # Create new journey
    now_iso = datetime.now(timezone.utc).isoformat()
    journey_id = f"SOJ-{datetime.now(timezone.utc).strftime('%Y%m')}-{farmer_id[-6:] if len(farmer_id) >= 6 else farmer_id}"

    new_journey = {
        "journeyId": journey_id,
        "farmerId": farmer_id,
        "farmerName": farmer_name or "Farmer",
        "farmerPhone": farmer_phone or "",
        "status": "in_progress",
        "currentStep": 1,
        "profileInput": {
            "district": initial_district or "Salem",
            "landArea": 1.0,
            "landUnit": "acres",
            "waterAvailability": "ample_borewell",
            "soilType": "unknown",
            "season": "unknown",
            "budgetRange": "low_15k_35k",
            "availableLabour": "family_only_1_2",
            "farmingGoal": "commercial_income"
        },
        "selectedCropId": None,
        "selectedCropName": None,
        "plantingDate": None,
        "landAreaNormalizedAcres": 1.0,
        "checklists": {},
        "observations": [],
        "costsWorksheet": {
            "entries": [],
            "totalOperatingCost": 0.0,
            "costPerUnitArea": 0.0,
            "disclaimer": "Estimates are illustrative guidelines based on TNAU Cost of Cultivation benchmarks. Profit is never guaranteed."
        },
        "salePlan": {
            "targetChannels": [],
            "mandiPriceSnapshot": None,
            "gradingPackagingDetails": [],
            "transportConsiderations": "",
            "disclaimer": "Quoted mandi prices are modal auction rates, not guaranteed buyback contracts."
        },
        "completionRecord": None,
        "remindersActive": True,
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    await col.insert_one(dict(new_journey))
    # Remove _id if inserted
    new_journey.pop("_id", None)
    return new_journey


async def update_journey_step(
    farmer_id: str,
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Saves user progress for any of the 10 steps.
    Advances or modifies current step, updates checklists, planting date, or worksheets.
    """
    col = get_special_operation_journeys_collection()
    if col is None:
        raise RuntimeError("Database unavailable.")

    now_iso = datetime.now(timezone.utc).isoformat()
    existing = await col.find_one({"farmerId": farmer_id}, {"_id": 0})
    if not existing:
        raise ValueError(f"No active journey found for farmer {farmer_id}")

    set_doc: Dict[str, Any] = {"updatedAt": now_iso}

    # Step update
    if "currentStep" in update_data and update_data["currentStep"] is not None:
        set_doc["currentStep"] = max(1, min(10, int(update_data["currentStep"])))

    # Status update
    if "status" in update_data and update_data["status"]:
        set_doc["status"] = update_data["status"]

    # Profile input update (Step 1)
    if "profileInput" in update_data and update_data["profileInput"]:
        p_in = update_data["profileInput"]
        set_doc["profileInput"] = p_in
        if "landArea" in p_in and "landUnit" in p_in:
            norm_acres = normalize_land_to_acres(float(p_in["landArea"]), str(p_in["landUnit"]))
            set_doc["landAreaNormalizedAcres"] = norm_acres

    # Crop selection (Step 2)
    if "selectedCropId" in update_data and update_data["selectedCropId"]:
        cid = update_data["selectedCropId"].lower().strip()
        set_doc["selectedCropId"] = cid
        guide = get_crop_agronomic_guide(cid)
        if guide:
            set_doc["selectedCropName"] = guide["cropName"]
            # Populate default costs if worksheet is currently empty
            current_costs = existing.get("costsWorksheet", {}).get("entries", [])
            if not current_costs or len(current_costs) == 0:
                acres = set_doc.get("landAreaNormalizedAcres", existing.get("landAreaNormalizedAcres", 1.0))
                set_doc["costsWorksheet"] = generate_default_cost_worksheet(cid, acres)

    # Actual Planting Date (Step 4)
    if "plantingDate" in update_data:
        set_doc["plantingDate"] = update_data["plantingDate"]

    # Checklists update (Step 3, 4, 5, 7, 10)
    if "checklists" in update_data and update_data["checklists"] is not None:
        # Merge checklists
        merged_checklists = dict(existing.get("checklists", {}))
        merged_checklists.update(update_data["checklists"])
        set_doc["checklists"] = merged_checklists

    # Cost worksheet update (Step 8)
    if "costsWorksheet" in update_data and update_data["costsWorksheet"] is not None:
        set_doc["costsWorksheet"] = update_data["costsWorksheet"]

    # Sale Plan (Step 9)
    if "salePlan" in update_data and update_data["salePlan"] is not None:
        set_doc["salePlan"] = update_data["salePlan"]

    # Completion record (Step 10)
    if "completionRecord" in update_data and update_data["completionRecord"] is not None:
        comp = update_data["completionRecord"]
        comp["completedAt"] = now_iso
        set_doc["completionRecord"] = comp
        set_doc["status"] = "completed"

    if "remindersActive" in update_data and update_data["remindersActive"] is not None:
        set_doc["remindersActive"] = bool(update_data["remindersActive"])

    await col.update_one({"farmerId": farmer_id}, {"$set": set_doc})
    updated = await col.find_one({"farmerId": farmer_id}, {"_id": 0})
    return updated or {}


async def add_journey_observation(
    farmer_id: str,
    note: str,
    stage_number: int = 1,
    photo_url: Optional[str] = None,
    is_deviation: bool = False,
    deviation_reason: Optional[str] = None
) -> Dict[str, Any]:
    """Adds a dated growth observation or deviation note to the farmer's journey."""
    col = get_special_operation_journeys_collection()
    if col is None:
        raise RuntimeError("Database unavailable.")

    now_iso = datetime.now(timezone.utc).isoformat()
    obs_id = f"OBS-{datetime.now(timezone.utc).strftime('%m%d%H%M%S')}"

    observation = {
        "id": obs_id,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "stageNumber": stage_number,
        "note": note,
        "photoUrl": photo_url,
        "isDeviation": is_deviation,
        "deviationReason": deviation_reason,
        "createdAt": now_iso
    }

    await col.update_one(
        {"farmerId": farmer_id},
        {
            "$push": {"observations": observation},
            "$set": {"updatedAt": now_iso}
        }
    )
    return observation


async def trigger_journey_reminder_notification(
    farmer_id: str,
    title: str,
    message: str
) -> Dict[str, Any]:
    """Dispatches a crop-care reminder directly into the user's in-app notification center."""
    return await create_in_app_notification(
        title=title,
        message=message,
        notification_type="special_operation",
        farmer_id=farmer_id
    )


async def reset_journey(farmer_id: str) -> bool:
    """
    Safely resets or restarts the beginner journey for the farmer.
    Crucial Safety: Does NOT touch any other farmer collections (bookings, marketplace, profile).
    """
    col = get_special_operation_journeys_collection()
    if col is None:
        return False

    res = await col.delete_one({"farmerId": farmer_id})
    return res.deleted_count > 0
