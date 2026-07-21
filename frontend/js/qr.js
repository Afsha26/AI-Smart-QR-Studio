// QR generator module migrated to `qr-code-styling`
// Exports: QRGenerator class and a default `init` helper
import { analyzeQR, validateInput } from "./api.js";

const validationMessages = {
  invalid_url: 'Please enter a valid website URL.',
  unsupported_scheme: 'Only HTTP and HTTPS links are supported.',
  local_host: 'Localhost URLs cannot be used in QR codes.',
  invalid_email: 'Please enter a valid email address.',
  invalid_phone: 'Please enter a valid phone number.',
  empty_text: 'Please enter some text.',
  text_too_long: 'The text is too long for a QR code.',
  invalid_message: 'Please enter a valid message.',
  message_too_long: 'The message is too long.',
  invalid_sms: 'Please enter a valid SMS format.',
  invalid_whatsapp: 'Please enter a valid WhatsApp number.',
  invalid_wifi: 'Please check the WiFi configuration.',
  invalid_wifi_encryption: 'Please choose a supported WiFi encryption type.',
  invalid_wifi_password: 'Please enter a valid WiFi password.',
  empty_ssid: 'Please enter a WiFi network name.',
  invalid_vcard: 'Please enter a valid contact card.',
  invalid_coordinates: 'Please enter valid latitude and longitude values.',
  unsupported_platform: 'Please select a supported social media platform.',
  unsupported_type: 'This QR code type is not supported.',
  empty_username: 'Please enter a social media username.',
  invalid_social_username: 'Please enter a valid social media username.',
  invalid_hostname: 'Please enter a valid website hostname.',
  invalid_message: 'Please enter a valid message.',
};

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getValidationMessage(issue) {
  return validationMessages[issue] || 'An unknown validation error occurred.';
}

function updateValidationUI(result) {
  const statusEl = document.getElementById('validation-status');
  const listEl = document.getElementById('validation-list');

  if (!statusEl || !listEl) return;

  const valid = Boolean(result?.valid);
  const issues = Array.isArray(result?.issues) ? result.issues.filter(Boolean) : [];
  const normalized = result?.normalized ?? null;

  statusEl.innerHTML = valid
    ? '✔ Validation successful.'
    : '❌ Validation failed.';

  if (normalized != null && normalized !== '') {
    statusEl.innerHTML += `<br><br>Normalized value:<br>${escapeHtml(normalized)}`;
  }

  listEl.innerHTML = '';
  if (!valid) {
    issues.forEach((issue) => {
      const li = document.createElement('li');
      li.textContent = getValidationMessage(issue);
      listEl.appendChild(li);
    });
  }
}

function updateQualityUI(result) {
  const contrastEl = document.getElementById('quality-contrast');
  const sizeEl = document.getElementById('quality-size');
  const logoEl = document.getElementById('quality-logo');
  const scoreEl = document.getElementById('quality-score');
  const recommendationsEl = document.getElementById('quality-recommendations');

  if (!contrastEl || !sizeEl || !logoEl) return;

  if (result?.error) {
    contrastEl.innerHTML = 'Contrast: <span class="muted">—</span>';
    sizeEl.innerHTML = 'Module size: <span class="muted">—</span>';
    logoEl.innerHTML = 'Logo impact: <span class="muted">—</span>';
    if (scoreEl) {
      scoreEl.innerHTML = 'Overall Score: <span class="muted">—</span>';
    }
    if (recommendationsEl) {
      recommendationsEl.innerHTML = '';
      const li = document.createElement('li');
      li.textContent = 'Analysis unavailable.';
      recommendationsEl.appendChild(li);
    }
    return;
  }

  const contrast = result?.contrast || {};
  const module = result?.module || {};
  const logo = result?.logo || {};
  const recommendations = Array.isArray(result?.recommendations) ? result.recommendations.filter(Boolean) : [];

  const contrastText = contrast?.status ? `${contrast.status}${contrast.ratio ? ` (${contrast.ratio})` : ''}` : '—';
  const moduleText = module?.status || '—';
  const logoText = logo?.status || '—';
  const scoreText = result?.score != null ? `${result.score} / 100` : '—';

  contrastEl.innerHTML = `Contrast: <span class="muted">${escapeHtml(contrastText)}</span>`;
  sizeEl.innerHTML = `Module size: <span class="muted">${escapeHtml(moduleText)}</span>`;
  logoEl.innerHTML = `Logo impact: <span class="muted">${escapeHtml(logoText)}</span>`;

  if (scoreEl) {
    scoreEl.innerHTML = `Overall Score: <span class="muted">${escapeHtml(scoreText)}</span>`;
  }

  if (recommendationsEl) {
    recommendationsEl.innerHTML = '';
    if (recommendations.length) {
      recommendations.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        recommendationsEl.appendChild(li);
      });
    } else {
      const li = document.createElement('li');
      li.textContent = 'This QR code should scan reliably.';
      recommendationsEl.appendChild(li);
    }
  }
}

