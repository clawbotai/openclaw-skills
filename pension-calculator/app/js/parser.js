// parser.js — Extracción de datos desde PDF y Excel de Colpensiones

/**
 * Extraer texto de PDF protegido con contraseña usando pdf.js
 * @param {ArrayBuffer} buffer - contenido del archivo
 * @param {string} password - cédula del usuario
 * @returns {Promise<string>} texto completo del PDF
 */
async function extractPDFText(buffer, password) {
  const pdfjsLib = window['pdfjs-dist/build/pdf'];
  const loadingTask = pdfjsLib.getDocument({ data: buffer, password });
  const pdf = await loadingTask.promise;
  let fullText = '';
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const pageText = content.items.map(item => item.str).join(' ');
    fullText += pageText + '\n';
  }
  return fullText;
}

/**
 * Extraer texto de archivo Excel usando SheetJS
 * @param {ArrayBuffer} buffer
 * @returns {string} texto concatenado de todas las hojas
 */
function extractExcelText(buffer) {
  const workbook = XLSX.read(buffer, { type: 'array' });
  let fullText = '';
  workbook.SheetNames.forEach(name => {
    const sheet = workbook.Sheets[name];
    const csv = XLSX.utils.sheet_to_csv(sheet, { FS: '\t' });
    fullText += csv + '\n';
  });
  return fullText;
}

/**
 * Resultado del parsing del documento de Colpensiones
 * @typedef {Object} ParsedDocument
 * @property {Array<Employer>} employers - Lista de empleadores
 * @property {Array<DetailRecord>} details - Detalle mensual de aportes
 * @property {number|null} totalWeeksReported - Semanas reportadas en Item [26]
 * @property {string} rawText - Texto crudo extraído
 */

/**
 * @typedef {Object} Employer
 * @property {string} nit - NIT del aportante
 * @property {string} name - Nombre del aportante
 * @property {Date} startDate - Fecha de inicio
 * @property {Date} endDate - Fecha de fin
 * @property {number} lastSalary - Último salario reportado
 * @property {number} weeks - Semanas cotizadas
 */

/**
 * @typedef {Object} DetailRecord
 * @property {number} year
 * @property {number} month
 * @property {number} ibc - Ingreso Base de Cotización
 * @property {number} days - Días cotizados
 * @property {string} employerNit
 */

/**
 * Parsear el texto extraído del documento de Colpensiones
 * @param {string} text
 * @returns {ParsedDocument}
 */
function parseColpensionesText(text) {
  const result = {
    employers: [],
    details: [],
    totalWeeksReported: null,
    rawText: text
  };

  // Extraer Item [26] - TOTAL SEMANAS
  const weeksMatch = text.match(/(?:\[26\]|TOTAL\s+SEMANAS)[:\s]*([0-9.,]+)/i);
  if (weeksMatch) {
    result.totalWeeksReported = parseFloat(weeksMatch[1].replace(',', '.'));
  }

  // Parsear tabla de empleadores
  // Buscar patrones: NIT, Nombre, Desde, Hasta, Último Salario, Semanas
  const employerPatterns = extractEmployerTable(text);
  if (employerPatterns.length > 0) {
    result.employers = employerPatterns;
  }

  // Parsear detalle mensual de IBC
  const detailRecords = extractDetailTable(text);
  if (detailRecords.length > 0) {
    result.details = detailRecords;
  }

  return result;
}

/**
 * Extraer tabla de empleadores del texto
 */
