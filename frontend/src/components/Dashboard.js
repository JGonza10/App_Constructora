import React from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { toast } from 'react-toastify';

const coloresRol = {
  admin: '#dc2626',
  supervisor: '#d97706',
  empleado: '#2563eb'
};

export default function Dashboard() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.info('Sesión cerrada');
    navigate('/login');
  };

  const navLinks = [
    { to: '/dashboard/tablero', label: '📊 Tablero', roles: ['admin', 'supervisor'] },
    { to: '/dashboard/obras', label: '🏗️ Obras', roles: ['admin', 'supervisor', 'empleado'] },
    { to: '/dashboard/presupuestos', label: '📋 Presupuestos', roles: ['admin', 'supervisor', 'empleado'] },
    { to: '/dashboard/clientes', label: '👥 Clientes', roles: ['admin', 'supervisor', 'empleado'] },
    { to: '/dashboard/proveedores', label: '🚚 Proveedores', roles: ['admin', 'supervisor'] },
    { to: '/dashboard/alertas', label: '🔔 Alertas', roles: ['admin', 'supervisor', 'empleado'] },
    { to: '/dashboard/perfil', label: '👤 Mi Perfil', roles: ['admin', 'supervisor', 'empleado'] },
    { to: '/dashboard/admin', label: '⚙️ Administración', roles: ['admin', 'supervisor'] },
  ];

  return (
    <div style={styles.layout}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.logo}>🏗️ Constructora</div>
        <div style={{ ...styles.badge, background: coloresRol[usuario?.rol] }}>
          {usuario?.rol?.toUpperCase()}
        </div>
        <p style={styles.nombreUsuario}>{usuario?.nombre}</p>
        <nav style={styles.nav}>
          {navLinks
            .filter(l => l.roles.includes(usuario?.rol))
            .map(l => (
              <Link key={l.to} to={l.to} style={styles.navLink}>{l.label}</Link>
            ))
          }
        </nav>
        <button onClick={handleLogout} style={styles.btnLogout}>🚪 Cerrar Sesión</button>
      </aside>

      {/* Contenido */}
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}

const styles = {
  layout: { display: 'flex', minHeight: '100vh', fontFamily: 'sans-serif' },
  sidebar: { width: '220px', background: '#1a1a2e', color: '#fff', display: 'flex', flexDirection: 'column', padding: '24px 16px', position: 'fixed', height: '100vh' },
  logo: { fontSize: '20px', fontWeight: 'bold', marginBottom: '12px', textAlign: 'center' },
  badge: { color: '#fff', padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 'bold', textAlign: 'center', marginBottom: '6px' },
  nombreUsuario: { textAlign: 'center', fontSize: '13px', color: '#aaa', marginBottom: '24px' },
  nav: { display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 },
  navLink: { color: '#ccc', textDecoration: 'none', padding: '10px 12px', borderRadius: '8px', fontSize: '14px', transition: 'background 0.2s' },
  main: { marginLeft: '220px', flex: 1, padding: '32px', background: '#f0f2f5' },
  btnLogout: { background: '#dc2626', color: '#fff', border: 'none', padding: '10px', borderRadius: '8px', cursor: 'pointer', marginTop: '16px' }
};
