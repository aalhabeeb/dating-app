/* ── FlameDate - Tinder-style Dating App ── */

const API = '';
let token = localStorage.getItem('token');
let currentUser = null;
let profiles = [];
let currentCardIndex = 0;

// ── Color palette for profile avatars ──
const COLORS = [
  ['#667eea','#764ba2'],['#f093fb','#f5576c'],['#4facfe','#00f2fe'],
  ['#43e97b','#38f9d7'],['#fa709a','#fee140'],['#a18cd1','#fbc2eb'],
  ['#fccb90','#d57eeb'],['#e0c3fc','#8ec5fc'],['#f5576c','#ff6b6b'],
];

function getColor(name) {
  const i = (name || 'A').charCodeAt(0) % COLORS.length;
  return COLORS[i];
}

// ══════════════════════════════════════════
//  API HELPERS
// ══════════════════════════════════════════

async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  if (res.status === 401) { logout(); throw new Error('Sessie verlopen'); }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Er ging iets mis');
  return data;
}

async function apiForm(path, body) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method: 'POST', headers,
    body: new URLSearchParams(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Er ging iets mis');
  return data;
}

// ══════════════════════════════════════════
//  AUTH
// ══════════════════════════════════════════

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab').forEach((t, i) => {
    t.classList.toggle('active', (tab === 'login' ? i === 0 : i === 1));
  });
  document.getElementById('loginForm').style.display = tab === 'login' ? '' : 'none';
  document.getElementById('registerForm').style.display = tab === 'register' ? '' : 'none';
  document.getElementById('authError').classList.remove('show');
}

async function handleLogin(e) {
  e.preventDefault();
  const errEl = document.getElementById('authError');
  errEl.classList.remove('show');
  try {
    const data = await apiForm('/api/auth/login', {
      username: document.getElementById('loginEmail').value,
      password: document.getElementById('loginPassword').value,
    });
    token = data.access_token;
    localStorage.setItem('token', token);
    await loadApp();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.add('show');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const errEl = document.getElementById('authError');
  errEl.classList.remove('show');
  try {
    const data = await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value,
      }),
    });
    token = data.access_token;
    localStorage.setItem('token', token);
    await loadApp();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.add('show');
  }
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem('token');
  showOnly('authScreen');
}

// ══════════════════════════════════════════
//  PROFILE SETUP
// ══════════════════════════════════════════

async function handleSetup(e) {
  e.preventDefault();
  const errEl = document.getElementById('setupError');
  errEl.classList.remove('show');
  try {
    await api('/api/profiles/', {
      method: 'POST',
      body: JSON.stringify({
        display_name: document.getElementById('setupName').value,
        age: parseInt(document.getElementById('setupAge').value),
        gender: document.getElementById('setupGender').value,
        city: document.getElementById('setupCity').value,
        bio: document.getElementById('setupBio').value,
      }),
    });
    await loadApp();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.add('show');
  }
}

// ══════════════════════════════════════════
//  SCREENS
// ══════════════════════════════════════════

