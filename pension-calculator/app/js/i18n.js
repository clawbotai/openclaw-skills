// i18n.js — Sistema de internacionalización (Español / English)

const TRANSLATIONS = {
  es: {
    // Header
    'app.title': 'Calculadora Pensional',
    'app.subtitle': 'Régimen de Prima Media • Colombia',
    'app.startOver': '← Inicio',

    // Welcome
    'welcome.title': 'Calcule su Pensión',
    'welcome.desc': 'Analice su historia laboral de Colpensiones y conozca su proyección pensional bajo la Ley 797 de 2003',
    'welcome.cedula': 'Número de Cédula',
    'welcome.cedulaPlaceholder': 'Ingrese su número de cédula',
    'welcome.continue': 'Continuar',
    'welcome.privacy': 'Su cédula se usa como contraseña para descifrar el PDF de Colpensiones.',
    'welcome.noStorage': 'No almacenamos ningún dato — todo se procesa en su navegador.',

    // Upload
    'upload.title': 'Cargue su documento',
    'upload.desc': 'Suba el PDF o Excel de su historia laboral de Colpensiones',
    'upload.drop': 'Arrastre su archivo aquí',
    'upload.click': 'o haga clic para seleccionar',
    'upload.formats': 'PDF (protegido con cédula) o Excel • Máx. 20MB',
    'upload.back': '← Cambiar cédula',

    // Loading
    'loading.decrypting': 'Descifrando documento...',
    'loading.analyzing': 'Analizando historia laboral...',
    'loading.local': 'Todo se procesa localmente en su navegador',

    // Terms
    'terms.title': 'Términos de Servicio',
    'terms.legal': 'AVISO LEGAL IMPORTANTE',
    'terms.p1': 'Esta herramienta es un estimador informativo y NO constituye asesoría legal, financiera ni pensional certificada.',
    'terms.p2': 'Los resultados son estimaciones basadas en la información extraída de su documento de Colpensiones y las fórmulas establecidas en la Ley 797 de 2003.',
    'terms.p3': 'Toda la información se procesa exclusivamente en su navegador. No almacenamos, transmitimos ni recopilamos sus datos personales.',
    'terms.p4': 'Los valores de IPC utilizados para indexación son aproximaciones. Los resultados deben tomarse como referencia, no como liquidación definitiva.',
    'terms.p5': 'Para decisiones importantes sobre su pensión, consulte con un abogado laboralista o asesor pensional certificado.',
    'terms.p6': 'No nos hacemos responsables por decisiones tomadas con base en los resultados de esta herramienta.',
    'terms.p7': 'Al continuar, usted acepta que comprende la naturaleza estimativa de esta herramienta.',
    'terms.checkbox': 'He leído y acepto los términos de servicio',
    'terms.accept': 'Acepto y Continuar',

    // Free results
    'free.totalWeeks': 'Total Semanas Cotizadas',
    'free.weeks': 'Semanas',
    'free.verified': '✓ Verificado',
    'free.estimate': '⚠ Estimación',
    'free.age': 'Su edad actual',
    'free.gender': 'Género',
    'free.genderM': 'Masculino (62 años)',
    'free.genderF': 'Femenino (57 años)',
    'free.employers': 'Historial de Empleadores',
    'free.noEmployers': 'No se encontraron empleadores',
    'free.pensionEstimate': 'Mesada Pensional Estimada',
    'free.premium': '🔒 Contenido Premium',
    'free.unlock': 'Desbloquee el reporte completo',
    'free.unlockBtn': 'Desbloquear Reporte • $350.000 COP',
    'free.lastSalary': 'Último salario',
    'free.sem': 'sem.',

    // Paywall
    'pay.title': 'Desbloquear Reporte Completo',
    'pay.desc': 'Acceda a todos los cálculos detallados de su pensión',
    'pay.includes': 'Incluye:',
    'pay.item1': 'Mesada pensional estimada (IBL detallado)',
    'pay.item2': 'Tasa de reemplazo con desglose',
    'pay.item3': 'Estado de elegibilidad y fecha proyectada',
    'pay.item4': 'Buscador de Meta (pensión objetivo)',
    'pay.item5': 'Calculadora de carga total (independientes)',
    'pay.item6': 'Indemnización sustitutiva (si aplica)',
    'pay.price': '$350.000',
    'pay.currency': 'COP',
    'pay.oneTime': 'Pago único — acceso inmediato',
    'pay.button': '💳 Pagar con MercadoPago',
    'pay.mvpNote': '(MVP: el pago se simula al hacer clic)',
    'pay.back': '← Volver a resultados gratuitos',

    // Dashboard
    'dash.pensionTitle': 'Su Mesada Pensional Estimada',
    'dash.monthly': 'mensual',
    'dash.iblTitle': 'Ingreso Base de Liquidación',
    'dash.method': 'Método',
    'dash.last10': 'Últimos 10 años',
    'dash.lifetime': 'Vida laboral',
    'dash.rateTitle': 'Tasa de Reemplazo',
    'dash.baseRate': 'Tasa base',
    'dash.weekBonus': 'Bonificación semanas',
    'dash.cotizacion': 'Cotización',
    'dash.weeksLabel': 'Semanas',
    'dash.monthsLabel': 'Meses con aportes',
    'dash.eligTitle': 'Elegibilidad',
    'dash.eligible': '✓ Cumple requisitos',
    'dash.notEligible': '⏳ Aún no cumple',
    'dash.weeksLeft': 'semanas faltantes',
    'dash.yearsLeft': 'años para la edad',
    'dash.projected': 'Fecha proyectada',
    'dash.indemnTitle': '⚠ Indemnización Sustitutiva',
    'dash.indemnDesc': 'Si no alcanza las 1.300 semanas, puede solicitar una devolución por:',

    // Goal Seeker
    'goal.title': '🎯 Buscador de Meta',
    'goal.desc': '¿Cuánto debe cotizar para alcanzar su pensión objetivo?',
    'goal.target': 'Mesada objetivo (COP)',
    'goal.calculate': 'Calcular',
    'goal.year': 'año',
    'goal.years': 'años',
    'goal.extraWeeks': 'semanas extra',
    'goal.missingWeeks': 'semanas faltantes',
    'goal.requiredIBC': 'IBC mensual requerido',
    'goal.monthlyPayment': 'Aporte mensual',
    'goal.pension': 'Pensión',
    'goal.notFeasible': '⚠ Excede 25 SMMLV — no factible',

    // Burden
    'burden.title': '💰 Calculadora de Carga Total',
    'burden.desc': 'Costo real mensual para independientes',
    'burden.ibc': 'IBC mensual (COP)',
    'burden.calculate': 'Calcular',
    'burden.pension': 'Pensión (16%)',
    'burden.health': 'Salud (12.5%)',
    'burden.arl': 'ARL Nivel I (0.522%)',
    'burden.total': 'TOTAL MENSUAL',
    'burden.ofIBC': 'del IBC',

    // Footer
    'footer.disclaimer': 'Estimación basada en Ley 797 de 2003 • No constituye asesoría legal',
    'footer.local': 'Todos los cálculos se realizan localmente en su navegador',

    // Errors
    'err.cedulaInvalid': 'Ingrese un número de cédula válido (5-15 dígitos)',
    'err.passwordWrong': 'Contraseña incorrecta. Verifique que su número de cédula sea correcto.',
    'err.fileError': 'Error al procesar el documento',
    'err.termsRequired': 'Debe aceptar los términos de servicio para continuar',
    'err.minSMMLV': 'El valor mínimo es 1 SMMLV',

    // Language toggle
    'lang.toggle': 'English'
  },
  en: {
    'app.title': 'Pension Calculator',
    'app.subtitle': 'Average Premium Regime • Colombia',
    'app.startOver': '← Start Over',

    'welcome.title': 'Calculate Your Pension',
    'welcome.desc': 'Analyze your Colpensiones work history and view your pension projection under Law 797 of 2003',
    'welcome.cedula': 'ID Number (Cédula)',
    'welcome.cedulaPlaceholder': 'Enter your cédula number',
    'welcome.continue': 'Continue',
    'welcome.privacy': 'Your cédula is used as the password to decrypt the Colpensiones PDF.',
    'welcome.noStorage': 'We store no data — everything is processed in your browser.',

    'upload.title': 'Upload Your Document',
    'upload.desc': 'Upload your Colpensiones work history PDF or Excel file',
    'upload.drop': 'Drag your file here',
    'upload.click': 'or click to select',
    'upload.formats': 'PDF (password-protected with cédula) or Excel • Max 20MB',
    'upload.back': '← Change cédula',

    'loading.decrypting': 'Decrypting document...',
    'loading.analyzing': 'Analyzing work history...',
    'loading.local': 'Everything is processed locally in your browser',

    'terms.title': 'Terms of Service',
    'terms.legal': 'IMPORTANT LEGAL NOTICE',
    'terms.p1': 'This tool is an informational estimator and does NOT constitute certified legal, financial, or pension advice.',
    'terms.p2': 'Results are estimates based on information extracted from your Colpensiones document and formulas from Law 797 of 2003.',
    'terms.p3': 'All information is processed exclusively in your browser. We do not store, transmit, or collect your personal data.',
    'terms.p4': 'CPI (IPC) values used for indexation are approximations. Results should be used as reference, not as a definitive settlement.',
    'terms.p5': 'For important pension decisions, consult with a certified labor attorney or pension advisor.',
    'terms.p6': 'We are not responsible for decisions made based on this tool\'s results.',
    'terms.p7': 'By continuing, you accept that you understand the estimative nature of this tool.',
    'terms.checkbox': 'I have read and accept the terms of service',
    'terms.accept': 'Accept & Continue',

    'free.totalWeeks': 'Total Weeks Contributed',
    'free.weeks': 'Weeks',
    'free.verified': '✓ Verified',
    'free.estimate': '⚠ Estimate',
    'free.age': 'Your current age',
    'free.gender': 'Gender',
    'free.genderM': 'Male (age 62)',
    'free.genderF': 'Female (age 57)',
    'free.employers': 'Employer History',
    'free.noEmployers': 'No employers found',
    'free.pensionEstimate': 'Estimated Monthly Pension',
    'free.premium': '🔒 Premium Content',
    'free.unlock': 'Unlock the full report',
    'free.unlockBtn': 'Unlock Report • $350,000 COP',
    'free.lastSalary': 'Last salary',
    'free.sem': 'wks.',

    'pay.title': 'Unlock Full Report',
    'pay.desc': 'Access all detailed pension calculations',
    'pay.includes': 'Includes:',
    'pay.item1': 'Estimated monthly pension (detailed IBL)',
    'pay.item2': 'Replacement rate breakdown',
    'pay.item3': 'Eligibility status & projected date',
    'pay.item4': 'Goal Finder (target pension)',
    'pay.item5': 'Full burden calculator (freelancers)',
    'pay.item6': 'Substitute indemnification (if applicable)',
    'pay.price': '$350,000',
    'pay.currency': 'COP',
    'pay.oneTime': 'One-time payment — instant access',
    'pay.button': '💳 Pay with MercadoPago',
    'pay.mvpNote': '(MVP: payment is simulated on click)',
    'pay.back': '← Back to free results',

    'dash.pensionTitle': 'Your Estimated Monthly Pension',
    'dash.monthly': 'monthly',
    'dash.iblTitle': 'Base Settlement Income (IBL)',
    'dash.method': 'Method',
    'dash.last10': 'Last 10 years',
    'dash.lifetime': 'Lifetime average',
    'dash.rateTitle': 'Replacement Rate',
    'dash.baseRate': 'Base rate',
    'dash.weekBonus': 'Extra weeks bonus',
    'dash.cotizacion': 'Contributions',
    'dash.weeksLabel': 'Weeks',
    'dash.monthsLabel': 'Months contributed',
    'dash.eligTitle': 'Eligibility',
    'dash.eligible': '✓ Meets requirements',
    'dash.notEligible': '⏳ Not yet eligible',
    'dash.weeksLeft': 'weeks remaining',
    'dash.yearsLeft': 'years to required age',
    'dash.projected': 'Projected date',
    'dash.indemnTitle': '⚠ Substitute Indemnification',
    'dash.indemnDesc': 'If you don\'t reach 1,300 weeks, you can request a lump-sum refund of:',

    'goal.title': '🎯 Goal Finder',
    'goal.desc': 'How much must you contribute to reach your target pension?',
    'goal.target': 'Target pension (COP)',
    'goal.calculate': 'Calculate',
    'goal.year': 'year',
    'goal.years': 'years',
    'goal.extraWeeks': 'extra weeks',
    'goal.missingWeeks': 'weeks short',
    'goal.requiredIBC': 'Required monthly IBC',
    'goal.monthlyPayment': 'Monthly payment',
    'goal.pension': 'Pension',
    'goal.notFeasible': '⚠ Exceeds 25 SMMLV — not feasible',

    'burden.title': '💰 Full Burden Calculator',
    'burden.desc': 'True monthly cost for freelancers/independents',
    'burden.ibc': 'Monthly IBC (COP)',
    'burden.calculate': 'Calculate',
    'burden.pension': 'Pension (16%)',
    'burden.health': 'Health (12.5%)',
    'burden.arl': 'ARL Level I (0.522%)',
    'burden.total': 'MONTHLY TOTAL',
    'burden.ofIBC': 'of IBC',

    'footer.disclaimer': 'Estimate based on Law 797 of 2003 • Not legal advice',
    'footer.local': 'All calculations are performed locally in your browser',

    'err.cedulaInvalid': 'Enter a valid cédula number (5-15 digits)',
    'err.passwordWrong': 'Incorrect password. Verify your cédula number is correct.',
    'err.fileError': 'Error processing document',
    'err.termsRequired': 'You must accept the terms of service to continue',
    'err.minSMMLV': 'Minimum value is 1 SMMLV',

    'lang.toggle': 'Español'
  }
};

let currentLang = 'es';

function t(key) {
  return (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) || key;
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('pension-lang', lang);
  applyTranslations();
}

function toggleLanguage() {
  setLanguage(currentLang === 'es' ? 'en' : 'es');
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = t(key);
    if (el.tagName === 'INPUT' && el.type !== 'checkbox') {
      el.placeholder = text;
    } else {
      el.textContent = text;
    }
  });
  // Update lang toggle button
  const btn = document.getElementById('btn-lang');
  if (btn) btn.textContent = t('lang.toggle');
}

// Initialize from localStorage
(function() {
  const saved = localStorage.getItem('pension-lang');
  if (saved && TRANSLATIONS[saved]) currentLang = saved;
})();
