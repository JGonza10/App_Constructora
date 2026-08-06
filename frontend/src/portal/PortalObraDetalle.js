import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { usePortalAuth } from '../PortalAuthContext';

const ICONO_DOC = { plano: '📐', licencia: '📜', contrato: '📝', acta: '📋', factura: '🧾', otro: '📁' };

export default function PortalObraDetalle() {
  const { id } = useParams();
  const { portalAxios, cliente } = usePortalAuth();
  const navigate = useNavigate();
  const [obra, setObra] = useState(null);
  const [avance, setAvance] = useState([]);
  const [pagos, setPagos] = useState([]);
  const [documentos, setDocumentos] = useState([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    Promise.all([
      portalAxios.get(`/api/portal/obras/${id}`),
      portalAxios.get(`/api/portal/obras/${id}/avance`),
      portalAxios.get(`/api/portal/obras/${id}/pagos`),
      portalAxios.get(`/api/portal/obras/${id}/documentos`)
    ])
      .then(([o, a, p, d]) => {
        setObra(o.data); setAvance(a.data); setPagos(p.data); setDocumentos(d.data);
      })
      .catch(() => toast.error('Error al cargar la obra'))
      .finally(() => setCargando(false));
  }, [id]);

  if (cargando) return <p style={{ padding: '40px', textAlign: 'center' }}>Cargando...</p>;
  if (!obra) return <p style={{ padding: '40px', textAlign: 'center' }}>Obra no encontrada.</p>;

  return (
    <div style={styles.layout}>
      <header style={styles.header}>
        <button onClick={() => navigate('/portal/obras')} style={styles.btnVolver}>← Mis obras</button>
        <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>{cliente.nombre}</p>
      </header>

      <div style={styles.contenido}>
        <div style={styles.card}>
          <h2 style={{ margin: '0 0 4px' }}>{obra.nombre}</h2>
          <p style={{ margin: 0, color: '#666' }}>📍 {obra.direccion || 'Sin dirección registrada'}</p>
          {obra.descripcion && <p style={{ marginTop: '10px', color: '#444', fontSize: '14px' }}>{obra.descripcion}</p>}
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
              <span>Avance general</span><span>{obra.avance_porcentaje}%</span>
            </div>
            <div style={styles.barraFondo}><div style={{ ...styles.barraRelleno, width: `${obra.avance_porcentaje}%` }} /></div>
          </div>
        </div>

        <div style={styles.dosColumnas}>
          {/* Avance por etapa */}
          <div style={styles.card}>
            <h3 style={{ marginTop: 0 }}>📈 Avance por etapa</h3>
            {avance.length === 0 ? <p style={{ color: '#999' }}>Sin actualizaciones aún.</p> :
              avance.map((a, i) => (
                <div key={i} style={styles.itemLista}>
                  <div>
                    <strong>{a.etapa}</strong>
                    <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>
                      Semana del {new Date(a.semana).toLocaleDateString('es-MX')}
                    </p>
                    {a.descripcion && <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#444' }}>{a.descripcion}</p>}
                  </div>
                  <strong style={{ color: '#16a34a' }}>{a.porcentaje}%</strong>
                </div>
              ))
            }
          </div>

          {/* Estado de cuenta */}
          <div style={styles.card}>
            <h3 style={{ marginTop: 0 }}>💰 Estado de cuenta</h3>
            {pagos.length === 0 ? <p style={{ color: '#999' }}>Sin pagos registrados.</p> :
              pagos.map((p, i) => (
                <div key={i} style={styles.itemLista}>
                  <div>
                    <strong>{p.concepto}</strong>
                    <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>
                      Programado: {new Date(p.fecha_programada).toLocaleDateString('es-MX')}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <strong>${Number(p.monto).toLocaleString('es-MX')}</strong>
                    <p style={{ margin: 0, fontSize: '11px', color: p.estado === 'recibido' ? '#16a34a' : '#d97706' }}>
                      {p.estado === 'recibido' ? '✓ Pagado' : 'Pendiente'}
                    </p>
                  </div>
                </div>
              ))
            }
          </div>
        </div>

        {/* Documentos compartidos */}
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>📁 Documentos compartidos</h3>
          {documentos.length === 0 ? <p style={{ color: '#999' }}>Tu arquitecto aún no ha compartido documentos.</p> :
            <div style={styles.gridDocs}>
              {documentos.map(d => (
                <div key={d.id} style={styles.docItem}>
                  <span style={{ fontSize: '24px' }}>{ICONO_DOC[d.categoria]}</span>
                  <div>
                    <p style={{ margin: 0, fontWeight: '600', fontSize: '13px' }}>{d.nombre}</p>
                    <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#888', textTransform: 'capitalize' }}>{d.categoria}</p>
                  </div>
                </div>
              ))}
            </div>
          }
        </div>
      </div>
    </div>
  );
}

const styles = {
  layout: { minHeight: '100vh', background: '#f0f2f5' },
  header: { background: '#fff', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' },
  btnVolver: { background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '14px', fontWeight: '600' },
  contenido: { padding: '32px', maxWidth: '1000px', margin: '0 auto' },
  card: { background: '#fff', borderRadius: '12px', padding: '24px', marginBottom: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  dosColumnas: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  barraFondo: { width: '100%', height: '10px', background: '#f0f0f0', borderRadius: '10px', overflow: 'hidden' },
  barraRelleno: { height: '100%', background: '#16a34a', borderRadius: '10px' },
  itemLista: { display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0', fontSize: '13px' },
  gridDocs: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px' },
  docItem: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', background: '#f9fafb', borderRadius: '8px' }
};
