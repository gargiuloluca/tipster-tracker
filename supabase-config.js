// =====================================================================
// AtmBet - connessione a Supabase (condivisa da tutte le pagine)
// La chiave "publishable" e' PUBBLICA per progetto: la sicurezza e' nelle regole del database (RLS).
// NON inserire mai qui la chiave "secret" / "service_role".
// =====================================================================
(function () {
    const SUPABASE_URL = 'https://kepejyxhwpbyvjwpmyff.supabase.co';
    const SUPABASE_KEY = 'sb_publishable_tadf2N16hk5FwTXIYj4Daw_TYn-ln99';
    const SESSION_KEY = 'atmbet_active_user_session';

    function todayRome() {
        return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Rome' }).format(new Date());
    }

    const client = (window.supabase && window.supabase.createClient)
        ? window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY, { auth: { persistSession: true, autoRefreshToken: true } })
        : null;

    // Trasforma il profilo del server nell'oggetto "sessione" che le pagine gia usano per mostrare l'interfaccia.
    function toLegacySession(p) {
        let plan = p.plan === 'none' ? 'credits' : p.plan;
        const expired = p.expires_at && p.expires_at < todayRome();
        if (expired && (plan === 'pure' || plan === 'all_inclusive' || plan === 'trial_vip')) plan = 'credits';
        return {
            id: p.id,
            name: p.name || (p.email || '').split('@')[0],
            email: p.email,
            telegram_username: p.telegram_username || '',
            role: p.role || 'user',
            plan: plan,
            expires_at: p.expires_at || '2099-12-31',
            credits: p.credits || 0,
            unlocked_bets: p.unlocked_bets || [],
            ref_code: p.ref_code || ''
        };
    }

    // Allinea la sessione locale con quella VERA del server. Se non sei loggato, cancella ogni traccia.
    async function syncSession() {
        if (!client) return null;
        try {
            const { data } = await client.auth.getSession();
            if (!data || !data.session) { localStorage.removeItem(SESSION_KEY); localStorage.removeItem('atmbet_is_admin'); return null; }
            const { data: prof, error } = await client.from('profiles').select('*').eq('id', data.session.user.id).single();
            if (error || !prof) return null;
            const s = toLegacySession(prof);
            localStorage.setItem(SESSION_KEY, JSON.stringify(s));
            if (s.role === 'admin' || s.role === 'gestore') localStorage.setItem('atmbet_is_admin', 'true');
            else localStorage.removeItem('atmbet_is_admin');
            return s;
        } catch (e) { console.warn('[AtmBet] syncSession', e); return null; }
    }

    async function signOut() {
        try { if (client) await client.auth.signOut(); } catch (e) {}
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem('atmbet_is_admin');
        sessionStorage.removeItem('atmbet_admin_authenticated');
    }

    window.sb = client;
    window.AtmAuth = { syncSession, signOut, toLegacySession, todayRome };
})();
