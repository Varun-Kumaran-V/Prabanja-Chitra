/**
 * Reusable Card Components
 */
import { memo } from 'react';

// Base Card component
export const Card = memo(function Card({ 
  children, 
  className = '', 
  variant = 'default',
  padding = 'normal',
  hover = true,
  glow = false,
  borderAccent = null, // 'left', 'top', or color value
  style = {},
}) {
  const variants = {
    default: 'bg-[#1a1d26] border-[#2a2f3a]',
    elevated: 'bg-[#1f2430] border-[#3a3f4a] shadow-xl',
    dark: 'bg-[#0b0e14] border-[#3c4947]/20',
    glass: 'bg-[#1d2026]/60 backdrop-blur-xl border-[#4fdbc8]/20',
  };

  const paddings = {
    none: '',
    small: 'p-4',
    medium: 'p-5',
    normal: 'p-6',
    large: 'p-8',
  };

  const hoverClass = hover 
    ? 'hover:shadow-xl hover:border-[#3a3f4a] hover:scale-[1.02] transition-all duration-300' 
    : '';

  const glowClass = glow 
    ? 'shadow-[0_0_30px_rgba(79,219,200,0.1)]' 
    : 'shadow-lg';

  let borderClass = '';
  if (borderAccent === 'left') {
    borderClass = 'border-l-4 border-l-[#4fdbc8]';
  } else if (borderAccent === 'top') {
    borderClass = 'border-t-4 border-t-[#4fdbc8]';
  } else if (borderAccent) {
    borderClass = `border-l-4 border-l-[${borderAccent}]`;
  }

  return (
    <div 
      className={`
        rounded-xl border 
        ${variants[variant]} 
        ${paddings[padding]} 
        ${hoverClass}
        ${glowClass}
        ${borderClass}
        ${className}
      `}
      style={style}
    >
      {children}
    </div>
  );
});

// Stat Card - for displaying key metrics
export const StatCard = memo(function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendDirection = 'up', // 'up', 'down', 'neutral'
  accentColor = '#4fdbc8',
  size = 'normal', // 'small', 'normal', 'large'
  className = '',
}) {
  const sizeClasses = {
    small: { value: 'text-2xl', icon: 'text-xl' },
    normal: { value: 'text-4xl', icon: 'text-2xl' },
    large: { value: 'text-5xl', icon: 'text-3xl' },
  };

  const trendColors = {
    up: 'text-[#4fdbc8]',
    down: 'text-[#ffb4ab]',
    neutral: 'text-[#bbcac6]',
  };

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <Card 
      className={`group relative overflow-hidden ${className}`}
      style={{ borderLeftColor: accentColor }}
      borderAccent="left"
    >
      {/* Subtle glow effect on hover */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ 
          background: `radial-gradient(circle at top right, ${accentColor}10 0%, transparent 70%)` 
        }}
      />
      
      <div className="relative">
        {/* Header with title and icon */}
        <div className="flex justify-between items-start mb-4">
          <span className="text-[0.6875rem] font-bold uppercase tracking-widest text-[#6c7086] group-hover:text-[#bbcac6] transition-colors">
            {title}
          </span>
          {icon && (
            <span className={`${sizeClasses[size].icon} opacity-60 group-hover:opacity-100 transition-opacity`}>
              {icon}
            </span>
          )}
        </div>

        {/* Value */}
        <div 
          className={`${sizeClasses[size].value} font-extrabold tracking-tight mb-2 metric-value`}
          style={{ color: accentColor === '#4fdbc8' ? '#e1e2eb' : accentColor }}
        >
          {value}
        </div>

        {/* Subtitle and trend */}
        <div className="flex items-center gap-2">
          {subtitle && (
            <span className="text-xs text-[#6c7086] italic">{subtitle}</span>
          )}
          {trend && (
            <span className={`text-xs font-bold ${trendColors[trendDirection]}`}>
              {trendIcons[trendDirection]} {trend}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
});