class QRGenerator {
  constructor(options = {}) {
    this.formSelector = options.formSelector || '#qr-form';
    this.previewSelector = options.previewSelector || '#qr-preview';
    this.previewPlaceholder = options.previewPlaceholder || '.qr-canvas-placeholder';
    this.debounceMs = options.debounceMs || 250;
    this.size = Number(options.size) || 512;
    // instance of QRCodeStyling
    this.qrCode = null;
    this.logoDataUrl = null;
    this._debounceTimer = null;

    this._onGenerated = options.onGenerated || (() => {});
  }

  init() {
    this.form = document.querySelector(this.formSelector);
    this.previewEl = document.querySelector(this.previewSelector);
    if (!this.form || !this.previewEl) return;

    this._bindElements();
    this._attachEvents();

    // create a container for the QR canvas/SVG and append QRCodeStyling once
    this._createPreviewContainer();

    // initial render
    this.generate();
  }

  _bindElements() {
    const f = this.form;
    this.typeEl = f.querySelector('#qr-type');
    this.contentEl = f.querySelector('#content');
    this.sizeEl = f.querySelector('#size');
    this.fgColorEl = f.querySelector('#fg-color');
    this.bgColorEl = f.querySelector('#bg-color');
    this.gradientEl = f.querySelector('#gradient');
    this.dotStyleEl = f.querySelector('#dot-style');
    this.eyeStyleEl = f.querySelector('#eye-style');
    this.marginEl = f.querySelector('#margin');
    this.eccEl = f.querySelector('#ecc');
    this.logoInput = f.querySelector('#logo-upload');

    console.log('Logo input found:', Boolean(this.logoInput));

    this.previewBtn = document.querySelector('#preview-btn');
    this.downloadPngBtn = document.querySelector('#download-png');
    this.downloadSvgBtn = document.querySelector('#download-svg');
  }

  _attachEvents() {
    // Live preview on input changes
    this.form.addEventListener('input', () => this._debounceGenerate());
    this.form.addEventListener('change', (event) => {
      if (event.target && event.target.id === 'logo-upload') {
        return;
      }
      this._debounceGenerate();
    });

    // Buttons
    if (this.previewBtn) this.previewBtn.addEventListener('click', () => this.generate());
    if (this.downloadPngBtn) this.downloadPngBtn.addEventListener('click', () => this.downloadPNG());
    if (this.downloadSvgBtn) this.downloadSvgBtn.addEventListener('click', () => this.downloadSVG());

    // Logo upload
    if (this.logoInput) {
      this.logoInput.addEventListener('change', (e) => {
        console.log('Logo change event fired');
        this._handleLogoUpload(e);
      });
    }
  }

  _debounceGenerate() {
    clearTimeout(this._debounceTimer);
    this._debounceTimer = setTimeout(() => this.generate(), this.debounceMs);
  }

  _handleLogoUpload(e) {
    const file = e.target.files && e.target.files[0];
    console.log('Logo file selected:', file);
    if (!file) {
      this.logoDataUrl = null;
      this._debounceGenerate();
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const nextDataUrl = reader.result;
      console.log('FileReader finished');
      console.log('reader.result:', nextDataUrl ? nextDataUrl.slice(0, 80) : nextDataUrl);

      if (typeof nextDataUrl === 'string' && nextDataUrl.startsWith('data:image/')) {
        this.logoDataUrl = nextDataUrl;
        console.log('logoDataUrl assigned');
        this._debounceGenerate();
      } else {
        console.warn('Uploaded logo did not produce a usable data URL; image will be skipped.');
        this.logoDataUrl = null;
      }
    };

    console.log('FileReader started');
    reader.readAsDataURL(file);
  }

