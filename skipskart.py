"""Skipskartene i mobilappen.

Kartene — tretti rom med lys og skygge, dag og natt, strømbrudd, vær,
spor og alt som kan flyttes — finnes ferdig i nettversjonen
(web/index.html, bygd av web/build.py). Å skrive alt det på nytt i Kivy
ville gitt to kart som sakte glir fra hverandre. Appen viser derfor den
samme siden:

  Android  i en WebView lagt over appen. Siden lastes fra filene som
           ligger i APK-en (file://), så den virker uten nett. Det
           Keeperen flytter og slår av og på, huskes av WebView-en til
           neste gang.
  PC       i nettleseren.

Siden åpnes med ?app=kart, og viser da bare kartfanen, med en egen
linje øverst: «Tilbake til appen», og «Cast scenen til TV» når appen
kan caste. En WebView kan ikke kalle Python direkte, så siden legger
meldingene sine i en kø (window.eldritchApp), og appen henter køen selv
et par ganger i sekundet. Svar går tilbake som eldritchApp.svar("…").

Tilbake-knappen på telefonen lukker kartet.
"""
import json
import os
import pathlib
import webbrowser

from kivy.clock import Clock
from kivy.utils import platform

BUNDLE = os.path.dirname(os.path.abspath(__file__))
WEB_INDEX = os.path.join(BUNDLE, "web", "index.html")

# Hvor ofte appen henter meldinger fra siden, i sekunder.
HENT_HVER = 0.4


def finnes():
    """Er nettkartene pakket med appen?"""
    return os.path.isfile(WEB_INDEX)


def kart_url(cast=False):
    """Adressen til kartsiden i app-modus."""
    url = pathlib.Path(WEB_INDEX).as_uri() + "?app=kart"
    if cast:
        url += "&cast=1"
    return url


def les_meldinger(svar):
    """Gjør svaret fra evaluateJavascript om til en liste meldinger.

    WebView-en JSON-koder det JavaScript returnerer. Siden returnerer
    selv en JSON-streng, så svaret er kodet to ganger: først en streng,
    så lista inni den."""
    if svar is None:
        return []
    try:
        verdi = json.loads(svar)
        if isinstance(verdi, str):
            verdi = json.loads(verdi)
    except (TypeError, ValueError):
        return []
    return [m for m in verdi if isinstance(m, dict)] if isinstance(verdi, list) else []


class Skipskart:
    """Kartsiden, åpen eller lukket. ved_melding får hver melding siden
    sender (som dict), på Kivy-tråden."""

    def __init__(self, ved_melding):
        self.ved_melding = ved_melding
        self.apen = False
        self._android = None
        self._hent = None

    def apne(self, cast=False):
        url = kart_url(cast)
        if platform == "android":
            if self._android is None:
                self._android = _AndroidVisning(
                    self._mottatt,
                    lambda: Clock.schedule_once(lambda dt: self.lukk(), 0))
            self._android.vis(url)
            self.apen = True
            if self._hent is None:
                self._hent = Clock.schedule_interval(
                    lambda dt: self._android.hent(), HENT_HVER)
            return "android"
        # PC: nettleseren. Der finnes ingen vei tilbake til appen, så
        # Cast-knappen vises ikke.
        webbrowser.open(kart_url(False))
        return "nettleser"

    def lukk(self):
        if self._hent is not None:
            self._hent.cancel()
            self._hent = None
        if self._android is not None:
            self._android.skjul()
        self.apen = False

    def svar(self, tekst):
        """Vis en kort beskjed nederst på kartsiden."""
        if self._android is not None and self.apen:
            self._android.kjor("window.eldritchApp && eldritchApp.svar(%s)"
                               % json.dumps(tekst))

    def _mottatt(self, svar):
        for melding in les_meldinger(svar):
            Clock.schedule_once(lambda dt, m=melding: self.ved_melding(m), 0)


if platform == "android":
    from android.runnable import run_on_ui_thread
    from jnius import PythonJavaClass, autoclass, java_method

    class _Svar(PythonJavaClass):
        """ValueCallback for evaluateJavascript."""
        __javainterfaces__ = ["android/webkit/ValueCallback"]
        __javacontext__ = "app"

        def __init__(self, fn):
            super().__init__()
            self.fn = fn

        @java_method("(Ljava/lang/Object;)V")
        def onReceiveValue(self, verdi):
            if verdi is not None and not isinstance(verdi, str):
                verdi = verdi.toString()
            self.fn(verdi)

    class _Tast(PythonJavaClass):
        """Tilbake-knappen mens WebView-en har fokus. Uten denne går
        trykket forbi Kivy og rett til aktiviteten, som da avslutter
        hele appen."""
        __javainterfaces__ = ["android/view/View$OnKeyListener"]
        __javacontext__ = "app"

        def __init__(self, fn):
            super().__init__()
            self.fn = fn

        @java_method("(Landroid/view/View;ILandroid/view/KeyEvent;)Z")
        def onKey(self, view, kode, hendelse):
            if kode != 4:                         # KeyEvent.KEYCODE_BACK
                return False
            if hendelse.getAction() == 1:         # KeyEvent.ACTION_UP
                self.fn()
            return True

    class _AndroidVisning:
        """WebView-en, lagt over hele appen. Alt som rører den må skje
        på Androids UI-tråd."""

        def __init__(self, ved_svar, ved_tilbake):
            self.wv = None
            # Tilbakekallene må leve så lenge WebView-en kan kalle dem.
            self._svar = _Svar(ved_svar)
            self._tast = _Tast(ved_tilbake)

        @run_on_ui_thread
        def vis(self, url):
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            if self.wv is None:
                WebView = autoclass("android.webkit.WebView")
                WebViewClient = autoclass("android.webkit.WebViewClient")
                LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
                wv = WebView(activity)
                s = wv.getSettings()
                s.setJavaScriptEnabled(True)
                # Det Keeperen flytter og slår av og på, lagres i
                # localStorage og IndexedDB.
                s.setDomStorageEnabled(True)
                s.setDatabaseEnabled(True)
                # Siden og bildene ligger som filer i appen. Uten dette
                # får ikke siden lese bildene inn i et lerret, og
                # «Cast scenen» kan ikke lage bildet.
                s.setAllowFileAccess(True)
                s.setAllowFileAccessFromFileURLs(True)
                s.setUseWideViewPort(True)
                s.setLoadWithOverviewMode(True)
                wv.setWebViewClient(WebViewClient())
                wv.setOnKeyListener(self._tast)
                wv.setBackgroundColor(0xFF120D0B - (1 << 32))
                activity.addContentView(wv, LayoutParams(
                    LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
                wv.loadUrl(url)
                self.wv = wv
            else:
                self.wv.setVisibility(0)          # View.VISIBLE
                self.wv.onResume()
            self.wv.requestFocus()

        @run_on_ui_thread
        def skjul(self):
            # Skjules, ikke rives: neste gang åpnes kartet der man slapp.
            if self.wv is not None:
                self.wv.setVisibility(8)          # View.GONE
                # Stopp animasjonene mens kartet ikke vises.
                self.wv.onPause()

        @run_on_ui_thread
        def hent(self):
            if self.wv is not None:
                self.wv.evaluateJavascript(
                    "window.eldritchApp ? eldritchApp.hent() : '[]'", self._svar)

        @run_on_ui_thread
        def kjor(self, js):
            if self.wv is not None:
                self.wv.evaluateJavascript(js, None)
