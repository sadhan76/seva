import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  headerAction?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  icon,
  headerAction,
  footer,
  children,
  className = '',
}) => {
  return (
    <div
      className={`rounded-2xl bg-white border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col justify-between ${className}`}
    >
      <div>
        {(title || headerAction) && (
          <div className="flex items-start justify-between border-b border-slate-100 p-4 md:p-5 gap-3">
            <div className="flex items-center gap-3 min-w-0">
              {icon && (
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100 shrink-0">
                  {icon}
                </div>
              )}
              <div className="min-w-0">
                <h3 className="text-base font-bold text-slate-800 truncate leading-snug">
                  {title}
                </h3>
                {subtitle && (
                  <p className="text-xs text-slate-500 font-medium truncate mt-0.5">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
            {headerAction && <div className="shrink-0">{headerAction}</div>}
          </div>
        )}
        <div className="p-4 md:p-5">{children}</div>
      </div>

      {footer && (
        <div className="bg-slate-50/70 border-t border-slate-100 px-4 py-3 md:px-5">
          {footer}
        </div>
      )}
    </div>
  );
};