  _getValidationType(type) {
    switch ((type || '').toLowerCase()) {
      case 'url':
      case 'maps':
        return 'url';
      case 'text':
        return 'text';
      case 'email':
        return 'email';
      case 'phone':
        return 'phone';
      case 'sms':
        return 'sms';
      case 'wifi':
        return 'wifi';
      case 'whatsapp':
        return 'whatsapp';
      case 'contact':
        return 'vcard';
      case 'social':
        return 'social';
      default:
        return null;
    }
  }

  _getValidationValue(type) {
    const get = (name) => {
      const el = this.form.elements[name];
      if (!el) return null;
      return el.value;
    };

    const content = (this.contentEl && this.contentEl.value) || '';

    switch ((type || '').toLowerCase()) {
      case 'sms': {
        const number = get('sms_number') || get('phone') || content.trim();
        const message = get('sms_body') || '';
        return `${number}|${message}`.trim();
      }
      case 'whatsapp': {
        const number = get('whatsapp_number') || content.trim();
        const text = get('whatsapp_text') || '';
        return `${number}|${text}`.trim();
      }
      case 'wifi': {
        const ssid = get('wifi_ssid') || '';
        const password = get('wifi_password') || '';
        const encryption = get('wifi_encryption') || get('wifi_type') || 'WPA';
        return `${ssid}|${password}|${encryption}`;
      }
      case 'social':
        return content.trim();
      default:
        return content;
    }
  }

  // Build payload string based on available form fields. Falls back to `#content`.
  buildPayload() {
    const type = (this.typeEl && this.typeEl.value) || 'text';
    const get = (name) => {
      const el = this.form.elements[name];
      if (!el) return null;
      return el.value;
    };

    const content = (this.contentEl && this.contentEl.value) || '';

    switch (type) {
      case 'url':
        return content.trim();
      case 'text':
        return content;
      case 'email': {
        const email = get('email') || content.trim();
        const subject = get('subject') || '';
        const body = get('body') || '';
        let mailto = `mailto:${encodeURIComponent(email)}`;
        const params = new URLSearchParams();
        if (subject) params.set('subject', subject);
        if (body) params.set('body', body);
        const qs = params.toString();
        if (qs) mailto += `?${qs}`;
        return mailto;
      }
      case 'phone': {
        const phone = get('phone') || content.trim();
        return `tel:${phone}`;
      }
      case 'sms': {
        const number = get('sms_number') || get('phone') || '';
        const msg = get('sms_body') || '';
        let sms = `sms:${number}`;
        if (msg) sms += `?body=${encodeURIComponent(msg)}`;
        return sms;
      }
      case 'wifi': {
        // Expect fields: wifi_ssid, wifi_password, wifi_encryption, wifi_hidden
        const ssid = get('wifi_ssid') || '';
        const pass = get('wifi_password') || '';
        const typeEnc = get('wifi_encryption') || get('wifi_type') || 'WPA';
        const hidden = get('wifi_hidden') || 'false';
        // Format: WIFI:T:WPA;S:mynetwork;P:mypass;H:true;;
        return `WIFI:T:${typeEnc};S:${ssid};P:${pass};H:${hidden};;`;
      }
      case 'whatsapp': {
        const number = get('whatsapp_number') || content.trim();
        const text = get('whatsapp_text') || '';
        let url = `https://wa.me/${number}`;
        if (text) url += `?text=${encodeURIComponent(text)}`;
        return url;
      }
      case 'maps': {
        // Use Google Maps search query param
        const query = get('maps_query') || content.trim();
        const encoded = encodeURIComponent(query);
        return `https://www.google.com/maps/search/?api=1&query=${encoded}`;
      }
      case 'contact': {
        // vCard generation
        const fn = get('vcard_fullname') || get('vcard_name') || '';
        const given = get('vcard_first') || '';
        const family = get('vcard_last') || '';
        const org = get('vcard_org') || '';
        const title = get('vcard_title') || '';
        const tel = get('vcard_tel') || get('phone') || '';
        const email = get('vcard_email') || '';
        const url = get('vcard_url') || '';
        const adr = get('vcard_address') || '';

        const lines = [];
        lines.push('BEGIN:VCARD');
        lines.push('VERSION:3.0');
        if (fn) lines.push(`FN:${fn}`);
        if (given || family) lines.push(`N:${family};${given};;;`);
        if (org) lines.push(`ORG:${org}`);
        if (title) lines.push(`TITLE:${title}`);
        if (tel) lines.push(`TEL;TYPE=VOICE,WORK,MSG:${tel}`);
        if (email) lines.push(`EMAIL:${email}`);
        if (adr) lines.push(`ADR:${adr}`);
        if (url) lines.push(`URL:${url}`);
        lines.push('END:VCARD');
        return lines.join('\n');
      }
      case 'social':
        // Expect a JSON-style or newline-separated list in content
        return content;
      default:
        return content;
    }
  }
  // Map ECC letter to string acceptable by qr-code-styling
  _getCorrectLevel(eccValue) {
    const m = (eccValue || 'M').toUpperCase();
    if (['L','M','Q','H'].includes(m)) return m;
    return 'M';
  }

