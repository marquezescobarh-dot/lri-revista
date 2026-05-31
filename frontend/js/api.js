const API = 'https://lri-revista.onrender.com';

function getToken() { return localStorage.getItem('lri_token'); }
function getUsuario() { const u = localStorage.getItem('lri_usuario'); return u ? JSON.parse(u) : null; }
function setSession(token, usuario) { localStorage.setItem('lri_token', token); localStorage.setItem('lri_usuario', JSON.stringify(usuario)); }
function cerrarSesion() { localStorage.removeItem('lri_token'); localStorage.removeItem('lri_usuario'); window.location.href = '/index.html'; }
function estaLogueado() { return !!getToken(); }
function esAdmin() { const u = getUsuario(); return u && (u.rol === 'admin' || u.rol === 'superadmin'); }
function esSuperadmin() { const u = getUsuario(); return u && u.rol === 'superadmin'; }

async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || 'Error en la solicitud');
  }
  return res.json();
}

async function apiFetchForm(endpoint, formData, method = 'POST') {
  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${endpoint}`, { method, headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || 'Error en la solicitud');
  }
  return res.json();
}

function toast(msg, tipo = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) { container = document.createElement('div'); container.className = 'toast-container'; document.body.appendChild(container); }
  const t = document.createElement('div');
  const iconos = { success: '✓', error: '✕', info: 'ℹ' };
  t.className = `toast toast-${tipo}`;
  t.innerHTML = `<span>${iconos[tipo]}</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => { t.style.animation = 'slideIn 0.3s ease reverse'; setTimeout(() => t.remove(), 300); }, 3500);
}

function fechaLegible(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { year: 'numeric', month: 'long', day: 'numeric' });
}

