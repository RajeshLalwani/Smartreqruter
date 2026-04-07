"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlowButton } from '@/components/ui/GlowButton';
import api from '@/lib/api';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/token/', { username: email, password });
      localStorage.setItem('access_token', res.data.access);
      localStorage.setItem('refresh_token', res.data.refresh);
      router.push('/dashboard');
    } catch (err) {
      alert("Invalid credentials. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center p-4">
      <GlassCard className="w-full max-w-md border-cyan-500/20 shadow-[0_0_50px_rgba(6,182,212,0.1)]">
        <h1 className="mb-6 text-2xl font-bold text-center tracking-tight text-white">SmartRecruit <span className="text-cyan-400">Portal</span></h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email / Username</label>
            <input 
              type="text" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg bg-white/5 border border-white/10 p-2.5 text-white focus:border-cyan-500/50 outline-none transition-all"
              placeholder="neo@matrix.ai"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg bg-white/5 border border-white/10 p-2.5 text-white focus:border-cyan-500/50 outline-none transition-all"
              placeholder="••••••••"
              required
            />
          </div>
          <GlowButton type="submit" className="w-full mt-4" disabled={loading}>
            {loading ? "Authenticating..." : "Synchronize Profile"}
          </GlowButton>
        </form>
      </GlassCard>
    </div>
  );
}
