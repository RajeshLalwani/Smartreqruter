"use client";

import { useEffect, useState } from 'react';

export function useRecruitmentSocket() {
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/recruitment/?token=${token}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
    };

    ws.onopen = () => console.log("[NeuralLink] Connected");
    ws.onclose = () => console.log("[NeuralLink] Disconnected");

    return () => ws.close();
  }, []);

  return lastMessage;
}
