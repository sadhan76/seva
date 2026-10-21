import React, { useState, useEffect } from 'react';
import {
  Package,
  Calculator,
  ShieldCheck,
  Building2,
  ExternalLink,
  RefreshCw,
  Phone,
  Mail,
  FileCheck2,
  UtensilsCrossed,
  Check
} from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';
import {
  getValueAdditionProducts,
  calculateValueAddition
} from '../../services/api';
import type {
  ValueAdditionProductBlueprint,
  ValueAdditionCalculationRequest,
  ValueAdditionCalculationResponse,
  NavTab
} from '../../types';

interface ValueAddedProductsViewProps {
  onNavigate?: (tab: NavTab) => void;
  initialProduceFilter?: string;
}

export const ValueAddedProductsView: React.FC<ValueAddedProductsViewProps> = ({
  onNavigate: _onNavigate,
  initialProduceFilter
}) => {
  const { language } = useLanguage();
  const isTa = language === 'ta';

  // Filters
  const [selectedRawMaterial, setSelectedRawMaterial] = useState<string>(initialProduceFilter || 'All');
  const [selectedMethodCategory, setSelectedMethodCategory] = useState<string>('All');

  // Blueprints list
  const [products, setProducts] = useState<ValueAdditionProductBlueprint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedProduct, setSelectedProduct] = useState<ValueAdditionProductBlueprint | null>(null);

  // Detail Modal State
  const [detailModalOpen, setDetailModalOpen] = useState<boolean>(false);
  const [activeDetailTab, setActiveDetailTab] = useState<'sop' | 'equipment' | 'recipe' | 'training'>('sop');

  // Calculator State
  const [calculatorModalOpen, setCalculatorModalOpen] = useState<boolean>(false);
  const [calcForm, setCalcForm] = useState<ValueAdditionCalculationRequest>({
    productId: 'tomato_puree',
    rawMaterialQuantityKg: 100,
    rawMaterialCostPerKg: 12,
    yieldLossPercentage: undefined,
    processingCostPerKgOrBatch: 350,
    packagingCostPerFinishedUnit: 15,
    finishedUnitSize: 1.0,
    labourCostTotal: 400,
    transportAndMarketingCost: 250,
    expectedSellingPricePerFinishedUnit: 75,
    includeByproductRecovery: true,
    byproductSellingPricePerKg: 4.5
  });

  const [calculationResult, setCalculationResult] = useState<ValueAdditionCalculationResponse | null>(null);
  const [isCalculating, setIsCalculating] = useState<boolean>(false);

  const rawMaterialFilters = ['All', 'Tomato', 'Groundnut', 'Tapioca', 'Turmeric', 'Millets'];

  const methodFilters = [
    { id: 'All', en: 'All Methods', ta: 'அனைத்து முறைகளும்' },
    { id: 'thermal_processing', en: 'Thermal Processing (Hot Break)', ta: 'வெப்ப பதப்படுத்துதல்' },
    { id: 'cold_extraction', en: 'Cold Extraction (Chekku)', ta: 'மரச்செக்கு பிழிதல்' },
    { id: 'dehydration_drying', en: 'Solar Dehydration & Drying', ta: 'சூரிய கூடார உலர்த்தல்' },
    { id: 'milling_pulverizing', en: 'Milling & Micron Pulverizing', ta: 'அரைவை மற்றும் சலித்தல்' }
  ];

  // Load products
  const loadProducts = async () => {
    setIsLoading(true);
    try {
      const res = await getValueAdditionProducts({
        raw_material: selectedRawMaterial === 'All' ? undefined : selectedRawMaterial,
        method_category: selectedMethodCategory === 'All' ? undefined : selectedMethodCategory
      });
      setProducts(res.items || []);
    } catch (err) {
      console.error('Failed to load value added products:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, [selectedRawMaterial, selectedMethodCategory]);

  // Open Calculator with pre-configured parameters for product
  const handleOpenCalculator = (prod: ValueAdditionProductBlueprint) => {
    setSelectedProduct(prod);

    const defaultRawCost = prod.productId === 'tomato_puree' ? 12 :
                           prod.productId === 'groundnut_cold_pressed_oil' ? 90 :
                           prod.productId === 'tapioca_crisps' ? 14 :
                           prod.productId === 'turmeric_cured_powder' ? 24 : 35;

    const defaultSellingPrice = prod.productId === 'tomato_puree' ? 75 :
                                prod.productId === 'groundnut_cold_pressed_oil' ? 320 :
                                prod.productId === 'tapioca_crisps' ? 180 :
                                prod.productId === 'turmeric_cured_powder' ? 260 : 160;

    const defaultUnitSize = prod.productId === 'tapioca_crisps' ? 0.5 :
                            prod.productId === 'turmeric_cured_powder' ? 0.5 : 1.0;

    const defaultYieldLoss = Math.round((1.0 - prod.rawMaterialToFinishedRatio) * 100);

    const initialCalc: ValueAdditionCalculationRequest = {
      productId: prod.productId,
      rawMaterialQuantityKg: 100,
      rawMaterialCostPerKg: defaultRawCost,
      yieldLossPercentage: defaultYieldLoss,
      processingCostPerKgOrBatch: prod.productId === 'groundnut_cold_pressed_oil' ? 1200 : 400,
      packagingCostPerFinishedUnit: 18,
      finishedUnitSize: defaultUnitSize,
      labourCostTotal: 500,
      transportAndMarketingCost: 300,
      expectedSellingPricePerFinishedUnit: defaultSellingPrice,
      includeByproductRecovery: true,
      byproductSellingPricePerKg: prod.typicalByproducts[0]?.typicalValuePerKg || 5.0
    };

    setCalcForm(initialCalc);
    setCalculatorModalOpen(true);
    runLiveCalculation(initialCalc);
  };

  const runLiveCalculation = async (req: ValueAdditionCalculationRequest) => {
    setIsCalculating(true);
    try {
      const res = await calculateValueAddition(req);
      setCalculationResult(res);
    } catch (err) {
      console.error('Calculation error:', err);
    } finally {
      setIsCalculating(false);
    }
  };

  const handleOpenDetails = (prod: ValueAdditionProductBlueprint) => {
    setSelectedProduct(prod);
    setActiveDetailTab('sop');
    setDetailModalOpen(true);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner Header */}
      <div className="rounded-3xl bg-linear-to-r from-amber-900 via-orange-900 to-emerald-950 text-white p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-200 text-xs font-bold border border-amber-400/30">
            <UtensilsCrossed className="w-3.5 h-3.5 text-amber-300" />
            <span>{isTa ? 'மதிப்புக் கூட்டப்பட்ட உணவுப் பொருட்கள் மையம்' : 'Institutional Value-Added Food Blueprints'}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
            {isTa ? 'அறுவடைக்கு பின் கூடுதல் லாபம் தரும் மதிப்பு கூட்டல்' : 'Post-Harvest Processing & Value Addition'}
          </h1>
          <p className="text-amber-100 text-xs sm:text-sm leading-relaxed">
            {isTa
              ? 'தக்காளி, நிலக்கடலை, மரவள்ளி, மஞ்சள், மற்றும் சிறுதானியங்களை அரசு வழிகாட்டுதல்படி பதப்படுத்தி, FSSAI தரத்துடன் 3x மடங்கு லாபம் ஈட்டுங்கள்.'
              : 'Multiply farm gate realization by transforming raw agricultural produce into premium shelf-stable foods using verified SOPs from TNAU PHTC, NIFTEM-Thanjavur, and CFTRI.'}
          </p>

          {/* Institutional Integrity Alert */}
          <div className="pt-2">
            <div className="p-3 rounded-xl bg-amber-950/70 border border-amber-700/50 text-[11px] text-amber-200 flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong>{isTa ? 'உறுதிப்படுத்தப்பட்ட அறிவியல் முறைகள்:' : 'Institutionally Verified Processing Protocols:'} </strong>
                {isTa
                  ? 'பதப்படுத்தும் வழிமுறைகள் மற்றும் கழிவு இழப்பு விகிதங்கள் TNAU PHTC & NIFTEM-T அதிகாரப்பூர்வ கையேடுகளை அடிப்படையாகக் கொண்டவை. செயற்கை காலாவதி தேதிகள் சேர்க்கப்படவில்லை.'
                  : 'SOPs, yield recovery fractions, and shelf life parameters cite published technical bulletins of TNAU PHTC & NIFTEM-T. Profitability calculator incorporates mass loss and byproduct recovery.'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-xs space-y-4">
        {/* Raw Material Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-slate-500 mr-1">{isTa ? 'மூலப்பொருள்:' : 'Raw Material:'}</span>
          {rawMaterialFilters.map((rm) => (
            <button
              key={rm}
              onClick={() => setSelectedRawMaterial(rm)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedRawMaterial === rm
                  ? 'bg-amber-700 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {rm}
            </button>
          ))}
        </div>

        {/* Processing Method Pills */}
        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-xs font-bold text-slate-500 mr-1">{isTa ? 'பதப்படுத்தும் முறை:' : 'Processing Method:'}</span>
          {methodFilters.map((mf) => (
            <button
              key={mf.id}
              onClick={() => setSelectedMethodCategory(mf.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                selectedMethodCategory === mf.id
                  ? 'bg-emerald-800 text-white font-bold shadow-xs'
                  : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {isTa ? mf.ta : mf.en}
            </button>
          ))}
        </div>
      </div>

      {/* Products Blueprint Grid */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-amber-700" />
          <span>{isTa ? 'தயாரிப்பு வரைபடங்கள் ஏற்றப்படுகின்றன...' : 'Loading value-added product blueprints...'}</span>
        </div>
      ) : products.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <Package className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <h4 className="text-sm font-bold text-slate-700">{isTa ? 'தயாரிப்புகள் கிடைக்கவில்லை' : 'No products match selected filters'}</h4>
          <p className="text-xs text-slate-500 mt-1">
            {isTa ? 'அனைத்து வகைகளையும் காண பில்டர்களை மீட்டமைக்கவும்.' : 'Reset filters to view all institutional product blueprints.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {products.map((prod) => {
            const yieldPercent = Math.round(prod.rawMaterialToFinishedRatio * 100);
            const wastePercent = 100 - yieldPercent;

            return (
              <div
                key={prod.productId}
                className="bg-white rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-all flex flex-col justify-between overflow-hidden"
              >
                <div className="p-5 space-y-4">
                  {/* Category & Method Badges */}
                  <div className="flex items-center justify-between gap-1 flex-wrap">
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-900 border border-amber-200">
                      {prod.rawMaterial}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                      {prod.fssaiCategory.split(':')[0]}
                    </span>
                  </div>

                  {/* Title & Processing Method */}
                  <div>
                    <h3 className="text-base font-extrabold text-slate-900 leading-snug">
                      {isTa ? prod.productName.ta : prod.productName.en}
                    </h3>
                    <p className="text-xs text-emerald-800 font-semibold mt-1">
                      ⚙️ {prod.processingMethod}
                    </p>
                  </div>

                  {/* Yield & Loss Conversion Metric */}
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-[10px] font-bold text-slate-500 uppercase">{isTa ? 'பொருளாதார மீட்பு (Yield)' : 'Product Recovery'}</div>
                      <div className="text-base font-black text-emerald-800 font-mono mt-0.5">
                        {yieldPercent}%
                      </div>
                      <div className="text-[10px] text-slate-500">
                        100kg → <strong>{yieldPercent} kg/L</strong>
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] font-bold text-slate-500 uppercase">{isTa ? 'செயல்முறை கழிவு (Loss)' : 'Processing Loss'}</div>
                      <div className="text-base font-black text-amber-800 font-mono mt-0.5">
                        {wastePercent}%
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {isTa ? 'ஈரப்பதம் / தோல் நீக்கம்' : 'Moisture & Peel Loss'}
                      </div>
                    </div>
                  </div>

                  {/* Byproduct Recovery note */}
                  {prod.typicalByproducts && prod.typicalByproducts.length > 0 && (
                    <div className="text-[11px] text-slate-600 bg-amber-50/60 p-2.5 rounded-xl border border-amber-100 flex items-center justify-between">
                      <span>🌱 {isTa ? 'துணைப்பொருள்:' : 'Byproduct:'} <strong>{prod.typicalByproducts[0].name}</strong></span>
                      <span className="font-mono font-bold text-amber-900">~₹{prod.typicalByproducts[0].typicalValuePerKg}/kg</span>
                    </div>
                  )}

                  {/* Shelf Life & Storage */}
                  <div className="space-y-1 text-xs text-slate-600">
                    <div>
                      <span className="font-bold text-slate-700">{isTa ? 'காலாவதி & சேமிப்பு:' : 'Shelf Life:'} </span>
                      <span>{isTa ? prod.shelfLifeAndStorage.ta : prod.shelfLifeAndStorage.en}</span>
                    </div>
                  </div>

                  {/* Reference Citation */}
                  <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-500 flex items-center gap-1">
                    <Building2 className="w-3 h-3 text-slate-400 shrink-0" />
                    <span className="truncate">{prod.authoritativeReference.institute}</span>
                  </div>
                </div>

                {/* Card Action Buttons */}
                <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleOpenDetails(prod)}
                    className="text-xs font-bold text-slate-700 hover:text-emerald-800 hover:underline flex items-center gap-1"
                  >
                    <FileCheck2 className="w-3.5 h-3.5" />
                    <span>{isTa ? 'SOP & தரம்' : 'SOP & Hygiene'}</span>
                  </button>

                  <button
                    onClick={() => handleOpenCalculator(prod)}
                    className="px-3.5 py-2 rounded-xl bg-amber-700 hover:bg-amber-800 text-white font-bold text-xs shadow-xs transition-all flex items-center gap-1.5"
                  >
                    <Calculator className="w-3.5 h-3.5" />
                    <span>{isTa ? 'செலவு & லாபக் கணக்கு' : 'Cost & Profit'}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL 1: COSTING & PROFITABILITY CALCULATOR */}
      {calculatorModalOpen && selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl relative my-8 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Calculator className="w-5 h-5 text-amber-700" />
                <div>
                  <h3 className="text-lg font-extrabold text-slate-900">
                    {isTa ? 'உற்பத்தி செலவு மற்றும் லாப கணக்கீட்டுக் கருவி' : 'Value-Addition Cost & Profitability Calculator'}
                  </h3>
                  <p className="text-xs text-slate-500">{selectedProduct.productName.en}</p>
                </div>
              </div>
              <button
                onClick={() => setCalculatorModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Raw Material Batch Qty */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'மூலப்பொருள் அளவு (Batch Quantity kg) *' : 'Raw Material Quantity (kg) *'}
                </label>
                <input
                  type="number"
                  min="1"
                  value={calcForm.rawMaterialQuantityKg}
                  onChange={(e) => {
                    const updated = { ...calcForm, rawMaterialQuantityKg: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800"
                />
              </div>

              {/* Raw Material Farm Gate Cost */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'மூலப்பொருள் பண்ணை விலை (₹ / kg) *' : 'Raw Material Farm Price (₹ / kg) *'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={calcForm.rawMaterialCostPerKg}
                  onChange={(e) => {
                    const updated = { ...calcForm, rawMaterialCostPerKg: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800"
                />
              </div>

              {/* Yield Loss / Waste Deduction */}
              <div>
                <div className="flex justify-between mb-1">
                  <label className="font-bold text-slate-700">
                    {isTa ? 'செயல்முறை கழிவு & இழப்பு (%)' : 'Yield Loss / Moisture Loss (%)'}
                  </label>
                  <span className="font-mono font-bold text-amber-800">
                    {calcForm.yieldLossPercentage || Math.round((1.0 - selectedProduct.rawMaterialToFinishedRatio) * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="90"
                  value={calcForm.yieldLossPercentage || Math.round((1.0 - selectedProduct.rawMaterialToFinishedRatio) * 100)}
                  onChange={(e) => {
                    const updated = { ...calcForm, yieldLossPercentage: parseFloat(e.target.value) };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full accent-amber-700"
                />
                <span className="text-[10px] text-slate-400">
                  {isTa ? 'பல்கலைக்கழக நிலையான கழிவு விகிதம்' : 'University standard conversion baseline'}
                </span>
              </div>

              {/* Finished Package Size */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'முடிவுற்ற பாக்கெட் அளவு (kg அல்லது Litre)' : 'Finished Pack Size (kg or L)'}
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={calcForm.finishedUnitSize || 1.0}
                  onChange={(e) => {
                    const updated = { ...calcForm, finishedUnitSize: parseFloat(e.target.value) || 1.0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl font-bold text-slate-800"
                />
              </div>

              {/* Processing Cost (Power/Fuel) */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'பதப்படுத்துதல் செலவு (எரிபொருள்/மின்சாரம் ₹)' : 'Processing Energy / Fuel Cost (₹)'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={calcForm.processingCostPerKgOrBatch}
                  onChange={(e) => {
                    const updated = { ...calcForm, processingCostPerKgOrBatch: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>

              {/* Packaging Cost per Unit */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'பேக்கிங் செலவு (பாட்டில்/பை ₹ / unit)' : 'Packaging Cost (Bottle/Pouch ₹ / unit)'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={calcForm.packagingCostPerFinishedUnit}
                  onChange={(e) => {
                    const updated = { ...calcForm, packagingCostPerFinishedUnit: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>

              {/* Labour & Logistics */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'கூலி & வேலை ஆட்கள் செலவு (₹)' : 'Processing Labour Expense (₹)'}
                </label>
                <input
                  type="number"
                  min="0"
                  value={calcForm.labourCostTotal}
                  onChange={(e) => {
                    const updated = { ...calcForm, labourCostTotal: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>

              {/* Target Selling Price */}
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  {isTa ? 'எதிர்பார்க்கும் விற்பனை விலை (₹ / pack) *' : 'Target Selling Price (₹ / pack) *'}
                </label>
                <input
                  type="number"
                  min="1"
                  value={calcForm.expectedSellingPricePerFinishedUnit}
                  onChange={(e) => {
                    const updated = { ...calcForm, expectedSellingPricePerFinishedUnit: parseFloat(e.target.value) || 0 };
                    setCalcForm(updated);
                    runLiveCalculation(updated);
                  }}
                  className="w-full px-3 py-2 bg-emerald-50 border border-emerald-300 rounded-xl font-bold text-emerald-900"
                />
              </div>
            </div>

            {/* Live Calculation Results Breakdown */}
            {calculationResult && (
              <div className="space-y-3 pt-3 border-t border-slate-100 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                    {isTa ? 'நேரடி கணக்கீடு முடிவுகள்' : 'Live Unit Economics'}
                  </span>
                  {isCalculating && (
                    <span className="flex items-center gap-1 text-[11px] text-emerald-700">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      <span>{isTa ? 'கணக்கிடப்படுகிறது...' : 'Recalculating...'}</span>
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="text-[10px] text-slate-500 font-bold">{isTa ? 'உற்பத்தி அளவு' : 'Finished Output'}</div>
                    <div className="text-base font-black text-slate-900 font-mono mt-0.5">
                      {calculationResult.finishedUnitsCount} {isTa ? 'பாக்கெட்கள்' : 'Packs'}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      ({calculationResult.finishedProductQuantity} kg/L)
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="text-[10px] text-slate-500 font-bold">{isTa ? 'மொத்த உற்பத்தி செலவு' : 'Total Expenses'}</div>
                    <div className="text-base font-black text-slate-900 font-mono mt-0.5">
                      ₹{calculationResult.totalExpenses.total.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      Cost: <strong>₹{calculationResult.costPerFinishedUnit}/pk</strong>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
                    <div className="text-[10px] text-emerald-800 font-bold">{isTa ? 'மொத்த வரவு' : 'Gross Revenue'}</div>
                    <div className="text-base font-black text-emerald-950 font-mono mt-0.5">
                      ₹{calculationResult.totalGrossRevenue.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[10px] text-emerald-700">
                      Byproduct: +₹{calculationResult.byproductRevenue}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-emerald-100/70 border border-emerald-300">
                    <div className="text-[10px] text-emerald-900 font-bold">{isTa ? 'மதிப்பிடப்பட்ட லாபம்' : 'Estimated Profit'}</div>
                    <div className="text-base font-black text-emerald-950 font-mono mt-0.5">
                      ₹{calculationResult.estimatedGrossProfit.toLocaleString('en-IN')}
                    </div>
                    <div className="text-[10px] text-emerald-800 font-bold">
                      {calculationResult.estimatedProfitMarginPercent}% Margin
                    </div>
                  </div>
                </div>

                {/* Assumptions List */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-[11px] text-slate-600 space-y-1">
                  <strong className="text-slate-800 block">{isTa ? 'கணக்கீட்டு அனுமானங்கள்:' : 'Itemized Assumptions:'}</strong>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {calculationResult.itemizedAssumptions.map((as, i) => (
                      <li key={i}>{as}</li>
                    ))}
                  </ul>
                </div>

                {/* Disclaimer */}
                <p className="text-[10px] text-slate-500 italic">
                  "{calculationResult.disclaimer}"
                </p>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setCalculatorModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs shadow-md"
              >
                {isTa ? 'சரி (Done)' : 'Close Calculator'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: FULL BLUEPRINT DETAILS (SOP, HYGIENE, EQUIPMENT, TRAINING) */}
      {detailModalOpen && selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-3xl w-full p-6 space-y-5 shadow-2xl relative my-8 animate-in fade-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[11px] font-bold text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                  {selectedProduct.fssaiCategory}
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-1">
                  {isTa ? selectedProduct.productName.ta : selectedProduct.productName.en}
                </h3>
              </div>
              <button
                onClick={() => setDetailModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {/* Sub-Tabs for Details */}
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2 text-xs font-bold overflow-x-auto">
              <button
                onClick={() => setActiveDetailTab('sop')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeDetailTab === 'sop' ? 'bg-amber-700 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {isTa ? '1. தயாரிப்பு முறை (SOP & CCP)' : '1. Standard Operating Procedure'}
              </button>

              <button
                onClick={() => setActiveDetailTab('equipment')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeDetailTab === 'equipment' ? 'bg-amber-700 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {isTa ? '2. இயந்திரங்கள் & உபகரணங்கள்' : '2. Required Equipment'}
              </button>

              <button
                onClick={() => setActiveDetailTab('recipe')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeDetailTab === 'recipe' ? 'bg-amber-700 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {isTa ? '3. மூலப்பொருள் விகிதம்' : '3. Recipe Proportions'}
              </button>

              <button
                onClick={() => setActiveDetailTab('training')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeDetailTab === 'training' ? 'bg-amber-700 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {isTa ? '4. பயிற்சி & நிறுவனங்கள்' : '4. Training Providers'}
              </button>
            </div>

            {/* TAB CONTENT: SOP */}
            {activeDetailTab === 'sop' && (
              <div className="space-y-4 text-xs">
                {/* Food safety and hygiene notice */}
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1.5">
                  <div className="font-bold text-emerald-950 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-700" />
                    <span>{isTa ? 'FSSAI உணவு பாதுகாப்பு & சுகாதார விதிமுறைகள்:' : 'FSSAI Food Safety Standards:'}</span>
                  </div>
                  <ul className="space-y-1 text-emerald-900">
                    {selectedProduct.foodSafetyAndHygiene.map((h, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{isTa ? h.ta : h.en}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Steps */}
                <div className="space-y-2.5">
                  {selectedProduct.standardOperatingProcedure.map((s) => (
                    <div key={s.stepNumber} className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                      <div className="flex items-center justify-between">
                        <strong className="text-slate-900 font-bold">
                          {s.stepNumber}. {s.stepTitle}
                        </strong>
                        <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-md">
                          CCP: {s.criticalControlPoint}
                        </span>
                      </div>
                      <p className="text-slate-700 leading-relaxed">{s.details}</p>
                      <div className="text-[11px] text-slate-500 pt-1">
                        🧼 <em>{s.hygieneStandard}</em>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB CONTENT: EQUIPMENT */}
            {activeDetailTab === 'equipment' && (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <h4 className="font-bold text-slate-800 mb-2">{isTa ? 'தேவைப்படும் இயந்திரங்கள் மற்றும் முதலீடு:' : 'Equipment Benchmark Specs & Costs:'}</h4>
                  <div className="space-y-2">
                    {selectedProduct.requiredEquipment.map((eq, i) => (
                      <div key={i} className="p-2.5 rounded-lg bg-white border border-slate-200 flex items-center justify-between">
                        <div>
                          <strong className="text-slate-900 block">{eq.machineName}</strong>
                          <span className="text-[11px] text-slate-500">{eq.purpose} • Capacity: {eq.capacity}</span>
                        </div>
                        <span className="font-mono font-bold text-amber-900 text-sm">
                          ₹{eq.approxCostInr.toLocaleString('en-IN')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: RECIPE */}
            {activeDetailTab === 'recipe' && (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <h4 className="font-bold text-slate-800 mb-2">{isTa ? 'மூலப்பொருள் செய்முறை விகிதங்கள்:' : 'Formula & Recipe Proportions:'}</h4>
                  <div className="space-y-1.5">
                    {selectedProduct.ingredientsAndRecipe.map((ing, i) => (
                      <div key={i} className="p-2 rounded-lg bg-white border border-slate-200 flex items-center justify-between">
                        <div>
                          <strong className="text-slate-900">{ing.ingredientName}</strong>
                          <span className="text-[11px] text-slate-500 block">{ing.purpose} ({ing.foodGradeGrade})</span>
                        </div>
                        <span className="font-mono font-bold text-emerald-800 text-sm">
                          {ing.proportionPercentage}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: TRAINING & OFFICIAL INSTITUTES */}
            {activeDetailTab === 'training' && (
              <div className="space-y-3 text-xs">
                <div className="space-y-2">
                  {selectedProduct.trainingProviders.map((tp, i) => (
                    <div key={i} className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <strong className="text-amber-950 font-bold text-sm">{tp.institute}</strong>
                        <span className="text-[11px] font-semibold text-amber-800">{tp.location}</span>
                      </div>
                      <p className="text-amber-900">🎓 {tp.courseName}</p>
                      <div className="flex items-center gap-4 text-[11px] pt-1 border-t border-amber-200">
                        <span className="flex items-center gap-1 text-amber-950 font-semibold">
                          <Phone className="w-3 h-3 text-amber-700" /> {tp.contact}
                        </span>
                        <span className="flex items-center gap-1 text-amber-950 font-semibold">
                          <Mail className="w-3 h-3 text-amber-700" /> {tp.email}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Authoritative document link */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-600 flex items-center justify-between">
                  <span>📄 {selectedProduct.authoritativeReference.document}</span>
                  {selectedProduct.authoritativeReference.verificationUrl && (
                    <a
                      href={selectedProduct.authoritativeReference.verificationUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-amber-800 font-bold hover:underline inline-flex items-center gap-0.5"
                    >
                      Official Page <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-between items-center pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  setDetailModalOpen(false);
                  handleOpenCalculator(selectedProduct);
                }}
                className="px-4 py-2 rounded-xl bg-amber-700 hover:bg-amber-800 text-white font-bold text-xs shadow-xs flex items-center gap-1.5"
              >
                <Calculator className="w-3.5 h-3.5" />
                <span>{isTa ? 'செலவு கணக்கிடவும்' : 'Open Calculator'}</span>
              </button>

              <button
                onClick={() => setDetailModalOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 text-xs font-semibold"
              >
                {isTa ? 'மூடு' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
