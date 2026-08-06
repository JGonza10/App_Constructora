import { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../AuthContext';

const COLOR_ESTADO = {
  cotizacion: '#6b7280', activa: '#16a34a', pausada: '#d97706',
  terminada: '#2563eb', cancelada: '#dc2626'
};
const COLOR_CAT = {
  materiales: '#2563eb', mano_obra: '#d97706', subcontratista: '#7c3aed',
  equipo: '#0891b2', administrativo: '#6b7280', otro: '#374151'
};

export default function ObraDetalle() {
  const { id } = useParams();
  const { usuario } = useAuth();
  const [obra, setObra] = useState(null);
  const [tab, setTab] = useState('resumen');
  const [gastos, setGastos] = useState([]);
  const [avances, setAvances] = useState([]);
  const [pagos, setPagos] = useState([]);
  const [tareas, setTareas] = useState([]);
  const [bitacora, setBitacora] = useState([]);
  const [estimaciones, setEstimaciones] = useState([]);
  const [catalogo, setCatalogo] = useState([]);
  const [documentos, setDocumentos] = useState([]);
  const [cargando, setCargando] = useState(true);

  // formularios
  const [formGasto, setFormGasto] = useState({ categoria: 'materiales', concepto: '', monto: '', fecha: '' });
  const [formAvance, setFormAvance] = useState({ semana: '', etapa: '', porcentaje: '', descripcion: '' });
  const [formPago, setFormPago] = useState({ concepto: '', monto: '', fecha_programada: '' });
  const [formTarea, setFormTarea] = useState({ titulo: '', fecha_inicio: '', fecha_fin: '', prioridad: 'media' });
  const [formBitacora, setFormBitacora] = useState({ fecha: '', clima: 'soleado', personal_qty: '', actividades: '', incidencias: '' });
  const [formEstimacion, setFormEstimacion] = useState({ nombre: '', notas: '' });
  const [itemsEstimacion, setItemsEstimacion] = useState([{ material_id: '', cantidad: '' }]);
  const [formDocumento, setFormDocumento] = useState({ nombre: '', categoria: 'plano', url_archivo: '', visible_cliente: false });
  const [mostrarSub, setMostrarSub] = useState(false);

  const puedeEditar = usuario.rol === 'admin' || usuario.rol === 'supervisor';

  const cargarTodo = async () => {
    try {
      const [o, g, a, p, t, b, est, cat, doc] = await Promise.all([
        axios.get(`/api/obras/${id}`),
        axios.get(`/api/gastos?obra_id=${id}`),
        axios.get(`/api/avance?obra_id=${id}`),
        axios.get(`/api/pagos?obra_id=${id}`),
        axios.get(`/api/tareas?obra_id=${id}`),
        axios.get(`/api/bitacora?obra_id=${id}`),
        axios.get(`/api/estimaciones?obra_id=${id}`),
        axios.get('/api/estimaciones/catalogo'),
        axios.get(`/api/documentos?obra_id=${id}`)
      ]);
      setObra(o.data); setGastos(g.data); setAvances(a.data);
      setPagos(p.data); setTareas(t.data); setBitacora(b.data);
      setEstimaciones(est.data); setCatalogo(cat.data); setDocumentos(doc.data);
    } catch { toast.error('Error al cargar el detalle de la obra'); }
    finally { setCargando(false); }
  };

  useEffect(() => { cargarTodo(); }, [id]);

  const crearGasto = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/gastos', { ...formGasto, obra_id: id });
      toast.success('Gasto registrado');
      setFormGasto({ categoria: 'materiales', concepto: '', monto: '', fecha: '' });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const crearAvance = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/avance', { ...formAvance, obra_id: id });
      toast.success('Avance registrado');
      setFormAvance({ semana: '', etapa: '', porcentaje: '', descripcion: '' });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const crearPago = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/pagos', { ...formPago, obra_id: id });
      toast.success('Pago programado');
      setFormPago({ concepto: '', monto: '', fecha_programada: '' });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const marcarPagoRecibido = async (pagoId) => {
    try {
      await axios.patch(`/api/pagos/${pagoId}/recibir`);
      toast.success('Pago marcado como recibido');
      cargarTodo();
    } catch { toast.error('Error al actualizar pago'); }
  };

  const crearTarea = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/tareas', { ...formTarea, obra_id: id });
      toast.success('Tarea creada');
      setFormTarea({ titulo: '', fecha_inicio: '', fecha_fin: '', prioridad: 'media' });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error'); }
  };

  const cambiarEstadoTarea = async (tareaId, estado) => {
    try {
      await axios.patch(`/api/tareas/${tareaId}/estado`, { estado });
      toast.success('Tarea actualizada');
      cargarTodo();
    } catch { toast.error('Error al actualizar tarea'); }
  };

  const crearBitacora = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/bitacora', { ...formBitacora, obra_id: id });
      toast.success('Registro de bitácora guardado');
      setFormBitacora({ fecha: '', clima: 'soleado', personal_qty: '', actividades: '', incidencias: '' });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Ya existe un registro para esta fecha'); }
  };

  // ─── Estimación de materiales ───────────────────────────────
  const agregarItem = () => setItemsEstimacion([...itemsEstimacion, { material_id: '', cantidad: '' }]);
  const quitarItem = (idx) => setItemsEstimacion(itemsEstimacion.filter((_, i) => i !== idx));
  const actualizarItem = (idx, campo, valor) => {
    const nuevos = [...itemsEstimacion];
    nuevos[idx][campo] = valor;
    setItemsEstimacion(nuevos);
  };
  const totalEstimadoPreview = itemsEstimacion.reduce((sum, it) => {
    const mat = catalogo.find(m => m.id === Number(it.material_id));
    const precio = mat ? Number(mat.precio_unitario) : 0;
    return sum + precio * (Number(it.cantidad) || 0);
  }, 0);

  const crearEstimacion = async e => {
    e.preventDefault();
    const itemsValidos = itemsEstimacion.filter(it => it.material_id && it.cantidad);
    if (!itemsValidos.length) return toast.error('Agrega al menos un material con cantidad');
    try {
      await axios.post('/api/estimaciones', { ...formEstimacion, obra_id: id, items: itemsValidos });
      toast.success('Estimación creada');
      setFormEstimacion({ nombre: '', notas: '' });
      setItemsEstimacion([{ material_id: '', cantidad: '' }]);
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error al crear estimación'); }
  };

  // ─── Documentos ──────────────────────────────────────────────
  const crearDocumento = async e => {
    e.preventDefault();
    try {
      await axios.post('/api/documentos', { ...formDocumento, obra_id: id });
      toast.success('Documento registrado');
      setFormDocumento({ nombre: '', categoria: 'plano', url_archivo: '', visible_cliente: false });
      setMostrarSub(false); cargarTodo();
    } catch (err) { toast.error(err.response?.data?.mensaje || 'Error al registrar documento'); }
  };

  const toggleVisibilidadDoc = async (docId, actual) => {
    try {
      await axios.patch(`/api/documentos/${docId}/visibilidad`, { visible_cliente: !actual });
      toast.success(!actual ? 'Documento visible para el cliente' : 'Documento oculto del portal');
      cargarTodo();
    } catch { toast.error('Error al actualizar visibilidad'); }
  };

  if (cargando) return <p>Cargando...</p>;
  if (!obra) return <p>Obra no encontrada.</p>;

  const tabs = [
    { id: 'resumen', label: '📊 Resumen' },
    { id: 'gastos', label: '💵 Gastos' },
    { id: 'avance', label: '📈 Avance' },
    { id: 'pagos', label: '💰 Pagos' },
    { id: 'tareas', label: '✅ Tareas' },
    { id: 'bitacora', label: '📓 Bitácora' },
    { id: 'estimaciones', label: '🧮 Estimaciones' },
    { id: 'documentos', label: '📁 Documentos' },
  ];

  return (
    <div>
      {/* Encabezado */}
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <span style={{ ...styles.badge, background: COLOR_ESTADO[obra.estado] }}>{obra.estado}</span>
            <h2 style={{ margin: '8px 0 4px' }}>{obra.nombre}</h2>
            <p style={{ margin: 0, color: '#666' }}>👤 {obra.cliente_nombre} · 📍 {obra.direccion || 'Sin dirección'}</p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <p style={{ margin: 0, fontSize: '13px', color: '#888' }}>Contrato</p>
            <p style={{ margin: 0, fontSize: '22px', fontWeight: 'bold', color: '#1a1a2e' }}>
              ${Number(obra.monto_contrato).toLocaleString('es-MX')}
            </p>
          </div>
        </div>
        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
            <span>Avance de obra</span><span>{obra.avance_porcentaje}%</span>
          </div>
          <div style={styles.barraFondo}><div style={{ ...styles.barraRelleno, width: `${obra.avance_porcentaje}%` }} /></div>
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setMostrarSub(false); }}
            style={{ ...styles.tab, ...(tab === t.id ? styles.tabActivo : {}) }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* RESUMEN */}
      {tab === 'resumen' && (
        <div style={styles.metricas}>
          <div style={styles.metrica}>
            <div style={styles.metricaNum}>${Number(obra.gasto_real).toLocaleString('es-MX')}</div>
            <div style={styles.metricaLabel}>Gasto Real</div>
          </div>
          <div style={styles.metrica}>
            <div style={{ ...styles.metricaNum, color: Number(obra.saldo_presupuesto) < 0 ? '#dc2626' : '#16a34a' }}>
              ${Number(obra.saldo_presupuesto).toLocaleString('es-MX')}
            </div>
            <div style={styles.metricaLabel}>Saldo Disponible</div>
          </div>
          <div style={styles.metrica}>
            <div style={styles.metricaNum}>{tareas.filter(t => t.estado !== 'terminada').length}</div>
            <div style={styles.metricaLabel}>Tareas Pendientes</div>
          </div>
        </div>
      )}

      {/* GASTOS */}
      {tab === 'gastos' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Gastos registrados</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nuevo'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearGasto} style={styles.formGrid}>
              <select style={styles.input} value={formGasto.categoria} onChange={e => setFormGasto({ ...formGasto, categoria: e.target.value })}>
                <option value="materiales">Materiales</option><option value="mano_obra">Mano de obra</option>
                <option value="subcontratista">Subcontratista</option><option value="equipo">Equipo</option>
                <option value="administrativo">Administrativo</option><option value="otro">Otro</option>
              </select>
              <input style={styles.input} placeholder="Concepto *" value={formGasto.concepto}
                onChange={e => setFormGasto({ ...formGasto, concepto: e.target.value })} required />
              <input style={styles.input} type="number" placeholder="Monto *" value={formGasto.monto}
                onChange={e => setFormGasto({ ...formGasto, monto: e.target.value })} required min="0.01" step="0.01" />
              <input style={styles.input} type="date" value={formGasto.fecha}
                onChange={e => setFormGasto({ ...formGasto, fecha: e.target.value })} required />
              <button type="submit" style={{ ...styles.btnPrimario, gridColumn: 'span 2' }}>Registrar Gasto</button>
            </form>
          )}
          <table style={styles.tabla}>
            <thead><tr style={styles.thead}><th>Fecha</th><th>Categoría</th><th>Concepto</th><th>Monto</th></tr></thead>
            <tbody>
              {gastos.map(g => (
                <tr key={g.id} style={styles.fila}>
                  <td>{new Date(g.fecha).toLocaleDateString('es-MX')}</td>
                  <td><span style={{ ...styles.badge, background: COLOR_CAT[g.categoria] }}>{g.categoria}</span></td>
                  <td>{g.concepto}</td>
                  <td>${Number(g.monto).toLocaleString('es-MX')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* AVANCE */}
      {tab === 'avance' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Avance semanal</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nuevo'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearAvance} style={styles.formGrid}>
              <input style={styles.input} type="date" value={formAvance.semana}
                onChange={e => setFormAvance({ ...formAvance, semana: e.target.value })} required />
              <input style={styles.input} placeholder="Etapa (ej: Cimentación) *" value={formAvance.etapa}
                onChange={e => setFormAvance({ ...formAvance, etapa: e.target.value })} required />
              <input style={styles.input} type="number" placeholder="% Avance *" min="0" max="100" value={formAvance.porcentaje}
                onChange={e => setFormAvance({ ...formAvance, porcentaje: e.target.value })} required />
              <input style={styles.input} placeholder="Descripción" value={formAvance.descripcion}
                onChange={e => setFormAvance({ ...formAvance, descripcion: e.target.value })} />
              <button type="submit" style={{ ...styles.btnPrimario, gridColumn: 'span 2' }}>Registrar Avance</button>
            </form>
          )}
          {avances.map(a => (
            <div key={a.id} style={styles.itemLista}>
              <div>
                <strong>{a.etapa}</strong> — {new Date(a.semana).toLocaleDateString('es-MX')}
                {a.descripcion && <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#666' }}>{a.descripcion}</p>}
              </div>
              <span style={{ fontWeight: 'bold', color: '#2563eb' }}>{a.porcentaje}%</span>
            </div>
          ))}
        </div>
      )}

      {/* PAGOS */}
      {tab === 'pagos' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Calendario de pagos</h3>
            {puedeEditar && <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nuevo'}</button>}
          </div>
          {mostrarSub && (
            <form onSubmit={crearPago} style={styles.formGrid}>
              <input style={styles.input} placeholder="Concepto *" value={formPago.concepto}
                onChange={e => setFormPago({ ...formPago, concepto: e.target.value })} required />
              <input style={styles.input} type="number" placeholder="Monto *" value={formPago.monto}
                onChange={e => setFormPago({ ...formPago, monto: e.target.value })} required min="0.01" step="0.01" />
              <input style={styles.input} type="date" value={formPago.fecha_programada}
                onChange={e => setFormPago({ ...formPago, fecha_programada: e.target.value })} required />
              <button type="submit" style={{ ...styles.btnPrimario, gridColumn: 'span 2' }}>Programar Pago</button>
            </form>
          )}
          {pagos.map(p => (
            <div key={p.id} style={styles.itemLista}>
              <div>
                <strong>{p.concepto}</strong> — ${Number(p.monto).toLocaleString('es-MX')}
                <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>
                  Programado: {new Date(p.fecha_programada).toLocaleDateString('es-MX')}
                </p>
              </div>
              {p.estado === 'recibido'
                ? <span style={{ color: '#16a34a', fontWeight: '600' }}>✓ Recibido</span>
                : puedeEditar && <button onClick={() => marcarPagoRecibido(p.id)} style={styles.btnSec}>Marcar recibido</button>
              }
            </div>
          ))}
        </div>
      )}

      {/* TAREAS */}
      {tab === 'tareas' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Tareas de la obra</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nueva'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearTarea} style={styles.formGrid}>
              <input style={{ ...styles.input, gridColumn: 'span 2' }} placeholder="Título de la tarea *" value={formTarea.titulo}
                onChange={e => setFormTarea({ ...formTarea, titulo: e.target.value })} required />
              <input style={styles.input} type="date" value={formTarea.fecha_inicio}
                onChange={e => setFormTarea({ ...formTarea, fecha_inicio: e.target.value })} />
              <input style={styles.input} type="date" value={formTarea.fecha_fin}
                onChange={e => setFormTarea({ ...formTarea, fecha_fin: e.target.value })} />
              <select style={styles.input} value={formTarea.prioridad}
                onChange={e => setFormTarea({ ...formTarea, prioridad: e.target.value })}>
                <option value="baja">Baja</option><option value="media">Media</option><option value="alta">Alta</option>
              </select>
              <button type="submit" style={styles.btnPrimario}>Crear Tarea</button>
            </form>
          )}
          {tareas.map(t => (
            <div key={t.id} style={styles.itemLista}>
              <div>
                <strong>{t.titulo}</strong>
                {t.fecha_fin && <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>Vence: {new Date(t.fecha_fin).toLocaleDateString('es-MX')}</p>}
              </div>
              <select value={t.estado} onChange={e => cambiarEstadoTarea(t.id, e.target.value)} style={styles.selectMini}>
                <option value="pendiente">Pendiente</option>
                <option value="en_curso">En curso</option>
                <option value="terminada">Terminada</option>
              </select>
            </div>
          ))}
        </div>
      )}

      {/* BITÁCORA */}
      {tab === 'bitacora' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Bitácora diaria</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nuevo registro'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearBitacora} style={styles.formGrid}>
              <input style={styles.input} type="date" value={formBitacora.fecha}
                onChange={e => setFormBitacora({ ...formBitacora, fecha: e.target.value })} required />
              <select style={styles.input} value={formBitacora.clima}
                onChange={e => setFormBitacora({ ...formBitacora, clima: e.target.value })}>
                <option value="soleado">☀️ Soleado</option><option value="nublado">☁️ Nublado</option>
                <option value="lluvioso">🌧️ Lluvioso</option><option value="frio">🥶 Frío</option><option value="caluroso">🥵 Caluroso</option>
              </select>
              <input style={styles.input} type="number" placeholder="Personal en obra" value={formBitacora.personal_qty}
                onChange={e => setFormBitacora({ ...formBitacora, personal_qty: e.target.value })} />
              <textarea style={{ ...styles.input, gridColumn: 'span 2', height: '60px' }} placeholder="Actividades realizadas *"
                value={formBitacora.actividades} onChange={e => setFormBitacora({ ...formBitacora, actividades: e.target.value })} required />
              <textarea style={{ ...styles.input, gridColumn: 'span 2', height: '50px' }} placeholder="Incidencias (opcional)"
                value={formBitacora.incidencias} onChange={e => setFormBitacora({ ...formBitacora, incidencias: e.target.value })} />
              <button type="submit" style={{ ...styles.btnPrimario, gridColumn: 'span 2' }}>Guardar Registro</button>
            </form>
          )}
          {bitacora.map(b => (
            <div key={b.id} style={{ ...styles.itemLista, flexDirection: 'column', alignItems: 'flex-start' }}>
              <strong>{new Date(b.fecha).toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })}</strong>
              <p style={{ margin: '4px 0', fontSize: '13px' }}>👷 {b.personal_qty} personas · {b.clima}</p>
              <p style={{ margin: 0, fontSize: '13px', color: '#444' }}>{b.actividades}</p>
              {b.incidencias && <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#dc2626' }}>⚠️ {b.incidencias}</p>}
            </div>
          ))}
        </div>
      )}

      {/* ESTIMACIONES DE MATERIALES */}
      {tab === 'estimaciones' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Estimaciones de materiales</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nueva'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearEstimacion} style={{ background: '#f9fafb', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <input style={styles.input} placeholder="Nombre de la estimación *" value={formEstimacion.nombre}
                  onChange={e => setFormEstimacion({ ...formEstimacion, nombre: e.target.value })} required />
                <input style={styles.input} placeholder="Notas (opcional)" value={formEstimacion.notas}
                  onChange={e => setFormEstimacion({ ...formEstimacion, notas: e.target.value })} />
              </div>

              <p style={{ fontSize: '13px', fontWeight: '600', margin: '12px 0 8px' }}>Materiales</p>
              {itemsEstimacion.map((it, idx) => {
                const mat = catalogo.find(m => m.id === Number(it.material_id));
                return (
                  <div key={idx} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto auto', gap: '8px', marginBottom: '8px', alignItems: 'center' }}>
                    <select style={styles.input} value={it.material_id}
                      onChange={e => actualizarItem(idx, 'material_id', e.target.value)}>
                      <option value="">Selecciona material</option>
                      {catalogo.map(m => (
                        <option key={m.id} value={m.id}>{m.nombre} (${Number(m.precio_unitario).toLocaleString('es-MX')}/{m.unidad})</option>
                      ))}
                    </select>
                    <input style={styles.input} type="number" placeholder="Cantidad" min="0" step="0.01"
                      value={it.cantidad} onChange={e => actualizarItem(idx, 'cantidad', e.target.value)} />
                    <span style={{ fontSize: '13px', whiteSpace: 'nowrap' }}>
                      {mat ? `$${(Number(mat.precio_unitario) * (Number(it.cantidad) || 0)).toLocaleString('es-MX')}` : '—'}
                    </span>
                    {itemsEstimacion.length > 1 && (
                      <button type="button" onClick={() => quitarItem(idx)} style={styles.btnSec}>✕</button>
                    )}
                  </div>
                );
              })}
              <button type="button" onClick={agregarItem} style={{ ...styles.btnSec, marginBottom: '14px' }}>+ Agregar material</button>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #e5e7eb', paddingTop: '12px' }}>
                <strong>Total estimado: ${totalEstimadoPreview.toLocaleString('es-MX')}</strong>
                <button type="submit" style={styles.btnPrimario}>Guardar Estimación</button>
              </div>
            </form>
          )}

          {estimaciones.length === 0 ? <p style={{ color: '#999' }}>No hay estimaciones guardadas.</p> :
            estimaciones.map(e => (
              <div key={e.id} style={styles.itemLista}>
                <div>
                  <strong>{e.nombre}</strong>
                  {e.notas && <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>{e.notas}</p>}
                  <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#aaa' }}>
                    {e.creado_por_nombre} · {new Date(e.creado_en).toLocaleDateString('es-MX')}
                  </p>
                </div>
                <strong style={{ color: '#2563eb' }}>${Number(e.total).toLocaleString('es-MX')}</strong>
              </div>
            ))
          }
        </div>
      )}

      {/* DOCUMENTOS */}
      {tab === 'documentos' && (
        <div style={styles.card}>
          <div style={styles.subHeader}>
            <h3 style={{ margin: 0 }}>Documentos de la obra</h3>
            <button onClick={() => setMostrarSub(!mostrarSub)} style={styles.btnSec}>{mostrarSub ? '✕' : '+ Nuevo'}</button>
          </div>
          {mostrarSub && (
            <form onSubmit={crearDocumento} style={styles.formGrid}>
              <input style={styles.input} placeholder="Nombre del documento *" value={formDocumento.nombre}
                onChange={e => setFormDocumento({ ...formDocumento, nombre: e.target.value })} required />
              <select style={styles.input} value={formDocumento.categoria}
                onChange={e => setFormDocumento({ ...formDocumento, categoria: e.target.value })}>
                <option value="plano">Plano</option><option value="licencia">Licencia</option>
                <option value="contrato">Contrato</option><option value="acta">Acta</option>
                <option value="factura">Factura</option><option value="otro">Otro</option>
              </select>
              <input style={{ ...styles.input, gridColumn: 'span 2' }} placeholder="URL o ruta del archivo *"
                value={formDocumento.url_archivo} onChange={e => setFormDocumento({ ...formDocumento, url_archivo: e.target.value })} required />
              <label style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <input type="checkbox" checked={formDocumento.visible_cliente}
                  onChange={e => setFormDocumento({ ...formDocumento, visible_cliente: e.target.checked })} />
                Visible en el portal del cliente
              </label>
              <button type="submit" style={styles.btnPrimario}>Registrar Documento</button>
            </form>
          )}
          {documentos.length === 0 ? <p style={{ color: '#999' }}>No hay documentos registrados.</p> :
            documentos.map(d => (
              <div key={d.id} style={styles.itemLista}>
                <div>
                  <strong>{d.nombre}</strong> <span style={{ fontSize: '11px', color: '#888' }}>v{d.version}</span>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888', textTransform: 'capitalize' }}>{d.categoria}</p>
                </div>
                {puedeEditar && (
                  <button onClick={() => toggleVisibilidadDoc(d.id, d.visible_cliente)} style={styles.btnSec}>
                    {d.visible_cliente ? '👁️ Visible al cliente' : '🔒 Oculto'}
                  </button>
                )}
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

const styles = {
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  badge: { color: '#fff', padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize' },
  barraFondo: { width: '100%', height: '10px', background: '#f0f0f0', borderRadius: '10px', overflow: 'hidden' },
  barraRelleno: { height: '100%', background: '#2563eb', borderRadius: '10px' },
  tabs: { display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' },
  tab: { padding: '8px 16px', border: '1px solid #ddd', borderRadius: '8px', background: '#fff', cursor: 'pointer', fontSize: '13px' },
  tabActivo: { background: '#1a1a2e', color: '#fff', border: '1px solid #1a1a2e' },
  metricas: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' },
  metrica: { background: '#fff', borderRadius: '12px', padding: '24px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  metricaNum: { fontSize: '26px', fontWeight: 'bold', color: '#1a1a2e' },
  metricaLabel: { color: '#888', marginTop: '4px', fontSize: '13px' },
  subHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px', background: '#f9fafb', padding: '16px', borderRadius: '8px' },
  input: { padding: '9px 11px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '13px', resize: 'vertical' },
  btnPrimario: { padding: '9px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '13px' },
  btnSec: { padding: '6px 12px', background: '#f3f4f6', border: '1px solid #ddd', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' },
  tabla: { width: '100%', borderCollapse: 'collapse', fontSize: '13px' },
  thead: { background: '#f9fafb' },
  fila: { borderBottom: '1px solid #f0f0f0' },
  itemLista: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #f0f0f0', fontSize: '13px' },
  selectMini: { padding: '4px 8px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '12px' }
};
