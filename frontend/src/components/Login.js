import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../AuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [cargando, setCargando] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async e => {
    e.preventDefault();
    setCargando(true);
    try {
      const { data } = await axios.post('/api/usuarios/login', form);
      login(data.token, data.usuario);
      toast.success(`Bienvenido, ${data.usuario.nombre}`);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.mensaje || 'Error al iniciar sesión');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.titulo}>🏗️ Constructora</h1>
        <h2 style={styles.subtitulo}>Iniciar Sesión</h2>
        <form onSubmit={handleSubmit}>
          <div style={styles.campo}>
            <label style={styles.label}>Email</label>
            <input
              type="email" name="email" value={form.email}
              onChange={handleChange} required style={styles.input}
              placeholder="usuario@constructora.com"
            />
          </div>
          <div style={styles.campo}>
            <label style={styles.label}>Contraseña</label>
            <input
              type="password" name="password" value={form.password}
              onChange={handleChange} required style={styles.input}
              placeholder="••••••••"
            />
          </div>
          <button type="submit" disabled={cargando} style={styles.boton}>
            {cargando ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <p style={styles.hint}>
          Demo: admin@constructora.com / Admin123!
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' },
  card: { background: '#fff', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', width: '360px' },
  titulo: { textAlign: 'center', color: '#1a1a2e', marginBottom: '4px', fontSize: '28px' },
  subtitulo: { textAlign: 'center', color: '#666', marginBottom: '24px', fontWeight: 'normal', fontSize: '16px' },
  campo: { marginBottom: '16px' },
  label: { display: 'block', marginBottom: '6px', color: '#333', fontWeight: '600', fontSize: '14px' },
  input: { width: '100%', padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  boton: { width: '100%', padding: '12px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: '600', cursor: 'pointer', marginTop: '8px' },
  hint: { textAlign: 'center', color: '#999', fontSize: '12px', marginTop: '16px' }
};
