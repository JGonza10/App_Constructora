import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../AuthContext';

export default function Clientes() {
  const { usuario } = useAuth();
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState({ nombre: '', email: '', telefono: '', rfc: '', tipo: 'persona_fisica' });

  const cargar = () => {
    axios.get('/api/clientes')
      .then(({ data }) => setClientes(data))
      .catch(() => toast.error('Error al cargar clientes'))
      .finally(() => setCargando(false));
  };

  useEffect(() => { cargar(); }, []);

  const crear = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/clientes', form);
      toast.success('Cliente creado');
      setForm({ nombre: '', email: '', telefono: '', rfc: '', tipo: 'persona_fisica' });
      setMostrarForm(false);
      cargar();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const puedeEditar = usuario.rol === 'admin' || usuario.rol === 'supervisor';

  if (cargando) return <p>Cargando clientes...</p>;

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.titulo}>👥 Clientes</h2>
        {puedeEditar && (
          <button onClick={() => setMostrarForm(!mostrarForm)} style={styles.btnPrimario}>
            {mostrarForm ? '✕ Cancelar' : '+ Nuevo Cliente'}
          </button>
        )}
      </div>

      {mostrarForm && (
        <div style={styles.card}>
          <form onSubmit={crear} style={styles.formGrid}>
            <input style={styles.input} placeholder="Nombre completo / Razón social *" value={form.nombre}
              onChange={e => setForm({ ...form, nombre: e.target.value })} required />
            <select style={styles.input} value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
              <option value="persona_fisica">Persona Física</option>
              <option value="empresa">Empresa</option>
            </select>
            <input style={styles.input} type="email" placeholder="Email" value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })} />
            <input style={styles.input} placeholder="Teléfono" value={form.telefono}
              onChange={e => setForm({ ...form, telefono: e.target.value })} />
            <input style={styles.input} placeholder="RFC" value={form.rfc}
              onChange={e => setForm({ ...form, rfc: e.target.value })} />
            <button type="submit" style={styles.btnPrimario}>Crear Cliente</button>
          </form>
        </div>
      )}

      <div style={styles.grid}>
        {clientes.map(c => (
          <div key={c.id} style={styles.card}>
            <h3 style={{ margin: '0 0 4px' }}>{c.nombre}</h3>
            <p style={{ margin: 0, fontSize: '12px', color: '#888', textTransform: 'capitalize' }}>
              {c.tipo.replace('_', ' ')}
            </p>
            <div style={{ marginTop: '10px', fontSize: '13px', color: '#444' }}>
              {c.email && <p style={{ margin: '3px 0' }}>✉️ {c.email}</p>}
              {c.telefono && <p style={{ margin: '3px 0' }}>📞 {c.telefono}</p>}
            </div>
            <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
              <span>{c.total_obras} obra(s)</span>
              <strong>${Number(c.monto_total).toLocaleString('es-MX')}</strong>
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
  card: { background: '#fff', borderRadius: '12px', padding: '20px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  input: { padding: '10px 12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px' },
  btnPrimario: { padding: '10px 18px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }
};
