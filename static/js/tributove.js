/**
 * TributoVE - Lógica JS principal
 * Manejo de Modo Claro/Oscuro, Toasts, Sidebar y Sincronización
 */

// 1. Gestión de Tema Claro / Oscuro
(function () {
  function getTemaGuardado() {
    return localStorage.getItem('tv-theme') || 'dark'; // Por defecto estilo Dashboard oscuro
  }

  window.aplicarTema = function (tema) {
    document.documentElement.setAttribute('data-bs-theme', tema);
    localStorage.setItem('tv-theme', tema);

    // Actualizar icono de todos los toggles en la página
    var icons = document.querySelectorAll('.theme-toggle-icon');
    icons.forEach(function (icon) {
      if (tema === 'dark') {
        icon.className = 'bi bi-moon-stars-fill theme-toggle-icon text-warning';
      } else {
        icon.className = 'bi bi-sun-fill theme-toggle-icon text-warning';
      }
    });

    // Enviar evento al iframe de cálculo si existe en la vista
    var frame = document.getElementById('moduloFrame');
    if (frame && frame.contentWindow) {
      try {
        frame.contentWindow.postMessage({ type: 'tv-theme-change', theme: tema }, '*');
      } catch (e) {}
    }
  };

  // Inicializar tema inmediatamente
  var temaInicial = getTemaGuardado();
  document.documentElement.setAttribute('data-bs-theme', temaInicial);
})();

document.addEventListener('DOMContentLoaded', function () {
  // Inicializar tema en UI
  var temaActual = localStorage.getItem('tv-theme') || 'dark';
  window.aplicarTema(temaActual);

  // Toggle buttons
  var toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var actual = document.documentElement.getAttribute('data-bs-theme') || 'dark';
      var nuevo = actual === 'dark' ? 'light' : 'dark';
      window.aplicarTema(nuevo);
    });
  });

  // 2. Inicializar Toasts de Bootstrap
  var toastElements = document.querySelectorAll('.toast');
  toastElements.forEach(function (toastEl) {
    var toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
    toast.show();
  });

  // 3. Control del Sidebar en móviles
  var toggleBtn = document.getElementById('sidebarToggle');
  var sidebar = document.getElementById('appSidebar');
  var backdrop = document.getElementById('sidebarBackdrop');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('show');
    if (backdrop) backdrop.classList.add('show');
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      if (sidebar && sidebar.classList.contains('show')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  // 3.1 Buscador rápido del Sidebar y atajo Cmd/Ctrl + K
  var searchInput = document.getElementById('sidebarSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      var q = this.value.trim().toLowerCase();
      var navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
      var headings = document.querySelectorAll('.sidebar-nav .sidebar-heading');

      navLinks.forEach(function(link) {
        var txt = link.textContent.trim().toLowerCase();
        if (!q || txt.indexOf(q) !== -1) {
          link.style.display = 'flex';
        } else {
          link.style.display = 'none';
        }
      });

      headings.forEach(function(h) {
        h.style.display = q ? 'none' : 'block';
      });
    });

    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSidebar();
        searchInput.focus();
        searchInput.select();
      }
    });
  }

  // 4. Sincronización de tema y dimensionamiento al cargar el iframe
  var iframe = document.getElementById('moduloFrame');
  if (iframe) {
    var resizeIframe = function () {
      try {
        if (iframe.contentWindow && iframe.contentDocument) {
          var doc = iframe.contentDocument;
          var h = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight);
          if (h > 400) {
            iframe.style.height = (h + 30) + 'px';
          }
        }
      } catch (e) {}
    };

    iframe.addEventListener('load', function () {
      var t = document.documentElement.getAttribute('data-bs-theme') || 'dark';
      try {
        iframe.contentWindow.postMessage({ type: 'tv-theme-change', theme: t }, '*');
      } catch (e) {}
      setTimeout(resizeIframe, 300);
      setTimeout(resizeIframe, 1200);
    });

    window.addEventListener('resize', resizeIframe);
  }

  // 5. Listener para postMessage de los módulos en iframes (estados y UX)
  window.addEventListener('message', function (ev) {
    var data = ev.data;
    if (!data || data.type !== 'ux-status') return;

    var urlEstado = window.TV_URL_ESTADO;
    var csrfToken = window.TV_CSRF;

    if (!urlEstado || !csrfToken) return;

    fetch(urlEstado, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        modulo: data.mod,
        estado: data.st ? data.st.e : 'sin',
        detalle: data.st ? data.st.d : ''
      })
    })
    .catch(function(err) {
      console.warn('Error enviando estado de módulo:', err);
    });
  });

  // 6. Progressive Web App (PWA) - Registro de Service Worker e Instalación
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(function (reg) {
        console.log('[TributoVE PWA] Service Worker registrado con éxito. Scope:', reg.scope);
      })
      .catch(function (err) {
        console.warn('[TributoVE PWA] Error al registrar Service Worker:', err);
      });
  }

  var deferredInstallPrompt = null;
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredInstallPrompt = e;
    var pwaBtn = document.getElementById('pwaInstallBtn');
    var sidebarPwaContainer = document.getElementById('sidebarPwaInstallContainer');
    if (pwaBtn) pwaBtn.classList.remove('d-none');
    if (sidebarPwaContainer) sidebarPwaContainer.classList.remove('d-none');
  });

  function triggerPwaInstall() {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        var pwaBtn = document.getElementById('pwaInstallBtn');
        var sidebarPwaContainer = document.getElementById('sidebarPwaInstallContainer');
        if (pwaBtn) pwaBtn.classList.add('d-none');
        if (sidebarPwaContainer) sidebarPwaContainer.classList.add('d-none');
      }
      deferredInstallPrompt = null;
    });
  }

  var pwaInstallBtn = document.getElementById('pwaInstallBtn');
  if (pwaInstallBtn) pwaInstallBtn.addEventListener('click', triggerPwaInstall);
  var sidebarPwaInstallBtn = document.getElementById('sidebarPwaInstallBtn');
  if (sidebarPwaInstallBtn) sidebarPwaInstallBtn.addEventListener('click', triggerPwaInstall);
});
