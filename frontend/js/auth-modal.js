let emailRegistrado = '';

function togglePass(inputId, btnId) {
  const input = document.getElementById(inputId);
  const btn = document.getElementById(btnId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = 'Ocultar';
  } else {
    input.type = 'password';
    btn.textContent = 'Mostrar';
  }
}

function medirFuerzaPass(pass) {
  let score = 0;
  if (pass.length >= 8) score++;
  if (pass.length >= 12) score++;
  if (/[A-Z]/.test(pass)) score++;
  if (/[0-9]/.test(pass)) score++;
  if (/[^A-Za-z0-9]/.test(pass)) score++;
  return score;
}

document.addEventListener('input', (e) => {
  if (e.target.id === 'reg-pass') {
    const score = medirFuerzaPass(e.target.value);
    const bar = document.getElementById('pass-strength-bar');
    const hint = document.getElementById('pass-hint');
    if (!bar) return;
    const colores = ['#c0392b','#e67e22','#f1c40f','#27ae60','#1abc9c'];
    const labels = ['Muy débil','Débil','Regular','Buena','Muy segura'];
    bar.style.width = (score/5*100) + '%';
    bar.style.background = colores[Math.min(score-1, 4)] || 'var(--borde)';
    if (hint) hint.textContent = score > 0 ? labels[Math.min(score-1, 4)] : 'Mínimo 8 caracteres';
  }
});

function mostrarRecuperar() {
  document.querySelectorAll('.modal-form').forEach(f => f.style.display = 'none');
  document.getElementById('auth-tabs').style.display = 'none';
  document.getElementById('modal-auth-titulo').textContent = 'Recuperar contraseña';
  document.getElementById('form-recuperar').style.display = 'block';
}

function mostrarLogin() {
  document.querySelectorAll('.modal-form').forEach(f => f.style.display = 'none');
  document.getElementById('auth-tabs').style.display = 'flex';
  document.getElementById('modal-auth-titulo').textContent = 'Acceder a LRI';
  cambiarTab('login');
}

function mostrarVerificacion() {
  document.querySelectorAll('.modal-form').forEach(f => f.style.display = 'none');
  document.getElementById('auth-tabs').style.display = 'none';
  document.getElementById('modal-auth-titulo').textContent = 'Verifica tu email';
  document.getElementById('form-verificacion').style.display = 'block';
}

async function hacerLogin() {
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';
  const email = document.getElementById('login-email').value.trim();
  const pass = document.getElementById('login-pass').value;
  const remember = document.getElementById('login-remember')?.checked || false;
  if (!email || !pass) { errEl.textContent = 'Ingresa tu correo y contraseña'; errEl.style.display = 'block'; return; }
  try {
    const res = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, contrasena: pass, recordarme: remember }) });
    setSession(res.access_token, res.usuario);
    cerrarModal();
    toast('Bienvenido, ' + res.usuario.nombre.split(' ')[0] + '!', 'success');
    renderNavbar();
    if (typeof onLoginExito === 'function') onLoginExito(res.usuario);
  } catch(e) {
    errEl.textContent = e.message;
    errEl.style.display = 'block';
  }
}

async function hacerRegistro() {
  const errEl = document.getElementById('reg-error');
  errEl.style.display = 'none';
  const nombre = document.getElementById('reg-nombre').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const pass = document.getElementById('reg-pass').value;
  if (!nombre) { errEl.textContent = 'Ingresa tu nombre'; errEl.style.display = 'block'; return; }
  if (!email) { errEl.textContent = 'Ingresa tu correo'; errEl.style.display = 'block'; return; }
  if (pass.length < 8) { errEl.textContent = 'La contraseña debe tener al menos 8 caracteres'; errEl.style.display = 'block'; return; }
  try {
    const res = await apiFetch('/auth/registro', { method: 'POST', body: JSON.stringify({ nombre, email, contrasena: pass }) });
    setSession(res.access_token, res.usuario);
    emailRegistrado = email;
    mostrarVerificacion();
    toast('Cuenta creada. Revisa tu correo para el código.', 'success');
    renderNavbar();
  } catch(e) {
    errEl.textContent = e.message;
    errEl.style.display = 'block';
  }
}

async function verificarEmail() {
  const errEl = document.getElementById('ver-error');
  errEl.style.display = 'none';
  const codigo = document.getElementById('ver-codigo').value.trim();
  const u = getUsuario();
  const email = u?.email || emailRegistrado;
  if (codigo.length !== 6) { errEl.textContent = 'El código debe tener 6 dígitos'; errEl.style.display = 'block'; return; }
  try {
    await apiFetch('/auth/verificar-email', { method: 'POST', body: JSON.stringify({ email, codigo }) });
    if (u) { u.email_verificado = true; localStorage.setItem('lri_usuario', JSON.stringify(u)); }
    cerrarModal();
    toast('Email verificado. Ya puedes publicar en LRI.', 'success');
    if (typeof onVerificacionExito === 'function') onVerificacionExito();
  } catch(e) {
    errEl.textContent = e.message;
    errEl.style.display = 'block';
  }
}

async function reenviarCodigo() {
  const u = getUsuario();
  const email = u?.email || emailRegistrado;
  try {
    await apiFetch('/auth/reenviar-codigo', { method: 'POST', body: JSON.stringify({ email }) });
    toast('Código reenviado', 'info');
  } catch(e) { toast(e.message, 'error'); }
}

async function enviarCodigoRecuperacion() {
  const errEl = document.getElementById('rec-error1');
  errEl.style.display = 'none';
  const email = document.getElementById('rec-email').value.trim();
  if (!email) { errEl.textContent = 'Ingresa tu correo'; errEl.style.display = 'block'; return; }
  try {
    await apiFetch('/auth/recuperar-contrasena', { method: 'POST', body: JSON.stringify({ email }) });
    document.getElementById('recuperar-paso1').style.display = 'none';
    document.getElementById('recuperar-paso2').style.display = 'block';
    toast('Código enviado. Revisa la terminal del backend si estás en desarrollo.', 'success');
  } catch(e) {
    errEl.textContent = e.message;
    errEl.style.display = 'block';
  }
}

async function resetContrasena() {
  const errEl = document.getElementById('rec-error2');
  errEl.style.display = 'none';
  const email = document.getElementById('rec-email').value.trim();
  const codigo = document.getElementById('rec-codigo').value.trim();
  const nueva = document.getElementById('rec-nueva-pass').value;
  if (codigo.length !== 6) { errEl.textContent = 'Código de 6 dígitos requerido'; errEl.style.display = 'block'; return; }
  if (nueva.length < 8) { errEl.textContent = 'La contraseña debe tener al menos 8 caracteres'; errEl.style.display = 'block'; return; }
  try {
    await apiFetch('/auth/reset-contrasena', { method: 'POST', body: JSON.stringify({ email, codigo, nueva_contrasena: nueva }) });
    mostrarLogin();
    toast('Contraseña cambiada. Ya puedes iniciar sesión.', 'success');
  } catch(e) {
    errEl.textContent = e.message;
    errEl.style.display = 'block';
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const loginVisible = document.getElementById('form-login')?.style.display !== 'none';
    const regVisible = document.getElementById('form-registro')?.style.display !== 'none';
    if (loginVisible) hacerLogin();
    else if (regVisible) hacerRegistro();
  }
});
