import { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../AuthContext';

const COLORES_ROL = { admin: '#dc2626', supervisor: '#d97706', empleado: '#2563eb' };

export default function PerfilUsuario() {
  const { usuario } = useAuth();
  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    axios.get('/api/usuarios/perfil')
      .then(({ data }) => setPerfil(data))
      .catch(() => {})
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando perfil...</p>;
  if (!perfil) return <p>No se pudo cargar el perfil.</p>;

  return (
    <div>
      <h2 style={{ color: '#1a1a2e', marginBottom: '20px' }}>👤 Mi Perfil</h2>
      <div style={styles.card}>
        <div style={styles.avatar}>
          {perfil.nombre.charAt(0).toUpperCase()}
        </div>
        <h2 style={{ margin: '12px 0 4px' }}>{perfil.nombre}</h2>
        <span style={{ ...styles.badge, background: COLORES_ROL[perfil.rol] }}>
          {perfil.rol.toUpperCase()}
        </span>
        <div style={styles.info}>
          <div style={styles.fila}>
            <span style={styles.etiqueta}>Email</span>
            <span>{perfil.email}</span>
          </div>
          <div style={styles.fila}>
            <span style={styles.etiqueta}>Rol</span>
            <span style={{ textTransform: 'capitalize' }}>{perfil.rol}</span>
          </div>
          <div style={styles.fila}>
            <span style={styles.etiqueta}>Miembro desde</span>
            <span>{new Date(perfil.creado_en).toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  card: { background: '#fff', borderRadius: '12px', padding: '40px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', maxWidth: '500px', textAlign: 'center' },
  avatar: { width: '80px', height: '80px', borderRadius: '50%', background: '#2563eb', color: '#fff', fontSize: '36px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto' },
  badge: { color: '#fff', padding: '4px 14px', borderRadius: '20px', fontSize: '13px', fontWeight: 'bold' },
  info: { marginTop: '28px', textAlign: 'left' },
  fila: { display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #f0f0f0', fontSize: '15px' },
  etiqueta: { color: '#888', fontWeight: '600' }
};
