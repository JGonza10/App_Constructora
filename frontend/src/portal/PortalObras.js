import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { usePortalAuth } from '../PortalAuthContext';

const COLOR_ESTADO = {
  cotizacion: '#6b7280', activa: '#16a34a', pausada: '#d97706',
  terminada: '#2563eb', cancelada: '#dc2626'
};

export default function PortalObras() {
  const { cliente, logout, portalAxios } = usePortalAuth();
  const [obras, setObras] = useState([]);
  const [cargando, setCargando] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    portalAxios.get('/api/portal/obras')
      .then(({ data }) => setObras(data))
      .catch(() => toast.error('Error al cargar tus obras'))
      .finally(() => setCargando(false));
  }, []);

  const handleLogout = () => { logout(); navigate('/portal/login'); };

  if (cargando) return <p style={{ padding: '40px', textAlign: 'center' }}>Cargando...</p>;

  return (
    <div style={styles.layout}>
      <header style={styles.header}>
        <div>
          <h2 style={{ margin: 0 }}>🏗️ Portal del Cliente</h2>
          <p style={{ margin: '4px 0 0', color: '#666', fontSize: '14px' }}>Hola, {cliente.nombre}</p>
        </div>
        <button onClick={handleLogout} style={styles.btnSalir}>Cerrar sesión</button>
      </header>

      <div style={styles.contenido}>
        <h3 style={{ marginBottom: '16px' }}>Tus obras</h3>
        {obras.length === 0 ? (
          <p style={{ color: '#999' }}>Aún no tienes obras asignadas.</p>
        ) : (
          <div style={styles.grid}>
            {obras.map(o => (
              <div key={o.id} style={styles.card} onClick={() => navigate(`/portal/obras/${o.id}`)}>
                <span style={{ ...styles.badge, background: COLOR_ESTADO[o.estado] }}>{o.estado}</span>
                <h3 style={{ margin: '8px 0 4px' }}>{o.nombre}</h3>
                <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>📍 {o.direccion || 'Sin dirección'}</p>
                <div style={{ margin: '14px 0 6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#888' }}>
                    <span>Avance</span><span>{o.avance_porcentaje}%</span>
                  </div>
                  <div style={styles.barraFondo}><div style={{ ...styles.barraRelleno, width: `${o.avance_porcentaje}%` }} /></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  layout: { minHeight: '100vh', background: '#f0f2f5' },
  header: { background: '#fff', padding: '20px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' },
  btnSalir: { padding: '8px 16px', background: '#f3f4f6', border: '1px solid #ddd', borderRadius: '8px', cursor: 'pointer', fontSize: '13px' },
  contenido: { padding: '32px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' },
  card: { background: '#fff', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', cursor: 'pointer' },
  badge: { color: '#fff', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize' },
  barraFondo: { width: '100%', height: '8px', background: '#f0f0f0', borderRadius: '10px', overflow: 'hidden' },
  barraRelleno: { height: '100%', background: '#16a34a', borderRadius: '10px' }
};
