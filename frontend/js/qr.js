// QR generator module migrated to `qr-code-styling`
// Exports: QRGenerator class and a default `init` helper
import { validateURL } from "./api.js";
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

    this.previewBtn = document.querySelector('#preview-btn');
    this.downloadPngBtn = document.querySelector('#download-png');
    this.downloadSvgBtn = document.querySelector('#download-svg');
  }

  _attachEvents() {
    // Live preview on input changes
    this.form.addEventListener('input', () => this._debounceGenerate());
    this.form.addEventListener('change', () => this._debounceGenerate());

    // Buttons
    if (this.previewBtn) this.previewBtn.addEventListener('click', () => this.generate());
    if (this.downloadPngBtn) this.downloadPngBtn.addEventListener('click', () => this.downloadPNG());
    if (this.downloadSvgBtn) this.downloadSvgBtn.addEventListener('click', () => this.downloadSVG());

    // Logo upload
    if (this.logoInput) {
      this.logoInput.addEventListener('change', (e) => this._handleLogoUpload(e));
    }
  }

  _debounceGenerate() {
    clearTimeout(this._debounceTimer);
    this._debounceTimer = setTimeout(() => this.generate(), this.debounceMs);
  }

  _handleLogoUpload(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) {
      this.logoDataUrl = null;
      this._debounceGenerate();
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      this.logoDataUrl = reader.result;
      this._debounceGenerate();
    };
    reader.readAsDataURL(file);
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

    const payload = this.buildPayload();
    const type = this.typeEl?.value || "text";

    if (type === "url") {
        const result = await validateURL(payload);

        if (!result.valid) {
            alert("Invalid URL");

            console.log(result.issues);

            return;
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

    // build options object for QRCodeStyling
    const opts = {
      width: size,
      height: size,
      data: payload,
      image: this.logoDataUrl || undefined,
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

    // If instance exists, update it, otherwise create and append once
    if (this.qrCode) {
      try{
        this.qrCode.update(opts);
      }catch(e){
        // fallback: recreate
        this.qrCode = null;
      }
    }

    if (!this.qrCode) {
      // Use global QRCodeStyling exposed by loader
      this.qrCode = new window.QRCodeStyling(opts);
      if (!this.previewContainer) this._createPreviewContainer();
      this.qrCode.append(this.previewContainer);
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
