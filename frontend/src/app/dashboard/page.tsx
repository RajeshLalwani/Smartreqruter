"use client";

import React from 'react';
import useSWR from 'swr';
import api from '@/lib/api';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlowButton } from '@/components/ui/GlowButton';
import { ThunderSpinner } from '@/components/ui/ThunderSpinner';
import { Briefcase, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR('/v1/dashboard/', fetcher);

  if (isLoading) return (
    <div className="flex h-screen items-center justify-center">
      <ThunderSpinner className="scale-150" />
    </div>
  );

  if (error) return <div className="p-10 text-rose-500">Neural Sync Failed. Please login again.</div>;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Candidate <span className="text-cyan-400">Matrix</span></h1>
          <p className="text-slate-400">Welcome back, {data?.profile?.full_name}</p>
        </div>
        <GlowButton variant="secondary" onClick={() => { localStorage.clear(); window.location.href='/login'; }}>
          Logout
        </GlowButton>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="border-cyan-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-cyan-500/20 text-cyan-400"><Briefcase size={24} /></div>
            <div>
              <div className="text-2xl font-bold">{data?.applications?.length || 0}</div>
              <div className="text-sm text-slate-400">Active Applications</div>
            </div>
          </div>
        </GlassCard>

        <GlassCard className="border-purple-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-purple-500/20 text-purple-400"><Clock size={24} /></div>
            <div>
              <div className="text-2xl font-bold">{data?.interviews?.length || 0}</div>
              <div className="text-sm text-slate-400">Upcoming Interviews</div>
            </div>
          </div>
        </GlassCard>

        <GlassCard className="border-emerald-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-emerald-500/20 text-emerald-400"><CheckCircle size={24} /></div>
            <div>
              <div className="text-2xl font-bold">85%</div>
              <div className="text-sm text-slate-400">Match Accuracy</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <h2 className="text-xl font-semibold mt-10 mb-4 flex items-center gap-2">
        <Clock className="text-cyan-400" /> Application Timeline
      </h2>
      
      <div className="space-y-4">
        {data?.applications?.map((app: any) => (
          <GlassCard key={app.id} className="hover:bg-white/10 transition-colors">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium text-white">{app.job.title}</h3>
                <p className="text-sm text-slate-400">Applied on {new Date(app.applied_at).toLocaleDateString()}</p>
              </div>
              <div className={cn(
                "px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border",
                app.status.includes('PASSED') ? "bg-emerald-500/10 border-emerald-500 text-emerald-400" :
                app.status.includes('FAILED') ? "bg-rose-500/10 border-rose-500 text-rose-400" :
                "bg-cyan-500/10 border-cyan-500 text-cyan-400"
              )}>
                {app.status.replace(/_/g, ' ')}
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
