import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// En producción, define REACT_APP_API_URL (ej: https://tu-backend.up.railway.app)
// En desarrollo local, usa el proxy configurado en package.json y deja esto vacío.
axios.defaults.baseURL = process.env.REACT_APP_API_URL || '';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const u = localStorage.getItem('usuario');
    if (token && u) {
      setUsuario(JSON.parse(u));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setCargando(false);
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('usuario', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    setUsuario(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    delete axios.defaults.headers.common['Authorization'];
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, login, logout, cargando }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