  // Create a container inside previewEl and append QRCodeStyling instance once
  _createPreviewContainer(){
    // keep existing previewEl but create an inner wrapper to attach QR output
    this.previewContainer = document.createElement('div');
    this.previewContainer.className = 'qr-canvas-container';
    this.previewContainer.style.display = 'flex';
    this.previewContainer.style.justifyContent = 'center';
    this.previewContainer.style.alignItems = 'center';
    this.previewEl.innerHTML = '';
    this.previewEl.appendChild(this.previewContainer);

    // if QRCodeStyling already created earlier, append it; otherwise it will be appended on first generate
    if (this.qrCode && typeof this.qrCode.append === 'function'){
      this.qrCode.append(this.previewContainer);
    }
  }

  // Map UI-selected dot style to QRCodeStyling `dotsOptions.type`
  _mapDotType(val){
    switch((val||'square').toLowerCase()){
      case 'square': return 'square';
      case 'round': return 'rounded';
      case 'rounded': return 'rounded';
      case 'dots': return 'dots';
      case 'diamond': return 'diamond';
      case 'classy': return 'classy';
      case 'classy-rounded': return 'classy-rounded';
      default: return 'square';
    }
  }

  // Map UI-selected eye style to cornersSquareOptions.type
  _mapEyeType(val){
    switch((val||'frame').toLowerCase()){
      case 'frame': return 'square';
      case 'rounded': return 'rounded';
      case 'diamond': return 'extra-rounded';
      case 'classy': return 'classy';
      case 'classy-rounded': return 'classy-rounded';
      default: return 'square';
    }
  }

  // Helper: create a simple linear gradient between fg and a darker shade
  _buildGradient(type, fg){
    if(!type || type === 'none') return fg;
    // compute a slightly darker color for stop2
    const darker = this._darkenHex(fg, 0.18);
    const stops = [{offset:0, color: fg},{offset:1, color: darker}];
    return {type: type === 'radial' ? 'radial' : 'linear', rotation: 0, colorStops: stops};
  }

  _darkenHex(hex, amount){
    try{
      const c = hex.replace('#','');
      const num = parseInt(c,16);
      let r = (num >> 16) & 0xFF;
      let g = (num >> 8) & 0xFF;
      let b = num & 0xFF;
      r = Math.max(0, Math.floor(r * (1 - amount)));
      g = Math.max(0, Math.floor(g * (1 - amount)));
      b = Math.max(0, Math.floor(b * (1 - amount)));
      return '#'+((1<<24) + (r<<16) + (g<<8) + b).toString(16).slice(1);
    }catch(e){ return hex; }
  }

