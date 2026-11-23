/**
 * TributoVE - Lógica JS principal
 * Manejo de Modo Claro/Oscuro, Toasts, Sidebar y Sincronización
 */

// 1. Gestión de Tema Claro / Oscuro (Claro Institucional por defecto, sin destellos neón)
(function () {
  function getTemaGuardado() {
    return localStorage.getItem('tv-theme-mode') || 'light';
  }

  window.aplicarTema = function (tema) {
    document.documentElement.setAttribute('data-bs-theme', tema);
    localStorage.setItem('tv-theme-mode', tema);
    localStorage.setItem('tv-theme', tema);

    // Actualizar icono de todos los toggles en la página
    var icons = document.querySelectorAll('.theme-toggle-icon');
    icons.forEach(function (icon) {
      if (tema === 'dark') {
        icon.className = 'bi bi-moon-stars-fill theme-toggle-icon';
      } else {
        icon.className = 'bi bi-sun-fill theme-toggle-icon';
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
  var temaActual = localStorage.getItem('tv-theme-mode') || 'light';
  window.aplicarTema(temaActual);

  // Toggle buttons
  var toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  toggleBtns.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var actual = document.documentElement.getAttribute('data-bs-theme') || 'light';
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

  // 3. Control del Sidebar (Escritorio colapsable + Móvil drawer)
  var toggleBtn = document.getElementById('sidebarToggle');
  var closeBtn = document.getElementById('sidebarCloseBtn');
  var sidebar = document.getElementById('appSidebar');
  var backdrop = document.getElementById('sidebarBackdrop');
  var SIDEBAR_KEY = 'tv-sidebar-collapsed';

  try {
    if (window.innerWidth >= 992 && localStorage.getItem(SIDEBAR_KEY) === '1') {
      document.body.classList.add('sidebar-collapsed');
    }
  } catch (e) {}

  function openSidebar() {
    if (window.innerWidth >= 992) {
      document.body.classList.remove('sidebar-collapsed');
      try { localStorage.setItem(SIDEBAR_KEY, '0'); } catch (e) {}
      return;
    }
    if (sidebar) sidebar.classList.add('show');
    if (backdrop) backdrop.classList.add('show');
  }

  function closeSidebar() {
    if (window.innerWidth >= 992) {
      document.body.classList.add('sidebar-collapsed');
      try { localStorage.setItem(SIDEBAR_KEY, '1'); } catch (e) {}
      return;
    }
    if (sidebar) sidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      if (window.innerWidth >= 992) {
        if (document.body.classList.contains('sidebar-collapsed')) {
          openSidebar();
        } else {
          closeSidebar();
        }
      } else {
        if (sidebar && sidebar.classList.contains('show')) {
          closeSidebar();
        } else {
          openSidebar();
        }
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      closeSidebar();
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }

  // 3.1 Atajo Cmd/Ctrl + K para el buscador del Sidebar
  var searchInput = document.getElementById('sidebarSearchInput');
  if (searchInput) {
    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSidebar();
        searchInput.focus();
        searchInput.select();
      }
    });
  }

  // 4. Sincronización de tema, animación de carga y dimensionamiento del iframe
  var iframe = document.getElementById('moduloFrame');
  var moduloOverlay = document.getElementById('moduloLoaderOverlay');
  if (iframe) {
    var hideModuloLoader = function () {
      iframe.style.opacity = '1';
      if (moduloOverlay) moduloOverlay.classList.add('is-hidden');
    };

    iframe.addEventListener('load', function () {
      var t = document.documentElement.getAttribute('data-bs-theme') || 'light';
      try {
        iframe.contentWindow.postMessage({ type: 'tv-theme-change', theme: t }, '*');
      } catch (e) {}
      hideModuloLoader();
    });

    // Respaldo por si el navegador usa caché instantánea
    setTimeout(hideModuloLoader, 3500);
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

  // Evita que modales Bootstrap queden detrás del backdrop por contextos de apilamiento (.tv-fade-in, etc.)
  document.addEventListener('show.bs.modal', function (e) {
    if (e.target && e.target.parentElement !== document.body) {
      document.body.appendChild(e.target);
    }
  });

  // 7. Sincronización de Tasa Oficial del Banco Central de Venezuela (BCV)
  window.TASA_BCV = window.TASA_BCV || { usd: 65.0, eur: 70.2 };

  function fmtVe(n, dec) {
    var num = Number(n) || 0;
    return num.toLocaleString('es-VE', {
      minimumFractionDigits: dec,
      maximumFractionDigits: dec
    });
  }

  function pintarTasaBcv(data) {
    if (!data || !data.usd) return;
    window.TASA_BCV = data;

    document.querySelectorAll('[data-bcv-usd]').forEach(function (el) {
      el.textContent = fmtVe(data.usd, 2);
    });
    document.querySelectorAll('[data-bcv-eur]').forEach(function (el) {
      el.textContent = fmtVe(data.eur, 2);
    });
    document.querySelectorAll('[data-bcv-usd-full]').forEach(function (el) {
      el.textContent = fmtVe(data.usd, 4);
    });
    document.querySelectorAll('[data-bcv-eur-full]').forEach(function (el) {
      el.textContent = fmtVe(data.eur, 4);
    });
    if (data.cop) {
      document.querySelectorAll('[data-bcv-cop-full]').forEach(function (el) {
        el.textContent = fmtVe(data.cop, 4);
      });
    }
    if (data.ves_cop) {
      document.querySelectorAll('[data-bcv-ves-cop]').forEach(function (el) {
        el.textContent = fmtVe(data.ves_cop, 2);
      });
    }
    document.querySelectorAll('[data-bcv-fecha]').forEach(function (el) {
      el.textContent = data.fecha || '';
    });
    document.querySelectorAll('[data-bcv-fuente]').forEach(function (el) {
      el.textContent = data.fuente || 'BCV';
    });

    var frame = document.getElementById('moduloFrame');
    if (frame && frame.contentWindow) {
      try {
        frame.contentWindow.postMessage({ type: 'tv-bcv-update', bcv: data }, '*');
      } catch (e) {}
    }
  }

  window.actualizarTasaBcv = function (forzar) {
    var btn = document.getElementById('btnRefreshBcv');
    var icon = document.getElementById('iconRefreshBcv');
    var labelSpan = btn ? btn.querySelector('span') : null;
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add('tv-spin-icon');
    if (forzar && labelSpan) labelSpan.textContent = 'Consultando BCV…';
    var url = '/api/tasa-bcv/' + (forzar ? '?forzar=1' : '');
    return fetch(url, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        pintarTasaBcv(data);
        if (forzar && labelSpan) {
          labelSpan.textContent = 'Tasa actualizada';
          setTimeout(function () {
            labelSpan.textContent = 'Consultar BCV en vivo';
          }, 1800);
        }
        return data;
      })
      .catch(function (err) {
        console.warn('No se pudo consultar tasa BCV:', err);
        if (forzar && labelSpan) labelSpan.textContent = 'Consultar BCV en vivo';
      })
      .finally(function () {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove('tv-spin-icon');
      });
  };

  window.aplicarTasaBcvEmpresa = function (moneda) {
    var url = '/api/tasa-bcv/?forzar=1&aplicar=' + encodeURIComponent(moneda || 'USD');
    fetch(url, { headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        pintarTasaBcv(data);
        if (data && data.empresa_actualizada) {
          window.location.reload();
        }
      })
      .catch(function (err) {
        console.warn('Error aplicando tasa BCV a la empresa:', err);
      });
  };

  window.syncInputTasaConBcv = function (moneda) {
    var inp = document.getElementById('id_tasa_nav');
    if (inp) inp.style.display = moneda === 'VES' ? 'none' : 'block';
    if (moneda === 'USD' || moneda === 'EUR' || moneda === 'COP') {
      window.rellenarInputConBcv(moneda);
    }
  };

  window.rellenarInputConBcv = function (monedaForzada) {
    var sel = document.getElementById('id_moneda_nav');
    var inp = document.getElementById('id_tasa_nav');
    if (!inp) return;
    var mon = monedaForzada || (sel ? sel.value : 'USD');
    var val = mon === 'EUR' ? window.TASA_BCV.eur : (mon === 'COP' ? window.TASA_BCV.cop : window.TASA_BCV.usd);
    if (val) {
      inp.value = Number(val).toFixed(4);
    }
  };

  // Conversor bidireccional rápido COP <-> Bolívares
  var copIn = document.getElementById('copConvCop');
  var bsIn = document.getElementById('copConvBs');
  function getCopRate() {
    var bcv = window.TASA_BCV || {};
    if (bcv.cop && Number(bcv.cop) > 0) return Number(bcv.cop);
    var usd = Number(bcv.usd) || 0;
    var usdCop = Number(bcv.usd_cop) || 4200;
    return usd > 0 ? (usd / usdCop) : 0;
  }
  if (copIn && bsIn) {
    copIn.addEventListener('input', function () {
      var v = parseFloat(copIn.value);
      var rate = getCopRate();
      if (!isNaN(v) && rate > 0) {
        bsIn.value = (v * rate).toFixed(2);
      } else {
        bsIn.value = '';
      }
    });
    bsIn.addEventListener('input', function () {
      var v = parseFloat(bsIn.value);
      var rate = getCopRate();
      if (!isNaN(v) && rate > 0) {
        copIn.value = (v / rate).toFixed(2);
      } else {
        copIn.value = '';
      }
    });
  }

  // Consulta automática no bloqueante de la tasa BCV al cargar el panel
  if (document.querySelector('[data-bcv-usd]')) {
    setTimeout(function () {
      window.actualizarTasaBcv(false);
    }, 250);
  }

  // 8. Animación de carga en botones de formularios, enlaces del menú y barra superior
  var topLoader = document.createElement('div');
  topLoader.id = 'tv-top-loader';
  document.body.appendChild(topLoader);

  function activateTopLoader() {
    topLoader.classList.remove('is-active');
    void topLoader.offsetWidth;
    topLoader.classList.add('is-active');
  }

  window.setButtonLoading = function (btn, loadingText) {
    if (!btn || btn.classList.contains('tv-btn-loading')) return;
    btn.dataset.tvOrigHtml = btn.innerHTML;
    btn.classList.add('tv-btn-loading');
    btn.disabled = true;
    var label = loadingText || btn.getAttribute('data-loading-text') || btn.textContent.trim() || 'Procesando…';
    btn.innerHTML = '<span class="tv-btn-spinner" aria-hidden="true"></span><span>' + label + '</span>';
  };

  function resetAllLoadingButtons() {
    topLoader.classList.remove('is-active');
    document.querySelectorAll('.tv-btn-loading').forEach(function (btn) {
      if (btn.dataset.tvOrigHtml) {
        btn.innerHTML = btn.dataset.tvOrigHtml;
      }
      btn.classList.remove('tv-btn-loading');
      btn.disabled = false;
    });
  }

  // Animación automática al enviar formularios
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form || form.hasAttribute('data-no-loader')) return;
    var submitBtn = e.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn && submitBtn.tagName === 'BUTTON') {
      window.setButtonLoading(submitBtn);
    }
    activateTopLoader();
  });

  // Barra de progreso superior al navegar entre módulos o páginas del sistema
  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';
    if (!href || href.startsWith('#') || href.startsWith('javascript:') || link.target === '_blank' || link.hasAttribute('download')) {
      return;
    }
    if (e.ctrlKey || e.metaKey || e.shiftKey) return;
    activateTopLoader();
  });

  // Animación sutil de entrada en el contenido principal
  var mainEl = document.querySelector('.app-content > main');
  if (mainEl) {
    mainEl.classList.add('tv-fade-in');
  }

  window.addEventListener('pageshow', resetAllLoadingButtons);
});
