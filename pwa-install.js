// Tasto "Installa app" (PWA) sempre presente nella barra in alto, finche' l'app non e' installata.
(function () {
    var T = {
        it: { btn: 'Installa', title: 'Installa l\'app AtmBet', close: 'Chiudi',
              ios: 'Su iPhone/iPad (Safari): tocca il tasto <b>Condividi</b> in basso, poi <b>Aggiungi alla schermata Home</b>.',
              android: 'Sul telefono: apri il menu del browser (tre puntini) e tocca <b>Installa app</b> oppure <b>Aggiungi a schermata Home</b>.',
              desktop: 'Sul computer: cerca l\'icona di installazione nella barra degli indirizzi (Chrome/Edge) e conferma.' },
        en: { btn: 'Install', title: 'Install the AtmBet app', close: 'Close',
              ios: 'On iPhone/iPad (Safari): tap the <b>Share</b> button at the bottom, then <b>Add to Home Screen</b>.',
              android: 'On your phone: open the browser menu (three dots) and tap <b>Install app</b> or <b>Add to Home screen</b>.',
              desktop: 'On a computer: look for the install icon in the address bar (Chrome/Edge) and confirm.' },
        es: { btn: 'Instalar', title: 'Instala la app AtmBet', close: 'Cerrar',
              ios: 'En iPhone/iPad (Safari): toca el botón <b>Compartir</b> abajo y luego <b>Añadir a pantalla de inicio</b>.',
              android: 'En el móvil: abre el menú del navegador (tres puntos) y toca <b>Instalar app</b> o <b>Añadir a pantalla de inicio</b>.',
              desktop: 'En el ordenador: busca el icono de instalación en la barra de direcciones (Chrome/Edge) y confirma.' },
        pt: { btn: 'Instalar', title: 'Instala a app AtmBet', close: 'Fechar',
              ios: 'No iPhone/iPad (Safari): toca no botão <b>Partilhar</b> em baixo e depois em <b>Adicionar ao ecrã principal</b>.',
              android: 'No telemóvel: abre o menu do navegador (três pontos) e toca em <b>Instalar app</b> ou <b>Adicionar ao ecrã principal</b>.',
              desktop: 'No computador: procura o ícone de instalação na barra de endereços (Chrome/Edge) e confirma.' },
        fr: { btn: 'Installer', title: 'Installer l\'app AtmBet', close: 'Fermer',
              ios: 'Sur iPhone/iPad (Safari) : touchez le bouton <b>Partager</b> en bas, puis <b>Sur l\'écran d\'accueil</b>.',
              android: 'Sur le téléphone : ouvrez le menu du navigateur (trois points) et touchez <b>Installer l\'application</b> ou <b>Ajouter à l\'écran d\'accueil</b>.',
              desktop: 'Sur ordinateur : cherchez l\'icône d\'installation dans la barre d\'adresse (Chrome/Edge) et confirmez.' },
        de: { btn: 'Installieren', title: 'AtmBet-App installieren', close: 'Schließen',
              ios: 'Auf iPhone/iPad (Safari): Tippe unten auf <b>Teilen</b> und dann auf <b>Zum Home-Bildschirm</b>.',
              android: 'Auf dem Handy: Öffne das Browsermenü (drei Punkte) und tippe auf <b>App installieren</b> oder <b>Zum Startbildschirm hinzufügen</b>.',
              desktop: 'Am Computer: Suche das Installationssymbol in der Adressleiste (Chrome/Edge) und bestätige.' }
    };
    function lang() { var l = 'it'; try { l = localStorage.getItem('atmbet_lang') || 'it'; } catch (e) {} return T[l] ? l : 'it'; }
    function tr() { return T[lang()]; }

    var deferred = null, btn = null, installed = false;

    function isStandalone() {
        return (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || window.navigator.standalone === true;
    }
    function platform() {
        var ua = navigator.userAgent || '';
        if (/iPad|iPhone|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)) return 'ios';
        if (/Android/.test(ua)) return 'android';
        return 'desktop';
    }

    function showHelp() {
        var old = document.getElementById('pwa-help'); if (old) old.remove();
        var t = tr();
        var o = document.createElement('div');
        o.id = 'pwa-help';
        o.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(2,6,23,.85);display:flex;align-items:center;justify-content:center;padding:16px';
        o.innerHTML = '<div style="max-width:360px;width:100%;background:#0e1522;border:1px solid #1e293b;border-radius:20px;padding:22px;color:#e2e8f0;font-family:inherit">' +
            '<div style="font-weight:800;font-size:15px;margin-bottom:10px;color:#fff">' + t.title + '</div>' +
            '<p style="font-size:13px;line-height:1.5;color:#cbd5e1;margin:0 0 16px">' + t[platform()] + '</p>' +
            '<button type="button" id="pwa-help-close" style="width:100%;background:#10b981;color:#06210f;font-weight:800;font-size:13px;border:0;border-radius:12px;padding:10px;cursor:pointer">' + t.close + '</button></div>';
        o.addEventListener('click', function (e) { if (e.target === o) o.remove(); });
        document.body.appendChild(o);
        document.getElementById('pwa-help-close').onclick = function () { o.remove(); };
    }

    function onClick() {
        if (deferred) {
            var p = deferred; deferred = null;
            p.prompt();
            if (p.userChoice) p.userChoice.then(function (c) { if (c && c.outcome === 'accepted') hide(); }).catch(function () {});
        } else {
            showHelp();
        }
    }

    function hide() { installed = true; if (btn) btn.style.display = 'none'; }

    function label() { if (btn) btn.querySelector('span').textContent = tr().btn; }

    function build() {
        if (installed || isStandalone() || document.getElementById('pwa-install-btn')) return;
        var nav = document.querySelector('nav');
        var lang_sel = document.getElementById('lang-selector');
        if (!nav || !lang_sel || !lang_sel.parentNode) return;
        btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'pwa-install-btn';
        btn.setAttribute('aria-label', tr().title);
        btn.className = 'flex items-center gap-1.5 text-xs font-bold rounded-xl px-2.5 py-1.5 transition';
        btn.style.cssText = 'background:#10b981;color:#06210f;border:0;cursor:pointer;white-space:nowrap';
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/></svg><span></span>';
        btn.onclick = onClick;
        lang_sel.parentNode.insertBefore(btn, lang_sel);
        label();
    }

    window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); deferred = e; });
    window.addEventListener('appinstalled', hide);
    window.addEventListener('storage', label);
    document.addEventListener('click', function (e) { if (e.target && e.target.closest && e.target.closest('#lang-selector')) setTimeout(label, 600); });
    document.addEventListener('change', function (e) { if (e.target && e.target.id === 'lang-selector') setTimeout(label, 800); });
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