  // Generate or update the QR using QRCodeStyling
  async generate() {
    if (!window.QRCodeStyling) {
      console.warn('qr-code-styling not found. Include QRCodeStyling before using qr.js');
      return;
    }

    console.log('generate() called');

    const payload = this.buildPayload();
    const type = this.typeEl?.value || "text";
    const validationType = this._getValidationType(type);
    const validationValue = validationType ? this._getValidationValue(type) : payload;

    if (validationType) {
      try {
        const result = await validateInput(validationType, validationValue);
        updateValidationUI(result);
      } catch (error) {
        updateValidationUI({ valid: false, normalized: null, issues: [error?.message || 'validation_error'] });
      }
    }

    const size = Number((this.sizeEl && this.sizeEl.value) || this.size) || this.size;
    const fg = (this.fgColorEl && this.fgColorEl.value) || '#000000';
    const bg = (this.bgColorEl && this.bgColorEl.value) || '#ffffff';
    const margin = Number((this.marginEl && this.marginEl.value) || 8);
    const ecc = (this.eccEl && this.eccEl.value) || 'M';
    const gradient = (this.gradientEl && this.gradientEl.value) || 'none';
    const dotStyle = (this.dotStyleEl && this.dotStyleEl.value) || 'square';
    const eyeStyle = (this.eyeStyleEl && this.eyeStyleEl.value) || 'frame';

    const image = typeof this.logoDataUrl === 'string' && this.logoDataUrl.startsWith('data:image/')
      ? this.logoDataUrl
      : undefined;

    // build options object for QRCodeStyling
    const opts = {
      width: size,
      height: size,
      data: payload,
      image,
      margin: margin,
      qrOptions: { errorCorrectionLevel: this._getCorrectLevel(ecc) },
      backgroundOptions: { color: bg },
      dotsOptions: {
        color: this._buildGradient(gradient, fg),
        type: this._mapDotType(dotStyle)
      },
      cornersSquareOptions: {
        type: this._mapEyeType(eyeStyle),
        color: fg
      },
      cornersDotOptions: {
        type: 'dot',
        color: fg
      },
      imageOptions: {
        crossOrigin: 'anonymous',
        imageSize: 0.18, // image occupies ~18% width
        margin: 5
      }
    };

    console.log('QRCodeStyling update payload image present:', Boolean(image));

    // If instance exists, update it, otherwise create and append once
    if (this.qrCode) {
      try{
        console.log('QRCodeStyling.update() called with image');
        this.qrCode.update(opts);
      }catch(e){
        // fallback: recreate
        this.qrCode = null;
      }
    }

    if (!this.qrCode) {
      // Use global QRCodeStyling exposed by loader
      console.log('QRCodeStyling.create() called with image');
      this.qrCode = new window.QRCodeStyling(opts);
      if (!this.previewContainer) this._createPreviewContainer();
      this.qrCode.append(this.previewContainer);
    }
    try {
      const quality = await analyzeQR(payload, {
        fg,
        bg,
        size,
        logo: this.logoDataUrl || null,
        margin,
        ecc
      });
      updateQualityUI(quality);
    } catch (error) {
      console.error('Quality analysis failed:', error);
      updateQualityUI({ error: true });
    }

    // notify caller
    this._onGenerated();
  }

  // Download helpers using QRCodeStyling's download API
  async downloadPNG(filename = 'aiqr.png') {
    if (!this.qrCode) { this.generate(); }
    const name = (filename || 'aiqr.png').replace(/\.png$/i,'');
    try{
      this.qrCode.download({ name, extension: 'png' });
    }catch(e){
      // older API signature fallback
      if(typeof this.qrCode.download === 'function') this.qrCode.download('png');
    }
  }

  async downloadSVG(filename = 'aiqr.svg') {
    if (!this.qrCode) { this.generate(); }
    const name = (filename || 'aiqr.svg').replace(/\.svg$/i,'');
    try{
      this.qrCode.download({ name, extension: 'svg' });
    }catch(e){
      if(typeof this.qrCode.download === 'function') this.qrCode.download('svg');
    }
  }

  _triggerDownload(dataUrlOrUrl, filename = 'download.png', isObjectUrl = false) {
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = dataUrlOrUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}

// Convenience initializer
function initQR(options = {}) {
  const gen = new QRGenerator(options);
  // auto-init when DOM is ready if not explicitly called
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => gen.init());
  } else {
    gen.init();
  }
  return gen;
}

export { QRGenerator, initQR };
export default initQR;
