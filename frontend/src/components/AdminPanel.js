import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [tab, setTab] = useState('estadisticas');
  const [cargando, setCargando] = useState(true);
  const [nuevoUsuario, setNuevoUsuario] = useState({ nombre: '', email: '', password: '', rol: 'empleado' });

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      const [statsRes, usersRes] = await Promise.all([
        axios.get('/api/admin/estadisticas'),
        axios.get('/api/usuarios')
      ]);
      setStats(statsRes.data);
      setUsuarios(usersRes.data);
    } catch { toast.error('Error al cargar datos de administración'); }
    finally { setCargando(false); }
  };

  const toggleEstadoUsuario = async (id, activo) => {
    try {
      await axios.put(`/api/usuarios/${id}/estado`, { activo: !activo });
      toast.success(`Usuario ${!activo ? 'activado' : 'desactivado'}`);
      cargarDatos();
    } catch { toast.error('Error al cambiar estado'); }
  };

  const crearUsuario = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/usuarios/registro', nuevoUsuario);
      toast.success('Usuario creado');
      setNuevoUsuario({ nombre: '', email: '', password: '', rol: 'empleado' });
      cargarDatos();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const exportar = (formato) => {
    const token = localStorage.getItem('token');
    const base = process.env.REACT_APP_API_URL || '';
    window.open(`${base}/api/admin/exportar/${formato}?token=${token}`, '_blank');
    // Nota: ajustar en producción para pasar token en header
  };

  const chartData = stats ? {
    labels: stats.porEstado?.map(e => e.estado) || [],
    datasets: [{
      label: 'Presupuestos por estado',
      data: stats.porEstado?.map(e => e.cantidad) || [],
      backgroundColor: ['#6b7280', '#d97706', '#16a34a', '#dc2626']
    }]
  } : null;

  if (cargando) return <p>Cargando...</p>;

  return (
    <div>
      <h2 style={{ color: '#1a1a2e', marginBottom: '20px' }}>⚙️ Panel de Administración</h2>

      {/* Tabs */}
      <div style={styles.tabs}>
        {['estadisticas', 'usuarios', 'exportar'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ ...styles.tab, ...(tab === t ? styles.tabActivo : {}) }}>
            {t === 'estadisticas' ? '📊 Estadísticas' : t === 'usuarios' ? '👥 Usuarios' : '📤 Exportar'}
          </button>
        ))}
      </div>

      {/* Estadísticas */}
      {tab === 'estadisticas' && stats && (
        <div>
          <div style={styles.metricas}>
            <div style={styles.metrica}>
              <div style={styles.metricaNum}>{stats.totalPresupuestos[0]?.total || 0}</div>
              <div style={styles.metricaLabel}>Total Presupuestos</div>
            </div>
            <div style={styles.metrica}>
              <div style={styles.metricaNum}>${Number(stats.montoTotal[0]?.total || 0).toLocaleString('es-MX')}</div>
              <div style={styles.metricaLabel}>Monto Aprobado</div>
            </div>
            <div style={styles.metrica}>
              <div style={styles.metricaNum}>{stats.totalUsuarios[0]?.total || 0}</div>
              <div style={styles.metricaLabel}>Usuarios Activos</div>
            </div>
          </div>
          {chartData && (
            <div style={styles.card}>
              <Bar data={chartData} options={{ responsive: true, plugins: { legend: { display: false }, title: { display: true, text: 'Presupuestos por Estado' } } }} />
            </div>
          )}
        </div>
      )}

      {/* Gestión de usuarios */}
      {tab === 'usuarios' && (
        <div>
          <div style={styles.card}>
            <h3 style={{ marginTop: 0 }}>Crear nuevo usuario</h3>
            <form onSubmit={crearUsuario} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <input style={styles.input} placeholder="Nombre completo" value={nuevoUsuario.nombre}
                onChange={e => setNuevoUsuario({ ...nuevoUsuario, nombre: e.target.value })} required />
              <input style={styles.input} type="email" placeholder="Email" value={nuevoUsuario.email}
                onChange={e => setNuevoUsuario({ ...nuevoUsuario, email: e.target.value })} required />
              <input style={styles.input} type="password" placeholder="Contraseña" value={nuevoUsuario.password}
                onChange={e => setNuevoUsuario({ ...nuevoUsuario, password: e.target.value })} required />
              <select style={styles.input} value={nuevoUsuario.rol}
                onChange={e => setNuevoUsuario({ ...nuevoUsuario, rol: e.target.value })}>
                <option value="empleado">Empleado</option>
                <option value="supervisor">Supervisor</option>
                <option value="admin">Admin</option>
              </select>
              <button type="submit" style={{ ...styles.btn, gridColumn: 'span 2' }}>+ Crear Usuario</button>
            </form>
          </div>

          <div style={styles.card}>
            <h3 style={{ marginTop: 0 }}>Usuarios del sistema</h3>
            <table style={styles.tabla}>
              <thead><tr style={styles.thead}><th>Nombre</th><th>Email</th><th>Rol</th><th>Estado</th><th>Acción</th></tr></thead>
              <tbody>
                {usuarios.map(u => (
                  <tr key={u.id} style={styles.fila}>
                    <td>{u.nombre}</td>
                    <td>{u.email}</td>
                    <td style={{ textTransform: 'capitalize' }}>{u.rol}</td>
                    <td><span style={{ color: u.activo ? '#16a34a' : '#dc2626', fontWeight: '600' }}>{u.activo ? 'Activo' : 'Inactivo'}</span></td>
                    <td>
                      <button onClick={() => toggleEstadoUsuario(u.id, u.activo)} style={styles.btnSec}>
                        {u.activo ? '🔴 Desactivar' : '🟢 Activar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Exportar */}
      {tab === 'exportar' && (
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Exportar Presupuestos</h3>
          <p style={{ color: '#666' }}>Descarga el listado completo de presupuestos en tu formato preferido.</p>
          <div style={{ display: 'flex', gap: '16px', marginTop: '20px' }}>
            <button onClick={() => exportar('excel')} style={{ ...styles.btn, background: '#16a34a' }}>
              📊 Exportar Excel
            </button>
            <button onClick={() => exportar('pdf')} style={{ ...styles.btn, background: '#dc2626' }}>
              📄 Exportar PDF
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  tabs: { display: 'flex', gap: '8px', marginBottom: '20px' },
  tab: { padding: '10px 20px', border: '1px solid #ddd', borderRadius: '8px', background: '#fff', cursor: 'pointer', fontSize: '14px' },
  tabActivo: { background: '#2563eb', color: '#fff', border: '1px solid #2563eb' },
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  metricas: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' },
  metrica: { background: '#fff', borderRadius: '12px', padding: '24px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  metricaNum: { fontSize: '32px', fontWeight: 'bold', color: '#2563eb' },
  metricaLabel: { color: '#888', marginTop: '4px', fontSize: '14px' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px' },
  btn: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  btnSec: { padding: '6px 12px', background: '#f3f4f6', border: '1px solid #ddd', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' },
  tabla: { width: '100%', borderCollapse: 'collapse' },
  thead: { background: '#f9fafb' },
  fila: { borderBottom: '1px solid #f0f0f0' }
};
