import React from 'react';
import { CloudSun, Droplets, Wind, CloudRain, Sun } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { useLanguage } from '../../context/LanguageContext';
import type { WeatherData } from '../../types';

interface WeatherCardProps {
  weather: WeatherData;
  onViewForecast?: () => void;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({
  weather,
  onViewForecast,
}) => {
  const { t } = useLanguage();

  return (
    <Card
      title={t.dashboard.weatherTitle}
      subtitle={weather.updatedAt}
      icon={<CloudSun className="w-5 h-5 text-amber-500" />}
      headerAction={
        weather.isSample ? (
          <Badge variant="amber" dot>
            {t.sampleBadge}
          </Badge>
        ) : (
          <Badge variant="emerald" dot>
            Live
          </Badge>
        )
      }
      footer={
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="text-[11px] text-slate-400">
            {weather.isSample ? 'Sample Data' : 'Live Agro-Weather'}
          </span>
          {onViewForecast && (
            <button
              onClick={onViewForecast}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 hover:underline"
            >
              5-Day Forecast →
            </button>
          )}
        </div>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between bg-gradient-to-br from-amber-500/10 via-emerald-500/5 to-transparent p-3.5 rounded-xl border border-amber-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-100/80 text-amber-600">
              <Sun className="w-8 h-8 animate-spin-slow" />
            </div>
            <div>
              <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
                {weather.temperatureC}°C
              </div>
              <p className="text-xs font-medium text-slate-600">
                {weather.condition}
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className="inline-block text-xs font-semibold text-emerald-700 bg-emerald-100/70 px-2.5 py-1 rounded-full">
              Favorable for Sowing
            </span>
          </div>
        </div>

        {/* Weather sub-metrics */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
            <div className="flex items-center justify-center gap-1 text-slate-400 mb-1">
              <Droplets className="w-3.5 h-3.5 text-blue-500" />
              <span className="text-[11px] font-medium uppercase text-slate-500">{t.dashboard.labels.humidity}</span>
            </div>
            <p className="text-sm font-bold text-slate-800">{weather.humidity}%</p>
          </div>

          <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
            <div className="flex items-center justify-center gap-1 text-slate-400 mb-1">
              <CloudRain className="w-3.5 h-3.5 text-cyan-600" />
              <span className="text-[11px] font-medium uppercase text-slate-500">{t.dashboard.labels.rainfallChance}</span>
            </div>
            <p className="text-sm font-bold text-slate-800">{weather.rainfallChance}%</p>
          </div>

          <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
            <div className="flex items-center justify-center gap-1 text-slate-400 mb-1">
              <Wind className="w-3.5 h-3.5 text-slate-500" />
              <span className="text-[11px] font-medium uppercase text-slate-500">{t.dashboard.labels.windSpeed}</span>
            </div>
            <p className="text-sm font-bold text-slate-800">{weather.windSpeedKmh} km/h</p>
          </div>
        </div>

        {/* 3 Day forecast mini row */}
        <div className="border-t border-slate-100 pt-3">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            3-Day Mini Outlook (Simulated)
          </p>
          <div className="grid grid-cols-3 gap-2">
            {weather.forecast.map((f, idx) => (
              <div key={idx} className="rounded-lg bg-emerald-50/40 border border-emerald-100/60 p-2 text-center text-xs">
                <p className="font-semibold text-slate-700">{f.day}</p>
                <p className="text-[11px] text-slate-500 my-0.5">{f.temp}</p>
                <p className="text-[10px] text-emerald-700 font-medium">Rain: {f.rainProb}%</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};