function showOnly(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function showScreen(name) {
  const map = { main: 'mainScreen', matches: 'matchesScreen', profile: 'profileScreen' };
  showOnly(map[name]);
  // Update nav active state in new screen
  const screen = document.getElementById(map[name]);
  screen.querySelectorAll('.nav-item').forEach((btn, i) => {
    const tabs = ['main', 'matches', 'profile'];
    btn.classList.toggle('active', tabs[i] === name);
  });
  if (name === 'matches') loadMatches();
  if (name === 'profile') renderProfile();
}

// ══════════════════════════════════════════
//  CARDS / SWIPING
// ══════════════════════════════════════════

async function loadProfiles() {
  try {
    profiles = await api('/api/profiles/?limit=50');
    currentCardIndex = 0;
    renderCards();
  } catch { profiles = []; renderCards(); }
}

function renderCards() {
  const stack = document.getElementById('cardStack');
  const noCards = document.getElementById('noCards');
  const actions = document.getElementById('swipeActions');
  stack.innerHTML = '';

  const remaining = profiles.slice(currentCardIndex);
  if (remaining.length === 0) {
    noCards.style.display = '';
    actions.style.display = 'none';
    return;
  }
  noCards.style.display = 'none';
  actions.style.display = '';

  // Show up to 3 stacked cards
  const show = remaining.slice(0, 3).reverse();
  show.forEach((p, i) => {
    const isTop = i === show.length - 1;
    const card = createCard(p, isTop, show.length - 1 - i);
    stack.appendChild(card);
  });
}

function createCard(profile, isTop, stackIndex) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.transform = `scale(${1 - stackIndex * 0.04}) translateY(${stackIndex * 8}px)`;
  card.style.zIndex = 10 - stackIndex;

  const [c1, c2] = getColor(profile.display_name);
  const initial = (profile.display_name || '?')[0].toUpperCase();

  card.innerHTML = `
    <div class="card-photo" style="background:linear-gradient(135deg,${c1},${c2})">
      ${profile.photo_url
        ? `<img src="${profile.photo_url}" alt="${profile.display_name}" onerror="this.remove()">`
        : `<span class="initial">${initial}</span>`}
      <div class="card-gradient"></div>
      <div class="card-info">
        <h3>${esc(profile.display_name)} <span>${profile.age}</span></h3>
        ${profile.city ? `<div class="city">📍 ${esc(profile.city)}</div>` : ''}
        ${profile.bio ? `<div class="bio">${esc(profile.bio)}</div>` : ''}
      </div>
    </div>
    <div class="card-stamp like">LIKE</div>
    <div class="card-stamp nope">NOPE</div>
  `;

  card.dataset.userId = profile.user_id;

  if (isTop) initSwipeGesture(card);
  return card;
}

function initSwipeGesture(card) {
  let startX = 0, startY = 0, currentX = 0, isDragging = false;

  function onStart(e) {
    isDragging = true;
    const point = e.touches ? e.touches[0] : e;
    startX = point.clientX;
    startY = point.clientY;
    card.style.transition = 'none';
  }

  function onMove(e) {
    if (!isDragging) return;
    const point = e.touches ? e.touches[0] : e;
    currentX = point.clientX - startX;
    const rotate = currentX * 0.08;
    card.style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;

    const likeStamp = card.querySelector('.card-stamp.like');
    const nopeStamp = card.querySelector('.card-stamp.nope');
    likeStamp.style.opacity = Math.max(0, currentX / 100);
    nopeStamp.style.opacity = Math.max(0, -currentX / 100);
  }

  function onEnd() {
    if (!isDragging) return;
    isDragging = false;
    card.style.transition = 'transform 0.4s ease-out, opacity 0.4s';

    if (Math.abs(currentX) > 100) {
      const direction = currentX > 0 ? 'like' : 'dislike';
      flyOut(card, direction);
    } else {
      card.style.transform = '';
      card.querySelector('.card-stamp.like').style.opacity = 0;
      card.querySelector('.card-stamp.nope').style.opacity = 0;
    }
    currentX = 0;
  }

  card.addEventListener('mousedown', onStart);
  card.addEventListener('touchstart', onStart, { passive: true });
  document.addEventListener('mousemove', onMove);
  document.addEventListener('touchmove', onMove, { passive: true });
  document.addEventListener('mouseup', onEnd);
  document.addEventListener('touchend', onEnd);

  card._cleanup = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('touchmove', onMove);
    document.removeEventListener('mouseup', onEnd);
    document.removeEventListener('touchend', onEnd);
  };
}

function flyOut(card, direction) {
  const x = direction === 'like' ? 600 : -600;
  card.style.transform = `translateX(${x}px) rotate(${x * 0.08}deg)`;
  card.style.opacity = '0';

  if (card._cleanup) card._cleanup();

  const userId = card.dataset.userId;
  doSwipe(userId, direction);

  setTimeout(() => {
    currentCardIndex++;
    renderCards();
  }, 300);
}

