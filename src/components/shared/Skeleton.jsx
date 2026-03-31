/**
 * Skeleton loading components for professional loading states
 */
import { memo } from 'react';

// Base skeleton with shimmer effect
export const Skeleton = memo(function Skeleton({ className = '', variant = 'default' }) {
  const baseClasses = 'animate-skeleton bg-gradient-to-r from-[#1a1d26] via-[#272a31] to-[#1a1d26] bg-[length:200%_100%]';
  
  const variants = {
    default: 'rounded',
    circle: 'rounded-full',
    card: 'rounded-xl',
  };

  return (
    <div className={`${baseClasses} ${variants[variant]} ${className}`} />
  );
});

// Skeleton for stat cards
export const StatCardSkeleton = memo(function StatCardSkeleton() {
  return (
    <div className="bg-[#1a1d26] rounded-xl p-6 border border-[#2a2f3a]">
      <Skeleton className="h-3 w-24 mb-4" />
      <Skeleton className="h-10 w-20 mb-2" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
});

// Skeleton for metric cards
export const MetricCardSkeleton = memo(function MetricCardSkeleton() {
  return (
    <div className="bg-[#1a1d26] rounded-xl p-6 border border-[#2a2f3a] border-l-4 border-l-[#272a31]">
      <div className="flex justify-between items-start mb-4">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-8 w-8" variant="circle" />
      </div>
      <Skeleton className="h-10 w-24 mb-2" />
      <Skeleton className="h-3 w-36" />
    </div>
  );
});

// Skeleton for threat cards
export const ThreatCardSkeleton = memo(function ThreatCardSkeleton() {
  return (
    <div className="bg-[#1a1d26] rounded-xl p-4 border border-[#2a2f3a]">
      <div className="flex justify-between items-start mb-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-16 rounded" />
      </div>
      <Skeleton className="h-3 w-40 mb-2" />
      <Skeleton className="h-3 w-28" />
    </div>
  );
});

// Skeleton for event log items
export const EventLogSkeleton = memo(function EventLogSkeleton() {
  return (
    <div className="py-3">
      <Skeleton className="h-4 w-24 mb-2" />
      <Skeleton className="h-3 w-full mb-1" />
      <Skeleton className="h-3 w-3/4" />
    </div>
  );
});

// Skeleton for fuel bar
export const FuelBarSkeleton = memo(function FuelBarSkeleton() {
  return (
    <div className="flex items-center gap-3">
      <Skeleton className="w-2 h-2" variant="circle" />
      <div className="flex-1">
        <div className="flex justify-between mb-1">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-10" />
        </div>
        <Skeleton className="h-1.5 w-full rounded-full" />
      </div>
    </div>
  );
});

// Full page loading skeleton
export const PageSkeleton = memo(function PageSkeleton() {
  return (
    <div className="min-h-screen bg-[#10131a] pt-24 pb-12 px-8">
      <div className="max-w-[1440px] mx-auto">
        {/* Header skeleton */}
        <div className="mb-8">
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-10 w-64" />
        </div>
        
        {/* Stats grid skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        
        {/* Main content skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <ThreatCardSkeleton key={i} />
            ))}
          </div>
          <div className="lg:col-span-2">
            <Skeleton className="h-[400px] w-full" variant="card" />
          </div>
        </div>
      </div>
    </div>
  );
});

// Mission Control skeleton
export const MissionControlSkeleton = memo(function MissionControlSkeleton() {
  return (
    <div className="min-h-screen bg-[#10131a] pt-24 pb-12 px-8">
      <div className="max-w-[1440px] mx-auto">
        {/* Status strip skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-[#1a1d26] p-3 rounded-lg border border-[#2a2f3a]">
              <Skeleton className="h-3 w-20 mb-2" />
              <Skeleton className="h-6 w-12" />
            </div>
          ))}
        </div>

        {/* Main grid skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left column */}
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a]">
              <Skeleton className="h-4 w-28 mb-4" />
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <ThreatCardSkeleton key={i} />
                ))}
              </div>
            </div>
          </div>

          {/* Center column */}
          <div className="lg:col-span-6 space-y-6">
            <Skeleton className="h-[400px] w-full" variant="card" />
            <Skeleton className="h-32 w-full" variant="card" />
          </div>

          {/* Right column */}
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a]">
              <Skeleton className="h-4 w-32 mb-4" />
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <FuelBarSkeleton key={i} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default {
  Skeleton,
  StatCardSkeleton,
  MetricCardSkeleton,
  ThreatCardSkeleton,
  EventLogSkeleton,
  FuelBarSkeleton,
  PageSkeleton,
  MissionControlSkeleton,
};
