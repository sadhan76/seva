import React from 'react';
import { Loader2, AlertTriangle, Inbox, RefreshCw } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export const LoadingState: React.FC<{ message?: string; description?: string }> = ({
  message,
  description,
}) => {
  const { t } = useLanguage();
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl bg-white border border-slate-200">
      <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600 mb-4">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
      <h4 className="text-base font-semibold text-slate-800">
        {message || t.common.loading}
      </h4>
      <p className="text-xs md:text-sm text-slate-500 max-w-sm mt-1">
        {description || t.common.loadingDesc}
      </p>
    </div>
  );
};

export const EmptyState: React.FC<{
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}> = ({ title, description, actionText, onAction }) => {
  const { t } = useLanguage();
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl bg-white border border-dashed border-slate-300">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
        <Inbox className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-slate-800">
        {title || t.common.emptyTitle}
      </h4>
      <p className="text-xs md:text-sm text-slate-500 max-w-sm mt-1">
        {description || t.common.emptyDesc}
      </p>
      {onAction && actionText && (
        <button
          onClick={onAction}
          className="mt-4 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

export const ErrorState: React.FC<{
  title?: string;
  description?: string;
  onRetry?: () => void;
}> = ({ title, description, onRetry }) => {
  const { t } = useLanguage();
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl bg-white border border-rose-200 bg-rose-50/30">
      <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-rose-900">
        {title || t.common.errorTitle}
      </h4>
      <p className="text-xs md:text-sm text-rose-600 max-w-sm mt-1">
        {description || t.common.errorDesc}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {t.common.retry}
        </button>
      )}
    </div>
  );
};