function fechaRelativa(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'ahora';
  if (mins < 60) return `hace ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `hace ${hrs}h`;
  const dias = Math.floor(hrs / 24);
  if (dias < 7) return `hace ${dias}d`;
  return fechaLegible(iso);
}

const NIVELES = [
  { nivel: 1, titulo: "Lector",              emoji: "📖", puntos_min: 0 },
  { nivel: 2, titulo: "Colaborador",          emoji: "✍️", puntos_min: 100 },
  { nivel: 3, titulo: "Autor",                emoji: "📝", puntos_min: 300 },
  { nivel: 4, titulo: "Autor Destacado",      emoji: "⭐", puntos_min: 700 },
  { nivel: 5, titulo: "Investigador",          emoji: "🎓", puntos_min: 1100 },
  { nivel: 6, titulo: "Voz Académica",        emoji: "💼", puntos_min: 1600 },
  { nivel: 7, titulo: "Economista Principal", emoji: "🏆", puntos_min: 2500 },
];

function getNivelData(nivel) {
  return NIVELES[Math.min((nivel || 1) - 1, NIVELES.length - 1)];
}

function renderNavbar() {
  const usuario = getUsuario();
  const navUser = document.getElementById('nav-user');
  if (!navUser) return;

  if (usuario) {
    const nivelData = getNivelData(usuario.nivel || 1);
    const avatarHTML = usuario.foto_perfil
      ? `<img src="${API}/uploads/avatars/${usuario.foto_perfil}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,0.3)">`
      : `<div style="width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-size:0.85rem;font-weight:700;color:#fff;border:2px solid rgba(255,255,255,0.3)">${usuario.nombre[0].toUpperCase()}</div>`;

    navUser.innerHTML = `
      <div id="campana-wrap" style="position:relative">
        <button onclick="toggleNotificaciones()" style="background:rgba(255,255,255,0.1);border:1.5px solid rgba(255,255,255,0.2);border-radius:8px;color:#fff;width:38px;height:38px;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s" id="btn-campana">🔔</button>
        <span id="notif-badge" style="display:none;position:absolute;top:-4px;right:-4px;background:#c0392b;color:#fff;font-family:'DM Sans',sans-serif;font-size:0.65rem;font-weight:700;width:18px;height:18px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid var(--azul)">0</span>
        <div id="notif-panel" style="display:none;position:absolute;right:0;top:calc(100% + 8px);width:320px;background:#fff;border:1.5px solid var(--borde);border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,0.15);z-index:999;overflow:hidden">
          <div style="padding:1rem 1.2rem;border-bottom:1px solid var(--borde);display:flex;align-items:center;justify-content:space-between">
            <span style="font-family:'DM Sans',sans-serif;font-weight:600;font-size:0.9rem;color:var(--texto)">Notificaciones</span>
            <button onclick="marcarTodasLeidas()" style="font-family:'DM Sans',sans-serif;font-size:0.75rem;color:var(--azul);background:none;border:none;cursor:pointer">Marcar todas leídas</button>
          </div>
          <div id="notif-lista" style="max-height:360px;overflow-y:auto"></div>
        </div>
      </div>
      <button onclick="toggleMenu()" style="background:rgba(255,255,255,0.1);border:1.5px solid rgba(255,255,255,0.2);border-radius:8px;color:#fff;width:38px;height:38px;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s" id="btn-menu">☰</button>

      <div id="menu-lateral" style="display:none;position:fixed;top:0;right:0;bottom:0;width:280px;background:var(--azul);z-index:1000;box-shadow:-4px 0 20px rgba(0,0,0,0.3);flex-direction:column">
        <div style="padding:1.5rem;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:space-between">
          <div style="display:flex;align-items:center;gap:0.8rem">
            ${avatarHTML}
            <div>
              <div style="font-family:'DM Sans',sans-serif;font-weight:600;color:#fff;font-size:0.95rem">${usuario.nombre.split(' ')[0]}</div>
              <div style="font-family:'DM Sans',sans-serif;font-size:0.72rem;color:rgba(255,255,255,0.5)">${nivelData.emoji} ${nivelData.titulo}</div>
            </div>
          </div>
          <button onclick="cerrarMenu()" style="color:rgba(255,255,255,0.7);font-size:1.3rem;background:none;border:none;cursor:pointer">✕</button>
        </div>
        <div style="flex:1;padding:1rem 0;overflow-y:auto">
          <a href="/pages/perfil.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">👤 Mi perfil</a>
          <a href="/pages/perfil.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">⚙️ Editar perfil</a>
          <a href="/pages/publicar.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">✏️ Publicar artículo</a>
          <a href="/pages/perfil.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">📄 Mis artículos</a>
          <a href="/pages/organizaciones.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">🏛️ Organizaciones</a>
          <a href="/pages/ranking.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.8);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">🏆 Ranking</a>
          ${esAdmin() ? `<a href="/pages/admin.html" onclick="cerrarMenu()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:var(--oro);font-family:'DM Sans',sans-serif;font-size:0.9rem;text-decoration:none;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">🛡️ Panel admin</a>` : ''}
          <div style="margin:0.5rem 1.5rem;height:1px;background:rgba(255,255,255,0.1)"></div>
          <button onclick="cerrarSesion()" style="display:flex;align-items:center;gap:0.8rem;padding:0.8rem 1.5rem;color:rgba(255,255,255,0.6);font-family:'DM Sans',sans-serif;font-size:0.9rem;background:none;border:none;cursor:pointer;width:100%;text-align:left;transition:all 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.08)'" onmouseout="this.style.background='none'">← Cerrar sesión</button>
        </div>
      </div>
      <div id="menu-overlay" onclick="cerrarMenu()" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999"></div>`;

    cargarNotificaciones();
  } else {
    navUser.innerHTML = `
      <button onclick="abrirModal('login')" style="font-family:'DM Sans',sans-serif;font-size:0.85rem;font-weight:500;padding:0.45rem 1rem;border-radius:6px;color:rgba(255,255,255,0.9);border:1.5px solid rgba(255,255,255,0.35);background:none;cursor:pointer;transition:all 0.2s">Iniciar sesión</button>
      <button onclick="abrirModal('registro')" style="font-family:'DM Sans',sans-serif;font-size:0.85rem;font-weight:600;padding:0.45rem 1.1rem;border-radius:6px;background:var(--oro);color:#fff;border:none;cursor:pointer;transition:all 0.2s">Registrarse</button>`;
  }
}

