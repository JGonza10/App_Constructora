import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const PortalAuthContext = createContext(null);

export function PortalAuthProvider({ children }) {
  const [cliente, setCliente] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('portal_token');
    const c = localStorage.getItem('portal_cliente');
    if (token && c) {
      setCliente(JSON.parse(c));
    }
    setCargando(false);
  }, []);

  const login = (token, clienteData) => {
    localStorage.setItem('portal_token', token);
    localStorage.setItem('portal_cliente', JSON.stringify(clienteData));
    setCliente(clienteData);
  };

  const logout = () => {
    localStorage.removeItem('portal_token');
    localStorage.removeItem('portal_cliente');
    setCliente(null);
  };

  // Cliente axios independiente del sistema interno (headers propios)
  const portalAxios = axios.create({
    baseURL: process.env.REACT_APP_API_URL || ''
  });
  portalAxios.interceptors.request.use(config => {
    const token = localStorage.getItem('portal_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  return (
    <PortalAuthContext.Provider value={{ cliente, login, logout, cargando, portalAxios }}>
      {children}
    </PortalAuthContext.Provider>
  );
}

export function usePortalAuth() {
  return useContext(PortalAuthContext);
}
