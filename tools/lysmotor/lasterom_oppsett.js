// Lasterom 2 ved strømbrudd: bare nødlampene på veggene står igjen.
// Lampene henger lavt, så bagasjestablene kaster lange skygger tvers
// over rommet, og lyset er mettet rødt. Det er dramatisk med vilje —
// en dempet variant ble prøvd og valgt bort.
const W = 704, H = 448;
const rod = [255, 44, 34];
const lamper = [
  [W * 0.27, 7], [W * 0.83, 7],        // øvre vegg
  [6, H * 0.40],                       // venstre vegg
  [W - 6, H * 0.49],                   // høyre vegg
];
return {
  omgivelse: [50, 40, 44],
  vignett: 0.30,
  dis: 0.10,
  uskarp: 1.0,
  lys: lamper.map(([x, y]) => ({
    type: "punkt", x: x, y: y, radius: 330, farge: rod, styrke: 0.9,
    hoyde: 110, maksSkygge: 520,
  })),
  kilder: lamper.map(([x, y]) => ({
    x: x, y: y, kjerne: 3.4, glod: 26, haloStyrke: 0.75, farge: [255, 60, 44],
    kjerneFarge: [[255, 210, 200], [255, 70, 55], [200, 20, 14]],
  })),
};
