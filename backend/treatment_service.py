"""
NAMMA VIVASAYI AI - AUTHORITATIVE AGRICULTURAL TREATMENT RECOMMENDATION SERVICE
=================================================================================
Grounded in official agronomic guidelines from:
1. Tamil Nadu Agricultural University (TNAU) Agritech Portal & Crop Protection Guide (CPG)
2. Indian Council of Agricultural Research (ICAR) & National Institutes (IIRR, CRRI, CICR, IIOR)
3. Central Insecticides Board & Registration Committee (CIBRC), Ministry of Agriculture & Farmers Welfare, GoI
4. Directorate of Agriculture, Government of Tamil Nadu

SAFETY & INTEGRITY RULES:
- Never invent pesticide brands, dosage rates, registrations, or chemical combinations.
- Chemical treatments are strictly prohibited/inapplicable for physiological/abiotic disorders.
- Uncertain diagnoses flag that treatment must NOT be selected solely from image predictions.
- AI-generated observations are kept strictly separated from verified reference material.
- Technical active ingredients, dosage units, and safety instructions remain standardized.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger("treatment_service")

# ============================================================================
# PYDANTIC SCHEMAS FOR TREATMENT GUIDANCE
# ============================================================================

class AuthoritativeReference(BaseModel):
    organization: str = Field(..., description="Issuing body, e.g. TNAU, ICAR, CIBRC")
    sourceTitle: str = Field(..., description="Document or portal title, e.g. TNAU Crop Protection Guide")
    url: Optional[str] = Field(None, description="Direct URL to reference page")
    publicationType: str = Field("Official Extension Guide", description="Type of reference")


class BiologicalManagementGuidance(BaseModel):
    culturalPractices: List[str] = Field(default_factory=list, description="Agronomic & cultural methods")
    fieldSanitation: List[str] = Field(default_factory=list, description="Roguing, destruction of crop residues")
    cropRotationAndVarieties: List[str] = Field(default_factory=list, description="Resistant cultivars, crop rotation")
    biologicalControlAgents: List[str] = Field(default_factory=list, description="Biopesticides, parasitoids, antagonists")
    soilAndNutrientManagement: Optional[List[str]] = Field(None, description="Fertility, soil amendments, moisture")


class ChemicalTreatmentGuidance(BaseModel):
    isApplicable: bool = Field(..., description="Whether chemical application is agronomically valid")
    inapplicableReason: Optional[str] = Field(None, description="Explanation if chemical treatment is prohibited")
    activeIngredient: Optional[str] = Field(None, description="Standardized active ingredient and formulation")
    approvedTarget: Optional[str] = Field(None, description="Target pathogen or pest approved on the crop")
    dosageAndApplication: Optional[str] = Field(None, description="Verified dosage rate and water volume per acre")
    cibrcRegistrationStatus: Optional[str] = Field(None, description="CIBRC registration endorsement")
    preHarvestIntervalDays: Optional[int] = Field(None, description="Mandatory waiting period before harvest (PHI)")
    reEntryIntervalHours: Optional[int] = Field(None, description="Minimum waiting period before entering sprayed field (REI)")
    personalProtectiveEquipment: List[str] = Field(default_factory=list, description="Mandatory PPE requirements")
    safetyPrecautions: List[str] = Field(default_factory=list, description="Environmental, drift, and toxicity precautions")


class VerifiedTreatmentGuidance(BaseModel):
    crop: str
    cropTa: Optional[str] = None
    conditionKey: str
    conditionNameEn: str
    conditionNameTa: Optional[str] = None
    category: Literal["pest_damage", "plant_disease", "abiotic_disorder", "healthy", "inconclusive"]
    categoryLabelEn: str
    categoryLabelTa: str
    biologicalManagement: BiologicalManagementGuidance
    chemicalManagement: ChemicalTreatmentGuidance
    ipmStrategySummaryEn: str
    ipmStrategySummaryTa: str
    whenToConsultOfficer: List[str]
    isUncertainOrInconclusive: bool = False
    safetyNoticeEn: str
    safetyNoticeTa: str
    references: List[AuthoritativeReference] = Field(default_factory=list)


# ============================================================================
# AUTHORITATIVE KNOWLEDGEBASE (TNAU / ICAR / CIBRC VERIFIED DATA)
# ============================================================================

AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------------
    # 1. PADDY / RICE - CATEGORY 2: PLANT DISEASE (Rice Blast)
    # ------------------------------------------------------------------------
    "paddy_rice_blast": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "rice_blast",
        "conditionNameEn": "Rice Leaf & Neck Blast (Pyricularia oryzae)",
        "conditionNameTa": "நெல் இலைக்கருகல் / குலை நோய் (பைரிகுலேரியா ஓரைசே)",
        "category": "plant_disease",
        "categoryLabelEn": "Plant Disease (Fungal)",
        "categoryLabelTa": "பயிர் நோய் (பூஞ்சாணம்)",
        "biologicalManagement": {
            "culturalPractices": [
                "Avoid excessive basal or top-dressing nitrogen fertilization; split nitrogen into 3-4 applications.",
                "Maintain uniform standing water (2-3 cm) during critical tillering and panicle initiation stages.",
                "Avoid late planting in blast-prone delta seasons (Samba/Thaladi) when night temperatures dip below 20°C."
            ],
            "fieldSanitation": [
                "Collect and burn severely infected crop residue, stubbles, and collateral weed hosts on bunds (e.g. Digitaria marginata, Panicum repens).",
                "Clean farm implements after working in affected field sectors."
            ],
            "cropRotationAndVarieties": [
                "Cultivate resistant/moderately resistant varieties recommended by TNAU: ADT 43, TPS 5, CO 51, CR 1009 Sub 1.",
                "Avoid continuous monocropping of highly susceptible varieties in blast endemic tracts."
            ],
            "biologicalControlAgents": [
                "Seed treatment with Pseudomonas fluorescens @ 10 g/kg seed followed by seedling root dipping in P. fluorescens slurry (2.5 kg/ha).",
                "Foliar spray with Pseudomonas fluorescens (commercial formulation) @ 1.0 kg/acre (or 2.5 g/L) at boot-leaf and 5% flowering stages."
            ],
            "soilAndNutrientManagement": [
                "Apply Potassium (Muriate of Potash) in two splits to strengthen leaf epidermal cell walls and silica deposition."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Tricyclazole 75% WP",
            "approvedTarget": "Leaf and Neck Blast on Paddy (Pyricularia oryzae)",
            "dosageAndApplication": "120 g per acre dissolved in 200 liters of water using a knapsack sprayer.",
            "cibrcRegistrationStatus": "Registered under the Insecticides Act 1968 by CIBRC for blast control in Paddy.",
            "preHarvestIntervalDays": 30,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Wear chemical-resistant nitrile gloves, particulate respirator/mask, protective goggles, and full-sleeve protective clothing.",
                "Wash hands, face, and sprayer nozzle thoroughly with soap and clean water immediately after application."
            ],
            "safetyPrecautions": [
                "Do not spray against the direction of prevailing wind or during hot midday sun.",
                "Avoid spraying in close proximity to irrigation canals, fish ponds, or open water bodies (toxic to aquatic invertebrates).",
                "Dispose of empty pesticide sachets according to national hazardous waste regulations; never reuse empty containers."
            ]
        },
        "ipmStrategySummaryEn": "Integrate resistant varieties with seed treatment of Pseudomonas fluorescens. Reserve Tricyclazole 75% WP for ETL threshold breaches (initial spindle lesions on 5% of leaves or neck blast risk at heading).",
        "ipmStrategySummaryTa": "சூடோமோனாஸ் விதை நேர்த்தி மற்றும் நோய் எதிர்ப்பு ரகங்களை பயிரிடவும். இலைகளில் 5% க்கும் மேல் கண் வடிவ புள்ளிகள் அல்லது கதிர் கழுத்து நோய் அபாயம் இருந்தால் மட்டும் டிரைசைக்ளசோல் 75% WP தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If lesions rapidly spread to > 15% of the total canopy area within 48 hours despite initial bio-agent spraying.",
            "If neck nodes turn black and collapse prior to milky grain stage, threatening crop lodging."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Verify product label and expiry prior to purchase. Strictly abide by the 30-day Pre-Harvest Interval (PHI) to avoid harmful chemical residues.",
        "safetyNoticeTa": "மருந்தின் காலாவதி தேதியை சரிபார்க்கவும். அறுவடைக்கு முன் 30 நாட்கள் இடைவெளியை (PHI) கட்டாயம் கடைபிடிக்கவும்.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Protection Guide - Rice Diseases (Blast)",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_paddy_blast.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "Central Insecticides Board & Registration Committee (CIBRC)",
                "sourceTitle": "Major Uses of Pesticides (Fungicides Approved on Rice)",
                "url": "http://cibrc.gov.in/major_uses.htm",
                "publicationType": "Statutory Government Label Approval"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 2. PADDY / RICE - CATEGORY 2: PLANT DISEASE (Bacterial Leaf Blight)
    # ------------------------------------------------------------------------
    "paddy_bacterial_leaf_blight": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "bacterial_leaf_blight",
        "conditionNameEn": "Bacterial Leaf Blight - BLB (Xanthomonas oryzae pv. oryzae)",
        "conditionNameTa": "பாக்டீரியா இலைக்கருகல் நோய் (சாந்தோமோனாஸ் ஓரைசே)",
        "category": "plant_disease",
        "categoryLabelEn": "Plant Disease (Bacterial)",
        "categoryLabelTa": "பயிர் நோய் (பாக்டீரியா)",
        "biologicalManagement": {
            "culturalPractices": [
                "Drain standing stagnant field water immediately upon observing translucent water-soaked leaf streaks.",
                "Strictly withhold top-dressing of nitrogen/urea fertilizer during active disease spread.",
                "Delay irrigation until the soil surface reaches hairline crack stage to reduce humidity in the micro-canopy."
            ],
            "fieldSanitation": [
                "Remove and burn collateral weed hosts along bunds (e.g. Leersia hexandra, Cyperus rotundus).",
                "Avoid clipping leaf tips of seedlings at transplanting as wounds facilitate bacterial entry."
            ],
            "cropRotationAndVarieties": [
                "Cultivate resistant or tolerant varieties: IR 20, IRBB lines (incorporating xa5, xa13, Xa21 genes), ADT 45, CO 43.",
                "Avoid growing highly susceptible cultivars in cyclonic or flood-prone delta blocks."
            ],
            "biologicalControlAgents": [
                "Seed treatment with Pseudomonas fluorescens @ 10 g/kg seed.",
                "Foliar spray with fresh cow dung extract (20% filtrate) or Pseudomonas fluorescens @ 1.0 kg/acre."
            ],
            "soilAndNutrientManagement": [
                "Apply potassium fertilizer (MOP) @ 15 kg/acre to boost natural plant phytoalexin response."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Copper Oxychloride 50% WP + Streptomycin Sulphate + Tetracycline Hydrochloride (9:1)",
            "approvedTarget": "Bacterial Leaf Blight on Rice (Xanthomonas oryzae)",
            "dosageAndApplication": "Copper Oxychloride 50% WP @ 500 g + Streptocycline (Streptomycin sulphate + Tetracycline) @ 120 g per acre in 200 L water.",
            "cibrcRegistrationStatus": "Recognized under CIBRC / TNAU Crop Protection Schedule for bacterial blight suppressive sprays.",
            "preHarvestIntervalDays": 21,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Nitrile chemical gloves, splash-proof safety goggles, breathing mask, gumboots.",
                "Never eat, drink, or chew tobacco while mixing antibiotic/copper formulations."
            ],
            "safetyPrecautions": [
                "Copper fungicides must not be mixed with acidic foliar fertilizers or organophosphates.",
                "Do not spray during high wind speeds (> 15 km/h) to prevent drift to adjacent vegetable nurseries."
            ]
        },
        "ipmStrategySummaryEn": "Cease nitrogen top-dressing and drain excess field water immediately. Apply TNAU recommended Copper Oxychloride + Streptocycline combination at the early appearance of wavy yellow leaf margins.",
        "ipmStrategySummaryTa": "தழைச்சத்து உரங்களை உடனே நிறுத்தவும். வயலில் தேங்கிய தண்ணீரை வடிக்கவும். அறிகுறிகள் தென்பட்டவுடன் காப்பர் ஆக்ஸிகுளோரைடு 500 கிராம் + ஸ்ட்ரெப்டோசைக்ளின் 120 கிராம் தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If 'kresek' (systemic wilting of entire seedlings or tillers) appears in nursery or early tillering stages.",
            "If more than 20% of the flag leaf area is bleached white prior to grain filling."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Strict adherence to antibiotic dosage limits is essential to prevent environmental antimicrobial resistance (AMR).",
        "safetyNoticeTa": "பாக்டீரியா எதிர்ப்பு மருந்துகளின் அளவை சரியாக பயன்படுத்தவும்; அதிக அளவு பயன்படுத்துவது நன்மை செய்யும் நுண்ணுயிரிகளை அழிக்கும்.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Protection Guide - Rice Bacterial Diseases",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_paddy_bacterial_blight.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "ICAR - National Rice Research Institute (NRRI)",
                "sourceTitle": "Integrated Disease Management in Rice Ecosystems",
                "url": "https://icar-nrri.gov.in/",
                "publicationType": "National Institute Advisory"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 3. PADDY / RICE - CATEGORY 1: PEST DAMAGE (Brown Planthopper - BPH)
    # ------------------------------------------------------------------------
    "paddy_brown_planthopper": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "brown_planthopper",
        "conditionNameEn": "Brown Planthopper - BPH (Nilaparvata lugens)",
        "conditionNameTa": "நெல் புகையான் பூச்சி தாக்குதல் (நீலபர்வதா லூஜென்ஸ்)",
        "category": "pest_damage",
        "categoryLabelEn": "Pest & Insect Damage",
        "categoryLabelTa": "பூச்சி தாக்குதல்",
        "biologicalManagement": {
            "culturalPractices": [
                "Form 'alleyways' (pathways of 30 cm width every 2.0 to 2.5 meters in east-west direction) to provide micro-climatic aeration and sunlight penetration.",
                "Practice Alternate Wetting and Drying (AWD) irrigation; dry the field for 2-3 days when BPH incidence is observed.",
                "Avoid blanket prophylactic sprays of synthetic pyrethroids (e.g. cypermethrin, deltamethrin) which induce BPH pest resurgence by killing natural mirid bug predators."
            ],
            "fieldSanitation": [
                "Clear ratoon tillers and weed hosts along channel bunds where adults overwinter."
            ],
            "cropRotationAndVarieties": [
                "Grow tolerant varieties in endemic tracts: ADT 43, PY 3, White Ponni, CO 47."
            ],
            "biologicalControlAgents": [
                "Conserve natural predators: Mirid bug (Cyrtorhinus lividipennis), Wolf spider (Lycosa pseudoannulata), and rove beetles.",
                "Spray neem oil 3% (30 ml/L) or Azadirachtin 1% (10,000 ppm) @ 400 ml/acre at early nymphal hatching stage."
            ],
            "soilAndNutrientManagement": [
                "Avoid split application of nitrogen in excess of Soil Health Card recommendations."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Triflumezopyrim 10% SC",
            "approvedTarget": "Brown Planthopper (Nilaparvata lugens) on Rice",
            "dosageAndApplication": "94 ml per acre in 200 L water, directing spray strictly at the basal tillers (not canopy top).",
            "cibrcRegistrationStatus": "Registered under CIBRC for planthopper control in transplanted and direct-seeded rice.",
            "preHarvestIntervalDays": 21,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Wear rubber gloves, goggles, face shield, and chemical-resistant footwear.",
                "Clean spray equipment in a designated washing basin far from community water channels."
            ],
            "safetyPrecautions": [
                "Direct the nozzle towards the base of the rice hills where planthoppers congregate; spraying only the upper canopy is ineffective.",
                "Do not apply when honeybees are actively foraging on companion flowering plants along field boundaries."
            ]
        },
        "ipmStrategySummaryEn": "Form alleyways every 2m, practice Alternate Wetting and Drying (AWD), and conserve spider predators. If population exceeds Economic Threshold Level (ETL: 1 hopper/tiller at tillering or 2 hoppers/tiller at flowering), spray Triflumezopyrim 10% SC at the base of tillers.",
        "ipmStrategySummaryTa": "வயலில் 2 மீட்டருக்கு ஒரு இடைவெளி (பாதை) விடவும். தண்ணீரைக் கட்டி காயவைத்து பாசனம் செய்யவும். பொருளாதார சேத நிலையை (ஒரு தூர்ல 1-2 பூச்சிகள்) தாண்டினால் டிரிபுளுமெசோபைரிம் 10% SC மருந்தை செடியின் அடிப்பகுதியில் தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If circular patches of rapidly drying plants ('hopper burn') appear in multiple field quadrants.",
            "If hopper counts exceed 15-20 nymphs per hill at milky grain stage."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Targeting spray nozzle to the stem base is mandatory for efficacy. Never use synthetic pyrethroids which trigger devastating pest resurgence.",
        "safetyNoticeTa": "மருந்தை தூரின் அடிப்பகுதியில் மட்டுமே தெளிக்க வேண்டும். மேல் இலைகளில் தெளிப்பது பலனளிக்காது.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Protection Guide - Rice Insect Pests (BPH)",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect_pest_paddy_bph.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "Central Insecticides Board & Registration Committee (CIBRC)",
                "sourceTitle": "List of Insecticides Approved for BPH on Paddy",
                "url": "http://cibrc.gov.in/major_uses.htm",
                "publicationType": "Statutory Government Label Approval"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 4. PADDY / RICE - CATEGORY 1: PEST DAMAGE (Yellow Stem Borer)
    # ------------------------------------------------------------------------
    "paddy_yellow_stem_borer": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "yellow_stem_borer",
        "conditionNameEn": "Yellow Stem Borer (Scirpophaga incertulas)",
        "conditionNameTa": "நெல் குருத்துப்பூச்சி / தண்டு துளைப்பான் (ஸ்கிர்போபாகா இன்சர்டுலஸ்)",
        "category": "pest_damage",
        "categoryLabelEn": "Pest & Insect Damage",
        "categoryLabelTa": "பூச்சி தாக்குதல்",
        "biologicalManagement": {
            "culturalPractices": [
                "Clip seedling leaf tips before transplanting to eliminate stem borer egg masses.",
                "Synchronize planting in adjoining farm blocks to break the continuous breeding cycles of adult moths.",
                "Plough the stubbles immediately after harvest and submerge fields to kill pupating larvae in root crowns."
            ],
            "fieldSanitation": [
                "Manually pull out and destroy drying central shoots ('dead hearts') along with larvae inside."
            ],
            "cropRotationAndVarieties": [
                "Grow tolerant varieties like CO 43, CR 1009, ADT 36, TPS 5."
            ],
            "biologicalControlAgents": [
                "Release egg parasitoid Trichogramma japonicum @ 40,000 to 50,000 / acre (2-3 releases at weekly intervals from 30 DAT).",
                "Install sex pheromone traps with lures @ 5 traps per acre for pest population monitoring and mating disruption.",
                "Install light traps (one per acre) to monitor adult moth emergence."
            ],
            "soilAndNutrientManagement": [
                "Avoid excessive nitrogenous fertilizers which render rice tillers succulent and vulnerable to larval boring."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Chlorantraniliprole 18.5% SC",
            "approvedTarget": "Stem Borer in Paddy (Scirpophaga incertulas)",
            "dosageAndApplication": "60 ml per acre in 200 L water applied as a high-volume foliar spray.",
            "cibrcRegistrationStatus": "Registered under CIBRC with label claim for stem borer in rice.",
            "preHarvestIntervalDays": 21,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Protective mask, rubber gloves, goggles, boots, and washable protective coveralls.",
                "Do not inhale spray mist or smoke during chemical handling."
            ],
            "safetyPrecautions": [
                "Do not apply when pheromone trap catches are below ETL (less than 2 moths per trap per day or less than 5% dead hearts).",
                "Ensure spray does not drift into fish-rearing wetlands or adjacent apiaries."
            ]
        },
        "ipmStrategySummaryEn": "Clip seedling tips, install pheromone traps @ 5/acre, and release Trichogramma japonicum. Spray Chlorantraniliprole 18.5% SC @ 60 ml/acre if dead hearts exceed 5% at tillering or white ears exceed 2% at heading.",
        "ipmStrategySummaryTa": "நாற்று நுனியை கிள்ளி நடவு செய்யவும். ஏக்கருக்கு 5 இனக்கவர்ச்சி பொறிகள் வைக்கவும். டிரைக்கோடெர்மா ஒட்டுண்ணி அட்டை கட்டவும். சேதம் 5% தாண்டினால் குளோரான்ட்ரனிலிப்ரோல் 60 மி.லி தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If white ears (chaffy panicles with bore holes at node base) exceed 2-3% during panicle emergence.",
            "If continuous moth influx persists despite pheromone mass trapping."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Respect the Economic Threshold Level (ETL) before chemical intervention. Overuse destroys Trichogramma parasitoids.",
        "safetyNoticeTa": "பொருளாதார சேத நிலையை அடைந்த பின்பே ரசாயன மருந்தை தெளிக்க வேண்டும்.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Protection Guide - Yellow Stem Borer",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect_pest_paddy_ysb.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "Directorate of Plant Protection, Quarantine & Storage (DPPQS)",
                "sourceTitle": "Integrated Pest Management Package for Paddy",
                "url": "http://ppqs.gov.in/ipm-packages",
                "publicationType": "GoI Directorate Advisory"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 5. PADDY / RICE - CATEGORY 3: ABIOTIC DISORDER (Potassium Deficiency)
    # ------------------------------------------------------------------------
    "paddy_potassium_deficiency": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "potassium_deficiency",
        "conditionNameEn": "Potassium (K) Deficiency / Marginal Leaf Scorch",
        "conditionNameTa": "பொட்டாசியம் ஊட்டச்சத்து குறைபாடு / இலை ஓரக்கருகல்",
        "category": "abiotic_disorder",
        "categoryLabelEn": "Abiotic / Physiological Disorder",
        "categoryLabelTa": "உடலியல் / ஊட்டச்சத்து குறைபாடு",
        "biologicalManagement": {
            "culturalPractices": [
                "Incorporate paddy straw / stubbles into soil during pre-sowing ploughing; straw returns 80% of absorbed potassium back to the topsoil.",
                "Practice balanced NPK fertilization in a 4:2:1 or soil-test based ratio rather than applying urea alone.",
                "Maintain good subsoil aeration to facilitate active root ATP-driven potassium uptake."
            ],
            "fieldSanitation": [
                "No roguing or field destruction required; this is a non-infectious physiological condition."
            ],
            "cropRotationAndVarieties": [
                "Select varieties with extensive root surface area (e.g. CR 1009 Sub 1, CO 51) that forage subsoil potassium effectively."
            ],
            "biologicalControlAgents": [
                "Inoculate soil with Potassium Solubilizing Biofertilizers (KSB - Frateuria aurantia) @ 2.0 kg/acre mixed with 200 kg well-decomposed Farm Yard Manure (FYM).",
                "Biological pesticides/fungicides are NOT applicable."
            ],
            "soilAndNutrientManagement": [
                "Basal soil application: Muriate of Potash (MOP, 60% K2O) @ 25-30 kg/acre applied in two equal splits (at basal and active tillering).",
                "Corrective foliar spray: 1% Potassium Chloride (KCl) or 1% Potassium Nitrate (KNO3) (10 g/L water) sprayed twice at 10-day intervals for quick leaf absorption."
            ]
        },
        "chemicalManagement": {
            "isApplicable": False,
            "inapplicableReason": "CHEMICAL PESTICIDES AND FUNGICIDES ARE STRICTLY NOT APPLICABLE FOR PHYSIOLOGICAL OR NUTRIENT DISORDERS. Spraying insecticides or fungicides will cause crop phytotoxicity, unnecessary farmer expenditure, and zero agronomic benefit.",
            "activeIngredient": None,
            "approvedTarget": None,
            "dosageAndApplication": None,
            "cibrcRegistrationStatus": None,
            "preHarvestIntervalDays": None,
            "reEntryIntervalHours": None,
            "personalProtectiveEquipment": [
                "For foliar fertilizer spraying: Wear standard dust mask, gloves, and protective spectacles to avoid skin or eye irritation from concentrated salt solutions."
            ],
            "safetyPrecautions": [
                "Do not spray foliar potassium salts in midday heat (> 35°C) to prevent foliar salt scorch.",
                "Dissolve fertilizer salts completely in water before putting into spray tank; do not mix with pesticides unless tested for compatibility."
            ]
        },
        "ipmStrategySummaryEn": "Do NOT spray pesticides. Apply Muriate of Potash (MOP) to soil or spray 1% Potassium Nitrate (KNO3) foliar spray. Inoculate with Potassium Solubilizing Bacteria (KSB) with organic farmyard manure.",
        "ipmStrategySummaryTa": "பூச்சிக்கொல்லி மருந்துகள் தெளிக்க வேண்டாம்! ஏக்கருக்கு 25 கிலோ பொட்டாஷ் உரத்தை இடவும் அல்லது 1% பொட்டாசியம் நைட்ரேட் கரைசல் தெளிக்கவும். பொட்டாஷ் பாக்டீரியா உயிர் உரத்தை இடவும்.",
        "whenToConsultOfficer": [
            "If marginal scorching persists despite split potassium fertilizer application (may indicate subsoil salinity or toxic iron reduction in poorly drained fields).",
            "To obtain an official Soil Health Card analysis for soil exchangeable potassium levels."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "This is a non-infectious nutritional condition. Chemical pesticides are strictly prohibited as they provide zero control and waste farmer money.",
        "safetyNoticeTa": "இது பூச்சி அல்லது நோய் தாக்குதல் அல்ல; ஊட்டச்சத்து குறைபாடு. பூச்சிக்கொல்லிகளை தெளிக்கக் கூடாது.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Nutrition Management - Deficiency Symptoms in Rice",
                "url": "https://agritech.tnau.ac.in/agriculture/agri_nutrientmgt_rice.html",
                "publicationType": "State University Scientific Guide"
            },
            {
                "organization": "ICAR - Indian Institute of Rice Research (IIRR)",
                "sourceTitle": "Nutrient Deficiencies and Toxicities in Rice Systems",
                "url": "https://www.icar-iirr.org/",
                "publicationType": "National Institute Soil Advisory"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 6. PADDY / RICE - CATEGORY 3: ABIOTIC DISORDER (Zinc Deficiency / Khaira)
    # ------------------------------------------------------------------------
    "paddy_zinc_deficiency": {
        "crop": "Paddy / Rice",
        "cropTa": "நெல்",
        "conditionKey": "zinc_deficiency",
        "conditionNameEn": "Zinc (Zn) Deficiency / Khaira Disease",
        "conditionNameTa": "துத்தநாகம் ஊட்டச்சத்து குறைபாடு / வெண்காய் நோய்",
        "category": "abiotic_disorder",
        "categoryLabelEn": "Abiotic / Physiological Disorder",
        "categoryLabelTa": "உடலியல் / ஊட்டச்சத்து குறைபாடு",
        "biologicalManagement": {
            "culturalPractices": [
                "Avoid continuous standing water; drain field intermittently to increase soil redox potential and free up divalent zinc ions.",
                "Avoid over-application of phosphatic fertilizers (DAP/SSP) which induce insoluble zinc phosphate precipitation in soil.",
                "Apply well-decomposed organic manure (FYM or green manure) @ 5 tonnes/acre to enhance zinc chelation."
            ],
            "fieldSanitation": [
                "Not required; non-infectious physiological disorder."
            ],
            "cropRotationAndVarieties": [
                "Cultivate zinc-efficient rice varieties (e.g. CO 51, ADT 43) in known zinc-deficient delta belts."
            ],
            "biologicalControlAgents": [
                "Apply Zinc Solubilizing Biofertilizers (ZSB - Bacillus megaterium / Pseudomonas striata) @ 2 kg/acre with vermicompost."
            ],
            "soilAndNutrientManagement": [
                "Soil application: Zinc sulphate (heptahydrate, 21% Zn) @ 10-12 kg/acre as basal application before last puddling (do NOT mix directly with DAP).",
                "Foliar spray: 0.5% Zinc sulphate (5 g/L) + 1.0% Urea (10 g/L) sprayed twice at 15 and 30 days after transplanting."
            ]
        },
        "chemicalManagement": {
            "isApplicable": False,
            "inapplicableReason": "CHEMICAL PESTICIDES AND FUNGICIDES ARE STRICTLY NOT APPLICABLE FOR NUTRIENT DEFICIENCIES. Zinc deficiency is a micro-nutrient imbalance, not a biological pathogen.",
            "activeIngredient": None,
            "approvedTarget": None,
            "dosageAndApplication": None,
            "cibrcRegistrationStatus": None,
            "preHarvestIntervalDays": None,
            "reEntryIntervalHours": None,
            "personalProtectiveEquipment": [
                "Wear safety glasses, face mask, and cotton gloves when preparing micro-nutrient salt solutions."
            ],
            "safetyPrecautions": [
                "Always neutralize Zinc sulphate with equal or half quantity of lime if spraying sensitive vegetable crops; on rice, foliar spray of 0.5% ZnSO4 + 1% urea is recommended by TNAU."
            ]
        },
        "ipmStrategySummaryEn": "Do NOT spray fungicides. Apply Zinc Sulphate (21% Zn) @ 10-12 kg/acre to soil or spray 0.5% ZnSO4 + 1% urea foliar spray. Inoculate Zinc Solubilizing Bacteria (ZSB).",
        "ipmStrategySummaryTa": "பூஞ்சாண கொல்லி மருந்துகள் தெளிக்க வேண்டாம்! ஏக்கருக்கு 10-12 கிலோ ஜிங்க் சல்பேட் உரம் இடவும் அல்லது 0.5% துத்தநாக சல்பேட் + 1% யூரியா இலைவழி தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If rusty bronze blotching expands across entire tillers within 2-3 weeks after transplanting in alkaline or calcareous delta soils."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Do not mix Zinc Sulphate directly with DAP or SSP in the fertilizer basin, as it precipitates insoluble zinc phosphate.",
        "safetyNoticeTa": "ஜிங்க் சல்பேட்டை டி.ஏ.பி அல்லது சூப்பர் பாஸ்பேட் உரங்களுடன் நேரடியாக கலந்து இடக்கூடாது.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Soil Micronutrient Management (Zinc)",
                "url": "https://agritech.tnau.ac.in/agriculture/agri_nutrientmgt_micronutrients.html",
                "publicationType": "State University Scientific Guide"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 7. GROUNDNUT - CATEGORY 2: PLANT DISEASE (Tikka Leaf Spot)
    # ------------------------------------------------------------------------
    "groundnut_tikka_leaf_spot": {
        "crop": "Groundnut",
        "cropTa": "நிலக்கடலை",
        "conditionKey": "tikka_leaf_spot",
        "conditionNameEn": "Tikka Leaf Spot (Cercospora arachidicola & Phaeoisariopsis personata)",
        "conditionNameTa": "நிலக்கடலை டிக்கா இலைப்புள்ளி நோய் (செர்கோஸ்போரா அரச்சிடிகோலா)",
        "category": "plant_disease",
        "categoryLabelEn": "Plant Disease (Fungal)",
        "categoryLabelTa": "பயிர் நோய் (பூஞ்சாணம்)",
        "biologicalManagement": {
            "culturalPractices": [
                "Avoid continuous mono-cropping of groundnut on the same field; rotate with pearl millet (cumbu), sorghum, or maize.",
                "Synchronize sowing in the block to avoid continuous disease transmission between early and late planted fields."
            ],
            "fieldSanitation": [
                "Collect and burn crop haulms and post-harvest residues harboring resting ascospores."
            ],
            "cropRotationAndVarieties": [
                "Cultivate tolerant varieties recommended for Tamil Nadu: VRI 2, VRI 8, TMV 13, Kadiri 6."
            ],
            "biologicalControlAgents": [
                "Seed treatment with Trichoderma viride @ 4 g/kg seed or Pseudomonas fluorescens @ 10 g/kg seed.",
                "Foliar spray of 5% Neem Seed Kernel Extract (NSKE) or Pseudomonas fluorescens @ 1.0 kg/acre at first appearance of spots."
            ],
            "soilAndNutrientManagement": [
                "Apply gypsum @ 160-200 kg/acre at 40-45 days after sowing (flowering/pegging) to improve shell hardening and resistance."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Mancozeb 75% WP or Carbendazim 50% WP",
            "approvedTarget": "Tikka Leaf Spot on Groundnut",
            "dosageAndApplication": "Mancozeb 75% WP @ 400 g per acre (2 g/L) or Carbendazim 50% WP @ 200 g per acre (1 g/L) in 200 L water.",
            "cibrcRegistrationStatus": "Registered under CIBRC with label approval for Cercospora leaf spot in groundnut.",
            "preHarvestIntervalDays": 30,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Full protective apron, dust/mist respirator, nitrile gloves, safety goggles.",
                "Wash protective gear separately from household laundry."
            ],
            "safetyPrecautions": [
                "Do not graze milch cattle or livestock on crop haulms sprayed with Carbendazim within 30 days of application.",
                "Avoid spraying during peak flowering hours (8 AM to 11 AM) to safeguard bee pollinators."
            ]
        },
        "ipmStrategySummaryEn": "Treat seeds with Trichoderma viride. Spray 5% NSKE at initial symptoms. For severe infections, spray Mancozeb 75% WP @ 400 g/acre or Carbendazim 50% WP @ 200 g/acre, adhering to a 30-day PHI.",
        "ipmStrategySummaryTa": "ட்ரைக்கோடெர்மா விரிடி கொண்டு விதை நேர்த்தி செய்யவும். தொடக்க நிலையில் 5% வேப்பங்கொட்டை சாறு தெளிக்கவும். தீவிரமாக இருந்தால் மேன்கோசெப் 400 கிராம் அல்லது கார்பெண்டசிம் 200 கிராம் தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If defoliation exceeds 25% of leaves prior to 60 days after sowing (pod development stage)."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Ensure proper 30-day pre-harvest interval before lifting pods or harvesting haulms for cattle fodder.",
        "safetyNoticeTa": "அறுவடைக்கு 30 நாட்களுக்கு முன் ரசாயன தெளிப்பை நிறுத்த வேண்டும்; கால்நடைகளுக்கு உடனடியாக தீவனமாக கொடுக்கக்கூடாது.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Crop Protection Guide - Oilseeds (Groundnut Tikka Disease)",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_oilseeds_groundnut.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "ICAR - Directorate of Groundnut Research (DGR)",
                "sourceTitle": "Compendium of Groundnut Diseases & IPM Strategies",
                "url": "https://dgr.icar.gov.in/",
                "publicationType": "National Commodity Institute Guide"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 8. TOMATO - CATEGORY 2: PLANT DISEASE (Early Blight)
    # ------------------------------------------------------------------------
    "tomato_early_blight": {
        "crop": "Tomato",
        "cropTa": "தக்காளி",
        "conditionKey": "tomato_early_blight",
        "conditionNameEn": "Tomato Early Blight (Alternaria solani)",
        "conditionNameTa": "தக்காளி ஆரம்பக்கால இலைக்கருகல் நோய் (ஆல்டர்நேரியா சொலானி)",
        "category": "plant_disease",
        "categoryLabelEn": "Plant Disease (Fungal)",
        "categoryLabelTa": "பயிர் நோய் (பூஞ்சாணம்)",
        "biologicalManagement": {
            "culturalPractices": [
                "Stake plants to keep foliage and developing fruits off wet soil.",
                "Mulch the beds with straw or silver-black polythene to prevent rain-splash of fungal spores from soil.",
                "Use drip irrigation rather than overhead sprinklers to keep foliage dry."
            ],
            "fieldSanitation": [
                "Prune lower infected leaves up to 30 cm above ground and burn them; sanitize pruning shears in 70% alcohol."
            ],
            "cropRotationAndVarieties": [
                "Rotate with non-solanaceous crops (maize, pulses, okra) for at least 2 seasons.",
                "Select tolerant hybrid varieties: Arka Rakshak, Arka Abhed (multi-disease resistant)."
            ],
            "biologicalControlAgents": [
                "Seedling root dip with Trichoderma harzianum @ 10 g/L.",
                "Foliar spray with Bacillus subtilis or Pseudomonas fluorescens @ 1.0 kg/acre."
            ],
            "soilAndNutrientManagement": [
                "Maintain adequate calcium and potassium; avoid plant stress which accelerates Alternaria colonization."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Mancozeb 75% WP",
            "approvedTarget": "Early Blight on Tomato (Alternaria solani)",
            "dosageAndApplication": "400 g to 500 g per acre in 200 L water using a hollow cone nozzle.",
            "cibrcRegistrationStatus": "Registered under CIBRC for Alternaria leaf blight in solanaceous vegetables.",
            "preHarvestIntervalDays": 7,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Gloves, protective apron, particulate respirator, rubber boots.",
                "Do not pick ripe tomatoes on the same day as spraying."
            ],
            "safetyPrecautions": [
                "Strictly observe the 7-day Pre-Harvest Interval (PHI); do not harvest fruits for market within 7 days of spray.",
                "Avoid spraying during high ambient temperatures (> 32°C) to prevent foliar scorch."
            ]
        },
        "ipmStrategySummaryEn": "Stake vines, prune lower leaves, and use drip irrigation. Spray Mancozeb 75% WP @ 400-500 g/acre on observing concentric target-board lesions, observing a mandatory 7-day PHI.",
        "ipmStrategySummaryTa": "செடிகளுக்கு முட்டுக்கொடுக்கவும். கீழ் இலைகளை நீக்கவும். இலைகளில் வளைய வடிவ கரும்புள்ளிகள் தென்பட்டால் மேன்கோசெப் 400-500 கிராம் தெளிக்கவும். அறுவடைக்கு முன் 7 நாள் இடைவெளி விடவும்.",
        "whenToConsultOfficer": [
            "If lesions expand to fruit calyx and pedicels, causing dark leathery sunken fruit drop."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Vegetable food safety: Strictly maintain the 7-day PHI waiting period before sending harvested tomatoes to consumer markets.",
        "safetyNoticeTa": "காய்கறி பாதுகாப்பு: மருந்து தெளித்த பிறகு 7 நாட்களுக்கு காய்களை பறிக்கவோ விற்கவோ கூடாது.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Vegetable Pathology - Tomato Early Blight",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_diseases_veg_tomato.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "ICAR - Indian Institute of Horticultural Research (IIHR)",
                "sourceTitle": "Integrated Disease Management in Solanaceous Vegetables",
                "url": "https://www.iihr.res.in/",
                "publicationType": "National Horticultural Institute Guide"
            }
        ]
    },

    # ------------------------------------------------------------------------
    # 9. COTTON - CATEGORY 1: PEST DAMAGE (American Bollworm)
    # ------------------------------------------------------------------------
    "cotton_american_bollworm": {
        "crop": "Cotton",
        "cropTa": "பருத்தி",
        "conditionKey": "cotton_bollworm",
        "conditionNameEn": "American Bollworm / Gram Pod Borer (Helicoverpa armigera)",
        "conditionNameTa": "பருத்தி அமெரிக்க காய் புழு (ஹெலிகோவெர்பா ஆர்மிஜிரா)",
        "category": "pest_damage",
        "categoryLabelEn": "Pest & Insect Damage",
        "categoryLabelTa": "பூச்சி தாக்குதல்",
        "biologicalManagement": {
            "culturalPractices": [
                "Grow trap crops: Plant one row of African Marigold (Tagetes erecta) for every 10 rows of cotton to attract egg-laying moths away from squares.",
                "Handpick and destroy early instar caterpillars from flared squares and young bolls."
            ],
            "fieldSanitation": [
                "Deep summer ploughing to expose hibernating pupae in soil to predatory birds and sun desiccation."
            ],
            "cropRotationAndVarieties": [
                "Follow crop rotation with non-host cereals (maize, sorghum, ragi); avoid cotton following tomato or pulses."
            ],
            "biologicalControlAgents": [
                "Install sex pheromone traps with Helilure @ 5 traps/acre for monitoring and mass trapping.",
                "Release Trichogramma chilonis @ 60,000 / acre at weekly intervals (3-4 times starting from flower bud formation).",
                "Spray Helicoverpa armigera Nuclear Polyhedrosis Virus (HaNPV) @ 200 LE (Larval Equivalents) / acre in evening hours with 0.1% teepol / jaggery adjuvant."
            ],
            "soilAndNutrientManagement": [
                "Avoid high nitrogen doses which produce excessive leafy canopy and dense square sheltering."
            ]
        },
        "chemicalManagement": {
            "isApplicable": True,
            "inapplicableReason": None,
            "activeIngredient": "Chlorantraniliprole 18.5% SC or Emamectin Benzoate 5% SG",
            "approvedTarget": "Helicoverpa armigera in Cotton",
            "dosageAndApplication": "Chlorantraniliprole 18.5% SC @ 60 ml/acre or Emamectin Benzoate 5% SG @ 88 g/acre in 200 L water.",
            "cibrcRegistrationStatus": "Registered under CIBRC with approved label claim for cotton bollworm complex.",
            "preHarvestIntervalDays": 25,
            "reEntryIntervalHours": 24,
            "personalProtectiveEquipment": [
                "Full protective apron, respirator, chemical gloves, eye shield, and boots.",
                "Never spray without protective face coverings."
            ],
            "safetyPrecautions": [
                "Do not spray unless population exceeds Economic Threshold Level (ETL: 1 larva/meter row or 10% damaged squares).",
                "Rotate insecticide chemical groups to prevent rapid development of target pest resistance."
            ]
        },
        "ipmStrategySummaryEn": "Plant African marigold trap crop, install pheromone traps @ 5/acre, and release Trichogramma chilonis. If ETL is breached (> 10% damaged squares), spray Chlorantraniliprole 18.5% SC @ 60 ml/acre.",
        "ipmStrategySummaryTa": "துளசி அல்லது சாமந்தியை பொறிப்பயிராக நடவும். ஏக்கருக்கு 5 இனக்கவர்ச்சி பொறிகள் வைக்கவும். சேதம் 10% தாண்டினால் குளோரான்ட்ரனிலிப்ரோல் 60 மி.லி தெளிக்கவும்.",
        "whenToConsultOfficer": [
            "If square shedding ('flared squares') exceeds 15% during early boll formation."
        ],
        "isUncertainOrInconclusive": False,
        "safetyNoticeEn": "Strict adherence to ETL is crucial to maintain beneficial predators and prevent pesticide resistance.",
        "safetyNoticeTa": "பொருளாதார சேத நிலையை அடைந்த பின்பே மருந்து தெளிக்க வேண்டும்.",
        "references": [
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal: Cotton IPM - Bollworm Complex",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop_insect_pest_cotton_bollworm.html",
                "publicationType": "State University Extension Guide"
            },
            {
                "organization": "ICAR - Central Institute for Cotton Research (CICR)",
                "sourceTitle": "Cotton Pest Surveillance and Insecticide Resistance Management",
                "url": "https://cicr.icar.gov.in/",
                "publicationType": "National Institute Advisory"
            }
        ]
    }
}

# ============================================================================
# UNCERTAIN / INCONCLUSIVE / FALLBACK GUIDANCE BUILDER
# ============================================================================

def build_uncertain_or_inconclusive_guidance(
    crop: str = "Crop Specimen",
    condition: str = "Uncertain Condition",
    category: str = "inconclusive",
    crop_ta: Optional[str] = None,
    language: str = "en"
) -> VerifiedTreatmentGuidance:
    """
    Builds a defensive, truthful recommendation when the visual specimen lacks conclusive diagnostic evidence.
    STRICT SAFETY RULE: Never fabricate or guess chemical treatments for uncertain diagnoses.
    """
    is_ta = (language == "ta")

    return VerifiedTreatmentGuidance(
        crop=crop,
        cropTa=crop_ta or "பயிர் மாதிரி",
        conditionKey="inconclusive_specimen",
        conditionNameEn=f"Unconfirmed Condition ({condition})",
        conditionNameTa=f"உறுதிப்படுத்தப்படாத நிலை ({condition})",
        category="inconclusive",
        categoryLabelEn="Inconclusive / Uncertain Diagnosis",
        categoryLabelTa="முடிவற்ற / உறுதிப்படுத்தப்படாத மாதிரி",
        biologicalManagement=BiologicalManagementGuidance(
            culturalPractices=[
                "Maintain standard field sanitation and avoid hasty chemical applications.",
                "Ensure proper irrigation drainage to prevent root hypoxia.",
                "Monitor neighboring plants for identical or developing symptom patterns."
            ],
            fieldSanitation=[
                "Isolate or mark suspect plants rather than mass-spraying the entire field.",
                "Do not transport suspect diseased plant debris across unaffected plots."
            ],
            cropRotationAndVarieties=[
                "Maintain diversified crop rotations to reduce overall pest and pathogen pressure."
            ],
            biologicalControlAgents=[
                "Prophylactic application of certified biocontrol agents (e.g. Pseudomonas fluorescens @ 10 g/L or neem formulation) may be safe, but target identification is advised first."
            ],
            soilAndNutrientManagement=[
                "Collect composite soil samples for testing at your nearest Government Soil Testing Laboratory (STL)."
            ]
        ),
        chemicalManagement=ChemicalTreatmentGuidance(
            isApplicable=False,
            inapplicableReason="CHEMICAL TREATMENTS MUST NOT BE SELECTED SOLELY FROM AN UNCERTAIN OR INCONCLUSIVE IMAGE PREDICTION. Applying unverified pesticides causes financial loss, risks crop injury (phytotoxicity), and may destroy beneficial insect predators.",
            activeIngredient=None,
            approvedTarget=None,
            dosageAndApplication=None,
            cibrcRegistrationStatus=None,
            preHarvestIntervalDays=None,
            reEntryIntervalHours=None,
            personalProtectiveEquipment=[
                "PPE required only when handling approved treatments under agricultural officer guidance."
            ],
            safetyPrecautions=[
                "Do not purchase or spray unregistered or unverified pesticide combinations."
            ]
        ),
        ipmStrategySummaryEn="Do not apply chemical pesticides based on an uncertain photo. Isolate suspected plants, inspect in daylight, and consult your Assistant Agricultural Officer (AAO) or local Krishi Vigyan Kendra (KVK).",
        ipmStrategySummaryTa="தெளிவற்ற புகைப்படத்தின் அடிப்படையில் பூச்சிக்கொல்லிகளை தெளிக்க வேண்டாம்! பாதிக்கப்பட்ட பயிரை நேரில் ஆய்வு செய்து வேளாண்மை அலுவலர் அல்லது கே.வி.கே வல்லுநரை அணுகவும்.",
        whenToConsultOfficer=[
            "Consult your local Assistant Agricultural Officer (AAO) or TNAU Krishi Vigyan Kendra (KVK) with a fresh leaf sample.",
            "When symptoms are spreading rapidly across more than 5% of your plot.",
            "When lesions do not match standard visual keys in the TNAU reference catalog.",
            "Before purchasing any commercial chemical formulations or investing in spray equipment."
        ],
        isUncertainOrInconclusive=True,
        safetyNoticeEn="Diagnostic uncertainty: Visual AI analysis is a field aid, not a laboratory assay. Chemical treatment is withheld for your safety and economic protection.",
        safetyNoticeTa="நோயறிதல் வரம்பு: இந்த முடிவு உறுதிப்படுத்தப்படவில்லை. தவறான மருந்து தெளிப்பை தவிர்க்க ரசாயன பரிந்துரைகள் நிறுத்தி வைக்கப்பட்டுள்ளன.",
        references=[
            {
                "organization": "Department of Agriculture, Government of Tamil Nadu",
                "sourceTitle": "Uzhavan Portal - Farmer Advisory & Extension Services",
                "url": "https://agritech.tnau.ac.in/",
                "publicationType": "State Extension Portal"
            },
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal - Crop Protection Diagnostic Protocols",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot.html",
                "publicationType": "Diagnostic Reference"
            }
        ]
    )


# ============================================================================
# CORE REUSABLE TREATMENT RECOMMENDATION SERVICE
# ============================================================================

def get_verified_treatment_recommendation(
    crop: Optional[str] = None,
    condition_name: Optional[str] = None,
    category: Optional[str] = None,
    confidence_percent: int = 0,
    is_crop_leaf: bool = True,
    language: str = "en"
) -> VerifiedTreatmentGuidance:
    """
    Retrieves authoritative, crop-specific agricultural guidance based on crop, condition, and category.
    Strictly follows TNAU/ICAR/CIBRC standards:
    - Never fabricates pesticide brand names, unregistered chemical combos, or dosages.
    - Prohibits chemical pesticides for abiotic/physiological disorders.
    - Truthfully reports uncertain/inconclusive cases without forcing unverified chemicals.
    """
    normalized_crop = (crop or "").strip().lower()
    normalized_condition = (condition_name or "").strip().lower()
    normalized_category = (category or "").strip().lower()

    # Rule 1: If non-crop or inconclusive or extremely low confidence, return defensive inconclusive guidance
    if not is_crop_leaf or normalized_category == "inconclusive" or "inconclusive" in normalized_condition or confidence_percent < 30:
        return build_uncertain_or_inconclusive_guidance(
            crop=crop or "Crop Specimen",
            condition=condition_name or "Uncertain Condition",
            category="inconclusive",
            language=language
        )

    # Rule 2: Search authoritative knowledgebase by exact or keyword match
    matched_entry: Optional[Dict[str, Any]] = None

    # Check Paddy / Rice conditions
    if any(k in normalized_crop for k in ["paddy", "rice", "நெல்"]):
        if any(k in normalized_condition for k in ["blast", "pyricularia", "குலை"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_rice_blast"]
        elif any(k in normalized_condition for k in ["bacterial", "blight", "blb", "xanthomonas", "பாக்டீரியா"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_bacterial_leaf_blight"]
        elif any(k in normalized_condition for k in ["planthopper", "bph", "hopper", "புகையான்"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_brown_planthopper"]
        elif any(k in normalized_condition for k in ["stem borer", "borer", "dead heart", "incertulas", "குருத்து"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_yellow_stem_borer"]
        elif any(k in normalized_condition for k in ["potassium", "k deficiency", "marginal scorch", "பொட்டாசியம்"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_potassium_deficiency"]
        elif any(k in normalized_condition for k in ["zinc", "khaira", "துத்தநாகம்"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["paddy_zinc_deficiency"]

    # Check Groundnut
    elif any(k in normalized_crop for k in ["groundnut", "peanut", "நிலக்கடலை"]):
        if any(k in normalized_condition for k in ["tikka", "cercospora", "leaf spot", "டிக்கா"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["groundnut_tikka_leaf_spot"]

    # Check Tomato
    elif any(k in normalized_crop for k in ["tomato", "தக்காளி"]):
        if any(k in normalized_condition for k in ["early blight", "alternaria", "blight", "இலைக்கருகல்"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["tomato_early_blight"]

    # Check Cotton
    elif any(k in normalized_crop for k in ["cotton", "பருத்தி"]):
        if any(k in normalized_condition for k in ["bollworm", "helicoverpa", "காய் புழு"]):
            matched_entry = AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE["cotton_american_bollworm"]

    # Generic search across conditions if crop wasn't specified or matched loosely
    if not matched_entry:
        for key, data in AUTHORITATIVE_TREATMENT_KNOWLEDGEBASE.items():
            if data["conditionKey"] in normalized_condition or normalized_condition in data["conditionKey"]:
                matched_entry = data
                break

    # If an authoritative match is found, instantiate and return Pydantic schema
    if matched_entry:
        entry_copy = dict(matched_entry)
        
        # Enforce Rule: If category is abiotic disorder, chemical is strictly prohibited
        if entry_copy["category"] == "abiotic_disorder":
            entry_copy["chemicalManagement"]["isApplicable"] = False
            if not entry_copy["chemicalManagement"].get("inapplicableReason"):
                entry_copy["chemicalManagement"]["inapplicableReason"] = (
                    "Chemical pesticides and fungicides are not applicable for abiotic/nutritional disorders."
                )

        return VerifiedTreatmentGuidance(
            crop=entry_copy["crop"],
            cropTa=entry_copy.get("cropTa"),
            conditionKey=entry_copy["conditionKey"],
            conditionNameEn=entry_copy["conditionNameEn"],
            conditionNameTa=entry_copy.get("conditionNameTa"),
            category=entry_copy["category"],
            categoryLabelEn=entry_copy["categoryLabelEn"],
            categoryLabelTa=entry_copy["categoryLabelTa"],
            biologicalManagement=BiologicalManagementGuidance(**entry_copy["biologicalManagement"]),
            chemicalManagement=ChemicalTreatmentGuidance(**entry_copy["chemicalManagement"]),
            ipmStrategySummaryEn=entry_copy["ipmStrategySummaryEn"],
            ipmStrategySummaryTa=entry_copy["ipmStrategySummaryTa"],
            whenToConsultOfficer=entry_copy["whenToConsultOfficer"],
            isUncertainOrInconclusive=entry_copy.get("isUncertainOrInconclusive", False),
            safetyNoticeEn=entry_copy["safetyNoticeEn"],
            safetyNoticeTa=entry_copy["safetyNoticeTa"],
            references=[AuthoritativeReference(**ref) for ref in entry_copy.get("references", [])]
        )

    # Rule 3: Unknown or uncataloged condition -> safe fallback without guessing chemicals
    # If category is abiotic, ensure chemical is marked not applicable
    is_abiotic = (normalized_category == "abiotic_disorder")
    
    return VerifiedTreatmentGuidance(
        crop=crop or "Crop Specimen",
        cropTa=None,
        conditionKey="unmapped_condition",
        conditionNameEn=condition_name or "Uncataloged Agronomic Condition",
        conditionNameTa="பட்டியலிடப்படாத பயிர் நிலை",
        category=normalized_category if normalized_category in ["pest_damage", "plant_disease", "abiotic_disorder", "healthy"] else "inconclusive",
        categoryLabelEn="Uncataloged Condition (Consult AAO)",
        categoryLabelTa="பட்டியலிடப்படாத நிலை (வேளாண் அலுவலரை அணுகவும்)",
        biologicalManagement=BiologicalManagementGuidance(
            culturalPractices=[
                "Inspect field for pattern of spread (e.g. random patches vs uniform field coverage).",
                "Maintain clean farm bunds and remove dead or decaying plant parts."
            ],
            fieldSanitation=[
                "Do not compost suspect diseased material; burn or bury infected leaves if fungal spores or bacterial ooze is suspected."
            ],
            cropRotationAndVarieties=[
                "Follow standard regional crop rotation recommended by your district Agricultural Officer."
            ],
            biologicalControlAgents=[
                "Prophylactic application of certified biocontrol agents (Pseudomonas fluorescens or Neem formulations) is generally safe while awaiting physical confirmation."
            ],
            soilAndNutrientManagement=[
                "Review recent fertilizer applications against Soil Health Card recommendations."
            ]
        ),
        chemicalManagement=ChemicalTreatmentGuidance(
            isApplicable=False,
            inapplicableReason=(
                "CHEMICAL PESTICIDES ARE NOT APPLICABLE FOR PHYSIOLOGICAL/NUTRIENT DISORDERS."
                if is_abiotic else
                "SPECIFIC CHEMICAL RECOMMENDATION WITHHELD. A certified chemical recommendation cannot be verified from our TNAU/CIBRC knowledgebase for this exact condition. Never apply arbitrary or unverified chemical pesticides without an official diagnosis."
            ),
            activeIngredient=None,
            approvedTarget=None,
            dosageAndApplication=None,
            cibrcRegistrationStatus=None,
            preHarvestIntervalDays=None,
            reEntryIntervalHours=None,
            personalProtectiveEquipment=[
                "Standard PPE required for any farm chemical handling."
            ],
            safetyPrecautions=[
                "Consult your block Assistant Agricultural Officer (AAO) or Krishi Vigyan Kendra (KVK) before applying commercial chemicals."
            ]
        ),
        ipmStrategySummaryEn="Specific chemical treatment withheld to prevent unverified pesticide use. Please consult your local Assistant Agricultural Officer (AAO) or TNAU Krishi Vigyan Kendra with a physical sample.",
        ipmStrategySummaryTa="உறுதிப்படுத்தப்படாத மருந்து தெளிப்பை தவிர்க்க ரசாயன பரிந்துரை நிறுத்தி வைக்கப்பட்டுள்ளது. நேரடி மாதிரி உடன் வேளாண்மை அலுவலர் அல்லது கே.வி.கே வல்லுநரை அணுகவும்.",
        whenToConsultOfficer=[
            "Always consult your local Assistant Agricultural Officer (AAO) before applying chemical formulations for uncataloged conditions.",
            "Take fresh plant samples in a clean paper bag to your nearest Krishi Vigyan Kendra (KVK) plant pathology clinic."
        ],
        isUncertainOrInconclusive=True,
        safetyNoticeEn="In compliance with agricultural safety rules, unverified chemical formulations are never fabricated.",
        safetyNoticeTa="விவசாய பாதுகாப்பு நெறிமுறைகளின்படி, உறுதிப்படுத்தப்படாத ரசாயன பரிந்துரைகள் ஒருபோதும் வழங்கப்படாது.",
        references=[
            {
                "organization": "Tamil Nadu Agricultural University (TNAU)",
                "sourceTitle": "TNAU Agritech Portal - Crop Protection Diagnostic Protocols",
                "url": "https://agritech.tnau.ac.in/crop_protection/crop_prot.html",
                "publicationType": "Diagnostic Reference"
            },
            {
                "organization": "Department of Agriculture, Tamil Nadu",
                "sourceTitle": "Uzhavan Extension Advisory Services",
                "url": "https://agritech.tnau.ac.in/",
                "publicationType": "Government Extension Service"
            }
        ]
    )
