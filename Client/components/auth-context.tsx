'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  setUser: () => {},
  isLoading: true,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check localStorage for user data initially, then verify with backend
    const storedUser = localStorage.getItem('santibet_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse user from local storage', e);
      }
    }
    
    // Try fetching live user from GET /v1/users/me
    const token = localStorage.getItem('santibet_token');
    fetch('/v1/users/me', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Unauthorized');
      })
      .then(userData => {
        handleSetUser(userData);
      })
      .catch(() => {
        handleSetUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleSetUser = (newUser: User | null) => {
    setUser(newUser);
    if (newUser) {
      localStorage.setItem('santibet_user', JSON.stringify(newUser));
    } else {
      localStorage.removeItem('santibet_user');
      localStorage.removeItem('santibet_token');
    }
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    if (user) {
      import('@/lib/api').then(api => {
        api.fetchWsTicket().then(data => {
          if (data && data.ticket) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // Connect to our proxied endpoint (same host/port)
            ws = new WebSocket(`${protocol}//${window.location.host}/v1/ws/user?ticket=${data.ticket}`);
            ws.onmessage = (event) => {
              try {
                const msg = JSON.parse(event.data);
                console.log('WS User Message:', msg);
              } catch (e) {
                // Ignore parse errors
              }
            };
          }
        }).catch(console.error);
      });
    }
    return () => {
      if (ws) ws.close();
    };
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, setUser: handleSetUser, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
