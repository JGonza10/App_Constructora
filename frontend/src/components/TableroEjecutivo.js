import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const COLOR_CAT = {
  materiales: '#2563eb', mano_obra: '#d97706', subcontratista: '#7c3aed',
  equipo: '#0891b2', administrativo: '#6b7280', otro: '#374151'
};

export default function TableroEjecutivo() {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('/api/tablero')
      .then(({ data }) => setData(data))
      .catch(() => toast.error('Error al cargar el tablero'))
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando tablero...</p>;
  if (!data) return <p>No se pudo cargar el tablero.</p>;

  const totalActivas = data.obrasPorEstado.find(e => e.estado === 'activa')?.cantidad || 0;
  const montoActivo = data.obrasPorEstado.find(e => e.estado === 'activa')?.monto_total || 0;
  const utilidadTotal = data.rentabilidad.reduce((sum, r) => sum + Number(r.utilidad_estimada), 0);

  return (
    <div>
      <h2 style={{ color: '#1a1a2e', marginBottom: '20px' }}>📊 Tablero Ejecutivo</h2>

      {/* Métricas principales */}
      <div style={styles.metricas}>
        <div style={styles.metrica}>
          <div style={styles.metricaNum}>{totalActivas}</div>
          <div style={styles.metricaLabel}>Obras Activas</div>
        </div>
        <div style={styles.metrica}>
          <div style={styles.metricaNum}>${Number(montoActivo).toLocaleString('es-MX')}</div>
          <div style={styles.metricaLabel}>Monto en Ejecución</div>
        </div>
        <div style={styles.metrica}>
          <div style={{ ...styles.metricaNum, color: utilidadTotal >= 0 ? '#16a34a' : '#dc2626' }}>
            ${Number(utilidadTotal).toLocaleString('es-MX')}
          </div>
          <div style={styles.metricaLabel}>Utilidad Estimada</div>
        </div>
        <div style={styles.metrica}>
          <div style={{ ...styles.metricaNum, color: data.pagosAlerta.length ? '#d97706' : '#16a34a' }}>
            {data.pagosAlerta.length}
          </div>
          <div style={styles.metricaLabel}>Pagos por Cobrar</div>
        </div>
      </div>

      <div style={styles.dosColumnas}>
        {/* Obras activas con KPIs */}
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>🏗️ Obras en ejecución</h3>
          {data.obrasActivas.length === 0 ? <p style={{ color: '#999' }}>No hay obras activas.</p> :
            data.obrasActivas.map(o => (
              <div key={o.id} style={styles.obraItem} onClick={() => navigate(`/dashboard/obras/${o.id}`)}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{o.nombre}</strong>
                  <span style={{ fontSize: '12px', color: '#888' }}>{o.cliente}</span>
                </div>
                <div style={styles.barraFondo}><div style={{ ...styles.barraRelleno, width: `${o.avance_porcentaje}%` }} /></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginTop: '4px' }}>
                  <span>{o.avance_porcentaje}% avance</span>
                  <span style={{ color: Number(o.pct_gastado) > 90 ? '#dc2626' : '#666' }}>
                    {o.pct_gastado || 0}% gastado
                  </span>
                </div>
              </div>
            ))
          }
        </div>

        {/* Alertas de pagos */}
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>💰 Pagos próximos / vencidos</h3>
          {data.pagosAlerta.length === 0 ? <p style={{ color: '#999' }}>Sin pagos pendientes en 30 días.</p> :
            data.pagosAlerta.map(p => (
              <div key={p.id} style={styles.alertaItem}>
                <div>
                  <strong>{p.concepto}</strong> — {p.obra_nombre}
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>{p.cliente_nombre}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ margin: 0, fontWeight: 'bold' }}>${Number(p.monto).toLocaleString('es-MX')}</p>
                  <p style={{ margin: 0, fontSize: '11px', color: p.dias_restantes < 0 ? '#dc2626' : '#d97706' }}>
                    {p.dias_restantes < 0 ? `Vencido hace ${Math.abs(p.dias_restantes)}d` : `En ${p.dias_restantes}d`}
                  </p>
                </div>
              </div>
            ))
          }
        </div>
      </div>

      <div style={styles.dosColumnas}>
        {/* Tareas atrasadas */}
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>⚠️ Tareas atrasadas</h3>
          {data.tareasAtrasadas.length === 0 ? <p style={{ color: '#999' }}>Sin tareas atrasadas. 🎉</p> :
            data.tareasAtrasadas.map(t => (
              <div key={t.id} style={styles.alertaItem}>
                <div>
                  <strong>{t.titulo}</strong>
                  <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#888' }}>{t.obra_nombre} · {t.responsable || 'Sin asignar'}</p>
                </div>
                <span style={{ fontSize: '11px', color: '#dc2626' }}>
                  Venció: {new Date(t.fecha_fin).toLocaleDateString('es-MX')}
                </span>
              </div>
            ))
          }
        </div>

        {/* Gastos del mes por categoría */}
        <div style={styles.card}>
          <h3 style={{ marginTop: 0 }}>💵 Gastos del mes</h3>
          {data.gastosMes.length === 0 ? <p style={{ color: '#999' }}>Sin gastos este mes.</p> :
            data.gastosMes.map(g => {
              const total = data.gastosMes.reduce((s, x) => s + Number(x.total), 0);
              const pct = total ? (Number(g.total) / total * 100).toFixed(0) : 0;
              return (
                <div key={g.categoria} style={{ marginBottom: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '3px' }}>
                    <span style={{ textTransform: 'capitalize' }}>{g.categoria}</span>
                    <span>${Number(g.total).toLocaleString('es-MX')}</span>
                  </div>
                  <div style={styles.barraFondo}>
                    <div style={{ ...styles.barraRelleno, width: `${pct}%`, background: COLOR_CAT[g.categoria] }} />
                  </div>
                </div>
              );
            })
          }
        </div>
      </div>
    </div>
  );
}

const styles = {
  metricas: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '20px' },
  metrica: { background: '#fff', borderRadius: '12px', padding: '22px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  metricaNum: { fontSize: '24px', fontWeight: 'bold', color: '#1a1a2e' },
  metricaLabel: { color: '#888', marginTop: '4px', fontSize: '12px' },
  dosColumnas: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' },
  card: { background: '#fff', borderRadius: '12px', padding: '22px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  obraItem: { padding: '10px 0', borderBottom: '1px solid #f0f0f0', cursor: 'pointer' },
  alertaItem: { display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #f0f0f0', fontSize: '13px' },
  barraFondo: { width: '100%', height: '6px', background: '#f0f0f0', borderRadius: '10px', overflow: 'hidden', marginTop: '4px' },
  barraRelleno: { height: '100%', background: '#2563eb', borderRadius: '10px' }
};
