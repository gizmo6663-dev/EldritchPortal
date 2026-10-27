// Kabinen ved strømbrudd om dagen: sola står lavt og skinner inn
// gjennom de fire koøyene i skroget.
const koyer = [55.5, 127.5, 207.5, 279.5];
const varm = [255, 228, 182];
return {
  omgivelse: [82, 66, 62],
  vignett: 0.32,
  dis: 0.28,
  uskarp: 0.8,
  // Baderomsveggene og skilleveggen mot korridoren. Uten dem lekker
  // lyset rett gjennom.
  vegger: [
    [225, 89, 95, 5, 160],     // baderom, øvre vegg
    [225, 89, 5, 104, 160],    // baderom, venstre vegg
    [0, 191, 328, 6, 160],     // mot korridoren
  ],
  lys: koyer.map((x) => ({
    type: "stråle", x: x, y: 11, vinkel: 18, lengde: 190,
    bredde: 13, spredning: 2.3, farge: varm, styrke: 1.0,
    skyggelengde: 1.35,
  })),
  kilder: koyer.map((x) => ({
    x: x, y: 6.5, kjerne: 5.6, glod: 22, haloStyrke: 0.6, farge: [255, 226, 170],
  })),
};