function extractEmployerTable(text) {
  const employers = [];
  const lines = text.split('\n');

  // Patrón: buscar líneas con formato de fecha DD/MM/YYYY
  const datePattern = /(\d{2}\/\d{2}\/\d{4})/g;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const dates = line.match(datePattern);

    if (dates && dates.length >= 2) {
      // Intentar extraer NIT (número largo), nombre, fechas, salario, semanas
      const nitMatch = line.match(/(\d{6,12})/);
      const numberMatches = line.match(/[\d.,]+/g);

      if (nitMatch && numberMatches) {
        const startDate = parseColDate(dates[0]);
        const endDate = parseColDate(dates[1]);

        if (startDate && endDate) {
          // Buscar nombre del empleador (texto entre NIT y primera fecha)
          const nitIdx = line.indexOf(nitMatch[1]);
          const dateIdx = line.indexOf(dates[0]);
          let name = '';
          if (dateIdx > nitIdx) {
            name = line.substring(nitIdx + nitMatch[1].length, dateIdx).trim();
            // Limpiar caracteres especiales
            name = name.replace(/^[\s\-–]+|[\s\-–]+$/g, '');
          }

          // Buscar salario y semanas después de las fechas
          const afterDates = line.substring(line.lastIndexOf(dates[1]) + dates[1].length);
          const nums = afterDates.match(/[\d.,]+/g) || [];

          let lastSalary = 0;
          let weeks = 0;

          if (nums.length >= 2) {
            lastSalary = parseColNumber(nums[0]);
            weeks = parseFloat(nums[nums.length - 1].replace(',', '.')) || 0;
          } else if (nums.length === 1) {
            weeks = parseFloat(nums[0].replace(',', '.')) || 0;
          }

          employers.push({
            nit: nitMatch[1],
            name: name || 'Empleador ' + (employers.length + 1),
            startDate,
            endDate,
            lastSalary,
            weeks
          });
        }
      }
    }
  }

  return employers;
}

/**
 * Extraer detalle mensual de IBC del texto
 */
function extractDetailTable(text) {
  const details = [];
  const lines = text.split('\n');

  // Buscar líneas con patrón de año/mes y valores monetarios
  for (const line of lines) {
    // Patrón: YYYY MM o MM/YYYY seguido de valores
    const periodMatch = line.match(/(\d{4})\s+(\d{1,2})/);
    const altPeriodMatch = line.match(/(\d{1,2})\/(\d{4})/);

    let year, month;
    if (periodMatch) {
      year = parseInt(periodMatch[1]);
      month = parseInt(periodMatch[2]);
    } else if (altPeriodMatch) {
      month = parseInt(altPeriodMatch[1]);
      year = parseInt(altPeriodMatch[2]);
    } else {
      continue;
    }

    if (year < 1960 || year > 2030 || month < 1 || month > 12) continue;

    // Buscar valores monetarios en la línea
    const moneyValues = line.match(/[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})?/g);
    if (moneyValues && moneyValues.length > 0) {
      // El IBC suele ser el valor más grande
      let maxVal = 0;
      let days = 30;
      for (const v of moneyValues) {
        const parsed = parseColNumber(v);
        if (parsed > maxVal && parsed > 1000) {
          maxVal = parsed;
        }
        if (parsed >= 1 && parsed <= 30 && parsed !== maxVal) {
          days = parsed;
        }
      }

      if (maxVal > 0) {
        details.push({
          year,
          month,
          ibc: maxVal,
          days,
          employerNit: ''
        });
      }
    }
  }

  return details;
}

/**
 * Procesar archivo subido (PDF o Excel)
 * @param {File} file
 * @param {string} cedula
 * @returns {Promise<ParsedDocument>}
 */
async function processFile(file, cedula) {
  const buffer = await file.arrayBuffer();
  let text;

  if (file.name.toLowerCase().endsWith('.pdf')) {
    text = await extractPDFText(buffer, cedula);
  } else if (file.name.match(/\.(xlsx?|csv)$/i)) {
    text = extractExcelText(buffer);
  } else {
    throw new Error('Formato de archivo no soportado. Use PDF o Excel.');
  }

  if (!text || text.trim().length < 50) {
    throw new Error('No se pudo extraer información del documento. Verifique que el archivo sea correcto.');
  }

  return parseColpensionesText(text);
}
