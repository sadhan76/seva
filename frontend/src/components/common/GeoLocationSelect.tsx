import React, { useState, useEffect, useMemo } from 'react';
import { MapPin, Globe, AlertCircle, Loader2, Info } from 'lucide-react';
import { getStatesApi, getDistrictsApi, getGeoMetaApi } from '../../services/api';
import type { GeoStateItem, GeoDistrictItem, GeoMetaResponse } from '../../types';
import { useLanguage } from '../../context/LanguageContext';

export interface GeoLocationValue {
  country: string;
  state: string;
  stateCode?: string;
  district: string;
  districtCode?: string;
  village?: string;
  taluk?: string;
}

interface GeoLocationSelectProps {
  value: GeoLocationValue;
  onChange: (newValue: GeoLocationValue) => void;
  required?: boolean;
  disabled?: boolean;
  showTalukVillage?: boolean;
  showCountry?: boolean;
  showAttribution?: boolean;
  compact?: boolean;
  className?: string;
}

export const GeoLocationSelect: React.FC<GeoLocationSelectProps> = ({
  value,
  onChange,
  required = true,
  disabled = false,
  showTalukVillage = true,
  showCountry = true,
  showAttribution = false,
  compact = false,
  className = '',
}) => {
  const { language } = useLanguage();
  const [states, setStates] = useState<GeoStateItem[]>([]);
  const [districts, setDistricts] = useState<GeoDistrictItem[]>([]);
  const [isLoadingStates, setIsLoadingStates] = useState(true);
  const [isLoadingDistricts, setIsLoadingDistricts] = useState(false);
  const [districtError, setDistrictError] = useState<string | null>(null);
  const [meta, setMeta] = useState<GeoMetaResponse | null>(null);

  // Load all 36 states and Union Territories on mount
  useEffect(() => {
    let isMounted = true;
    async function loadStatesAndMeta() {
      setIsLoadingStates(true);
      try {
        const [statesData, metaData] = await Promise.all([getStatesApi(), getGeoMetaApi()]);
        if (isMounted) {
          setStates(statesData);
          setMeta(metaData);
        }
      } catch (err) {
        console.error('Failed to load Indian geographic directory states:', err);
      } finally {
        if (isMounted) setIsLoadingStates(false);
      }
    }
    loadStatesAndMeta();
    return () => {
      isMounted = false;
    };
  }, []);

  // Whenever the selected state changes, dynamically load its valid districts
  useEffect(() => {
    let isMounted = true;
    if (!value.state) {
      setDistricts([]);
      setIsLoadingDistricts(false);
      return;
    }

    async function loadDistricts() {
      setIsLoadingDistricts(true);
      setDistrictError(null);
      try {
        const districtList = await getDistrictsApi(value.state);
        if (isMounted) {
          setDistricts(districtList);
          // If the currently selected district is not in the newly loaded state's district list, clear it
          if (value.district && districtList.length > 0) {
            const isCurrentDistrictValid = districtList.some(
              (d) =>
                d.name.toLowerCase() === value.district.toLowerCase() ||
                d.id === value.district.toLowerCase() ||
                d.code === value.districtCode
            );
            if (!isCurrentDistrictValid) {
              onChange({
                ...value,
                district: '',
                districtCode: undefined,
              });
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          setDistrictError('Failed to load districts. Please check network.');
        }
      } finally {
        if (isMounted) setIsLoadingDistricts(false);
      }
    }

    loadDistricts();
    return () => {
      isMounted = false;
    };
  }, [value.state]);

  // Group states into States (28) and Union Territories (8)
  const { normalStates, unionTerritories } = useMemo(() => {
    const normal: GeoStateItem[] = [];
    const uts: GeoStateItem[] = [];
    states.forEach((s) => {
      if (s.type === 'union_territory') {
        uts.push(s);
      } else {
        normal.push(s);
      }
    });
    // Sort alphabetically
    normal.sort((a, b) => a.name.localeCompare(b.name));
    uts.sort((a, b) => a.name.localeCompare(b.name));
    return { normalStates: normal, unionTerritories: uts };
  }, [states]);

  // Helper to format localized state label
  const getStateLabel = (s: GeoStateItem) => {
    const localName = s.localNames && s.localNames[language];
    if (localName && localName !== s.name) {
      return `${s.name} (${localName})`;
    }
    return s.name;
  };

  // Helper to format localized district label
  const getDistrictLabel = (d: GeoDistrictItem) => {
    const localName = d.localNames && d.localNames[language];
    if (localName && localName !== d.name) {
      return `${d.name} (${localName})`;
    }
    return d.name;
  };

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedStateName = e.target.value;
    const matchedState = states.find((s) => s.name === selectedStateName || s.code === selectedStateName);
    onChange({
      ...value,
      country: 'India',
      state: matchedState ? matchedState.name : selectedStateName,
      stateCode: matchedState?.code,
      district: '', // Requirement 4: Clear previously selected district if region changes
      districtCode: undefined,
    });
  };

  const handleDistrictChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedDistrictName = e.target.value;
    const matchedDistrict = districts.find(
      (d) => d.name === selectedDistrictName || d.code === selectedDistrictName
    );
    onChange({
      ...value,
      district: matchedDistrict ? matchedDistrict.name : selectedDistrictName,
      districtCode: matchedDistrict?.code,
    });
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className={`grid grid-cols-1 ${compact ? 'sm:grid-cols-2' : showCountry ? 'sm:grid-cols-4' : 'sm:grid-cols-3'} gap-3`}>
        {/* Country (Defaulted to India) */}
        {showCountry && (
          <div>
            <label className="block font-bold text-slate-700 mb-1 text-xs flex items-center justify-between">
              <span>Country</span>
              <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                Official
              </span>
            </label>
            <div className="relative">
              <Globe className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                readOnly
                value="India"
                className="w-full pl-8 pr-2.5 py-2 bg-slate-100 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 cursor-not-allowed"
                title="AgriBharat supports all 28 States and 8 Union Territories across the Republic of India."
              />
            </div>
          </div>
        )}

        {/* State / Union Territory (All 36 regions) */}
        <div>
          <label className="block font-bold text-slate-700 mb-1 text-xs flex items-center justify-between">
            <span>
              State / UT {required && <span className="text-rose-500">*</span>}
            </span>
            {isLoadingStates && <Loader2 className="w-3 h-3 text-emerald-600 animate-spin" />}
          </label>
          <div className="relative">
            <select
              required={required}
              disabled={disabled || isLoadingStates}
              value={value.state || ''}
              onChange={handleStateChange}
              id="geo-state-select"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <option value="" disabled>
                {isLoadingStates ? 'Loading regions...' : '-- Select State / UT (36) --'}
              </option>
              <optgroup label={`States (${normalStates.length})`}>
                {normalStates.map((s) => (
                  <option key={s.code} value={s.name}>
                    {getStateLabel(s)} ({s.districtsCount} districts)
                  </option>
                ))}
              </optgroup>
              <optgroup label={`Union Territories (${unionTerritories.length})`}>
                {unionTerritories.map((s) => (
                  <option key={s.code} value={s.name}>
                    {getStateLabel(s)} ({s.districtsCount} districts)
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
        </div>

        {/* District (Dependent on Selected State) */}
        <div>
          <label className="block font-bold text-slate-700 mb-1 text-xs flex items-center justify-between">
            <span>
              District {required && <span className="text-rose-500">*</span>}
            </span>
            {isLoadingDistricts && (
              <span className="text-[10px] text-emerald-600 flex items-center gap-1 font-normal">
                <Loader2 className="w-2.5 h-2.5 animate-spin" /> Loading...
              </span>
            )}
            {!isLoadingDistricts && value.state && districts.length > 0 && (
              <span className="text-[10px] text-slate-400 font-normal">
                {districts.length} available
              </span>
            )}
          </label>
          <div className="relative">
            <select
              required={required}
              disabled={disabled || !value.state || isLoadingDistricts}
              value={value.district || ''}
              onChange={handleDistrictChange}
              id="geo-district-select"
              className={`w-full px-3 py-2 bg-slate-50 border ${
                districtError ? 'border-rose-300 bg-rose-50' : 'border-slate-200'
              } rounded-xl text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed`}
            >
              <option value="" disabled>
                {!value.state
                  ? 'First select a State / UT'
                  : isLoadingDistricts
                  ? 'Loading official districts...'
                  : districts.length === 0
                  ? 'No districts available'
                  : '-- Select District --'}
              </option>
              {districts.map((d) => (
                <option key={d.code} value={d.name}>
                  {getDistrictLabel(d)}
                </option>
              ))}
            </select>
          </div>
          {districtError && (
            <p className="text-[10px] text-rose-600 mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> {districtError}
            </p>
          )}
        </div>

        {/* Village / Town / Taluk */}
        {showTalukVillage && (
          <div>
            <label className="block font-bold text-slate-700 mb-1 text-xs">
              Village / Taluk / Mandal {required && <span className="text-rose-500">*</span>}
            </label>
            <div className="relative">
              <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required={required}
                disabled={disabled}
                value={value.village || value.taluk || ''}
                onChange={(e) =>
                  onChange({
                    ...value,
                    village: e.target.value,
                    taluk: e.target.value,
                  })
                }
                placeholder="e.g. Rampur, Kabisthalam"
                className="w-full pl-8 pr-2.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Attribution footer (Optional, for transparency) */}
      {showAttribution && meta && (
        <div className="flex items-center justify-between text-[10px] text-slate-400 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
          <span className="flex items-center gap-1">
            <Info className="w-3 h-3 text-slate-400" />
            Source: {meta.source} ({meta.version}, updated {meta.lastUpdated})
          </span>
          <span className="font-semibold text-slate-500">
            {meta.statesCount} States • {meta.unionTerritoriesCount} UTs • {meta.totalDistricts} Districts
          </span>
        </div>
      )}
    </div>
  );
};
