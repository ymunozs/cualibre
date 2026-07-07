/* Nube de palabras empaquetada (FR-034): layout propio en <canvas> con espiral
   de Arquímedes y detección de colisiones vía measureText (research.md D3).

   Solo se usan los colores de la paleta con contraste ≥3:1 sobre el fondo
   claro (#FFCC00 y #00CC66 quedan excluidos del texto por ilegibles). */

const WordCloud = {
  TEXT_COLORS: ["#FF3300", "#0066FF", "#FF0066", "#6600CC", "#CC0000", "#333333", "#0099CC"],
  onWordClick: null, // asignado por Views: abre las concordancias (FR-063)

  render(canvas, words) {
    const placedWords = []; // {x, y, w, h, word} — para el hit-test del clic
    const dpr = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 800;
    const cssHeight = 340;
    canvas.width = cssWidth * dpr;
    canvas.height = cssHeight * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, cssWidth, cssHeight);
    canvas.onclick = null;
    canvas.style.cursor = "default";

    if (!words.length) return;

    const maxCount = words[0].count;
    const minCount = words[words.length - 1].count;
    const span = Math.max(1, maxCount - minCount);
    const fontFor = (count) => Math.round(15 + ((count - minCount) / span) * 41); // 15–56 px

    const placed = []; // rects {x, y, w, h}
    const cx = cssWidth / 2, cy = cssHeight / 2;
    const pad = 4;

    const collides = (rect) => {
      if (rect.x < 2 || rect.y < 2 ||
          rect.x + rect.w > cssWidth - 2 || rect.y + rect.h > cssHeight - 2) return true;
      return placed.some(p =>
        rect.x < p.x + p.w + pad && rect.x + rect.w + pad > p.x &&
        rect.y < p.y + p.h + pad && rect.y + rect.h + pad > p.y
      );
    };

    words.slice(0, 40).forEach((word, index) => {
      const size = fontFor(word.count);
      ctx.font = `700 ${size}px "Space Grotesk", sans-serif`;
      const metrics = ctx.measureText(word.word);
      const w = metrics.width;
      const h = size * 1.05;

      // Espiral de Arquímedes desde el centro hasta encontrar hueco
      let position = null;
      for (let t = 0; t < 3000; t += 1) {
        const radius = 2.2 * t * 0.06;
        const theta = t * 0.35 + index; // fase por palabra para repartir direcciones
        const x = cx + radius * Math.cos(theta) - w / 2;
        const y = cy + radius * Math.sin(theta) * 0.62 - h / 2; // elipse: llena el ancho
        const rect = { x, y, w, h };
        if (!collides(rect)) { position = rect; break; }
        if (radius > Math.max(cssWidth, cssHeight)) break;
      }
      if (!position) return; // sin hueco: la palabra se omite

      placed.push(position);
      placedWords.push({ ...position, word: word.word });
      ctx.fillStyle = this.TEXT_COLORS[index % this.TEXT_COLORS.length];
      ctx.textBaseline = "top";
      ctx.fillText(word.word, position.x, position.y);
    });

    if (placedWords.length && this.onWordClick) {
      canvas.style.cursor = "pointer";
      canvas.onclick = (event) => {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const hit = placedWords.find(p => x >= p.x && x <= p.x + p.w && y >= p.y && y <= p.y + p.h);
        if (hit) this.onWordClick(hit.word);
      };
    }
  },
};
