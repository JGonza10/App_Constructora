import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AuthProvider, useAuth } from './AuthContext';
import { PortalAuthProvider, usePortalAuth } from './PortalAuthContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Presupuestos from './components/Presupuestos';
import AlertasTiempoReal from './components/AlertasTiempoReal';
import PerfilUsuario from './components/PerfilUsuario';
import AdminPanel from './components/AdminPanel';
import TableroEjecutivo from './components/TableroEjecutivo';
import Obras from './components/Obras';
import ObraDetalle from './components/ObraDetalle';
import Clientes from './components/Clientes';
import Proveedores from './components/Proveedores';
import PortalLogin from './portal/PortalLogin';
import PortalObras from './portal/PortalObras';
import PortalObraDetalle from './portal/PortalObraDetalle';

// Ruta protegida: solo usuarios autenticados
function RutaPrivada({ children }) {
  const { usuario, cargando } = useAuth();
  if (cargando) return <div style={{ padding: '40px', textAlign: 'center' }}>Cargando...</div>;
  return usuario ? children : <Navigate to="/login" replace />;
}

// Ruta protegida por rol
function RutaRol({ children, roles }) {
  const { usuario } = useAuth();
  if (!roles.includes(usuario?.rol)) {
    return <div style={{ padding: '40px', textAlign: 'center', color: '#dc2626' }}>
      <h2>🚫 Acceso denegado</h2>
      <p>No tienes permisos para ver esta sección.</p>
    </div>;
  }
  return children;
}

function IndiceDashboard() {
  const { usuario } = useAuth();
  const destino = (usuario.rol === 'admin' || usuario.rol === 'supervisor') ? 'tablero' : 'obras';
  return <Navigate to={destino} replace />;
}

// Ruta protegida exclusiva del portal del cliente
function RutaPortalPrivada({ children }) {
  const { cliente, cargando } = usePortalAuth();
  if (cargando) return <div style={{ padding: '40px', textAlign: 'center' }}>Cargando...</div>;
  return cliente ? children : <Navigate to="/portal/login" replace />;
}

function App() {
  return (
    <AuthProvider>
      <PortalAuthProvider>
        <BrowserRouter>
          <ToastContainer position="top-right" autoClose={3000} />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            <Route path="/dashboard" element={
              <RutaPrivada><Dashboard /></RutaPrivada>
            }>
              <Route index element={<IndiceDashboard />} />
              <Route path="tablero" element={
                <RutaRol roles={['admin', 'supervisor']}>
                  <TableroEjecutivo />
                </RutaRol>
              } />
              <Route path="obras" element={<Obras />} />
              <Route path="obras/:id" element={<ObraDetalle />} />
              <Route path="clientes" element={<Clientes />} />
              <Route path="proveedores" element={
                <RutaRol roles={['admin', 'supervisor']}>
                  <Proveedores />
                </RutaRol>
              } />
              <Route path="presupuestos" element={<Presupuestos />} />
              <Route path="alertas" element={<AlertasTiempoReal />} />
              <Route path="perfil" element={<PerfilUsuario />} />
              <Route path="admin" element={
                <RutaRol roles={['admin', 'supervisor']}>
                  <AdminPanel />
                </RutaRol>
              } />
            </Route>

            {/* Portal del cliente — sistema independiente, solo lectura */}
            <Route path="/portal/login" element={<PortalLogin />} />
            <Route path="/portal/obras" element={
              <RutaPortalPrivada><PortalObras /></RutaPortalPrivada>
            } />
            <Route path="/portal/obras/:id" element={
              <RutaPortalPrivada><PortalObraDetalle /></RutaPortalPrivada>
            } />

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </PortalAuthProvider>
    </AuthProvider>
  );
}

export default App;
