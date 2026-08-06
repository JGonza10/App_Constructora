import React, { useState } from 'react';
import axios from 'axios';
import { usePortalAuth } from '../PortalAuthContext';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

export default function PortalLogin() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [cargando, setCargando] = useState(false);
  const { login } = usePortalAuth();
  const navigate = useNavigate();

  const handleSubmit = async e => {
    e.preventDefault();
    setCargando(true);
    try {
      const { data } = await axios.post('/api/portal/login', form);
      login(data.token, data.cliente);
      toast.success(`Bienvenido, ${data.cliente.nombre}`);
      navigate('/portal/obras');
    } catch (err) {
      toast.error(err.response?.data?.mensaje || 'Error al iniciar sesión');
    } finally {
      setCargando(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.titulo}>🏗️ Portal del Cliente</h1>
        <p style={styles.subtitulo}>Consulta el avance de tu obra</p>
        <form onSubmit={handleSubmit}>
          <input
            type="email" placeholder="Email" required style={styles.input}
            value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
          />
          <input
            type="password" placeholder="Contraseña" required style={styles.input}
            value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
          />
          <button type="submit" disabled={cargando} style={styles.boton}>
            {cargando ? 'Entrando...' : 'Acceder a mi obra'}
          </button>
        </form>
        <p style={styles.hint}>¿No tienes acceso? Solicítalo con tu arquitecto.</p>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5' },
  card: { background: '#fff', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', width: '360px' },
  titulo: { textAlign: 'center', color: '#1a1a2e', marginBottom: '4px', fontSize: '24px' },
  subtitulo: { textAlign: 'center', color: '#666', marginBottom: '24px', fontSize: '14px' },
  input: { width: '100%', padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box', marginBottom: '12px' },
  boton: { width: '100%', padding: '12px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: '8px', fontSize: '16px', fontWeight: '600', cursor: 'pointer' },
  hint: { textAlign: 'center', color: '#999', fontSize: '12px', marginTop: '16px' }
};