// Section Header component
export const SectionHeader = memo(function SectionHeader({ 
  label, 
  title, 
  subtitle,
  action,
  className = '' 
}) {
  return (
    <header className={`flex flex-col md:flex-row md:items-end justify-between gap-4 ${className}`}>
      <div>
        {label && (
          <span className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold text-[#4fdbc8] mb-1 block">
            {label}
          </span>
        )}
        <h1 className="text-3xl font-extrabold tracking-tight text-[#e1e2eb]">
          {title}
        </h1>
        {subtitle && (
          <p className="text-[#bbcac6] mt-2">{subtitle}</p>
        )}
      </div>
      {action && (
        <div className="flex items-center gap-3">
          {action}
        </div>
      )}
    </header>
  );
});

// Status Badge component
export const StatusBadge = memo(function StatusBadge({ 
  status, 
  pulse = false,
  size = 'normal' 
}) {
  const statusConfig = {
    AUTONOMOUS: { color: '#4fdbc8', bg: 'rgba(79, 219, 200, 0.15)' },
    MANUAL: { color: '#ffb59e', bg: 'rgba(255, 181, 158, 0.15)' },
    CRITICAL: { color: '#ffb4ab', bg: 'rgba(255, 180, 171, 0.2)' },
    HIGH: { color: '#f38764', bg: 'rgba(243, 135, 100, 0.2)' },
    MEDIUM: { color: '#ffb59e', bg: 'rgba(255, 181, 158, 0.2)' },
    LOW: { color: '#a0d0c6', bg: 'rgba(160, 208, 198, 0.2)' },
    WATCH: { color: '#bbcac6', bg: 'rgba(187, 202, 198, 0.2)' },
    NOMINAL: { color: '#4fdbc8', bg: 'rgba(79, 219, 200, 0.15)' },
    ACTIVE: { color: '#4fdbc8', bg: 'rgba(79, 219, 200, 0.15)' },
    PENDING: { color: '#ffb59e', bg: 'rgba(255, 181, 158, 0.15)' },
  };

  const config = statusConfig[status] || statusConfig.WATCH;
  const sizeClasses = size === 'small' ? 'text-[0.6rem] px-2 py-0.5' : 'text-xs px-3 py-1.5';

  return (
    <span 
      className={`
        inline-flex items-center gap-2 rounded-lg font-bold uppercase tracking-wider
        ${sizeClasses}
      `}
      style={{ 
        backgroundColor: config.bg, 
        color: config.color 
      }}
    >
      {pulse && (
        <span 
          className="w-2 h-2 rounded-full animate-pulse"
          style={{ backgroundColor: config.color }}
        />
      )}
      {status}
    </span>
  );
});

// Progress Bar component
export const ProgressBar = memo(function ProgressBar({ 
  value, 
  max = 100, 
  color = '#4fdbc8',
  height = 'normal',
  showLabel = false,
  label = '',
  animated = true,
}) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  const heights = {
    small: 'h-1',
    normal: 'h-2',
    large: 'h-4',
  };

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between text-xs mb-1">
          <span className="text-[#bbcac6]">{label}</span>
          <span className="font-mono text-[#e1e2eb] metric-value">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className={`w-full bg-[#0b0e14] rounded-full overflow-hidden ${heights[height]} shadow-inner`}>
        <div
          className={`${heights[height]} rounded-full ${animated ? 'transition-all duration-500' : ''}`}
          style={{ 
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color}, ${color}cc)`,
          }}
        />
      </div>
    </div>
  );
});

// Empty State component
export const EmptyState = memo(function EmptyState({ 
  icon = '📭', 
  title = 'No data available', 
  description,
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <span className="text-4xl mb-4 opacity-50">{icon}</span>
      <h3 className="text-lg font-semibold text-[#e1e2eb] mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-[#bbcac6] max-w-xs">{description}</p>
      )}
      {action && (
        <div className="mt-4">{action}</div>
      )}
    </div>
  );
});

export default {
  Card,
  StatCard,
  SectionHeader,
  StatusBadge,
  ProgressBar,
  EmptyState,
};