function toggleMenu() {
  const menu = document.getElementById('menu-lateral');
  const overlay = document.getElementById('menu-overlay');
  if (menu.style.display === 'none') {
    menu.style.display = 'flex';
    overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';
  } else {
    cerrarMenu();
  }
}

function cerrarMenu() {
  const menu = document.getElementById('menu-lateral');
  const overlay = document.getElementById('menu-overlay');
  if (menu) menu.style.display = 'none';
  if (overlay) overlay.style.display = 'none';
  document.body.style.overflow = '';
}

function toggleNotificaciones() {
  const panel = document.getElementById('notif-panel');
  if (!panel) return;
  const visible = panel.style.display !== 'none';
  panel.style.display = visible ? 'none' : 'block';
  if (!visible) cargarNotificaciones();
}

async function cargarNotificaciones() {
  if (!estaLogueado()) return;
  try {
    const data = await apiFetch('/notificaciones/no-leidas');
    const badge = document.getElementById('notif-badge');
    if (badge) {
      if (data.count > 0) {
        badge.style.display = 'flex';
        badge.textContent = data.count > 9 ? '9+' : data.count;
      } else {
        badge.style.display = 'none';
      }
    }

    const lista = document.getElementById('notif-lista');
    if (!lista) return;
    const notifs = await apiFetch('/notificaciones/');
    if (!notifs.length) {
      lista.innerHTML = '<div style="padding:1.5rem;text-align:center;font-family:\'DM Sans\',sans-serif;font-size:0.85rem;color:var(--texto-3)">Sin notificaciones</div>';
      return;
    }
    const iconosNotif = { articulo_aprobado: '✅', articulo_rechazado: '❌', comentario_nuevo: '💬', respuesta_comentario: '↩️', like_recibido: '❤️', rol_cambiado: '🛡️', puntos_ajustados: '⭐' };
    lista.innerHTML = notifs.map(n => `
      <a href="${n.link || '#'}" onclick="marcarLeida(${n.id})" style="display:flex;align-items:flex-start;gap:0.8rem;padding:0.9rem 1.2rem;border-bottom:1px solid var(--borde);text-decoration:none;background:${n.leida ? '#fff' : 'var(--azul-claro)'};transition:background 0.2s">
        <span style="font-size:1.2rem;flex-shrink:0;margin-top:0.1rem">${iconosNotif[n.tipo] || '🔔'}</span>
        <div style="flex:1">
          <p style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:var(--texto);line-height:1.4;margin:0">${n.mensaje}</p>
          <span style="font-family:'DM Sans',sans-serif;font-size:0.72rem;color:var(--texto-3)">${fechaRelativa(n.creado_en)}</span>
        </div>
        ${!n.leida ? '<span style="width:8px;height:8px;border-radius:50%;background:var(--azul);flex-shrink:0;margin-top:0.3rem"></span>' : ''}
      </a>`).join('');
  } catch(e) {}
}

async function marcarLeida(id) {
  try { await apiFetch(`/notificaciones/${id}/leer`, { method: 'POST' }); } catch(e) {}
}

async function marcarTodasLeidas() {
  try {
    await apiFetch('/notificaciones/marcar-leidas', { method: 'POST' });
    cargarNotificaciones();
  } catch(e) {}
}

document.addEventListener('click', (e) => {
  const panel = document.getElementById('notif-panel');
  const wrap = document.getElementById('campana-wrap');
  if (panel && wrap && !wrap.contains(e.target)) {
    panel.style.display = 'none';
  }
  if (e.target.classList.contains('modal-overlay')) cerrarModal();
});

function abrirModal(tab = 'login') {
  const overlay = document.getElementById('modal-auth');
  if (!overlay) return;
  overlay.classList.add('open');
  cambiarTab(tab);
}
function cerrarModal() { const o = document.getElementById('modal-auth'); if (o) o.classList.remove('open'); }
function cambiarTab(tab) {
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.modal-form').forEach(f => f.style.display = 'none');
  const tabBtn = document.querySelector(`[data-tab="${tab}"]`);
  const form = document.getElementById(`form-${tab}`);
  if (tabBtn) tabBtn.classList.add('active');
  if (form) form.style.display = 'block';
}
