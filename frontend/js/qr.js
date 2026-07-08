// QR generator module using QRCode.js
// Exports: QRGenerator class and a default `init` helper

class QRGenerator {
  constructor(options = {}) {
    this.formSelector = options.formSelector || '#qr-form';
    this.previewSelector = options.previewSelector || '#qr-preview';
    this.previewPlaceholder = options.previewPlaceholder || '.qr-canvas-placeholder';
    this.debounceMs = options.debounceMs || 250;
    this.size = Number(options.size) || 512;
    this.qrcode = null;
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

  // Map ECC letter to library constant
  _getCorrectLevel(eccValue) {
    if (!window.QRCode || !window.QRCode.CorrectLevel) return undefined;
    const m = (eccValue || 'M').toUpperCase();
    switch (m) {
      case 'L': return QRCode.CorrectLevel.L;
      case 'M': return QRCode.CorrectLevel.M;
      case 'Q': return QRCode.CorrectLevel.Q;
      case 'H': return QRCode.CorrectLevel.H;
      default: return QRCode.CorrectLevel.M;
    }
  }

  // Generate QR using QRCode.js and then composite logo if present
  generate() {
    if (!window.QRCode) {
      console.warn('QRCode.js not found. Include QRCode.js before using qr.js');
      return;
    }

    const payload = this.buildPayload();
    const size = Number((this.sizeEl && this.sizeEl.value) || this.size) || this.size;
    const fg = (this.fgColorEl && this.fgColorEl.value) || '#000000';
    const bg = (this.bgColorEl && this.bgColorEl.value) || '#ffffff';
    const margin = Number((this.marginEl && this.marginEl.value) || 8);
    const ecc = (this.eccEl && this.eccEl.value) || 'M';

    // Clear preview
    this.previewEl.innerHTML = '';

    // Create QRCode instance
    try {
      this.qrcode = new QRCode(this.previewEl, {
        text: payload,
        width: size,
        height: size,
        colorDark: fg,
        colorLight: bg,
        correctLevel: this._getCorrectLevel(ecc),
      });
    } catch (err) {
      // Some forks require using makeCode after new QRCode(element)
      this.qrcode = new QRCode(this.previewEl, { width: size, height: size });
      if (typeof this.qrcode.clear === 'function') this.qrcode.clear();
      if (typeof this.qrcode.makeCode === 'function') this.qrcode.makeCode(payload);
    }

    // After a short delay, composite logo if present
    setTimeout(() => {
      this._compositeLogoIfNeeded();
      this._onGenerated();
    }, 50);
  }

  async _compositeLogoIfNeeded() {
    if (!this.logoDataUrl) return; // nothing to composite

    // Get rendered image (img or canvas) inside preview
    const img = this.previewEl.querySelector('img');
    const canvas = this.previewEl.querySelector('canvas');
    const svg = this.previewEl.querySelector('svg');

    let baseImg;
    let w = Number((this.sizeEl && this.sizeEl.value) || this.size) || this.size;
    let h = w;

    if (canvas) {
      // draw logo onto existing canvas
      const ctx = canvas.getContext('2d');
      const logo = await this._loadImage(this.logoDataUrl);
      const scale = Math.max(0.12, Math.min(0.25, 256 / w));
      const logoW = Math.floor(w * scale);
      const logoH = Math.floor((logo.height / logo.width) * logoW);
      const dx = Math.floor((w - logoW) / 2);
      const dy = Math.floor((h - logoH) / 2);
      ctx.drawImage(logo, dx, dy, logoW, logoH);
      return;
    }

    if (img) {
      baseImg = img;
    } else if (svg) {
      // serialize svg to data URL
      const svgStr = new XMLSerializer().serializeToString(svg);
      const svg64 = btoa(unescape(encodeURIComponent(svgStr)));
      const dataUrl = 'data:image/svg+xml;base64,' + svg64;
      baseImg = await this._loadImage(dataUrl);
    } else {
      // nothing we can composite
      return;
    }

    // Create canvas and composite
    const out = document.createElement('canvas');
    out.width = w;
    out.height = h;
    const ctx = out.getContext('2d');
    // draw base QR
    await new Promise((res) => {
      if (baseImg.complete) {
        ctx.drawImage(baseImg, 0, 0, w, h);
        res();
      } else {
        baseImg.onload = () => {
          ctx.drawImage(baseImg, 0, 0, w, h);
          res();
        };
        baseImg.onerror = res;
      }
    });

    // draw logo
    const logo = await this._loadImage(this.logoDataUrl);
    const scale = 0.18; // logo occupies ~18% of QR width
    const logoW = Math.floor(w * scale);
    const logoH = Math.floor((logo.height / logo.width) * logoW);
    const dx = Math.floor((w - logoW) / 2);
    const dy = Math.floor((h - logoH) / 2);
    // optional rounded background for logo
    ctx.save();
    ctx.fillStyle = '#ffffff';
    const pad = Math.floor(logoW * 0.12);
    const rx = dx - pad;
    const ry = dy - pad;
    const rw = logoW + pad * 2;
    const rh = logoH + pad * 2;
    // rounded rect
    const r = Math.floor(pad * 0.8);
    ctx.beginPath();
    ctx.moveTo(rx + r, ry);
    ctx.arcTo(rx + rw, ry, rx + rw, ry + rh, r);
    ctx.arcTo(rx + rw, ry + rh, rx, ry + rh, r);
    ctx.arcTo(rx, ry + rh, rx, ry, r);
    ctx.arcTo(rx, ry, rx + rw, ry, r);
    ctx.closePath();
    ctx.fill();
    ctx.drawImage(logo, dx, dy, logoW, logoH);
    ctx.restore();

    // replace preview with canvas
    this.previewEl.innerHTML = '';
    this.previewEl.appendChild(out);
  }

  _loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = (e) => reject(e);
      img.src = src;
    });
  }

  // Download helpers
  async downloadPNG(filename = 'aiqr.png') {
    // Ensure latest render
    this.generate();
    // small delay to ensure canvas available
    await new Promise((r) => setTimeout(r, 120));
    const canvas = this.previewEl.querySelector('canvas');
    if (canvas) {
      const dataUrl = canvas.toDataURL('image/png');
      this._triggerDownload(dataUrl, filename);
      return;
    }

    const img = this.previewEl.querySelector('img');
    if (img && img.src) {
      this._triggerDownload(img.src, filename);
      return;
    }

    // fallback: try to serialize svg
    const svg = this.previewEl.querySelector('svg');
    if (svg) {
      const svgStr = new XMLSerializer().serializeToString(svg);
      const canvas2 = document.createElement('canvas');
      const size = Number((this.sizeEl && this.sizeEl.value) || this.size) || this.size;
      canvas2.width = size;
      canvas2.height = size;
      const ctx = canvas2.getContext('2d');
      const imgObj = await this._loadImage('data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr));
      ctx.drawImage(imgObj, 0, 0);
      const dataUrl = canvas2.toDataURL('image/png');
      this._triggerDownload(dataUrl, filename);
      return;
    }

    console.warn('No renderable QR found to download.');
  }

  async downloadSVG(filename = 'aiqr.svg') {
    // Try to find an existing SVG
    const svg = this.previewEl.querySelector('svg');
    if (svg) {
      const svgStr = new XMLSerializer().serializeToString(svg);
      const blob = new Blob([svgStr], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      this._triggerDownload(url, filename, true);
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      return;
    }

    // If canvas present, convert to PNG then warn user
    const canvas = this.previewEl.querySelector('canvas');
    if (canvas) {
      // create PNG instead and name .png
      this.downloadPNG(filename.replace(/\.svg$/i, '.png'));
      return;
    }

    const img = this.previewEl.querySelector('img');
    if (img && img.src && img.src.startsWith('data:image/svg+xml')) {
      this._triggerDownload(img.src, filename);
      return;
    }

    console.warn('No SVG available to download.');
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
