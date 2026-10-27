/* ==================================================================
   LYSMOTOR

   Lys som stoppes av ting. Hver lyskilde tegnes i sitt eget lag, og
   skyggene skjæres ut av laget der gjenstander står i veien. Til slutt
   legges alle lagene sammen til et lyskart som multipliseres over
   scenen: der lyset når, står kunsten som tegnet; der det ikke når,
   ligger rommet i skygge.

   Skyggene regnes som i et ovenfra-sett spill: hver gjenstand er en
   firkant med en høyde, og for hver kant som vender bort fra lyset
   strekkes en firkant ut bort fra lyset. Unionen av dem er skyggen.
   Gjenstandens egen topp ligger ikke i skyggen — den er jo opplyst.

   Koøyer gir retningslys: parallelle skygger, slik sollys gjennom et
   vindu gir. Lamper og lykter gir punktlys: skyggene sprer seg ut fra
   lampa og blir lengre jo lavere lampa henger.
   ================================================================== */

const Lysmotor = (() => {
  "use strict";

  /* Hjørnene i en rotert firkant, i rekkefølge rundt. */
  function hjorner(x, y, w, h, grader) {
    const cx = x + w / 2, cy = y + h / 2;
    const a = (grader || 0) * Math.PI / 180;
    const cos = Math.cos(a), sin = Math.sin(a);
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]].map(([px, py]) => {
      const dx = px - cx, dy = py - cy;
      return [cx + dx * cos - dy * sin, cy + dx * sin + dy * cos];
    });
  }

  /* Kantene som vender bort fra lyset. For hver: [a, b, normal]. */
  function bakkanter(poly, vendt) {
    let mx = 0, my = 0;
    poly.forEach(([x, y]) => { mx += x; my += y; });
    mx /= poly.length; my /= poly.length;
    const ut = [];
    for (let i = 0; i < poly.length; i += 1) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      let nx = b[1] - a[1], ny = -(b[0] - a[0]);
      const ex = (a[0] + b[0]) / 2 - mx, ey = (a[1] + b[1]) / 2 - my;
      if (nx * ex + ny * ey < 0) { nx = -nx; ny = -ny; }
      if (vendt(nx, ny, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)) ut.push([a, b]);
    }
    return ut;
  }

  function fyllFirkant(g, s, pts) {
    g.beginPath();
    g.moveTo(pts[0][0] * s, pts[0][1] * s);
    for (let i = 1; i < pts.length; i += 1) g.lineTo(pts[i][0] * s, pts[i][1] * s);
    g.closePath();
    g.fill();
  }

  /* Skygger fra retningslys: alle strekkes samme vei, så langt som
     høyden tilsier. */
  function skyggerRetning(g, s, hindre, dx, dy, faktor) {
    hindre.forEach((h) => {
      const len = h.hoyde * faktor;
      const vx = dx * len, vy = dy * len;
      bakkanter(h.poly, (nx, ny) => nx * dx + ny * dy > 0).forEach(([a, b]) => {
        fyllFirkant(g, s, [a, b, [b[0] + vx, b[1] + vy], [a[0] + vx, a[1] + vy]]);
      });
    });
  }

  /* Skygger fra punktlys: strekkes ut fra lampa. Jo høyere gjenstanden
     er i forhold til lampa, jo lengre skygge. */
  function skyggerPunkt(g, s, hindre, lx, ly, lampehoyde, maks) {
    hindre.forEach((h) => {
      const tak = Math.max(4, lampehoyde - h.hoyde);
      const strekk = (p) => {
        const dx = p[0] - lx, dy = p[1] - ly;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        const len = Math.min(maks, d * h.hoyde / tak);
        return [p[0] + dx / d * len, p[1] + dy / d * len];
      };
      bakkanter(h.poly, (nx, ny, mx, my) => nx * (mx - lx) + ny * (my - ly) > 0)
        .forEach(([a, b]) => {
          fyllFirkant(g, s, [a, b, strekk(b), strekk(a)]);
        });
    });
  }

  function rgba(c, a) {
    return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")";
  }

  /* Ett lys i sitt eget lag, med skyggene skåret ut. */
  function tegnLys(W, H, s, lys, hindre) {
    const lag = document.createElement("canvas");
    lag.width = W * s; lag.height = H * s;
    const g = lag.getContext("2d");

    if (lys.type === "stråle") {
      // Lysstrålen fra en koøye: smal ved glasset, bredere innover,
      // og den svinner jo lenger den når.
      const dx = Math.sin(lys.vinkel * Math.PI / 180);
      const dy = Math.cos(lys.vinkel * Math.PI / 180);
      const px = -dy, py = dx;                    // på tvers av strålen
      const x0 = lys.x, y0 = lys.y;
      const x1 = x0 + dx * lys.lengde, y1 = y0 + dy * lys.lengde;
      const w0 = lys.bredde / 2, w1 = lys.bredde * lys.spredning / 2;
      const grad = g.createLinearGradient(x0 * s, y0 * s, x1 * s, y1 * s);
      grad.addColorStop(0, rgba(lys.farge, lys.styrke));
      grad.addColorStop(0.45, rgba(lys.farge, lys.styrke * 0.72));
      grad.addColorStop(1, rgba(lys.farge, 0));
      g.fillStyle = grad;
      fyllFirkant(g, s, [
        [x0 + px * w0, y0 + py * w0], [x0 - px * w0, y0 - py * w0],
        [x1 - px * w1, y1 - py * w1], [x1 + px * w1, y1 + py * w1]]);
      g.globalCompositeOperation = "destination-out";
      g.fillStyle = "#000";
      skyggerRetning(g, s, hindre, dx, dy, lys.skyggelengde);
    } else {
      // Punktlys: lampe, lykt, nødlys.
      const r = lys.radius;
      const grad = g.createRadialGradient(lys.x * s, lys.y * s, 0,
                                          lys.x * s, lys.y * s, r * s);
      grad.addColorStop(0, rgba(lys.farge, lys.styrke));
      grad.addColorStop(0.25, rgba(lys.farge, lys.styrke * 0.62));
      grad.addColorStop(0.6, rgba(lys.farge, lys.styrke * 0.22));
      grad.addColorStop(1, rgba(lys.farge, 0));
      g.fillStyle = grad;
      g.fillRect(0, 0, W * s, H * s);
      g.globalCompositeOperation = "destination-out";
      g.fillStyle = "#000";
      skyggerPunkt(g, s, hindre, lys.x, lys.y, lys.hoyde, lys.maksSkygge || 400);
    }
    return lag;
  }

  /* Selve lyskilden: glasset som lyser, lampa som gløder. */
  function tegnKilde(g, s, k) {
    g.save();
    g.globalCompositeOperation = "lighter";
    const halo = g.createRadialGradient(k.x * s, k.y * s, 0, k.x * s, k.y * s, k.glod * s);
    halo.addColorStop(0, rgba(k.farge, k.haloStyrke));
    halo.addColorStop(0.35, rgba(k.farge, k.haloStyrke * 0.35));
    halo.addColorStop(1, rgba(k.farge, 0));
    g.fillStyle = halo;
    g.fillRect((k.x - k.glod) * s, (k.y - k.glod) * s, k.glod * 2 * s, k.glod * 2 * s);
    g.restore();
    if (k.kjerne) {
      // Glasset selv: nesten hvitt i midten, varmt mot kanten.
      g.save();
      const c = g.createRadialGradient(k.x * s, k.y * s, 0, k.x * s, k.y * s, k.kjerne * s);
      const kf = k.kjerneFarge || [[255, 253, 245], [255, 240, 205], [255, 222, 160]];
      c.addColorStop(0, "rgba(" + kf[0].join(",") + ",1)");
      c.addColorStop(0.7, "rgba(" + kf[1].join(",") + ",1)");
      c.addColorStop(1, "rgba(" + kf[2].join(",") + ",0.95)");
      g.fillStyle = c;
      g.beginPath();
      g.arc(k.x * s, k.y * s, k.kjerne * s, 0, Math.PI * 2);
      g.fill();
      g.restore();
    }
  }

  /* Hele bildet: scene, lyskart, dis og lyskilder.

     opts.scene      ferdig tegnet scene, i W*s × H*s
     opts.lys        lyskildene
     opts.hindre     gjenstandene som kaster skygge: { poly, hoyde }
     opts.omgivelse  grunnlyset der ingen lys når, [r,g,b]
     opts.dis        hvor mye lysstrålene synes i lufta, 0–1
     opts.uskarp     hvor myke skyggekantene er, i rompiksler */
  function render(ut, W, H, s, opts) {
    const g = ut.getContext("2d");
    g.imageSmoothingEnabled = false;
    g.drawImage(opts.scene, 0, 0);

    // Lyskartet: grunnlys, så hvert lys lagt oppå.
    const kart = document.createElement("canvas");
    kart.width = W * s; kart.height = H * s;
    const kg = kart.getContext("2d");
    kg.fillStyle = "rgb(" + opts.omgivelse.join(",") + ")";
    kg.fillRect(0, 0, W * s, H * s);

    const lag = opts.lys.map((l) => tegnLys(W, H, s, l, opts.hindre));
    kg.globalCompositeOperation = "lighter";
    kg.filter = "blur(" + (opts.uskarp * s) + "px)";
    lag.forEach((l) => kg.drawImage(l, 0, 0));
    kg.filter = "none";

    // Mørke kanter: rommet faller bort mot veggene.
    if (opts.vignett) {
      kg.globalCompositeOperation = "multiply";
      const v = kg.createRadialGradient(W * s / 2, H * s * 0.45, Math.min(W, H) * s * 0.3,
                                        W * s / 2, H * s * 0.45, Math.max(W, H) * s * 0.75);
      v.addColorStop(0, "rgb(255,255,255)");
      v.addColorStop(1, "rgb(" + Math.round(255 * (1 - opts.vignett)) + "," +
                        Math.round(255 * (1 - opts.vignett)) + "," +
                        Math.round(255 * (1 - opts.vignett)) + ")");
      kg.fillStyle = v;
      kg.fillRect(0, 0, W * s, H * s);
    }

    g.globalCompositeOperation = "multiply";
    g.drawImage(kart, 0, 0);

    // Dis: lysstrålene synes i lufta, ikke bare på gulvet.
    if (opts.dis) {
      g.globalCompositeOperation = "screen";
      g.globalAlpha = opts.dis;
      g.filter = "blur(" + (opts.uskarp * 2.2 * s) + "px)";
      lag.forEach((l) => g.drawImage(l, 0, 0));
      g.filter = "none";
      g.globalAlpha = 1;
    }
    g.globalCompositeOperation = "source-over";

    (opts.kilder || []).forEach((k) => tegnKilde(g, s, k));
  }

  return { render, hjorner };
})();
