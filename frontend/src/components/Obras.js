import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

const COLOR_ESTADO = {
  cotizacion: '#6b7280', activa: '#16a34a', pausada: '#d97706',
  terminada: '#2563eb', cancelada: '#dc2626'
};
const LABEL_TIPO = {
  residencial: '🏠 Residencial', comercial: '🏢 Comercial',
  publica: '🏛️ Pública', mixta: '🏗️ Mixta', otro: 'Otro'
};

export default function Obras() {
  const { usuario } = useAuth();
  const navigate = useNavigate();
  const [obras, setObras] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [filtroEstado, setFiltroEstado] = useState('todas');
  const [form, setForm] = useState({
    nombre: '', tipo: 'residencial', cliente_id: '', monto_contrato: '',
    fecha_inicio: '', fecha_fin_estimada: '', direccion: '', descripcion: ''
  });

  const cargar = async () => {
    try {
      const [obrasRes, clientesRes] = await Promise.all([
        axios.get('/api/obras'),
        axios.get('/api/clientes')
      ]);
      setObras(obrasRes.data);
      setClientes(clientesRes.data);
    } catch { toast.error('Error al cargar obras'); }
    finally { setCargando(false); }
  };

  useEffect(() => { cargar(); }, []);

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/obras', form);
      toast.success('Obra creada correctamente');
      setForm({ nombre: '', tipo: 'residencial', cliente_id: '', monto_contrato: '',
        fecha_inicio: '', fecha_fin_estimada: '', direccion: '', descripcion: '' });
      setMostrarForm(false);
      cargar();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error al crear obra'); }
  };

  const obrasFiltradas = filtroEstado === 'todas'
    ? obras
    : obras.filter(o => o.estado === filtroEstado);

  if (cargando) return <p>Cargando obras...</p>;

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.titulo}>🏗️ Obras</h2>
        {(usuario.rol === 'admin' || usuario.rol === 'supervisor') && (
          <button onClick={() => setMostrarForm(!mostrarForm)} style={styles.btnPrimario}>
            {mostrarForm ? '✕ Cancelar' : '+ Nueva Obra'}
          </button>
        )}
      </div>

      {mostrarForm && (
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Nueva Obra</h3>
          <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <input style={styles.input} placeholder="Nombre de la obra *" value={form.nombre}
              onChange={e => setForm({ ...form, nombre: e.target.value })} required />
            <select style={styles.input} value={form.tipo}
              onChange={e => setForm({ ...form, tipo: e.target.value })}>
              <option value="residencial">Residencial</option>
              <option value="comercial">Comercial</option>
              <option value="publica">Pública</option>
              <option value="mixta">Mixta</option>
              <option value="otro">Otro</option>
            </select>
            <select style={styles.input} value={form.cliente_id}
              onChange={e => setForm({ ...form, cliente_id: e.target.value })} required>
              <option value="">Selecciona cliente *</option>
              {clientes.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <input style={styles.input} type="number" placeholder="Monto del contrato ($) *"
              value={form.monto_contrato} onChange={e => setForm({ ...form, monto_contrato: e.target.value })}
              required min="1" step="0.01" />
            <input style={styles.input} type="date" placeholder="Fecha inicio"
              value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} />
            <input style={styles.input} type="date" placeholder="Fecha fin estimada"
              value={form.fecha_fin_estimada} onChange={e => setForm({ ...form, fecha_fin_estimada: e.target.value })} />
            <input style={{ ...styles.input, gridColumn: 'span 2' }} placeholder="Dirección"
              value={form.direccion} onChange={e => setForm({ ...form, direccion: e.target.value })} />
            <textarea style={{ ...styles.input, gridColumn: 'span 2', height: '70px' }} placeholder="Descripción"
              value={form.descripcion} onChange={e => setForm({ ...form, descripcion: e.target.value })} />
            <button type="submit" style={{ ...styles.btnPrimario, gridColumn: 'span 2' }}>Crear Obra</button>
          </form>
        </div>
      )}

      {/* Filtros */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {['todas', 'cotizacion', 'activa', 'pausada', 'terminada', 'cancelada'].map(e => (
          <button key={e} onClick={() => setFiltroEstado(e)}
            style={{ ...styles.filtro, ...(filtroEstado === e ? styles.filtroActivo : {}) }}>
            {e === 'todas' ? 'Todas' : e}
          </button>
        ))}
      </div>

      {/* Tarjetas de obras */}
      <div style={styles.grid}>
        {obrasFiltradas.length === 0 ? (
          <p style={{ color: '#999' }}>No hay obras en este filtro.</p>
        ) : obrasFiltradas.map(o => (
          <div key={o.id} style={styles.cardObra} onClick={() => navigate(`/dashboard/obras/${o.id}`)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <p style={{ margin: 0, fontSize: '12px', color: '#888' }}>{LABEL_TIPO[o.tipo]}</p>
                <h3 style={{ margin: '4px 0', fontSize: '16px' }}>{o.nombre}</h3>
                <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>👤 {o.cliente_nombre}</p>
              </div>
              <span style={{ ...styles.badge, background: COLOR_ESTADO[o.estado] }}>{o.estado}</span>
            </div>

            {/* Barra de avance */}
            <div style={{ margin: '14px 0 8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#888', marginBottom: '4px' }}>
                <span>Avance</span><span>{o.avance_porcentaje}%</span>
              </div>
              <div style={styles.barraFondo}>
                <div style={{ ...styles.barraRelleno, width: `${o.avance_porcentaje}%` }} />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '10px' }}>
              <span style={{ color: '#666' }}>Contrato: <strong>${Number(o.monto_contrato).toLocaleString('es-MX')}</strong></span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span style={{ color: Number(o.pct_gasto) > 90 ? '#dc2626' : '#666' }}>
                Gastado: {o.pct_gasto || 0}%
              </span>
              <span style={{ color: Number(o.saldo_presupuesto) < 0 ? '#dc2626' : '#16a34a' }}>
                Saldo: ${Number(o.saldo_presupuesto).toLocaleString('es-MX')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  titulo: { margin: 0, color: '#1a1a2e' },
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', resize: 'vertical' },
  btnPrimario: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  filtro: { padding: '6px 14px', borderRadius: '20px', border: '1px solid #ddd', background: '#fff', cursor: 'pointer', fontSize: '13px', textTransform: 'capitalize' },
  filtroActivo: { background: '#1a1a2e', color: '#fff', border: '1px solid #1a1a2e' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' },
  cardObra: { background: '#fff', borderRadius: '12px', padding: '18px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', cursor: 'pointer', transition: 'transform 0.15s' },
  badge: { color: '#fff', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize', height: 'fit-content' },
  barraFondo: { width: '100%', height: '8px', background: '#f0f0f0', borderRadius: '10px', overflow: 'hidden' },
  barraRelleno: { height: '100%', background: '#2563eb', borderRadius: '10px', transition: 'width 0.3s' }
};
