import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../AuthContext';

const COLORES_ESTADO = {
  borrador: '#6b7280',
  revision: '#d97706',
  aprobado: '#16a34a',
  rechazado: '#dc2626'
};

export default function Presupuestos() {
  const { usuario } = useAuth();
  const [presupuestos, setPresupuestos] = useState([]);
  const [obras, setObras] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [editando, setEditando] = useState(null);
  const [form, setForm] = useState({ titulo: '', descripcion: '', monto: '', obra_id: '' });
  const [modalEstado, setModalEstado] = useState(null);
  const [comentario, setComentario] = useState('');

  const cargar = async () => {
    try {
      const [pRes, oRes] = await Promise.all([
        axios.get('/api/presupuestos'),
        axios.get('/api/obras')
      ]);
      setPresupuestos(pRes.data);
      setObras(oRes.data);
    } catch {
      toast.error('Error al cargar presupuestos');
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => { cargar(); }, []);

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      if (editando) {
        await axios.put(`/api/presupuestos/${editando}`, form);
        toast.success('Presupuesto actualizado');
      } else {
        await axios.post('/api/presupuestos', form);
        toast.success('Presupuesto creado');
      }
      setForm({ titulo: '', descripcion: '', monto: '', obra_id: '' });
      setMostrarForm(false);
      setEditando(null);
      cargar();
    } catch (err) {
      toast.error(err.response?.data?.mensaje || 'Error');
    }
  };

  const iniciarEdicion = (p) => {
    setForm({ titulo: p.titulo, descripcion: p.descripcion || '', monto: p.monto, obra_id: p.obra_id || '' });
    setEditando(p.id);
    setMostrarForm(true);
  };

  const cambiarEstado = async (estado) => {
    try {
      await axios.patch(`/api/presupuestos/${modalEstado.id}/estado`, { estado, comentario_revision: comentario });
      toast.success(`Estado cambiado a: ${estado}`);
      setModalEstado(null);
      setComentario('');
      cargar();
    } catch (err) {
      toast.error(err.response?.data?.mensaje || 'Error al cambiar estado');
    }
  };

  const accionesDisponibles = (p) => {
    if (usuario.rol === 'empleado' && p.estado === 'borrador') return ['revision'];
    if ((usuario.rol === 'supervisor' || usuario.rol === 'admin') && p.estado === 'revision') return ['aprobado', 'rechazado'];
    if (usuario.rol === 'admin' && p.estado === 'borrador') return ['revision'];
    return [];
  };

  if (cargando) return <p>Cargando...</p>;

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.titulo}>📋 Presupuestos</h2>
        <button onClick={() => { setMostrarForm(!mostrarForm); setEditando(null); setForm({ titulo: '', descripcion: '', monto: '', obra_id: '' }); }} style={styles.btnPrimario}>
          {mostrarForm ? '✕ Cancelar' : '+ Nuevo'}
        </button>
      </div>

      {/* Formulario crear/editar */}
      {mostrarForm && (
        <div style={styles.card}>
          <h3>{editando ? 'Editar Presupuesto' : 'Nuevo Presupuesto'}</h3>
          <form onSubmit={handleSubmit}>
            <select style={styles.input} value={form.obra_id}
              onChange={e => setForm({ ...form, obra_id: e.target.value })} required>
              <option value="">Selecciona una obra *</option>
              {obras.map(o => <option key={o.id} value={o.id}>{o.nombre}</option>)}
            </select>
            <input style={styles.input} placeholder="Título *" value={form.titulo}
              onChange={e => setForm({ ...form, titulo: e.target.value })} required />
            <textarea style={{ ...styles.input, height: '80px' }} placeholder="Descripción"
              value={form.descripcion} onChange={e => setForm({ ...form, descripcion: e.target.value })} />
            <input style={styles.input} type="number" placeholder="Monto ($) *" value={form.monto}
              onChange={e => setForm({ ...form, monto: e.target.value })} required min="1" step="0.01" />
            <button type="submit" style={styles.btnPrimario}>
              {editando ? 'Guardar Cambios' : 'Crear Presupuesto'}
            </button>
          </form>
        </div>
      )}

      {/* Tabla */}
      <div style={styles.card}>
        {presupuestos.length === 0 ? (
          <p style={{ color: '#999', textAlign: 'center' }}>No hay presupuestos aún.</p>
        ) : (
          <table style={styles.tabla}>
            <thead>
              <tr style={styles.thead}>
                <th>Título</th>
                <th>Obra</th>
                <th>Monto</th>
                <th>Estado</th>
                <th>Creado por</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {presupuestos.map(p => (
                <tr key={p.id} style={styles.fila}>
                  <td>
                    <strong>{p.titulo}</strong>
                    {p.descripcion && <p style={{ fontSize: '12px', color: '#666', margin: '2px 0 0' }}>{p.descripcion}</p>}
                  </td>
                  <td style={{ fontSize: '13px', color: '#666' }}>{p.obra_nombre || '—'}</td>
                  <td>${Number(p.monto).toLocaleString('es-MX')}</td>
                  <td>
                    <span style={{ ...styles.badge, background: COLORES_ESTADO[p.estado] }}>
                      {p.estado}
                    </span>
                  </td>
                  <td>{p.creador}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {/* Editar: solo creador en borrador */}
                      {p.estado === 'borrador' && (usuario.rol === 'admin' || p.creado_por === usuario.id) && (
                        <button onClick={() => iniciarEdicion(p)} style={styles.btnSec}>✏️ Editar</button>
                      )}
                      {/* Cambio de estado */}
                      {accionesDisponibles(p).length > 0 && (
                        <button onClick={() => setModalEstado(p)} style={styles.btnSec}>🔄 Estado</button>
                      )}
                    </div>
                    {p.comentario_revision && (
                      <p style={{ fontSize: '11px', color: '#888', marginTop: '4px' }}>
                        💬 {p.comentario_revision}
                      </p>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal cambio de estado */}
      {modalEstado && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h3>Cambiar Estado</h3>
            <p><strong>{modalEstado.titulo}</strong></p>
            <p>Estado actual: <span style={{ color: COLORES_ESTADO[modalEstado.estado] }}>{modalEstado.estado}</span></p>
            <textarea style={{ ...styles.input, height: '80px', marginTop: '12px' }}
              placeholder="Comentario (opcional)" value={comentario}
              onChange={e => setComentario(e.target.value)} />
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              {accionesDisponibles(modalEstado).map(accion => (
                <button key={accion} onClick={() => cambiarEstado(accion)}
                  style={{ ...styles.btnPrimario, background: COLORES_ESTADO[accion] }}>
                  → {accion}
                </button>
              ))}
              <button onClick={() => setModalEstado(null)} style={styles.btnSec}>Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  titulo: { margin: 0, color: '#1a1a2e' },
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  input: { display: 'block', width: '100%', padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', marginBottom: '12px', boxSizing: 'border-box', resize: 'vertical' },
  btnPrimario: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  btnSec: { padding: '6px 12px', background: '#f3f4f6', color: '#333', border: '1px solid #ddd', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' },
  tabla: { width: '100%', borderCollapse: 'collapse' },
  thead: { background: '#f9fafb' },
  fila: { borderBottom: '1px solid #f0f0f0' },
  badge: { color: '#fff', padding: '3px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: '600' },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { background: '#fff', borderRadius: '12px', padding: '28px', width: '400px', maxWidth: '90%' }
};
