import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../AuthContext';

const COLOR_ESTADO_OC = { solicitada: '#6b7280', confirmada: '#d97706', entregada: '#16a34a', cancelada: '#dc2626' };

export default function Proveedores() {
  const { usuario } = useAuth();
  const [proveedores, setProveedores] = useState([]);
  const [ordenes, setOrdenes] = useState([]);
  const [obras, setObras] = useState([]);
  const [tab, setTab] = useState('proveedores');
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [formProv, setFormProv] = useState({ nombre: '', contacto: '', telefono: '', categoria: 'materiales' });
  const [formOC, setFormOC] = useState({ obra_id: '', proveedor_id: '', concepto: '', monto_estimado: '', fecha_pedido: '' });

  const puedeEditar = usuario.rol === 'admin' || usuario.rol === 'supervisor';

  const cargar = async () => {
    try {
      const [p, o, ob] = await Promise.all([
        axios.get('/api/proveedores'),
        axios.get('/api/proveedores/ordenes'),
        axios.get('/api/obras')
      ]);
      setProveedores(p.data); setOrdenes(o.data); setObras(ob.data);
    } catch { toast.error('Error al cargar datos'); }
    finally { setCargando(false); }
  };

  useEffect(() => { cargar(); }, []);

  const crearProveedor = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/proveedores', formProv);
      toast.success('Proveedor creado');
      setFormProv({ nombre: '', contacto: '', telefono: '', categoria: 'materiales' });
      setMostrarForm(false); cargar();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const crearOrden = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/proveedores/ordenes', formOC);
      toast.success('Orden de compra creada');
      setFormOC({ obra_id: '', proveedor_id: '', concepto: '', monto_estimado: '', fecha_pedido: '' });
      setMostrarForm(false); cargar();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const cambiarEstadoOC = async (id, estado) => {
    try {
      await axios.patch(`/api/proveedores/ordenes/${id}/estado`, { estado });
      toast.success('Orden actualizada');
      cargar();
    } catch { toast.error('Error al actualizar'); }
  };

  if (cargando) return <p>Cargando...</p>;

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.titulo}>🚚 Proveedores</h2>
        {puedeEditar && (
          <button onClick={() => setMostrarForm(!mostrarForm)} style={styles.btnPrimario}>
            {mostrarForm ? '✕ Cancelar' : tab === 'proveedores' ? '+ Nuevo Proveedor' : '+ Nueva Orden'}
          </button>
        )}
      </div>

      <div style={styles.tabs}>
        <button onClick={() => { setTab('proveedores'); setMostrarForm(false); }}
          style={{ ...styles.tab, ...(tab === 'proveedores' ? styles.tabActivo : {}) }}>Proveedores</button>
        <button onClick={() => { setTab('ordenes'); setMostrarForm(false); }}
          style={{ ...styles.tab, ...(tab === 'ordenes' ? styles.tabActivo : {}) }}>Órdenes de Compra</button>
      </div>

      {tab === 'proveedores' && (
        <>
          {mostrarForm && (
            <div style={styles.card}>
              <form onSubmit={crearProveedor} style={styles.formGrid}>
                <input style={styles.input} placeholder="Nombre *" value={formProv.nombre}
                  onChange={e => setFormProv({ ...formProv, nombre: e.target.value })} required />
                <select style={styles.input} value={formProv.categoria} onChange={e => setFormProv({ ...formProv, categoria: e.target.value })}>
                  <option value="materiales">Materiales</option><option value="mano_obra">Mano de obra</option>
                  <option value="equipo">Equipo</option><option value="servicios">Servicios</option><option value="otro">Otro</option>
                </select>
                <input style={styles.input} placeholder="Contacto" value={formProv.contacto}
                  onChange={e => setFormProv({ ...formProv, contacto: e.target.value })} />
                <input style={styles.input} placeholder="Teléfono" value={formProv.telefono}
                  onChange={e => setFormProv({ ...formProv, telefono: e.target.value })} />
                <button type="submit" style={styles.btnPrimario}>Crear Proveedor</button>
              </form>
            </div>
          )}
          <div style={styles.grid}>
            {proveedores.map(p => (
              <div key={p.id} style={styles.card}>
                <h3 style={{ margin: '0 0 4px' }}>{p.nombre}</h3>
                <p style={{ margin: 0, fontSize: '12px', color: '#888', textTransform: 'capitalize' }}>{p.categoria}</p>
                {p.contacto && <p style={{ margin: '8px 0 0', fontSize: '13px' }}>👤 {p.contacto}</p>}
                {p.telefono && <p style={{ margin: '3px 0', fontSize: '13px' }}>📞 {p.telefono}</p>}
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span>{p.total_ordenes} orden(es)</span>
                  <strong>${Number(p.monto_total).toLocaleString('es-MX')}</strong>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'ordenes' && (
        <>
          {mostrarForm && (
            <div style={styles.card}>
              <form onSubmit={crearOrden} style={styles.formGrid}>
                <select style={styles.input} value={formOC.obra_id} onChange={e => setFormOC({ ...formOC, obra_id: e.target.value })} required>
                  <option value="">Selecciona obra *</option>
                  {obras.map(o => <option key={o.id} value={o.id}>{o.nombre}</option>)}
                </select>
                <select style={styles.input} value={formOC.proveedor_id} onChange={e => setFormOC({ ...formOC, proveedor_id: e.target.value })} required>
                  <option value="">Selecciona proveedor *</option>
                  {proveedores.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
                <input style={styles.input} placeholder="Concepto *" value={formOC.concepto}
                  onChange={e => setFormOC({ ...formOC, concepto: e.target.value })} required />
                <input style={styles.input} type="number" placeholder="Monto estimado" value={formOC.monto_estimado}
                  onChange={e => setFormOC({ ...formOC, monto_estimado: e.target.value })} />
                <input style={styles.input} type="date" value={formOC.fecha_pedido}
                  onChange={e => setFormOC({ ...formOC, fecha_pedido: e.target.value })} required />
                <button type="submit" style={styles.btnPrimario}>Crear Orden</button>
              </form>
            </div>
          )}
          <div style={styles.card}>
            <table style={styles.tabla}>
              <thead><tr style={styles.thead}><th>Obra</th><th>Proveedor</th><th>Concepto</th><th>Monto</th><th>Estado</th></tr></thead>
              <tbody>
                {ordenes.map(o => (
                  <tr key={o.id} style={styles.fila}>
                    <td>{o.obra_nombre}</td>
                    <td>{o.proveedor_nombre}</td>
                    <td>{o.concepto}</td>
                    <td>${Number(o.monto_real || o.monto_estimado || 0).toLocaleString('es-MX')}</td>
                    <td>
                      {puedeEditar ? (
                        <select value={o.estado} onChange={e => cambiarEstadoOC(o.id, e.target.value)} style={styles.selectMini}>
                          <option value="solicitada">Solicitada</option><option value="confirmada">Confirmada</option>
                          <option value="entregada">Entregada</option><option value="cancelada">Cancelada</option>
                        </select>
                      ) : (
                        <span style={{ ...styles.badge, background: COLOR_ESTADO_OC[o.estado] }}>{o.estado}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  titulo: { margin: 0, color: '#1a1a2e' },
  tabs: { display: 'flex', gap: '8px', marginBottom: '20px' },
  tab: { padding: '8px 16px', border: '1px solid #ddd', borderRadius: '8px', background: '#fff', cursor: 'pointer', fontSize: '13px' },
  tabActivo: { background: '#1a1a2e', color: '#fff', border: '1px solid #1a1a2e' },
  card: { background: '#fff', borderRadius: '12px', padding: '20px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px' },
  btnPrimario: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px' },
  tabla: { width: '100%', borderCollapse: 'collapse', fontSize: '13px' },
  thead: { background: '#f9fafb' },
  fila: { borderBottom: '1px solid #f0f0f0' },
  badge: { color: '#fff', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600' },
  selectMini: { padding: '4px 8px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '12px' }
};
