/**
 * TributoVE - Motor Unificado de Reportes Formales e Impresión PDF
 * Genera automáticamente membrete corporativo, ficha del contribuyente,
 * tasa BCV de referencia y bloque de firmas en todos los módulos.
 */
(function () {
  var TITULOS_MODULO = {
    plan: {
      titulo: 'PLANIFICACIÓN FISCAL Y PROYECCIÓN TRIBUTARIA',
      subtitulo: 'Presupuesto Fiscal, Desviaciones, Riesgos y Exposición Cambiaria',
      base: 'LISLR, Código Orgánico Tributario, Ley de IVA, IGTF y Contribución de Pensiones.'
    },
    ret: {
      titulo: 'REPORTE DE RETENCIONES DE ISLR',
      subtitulo: 'Tabla Oficial de Porcentajes y Sustraendos Aplicables',
      base: 'Decreto N.° 1.808 (Reglamento Parcial de la Ley de ISLR en Materia de Retenciones).'
    },
    sanc: {
      titulo: 'ESTIMACIÓN DE SANCIONES E INTERESES MORATORIOS',
      subtitulo: 'Cuantificación de Ilícitos Formales, Materiales y Concurrencia',
      base: 'Código Orgánico Tributario (G.O.E. 6.507 / 2020), Arts. 66, 81, 82, 92, 103, 110–115.'
    },
    cal: {
      titulo: 'CRONOGRAMA DE OBLIGACIONES FISCALES SPE',
      subtitulo: 'Calendario Oficial de Sujetos Pasivos Especiales',
      base: 'Providencia Administrativa SENIAT de Calendario SPE y G.O. 470.333.'
    },
    ari: {
      titulo: 'DETERMINACIÓN DE PORCENTAJE DE RETENCIÓN AR-I',
      subtitulo: 'Estimación Anual de Remuneraciones y Retención de ISLR sobre Sueldos',
      base: 'Decreto N.° 1.808, Arts. 2–8, y Ley de ISLR (Tarifa N.° 1, Arts. 50, 59–61).'
    },
    est: {
      titulo: 'PAPEL DE TRABAJO: DECLARACIÓN ESTIMADA DE ISLR',
      subtitulo: 'Cálculo de Base Imponible (80%), Impuesto Estimado (75%) y Porciones',
      base: 'Ley de ISLR Art. 80 y Reglamento de la Ley de ISLR Arts. 156 y 158.'
    },
    igp: {
      titulo: 'DETERMINACIÓN DEL IMPUESTO A LOS GRANDES PATRIMONIOS (IGP)',
      subtitulo: 'Valoración Patrimonial Neta y Liquidación del Tributo',
      base: 'Ley Constitucional que crea el Impuesto a los Grandes Patrimonios (G.O. 41.696).'
    },
    ing: {
      titulo: 'AUDITORÍA Y SEPARACIÓN DE INGRESOS BANCARIOS',
      subtitulo: 'Conciliación de Abonos Bancarios Gravables vs. Partidas No Gravables',
      base: 'LISLR, Ley de IVA, Ley de IGTF y Código Orgánico Tributario (Deberes Formales).'
    },
    conc: {
      titulo: 'CONCILIACIÓN BANCARIA Y FISCAL MULTICUENTA',
      subtitulo: 'Cruce de Movimientos Bancarios, Retenciones IVA/ISLR y Asientos Contables',
      base: 'Normativa VEN-NIF, Providencia 000054 (IVA) y Decreto 1.808 (ISLR).'
    },
    cislr: {
      titulo: 'CONCILIACIÓN FISCAL INTEGRAL DE LA RENTA (ISLR)',
      subtitulo: 'Balance de Comprobación, Conciliación Art. 27, API, Retenciones y Dictamen',
      base: 'Ley de ISLR (Arts. 27, 173–193), Reglamento de ISLR y Normas VEN-NIF / NIC 12.'
    },
    pt: {
      titulo: 'ESTUDIO DE PRECIOS DE TRANSFERENCIA (PT-99)',
      subtitulo: 'Análisis de Partes Vinculadas, Rango Intercuartil OCDE y Análisis FAR',
      base: 'Ley de ISLR Título VII Capítulo III (Arts. 111–170) y Directrices OCDE.'
    },
    cban: {
      titulo: 'CONTROL BANCARIO Y CONCILIACIÓN DE VENTAS',
      subtitulo: 'Seguimiento de Cuentas Bancarias, Tasas BCV y Retenciones de IVA',
      base: 'Providencia Administrativa 000054 y Libros de Ventas / Compras IVA.'
    }
  };

  function getActiveTabName() {
    var selectors = [
      'nav [aria-selected="true"]',
      'nav .on',
      'nav .active',
      '.tabs [aria-selected="true"]',
      '.tabs .active',
      '#main-tabs .active'
    ];
    for (var i = 0; i < selectors.length; i++) {
      var el = document.querySelector(selectors[i]);
      if (el && el.textContent.trim()) {
        return el.textContent.trim().replace(/\s+/g, ' ');
      }
    }
    return 'Reporte General';
  }

  function ensureReportNodes() {
    if (!document.body) return;

    var hdr = document.getElementById('tv-rpt-header');
    if (!hdr) {
      hdr = document.createElement('div');
      hdr.id = 'tv-rpt-header';
      document.body.insertBefore(hdr, document.body.firstChild);
    }

    var ftr = document.getElementById('tv-rpt-footer');
    if (!ftr) {
      ftr = document.createElement('div');
      ftr.id = 'tv-rpt-footer';
      document.body.appendChild(ftr);
    }
  }

  function populateFormalReport() {
    ensureReportNodes();
    var E = window.EMPRESA || {};
    var modId = (window.UXMODID || '').toLowerCase();
    var info = TITULOS_MODULO[modId] || {
      titulo: (document.title || 'REPORTE TRIBUTARIO').toUpperCase(),
      subtitulo: 'Papel de Trabajo Fiscal · Venezuela',
      base: 'Normativa Tributaria Vigente (SENIAT / LISLR / COT).'
    };

    var bcv = E.bcv || {};
    var bcvTxt = bcv.usd ? ('USD Bs. ' + Number(bcv.usd).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) +
      ' | EUR Bs. ' + Number(bcv.eur || 0).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 4 })) : 'Referencia BCV vigente';

    var mon = E.moneda || {};
    var monTxt = mon.cod && mon.cod !== 'VES' ? (mon.cod + ' (Tasa: Bs. ' + (mon.tasa || 1) + ')') : 'Bolívares (Bs.)';
    var seccion = getActiveTabName();
    var codPt = 'PT-' + (modId ? modId.toUpperCase() : 'TVE') + '-' + new Date().getFullYear();

    var hdr = document.getElementById('tv-rpt-header');
    if (hdr) {
      hdr.innerHTML =
        '<div class="tv-rpt-top">' +
          '<div>' +
            '<div class="tv-rpt-kicker">República Bolivariana de Venezuela · Control Tributario y Fiscal</div>' +
            '<h2 class="tv-rpt-title">' + info.titulo + '</h2>' +
            '<p class="tv-rpt-subtitle">' + info.subtitulo + '</p>' +
          '</div>' +
          '<div class="tv-rpt-empbox">' +
            '<div class="tv-rpt-empname">' + (E.nombre || 'Contribuyente') + '</div>' +
            '<div class="tv-rpt-emprif">RIF: <strong>' + (E.rif || 'J-00000000-0') + '</strong> · ' + (E.condicion || 'Contribuyente') + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="tv-rpt-meta">' +
          '<span><strong>Papel de Trabajo:</strong> ' + codPt + '</span>' +
          '<span><strong>Sección:</strong> ' + seccion + '</span>' +
          '<span><strong>Moneda:</strong> ' + monTxt + '</span>' +
          '<span><strong>BCV:</strong> ' + bcvTxt + '</span>' +
          '<span><strong>Emisión:</strong> ' + new Date().toLocaleString('es-VE') + '</span>' +
        '</div>';
    }

    var ftr = document.getElementById('tv-rpt-footer');
    if (ftr) {
      ftr.innerHTML =
        '<div class="tv-rpt-legal">' +
          '<strong>Base Legal y Alcance:</strong> ' + info.base + ' ' +
          'Este papel de trabajo constituye un soporte técnico de cálculo y conciliación fiscal; valide los montos y alícuotas contra los comprobantes originales y el portal fiscal SENIAT antes de presentar la declaración definitiva.' +
        '</div>' +
        '<div class="tv-rpt-sigs">' +
          '<div><div class="tv-rpt-sigline">Elaborado por<div class="tv-rpt-sigsub">Contador Público / Administración</div></div></div>' +
          '<div><div class="tv-rpt-sigline">Revisado por<div class="tv-rpt-sigsub">Gerencia Tributaria / Auditoría</div></div></div>' +
          '<div><div class="tv-rpt-sigline">Aprobado por<div class="tv-rpt-sigsub">' + (E.nombre || 'Representante Legal') + '</div></div></div>' +
        '</div>';
    }
  }

  window.addEventListener('beforeprint', populateFormalReport);

  window.addEventListener('message', function (e) {
    if (e.data && e.data.type === 'ux-do-print') {
      populateFormalReport();
      setTimeout(function () {
        window.print();
      }, 60);
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', populateFormalReport);
  } else {
    populateFormalReport();
  }
})();
