import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import { toast } from 'react-toastify';
import { useAuth } from '../AuthContext';

const ICONOS = { info: 'ℹ️', warning: '⚠️', success: '✅', error: '❌' };
const COLORES = { info: '#3b82f6', warning: '#f59e0b', success: '#10b981', error: '#ef4444' };

let socket;

export default function AlertasTiempoReal() {
  const { usuario } = useAuth();
  const [alertas, setAlertas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [nuevaAlerta, setNuevaAlerta] = useState({ mensaje: '', tipo: 'info' });

  useEffect(() => {
    // Cargar alertas históricas
    const cargar = async () => {
      try {
        const endpoint = (usuario.rol === 'admin' || usuario.rol === 'supervisor')
          ? '/api/admin/alertas'
          : null;
        if (endpoint) {
          const { data } = await axios.get(endpoint);
          setAlertas(data);
        }
      } catch { /* sin alertas */ } finally {
        setCargando(false);
      }
    };
    cargar();

    // Conectar Socket.io
    socket = io(process.env.REACT_APP_API_URL || 'http://localhost:3001');
    socket.emit('unirse_sala', usuario.rol);

    socket.on('alerta_recibida', (data) => {
      setAlertas(prev => [data, ...prev]);
      toast.info(`🔔 ${data.mensaje}`);
    });

    socket.on('presupuesto_cambio', (data) => {
      toast.success(`📋 ${data.mensaje}`);
    });

    return () => socket.disconnect();
  }, [usuario]);

  const marcarLeida = async (id) => {
    try {
      await axios.patch(`/api/admin/alertas/${id}/leer`);
      setAlertas(prev => prev.map(a => a.id === id ? { ...a, leida: true } : a));
    } catch { toast.error('Error al marcar alerta'); }
  };

  const enviarAlerta = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/admin/alertas', nuevaAlerta);
      socket.emit('nueva_alerta', { ...nuevaAlerta, creado_en: new Date() });
      toast.success('Alerta enviada');
      setNuevaAlerta({ mensaje: '', tipo: 'info' });
    } catch (err) {
      toast.error(err.response?.data?.mensaje || 'Error');
    }
  };

  return (
    <div>
      <h2 style={{ color: '#1a1a2e', marginBottom: '20px' }}>🔔 Alertas en Tiempo Real</h2>

      {/* Formulario solo para admin y supervisor */}
      {(usuario.rol === 'admin' || usuario.rol === 'supervisor') && (
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Enviar nueva alerta</h3>
          <form onSubmit={enviarAlerta} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <input
              style={{ ...styles.input, flex: 1, minWidth: '200px' }}
              placeholder="Mensaje de alerta..."
              value={nuevaAlerta.mensaje}
              onChange={e => setNuevaAlerta({ ...nuevaAlerta, mensaje: e.target.value })}
              required
            />
            <select
              style={styles.input}
              value={nuevaAlerta.tipo}
              onChange={e => setNuevaAlerta({ ...nuevaAlerta, tipo: e.target.value })}
            >
              <option value="info">ℹ️ Info</option>
              <option value="success">✅ Éxito</option>
              <option value="warning">⚠️ Advertencia</option>
              <option value="error">❌ Error</option>
            </select>
            <button type="submit" style={styles.btn}>📢 Enviar</button>
          </form>
        </div>
      )}

      {/* Lista de alertas */}
      <div style={styles.card}>
        <h3 style={{ marginTop: 0 }}>Historial de alertas</h3>
        {cargando ? <p>Cargando...</p> : alertas.length === 0 ? (
          <p style={{ color: '#999', textAlign: 'center' }}>No hay alertas.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alertas.map((a, i) => (
              <div key={a.id || i} style={{
                ...styles.alerta,
                borderLeft: `4px solid ${COLORES[a.tipo] || '#3b82f6'}`,
                opacity: a.leida ? 0.6 : 1
              }}>
                <span style={{ fontSize: '20px' }}>{ICONOS[a.tipo] || 'ℹ️'}</span>
                <div style={{ flex: 1 }}>
                  <p style={{ margin: 0, fontWeight: a.leida ? 'normal' : '600' }}>{a.mensaje}</p>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>
                    {a.usuario_nombre && `De: ${a.usuario_nombre} · `}
                    {a.creado_en && new Date(a.creado_en).toLocaleString('es-MX')}
                  </p>
                </div>
                {!a.leida && a.id && (
                  <button onClick={() => marcarLeida(a.id)} style={styles.btnSec}>✓ Leído</button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px' },
  btn: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  btnSec: { padding: '6px 10px', background: '#f3f4f6', border: '1px solid #ddd', borderRadius: '6px', cursor: 'pointer', fontSize: '13px', whiteSpace: 'nowrap' },
  alerta: { display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 16px', background: '#f9fafb', borderRadius: '8px' }
};