function swipeButton(action) {
  const stack = document.getElementById('cardStack');
  const topCard = stack.lastElementChild;
  if (!topCard) return;
  flyOut(topCard, action);
}

async function doSwipe(userId, action) {
  try {
    await api('/api/matches/swipe', {
      method: 'POST',
      body: JSON.stringify({ swiped_id: userId, action }),
    });

    if (action === 'like') {
      // Check if it was a match by fetching matches
      const matches = await api('/api/matches/');
      const justMatched = matches.find(m =>
        m.user1_id === userId || m.user2_id === userId
      );
      if (justMatched) {
        const name = justMatched.matched_profile?.display_name || 'Iemand';
        showMatchPopup(name);
      }
    }
  } catch (err) {
    console.log('Swipe error:', err.message);
  }
}

// ══════════════════════════════════════════
//  MATCHES
// ══════════════════════════════════════════

async function loadMatches() {
  const list = document.getElementById('matchList');
  try {
    const matches = await api('/api/matches/');
    if (matches.length === 0) {
      list.innerHTML = `<div class="no-matches"><div class="emoji">💫</div><h3>Nog geen matches</h3><p>Blijf swipen om je eerste match te maken!</p></div>`;
      return;
    }
    list.innerHTML = matches.map(m => {
      const p = m.matched_profile;
      const [c1, c2] = getColor(p.display_name);
      const initial = (p.display_name || '?')[0].toUpperCase();
      return `
        <div class="match-item">
          <div class="match-avatar" style="background:linear-gradient(135deg,${c1},${c2})">${initial}</div>
          <div class="match-info">
            <h4>${esc(p.display_name)}, ${p.age}</h4>
            <p>${p.city ? '📍 ' + esc(p.city) : ''} ${p.bio ? '· ' + esc(p.bio.substring(0, 50)) : ''}</p>
          </div>
        </div>
      `;
    }).join('');
  } catch {
    list.innerHTML = '<div class="no-matches"><p>Kon matches niet laden</p></div>';
  }
}

// ══════════════════════════════════════════
//  PROFILE
// ══════════════════════════════════════════

function renderProfile() {
  if (!currentUser) return;
  const card = document.getElementById('profileCard');
  const p = currentUser;
  const [c1, c2] = getColor(p.display_name);
  const initial = (p.display_name || '?')[0].toUpperCase();
  const genderLabel = {male:'Man', female:'Vrouw', non_binary:'Non-binair', other:'Anders'}[p.gender] || p.gender;

  card.innerHTML = `
    <div class="profile-photo" style="background:linear-gradient(135deg,${c1},${c2})">
      ${initial}
    </div>
    <div class="profile-details">
      <h2>${esc(p.display_name)}, ${p.age}</h2>
      <div class="meta">${genderLabel}${p.city ? ' · 📍 ' + esc(p.city) : ''}</div>
      ${p.bio ? `<div class="bio-text">${esc(p.bio)}</div>` : ''}
    </div>
  `;
}

// ══════════════════════════════════════════
//  MATCH POPUP
// ══════════════════════════════════════════

function showMatchPopup(name) {
  document.getElementById('matchName').textContent = `Jij en ${name} vinden elkaar leuk!`;
  document.getElementById('matchPopup').classList.add('show');
}

function closeMatchPopup() {
  document.getElementById('matchPopup').classList.remove('show');
}

// ══════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════

async function loadApp() {
  if (!token) { showOnly('authScreen'); return; }

  try {
    currentUser = await api('/api/profiles/me');
    showOnly('mainScreen');
    await loadProfiles();
  } catch (err) {
    if (err.message.includes('niet gevonden') || err.message.includes('Not Found')) {
      showOnly('setupScreen');
    } else {
      logout();
    }
  }
}

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

// Start
loadApp();
