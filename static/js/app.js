/* ═══════════════════════════════════════════════════════════
   Shadowing Practice — Frontend (LMNT + Piper + Multi-IA fallback)
   ═══════════════════════════════════════════════════════════ */

const state = {
    sessionData: null,
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
    recordingCount: 0,
    activeTimer: null,
    voices: [],
    apiStatus: {
        lmnt: false,
        piper: false,
        deepseek: false,
        openrouter: false,
        openai_chat: false,
        ollama: false,
        ai_text: false,
        deepgram: false,
        youtube_transcript: false,
        yt_dlp: false,
        local_whisper: false,
        openai_transcribe: false,
    },
    loopEnabled: false,
    loopCount: 0,
    loopMax: 5,
    historyAccordionOpen: true,
    adaptiveFlashcards: {
        deck: [],
        index: 0,
        flipped: false,
        submitting: false,
        lastData: null,
    },
    ttsCache: {},  // Cache TTS per sentence to avoid repeat API calls
    youtubeKaraoke: {
        apiPromise: null,
        player: null,
        playerReady: false,
        videoId: '',
        segments: [],
        transcriptMeta: null,
        segmentEls: [],
        activeSegment: -1,
        syncRafId: null,
        autoScroll: true,
        delaySec: 0,
        study: null,
        studyLoading: false,
        studyAudio: null,
        studyAudioButton: null,
        studySpeechUtterance: null,
        autoScrollHoldUntil: 0,
        autoScrollLastAt: 0,
    },
};

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const LEARNER_KEY_STORAGE = 'shadowingLearnerKey';

function getLearnerKey() {
    try {
        let key = localStorage.getItem(LEARNER_KEY_STORAGE);
        if (key) return key;
        if (window.crypto?.randomUUID) key = `web-${window.crypto.randomUUID()}`;
        else key = `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
        localStorage.setItem(LEARNER_KEY_STORAGE, key);
        return key;
    } catch {
        return 'web-default';
    }
}

function getIntegrationContext() {
    try {
        const params = new URLSearchParams(window.location.search || '');
        return {
            external_user_id: (params.get('external_user_id') || params.get('user_id') || '').trim(),
            external_email: (params.get('external_email') || params.get('email') || '').trim(),
            external_phone: (params.get('external_phone') || params.get('phone') || '').trim(),
            source_system: (params.get('source_system') || '').trim(),
        };
    } catch {
        return {
            external_user_id: '',
            external_email: '',
            external_phone: '',
            source_system: '',
        };
    }
}

function buildLearnerHeaders(extraHeaders = {}) {
    const integration = getIntegrationContext();
    const headers = {
        ...extraHeaders,
        'X-Learner-Key': getLearnerKey(),
    };
    if (integration.external_user_id) headers['X-External-User-Id'] = integration.external_user_id;
    if (integration.external_email) headers['X-External-User-Email'] = integration.external_email;
    if (integration.external_phone) headers['X-External-Phone'] = integration.external_phone;
    if (integration.source_system) headers['X-Source-System'] = integration.source_system;
    return headers;
}

function withLearnerPayload(payload) {
    const integration = getIntegrationContext();
    return {
        ...(payload || {}),
        learner_key: payload?.learner_key || getLearnerKey(),
        external_user_id: payload?.external_user_id || integration.external_user_id || undefined,
        external_email: payload?.external_email || integration.external_email || undefined,
        external_phone: payload?.external_phone || integration.external_phone || undefined,
        source_system: payload?.source_system || integration.source_system || undefined,
    };
}

function withLearnerQuery(url) {
    try {
        const parsed = new URL(url, window.location.origin);
        const integration = getIntegrationContext();
        if (!parsed.searchParams.get('learner_key')) {
            parsed.searchParams.set('learner_key', getLearnerKey());
        }
        if (integration.external_user_id && !parsed.searchParams.get('external_user_id') && !parsed.searchParams.get('user_id')) {
            parsed.searchParams.set('external_user_id', integration.external_user_id);
        }
        if (integration.external_email && !parsed.searchParams.get('external_email') && !parsed.searchParams.get('email')) {
            parsed.searchParams.set('external_email', integration.external_email);
        }
        if (integration.external_phone && !parsed.searchParams.get('external_phone') && !parsed.searchParams.get('phone')) {
            parsed.searchParams.set('external_phone', integration.external_phone);
        }
        if (integration.source_system && !parsed.searchParams.get('source_system')) {
            parsed.searchParams.set('source_system', integration.source_system);
        }
        return `${parsed.pathname}${parsed.search}`;
    } catch {
        const integration = getIntegrationContext();
        const joiner = url.includes('?') ? '&' : '?';
        const params = [`learner_key=${encodeURIComponent(getLearnerKey())}`];
        if (integration.external_user_id) params.push(`external_user_id=${encodeURIComponent(integration.external_user_id)}`);
        if (integration.external_email) params.push(`external_email=${encodeURIComponent(integration.external_email)}`);
        if (integration.external_phone) params.push(`external_phone=${encodeURIComponent(integration.external_phone)}`);
        if (integration.source_system) params.push(`source_system=${encodeURIComponent(integration.source_system)}`);
        return `${url}${joiner}${params.join('&')}`;
    }
}

function getSelectedTtsEngine() {
    return ($('#engine-select')?.value || 'local').trim().toLowerCase() || 'local';
}

function getTtsLoadingMessage(engine) {
    if (engine === 'lmnt') return '🎙️ Gerando áudio com voz natural LMNT...';
    if (engine === 'deepgram') return '🧠 Gerando áudio com voz natural Deepgram Aura-2...';
    return '🖥️ Gerando áudio local com Piper...';
}

function inferPiperPracticeProfile(text, fallbackProfile = 'lesson') {
    const normalized = String(text || '').trim();
    if (!normalized) return fallbackProfile;
    const wordCount = normalized.split(/\s+/).filter(Boolean).length;
    const sentenceCount = (normalized.match(/[.!?。！？]+/g) || []).length;

    // For long passages, keep the stable fallback profile instead of
    // promoting the whole block to "question" just because it ends with "?".
    if (wordCount > 18 || sentenceCount > 1) return fallbackProfile;

    if (/[?？]\s*$/.test(normalized)) return 'question';
    if (/[!！]\s*$/.test(normalized)) return 'expressive';
    return fallbackProfile;
}

function buildPiperPracticePayload(text, contextHint, fallbackProfile = 'lesson') {
    return {
        tts_context: contextHint,
        piper_profile: inferPiperPracticeProfile(text, fallbackProfile),
    };
}

function extractApiErrorMessage(data, fallback = 'Erro na requisição.') {
    if (!data) return fallback;
    if (typeof data === 'string') return data;
    if (Array.isArray(data.errors) && data.errors.length) return String(data.errors[0]);
    if (typeof data.error === 'string' && data.error.trim()) return data.error.trim();
    if (typeof data.message === 'string' && data.message.trim()) return data.message.trim();
    return fallback;
}

async function readJsonSafe(response) {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

async function postJson(url, payload) {
    const response = await fetch(url, {
        method: 'POST',
        headers: buildLearnerHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(withLearnerPayload(payload)),
    });
    const data = await readJsonSafe(response);
    if (!response.ok) {
        throw new Error(extractApiErrorMessage(data, `Erro HTTP ${response.status} em ${url}.`));
    }
    if (data === null) {
        throw new Error(`Resposta inválida em ${url}.`);
    }
    return data;
}

async function getJson(url) {
    const response = await fetch(withLearnerQuery(url), {
        headers: buildLearnerHeaders(),
    });
    const data = await readJsonSafe(response);
    if (!response.ok) {
        throw new Error(extractApiErrorMessage(data, `Erro HTTP ${response.status} em ${url}.`));
    }
    if (data === null) {
        throw new Error(`Resposta inválida em ${url}.`);
    }
    return data;
}

async function runAgent(intent, query, payload) {
    const envelope = await postJson('/api/agent/run', {
        intent: intent || 'auto',
        query: query || '',
        payload: withLearnerPayload(payload),
    });
    if (!envelope?.ok) {
        throw new Error(extractApiErrorMessage(envelope, 'Falha no orquestrador de agentes.'));
    }
    return envelope;
}

async function runAgentWithFallback({ intent, query, payload, fallbackCall, operation = 'agent_call' }) {
    try {
        const envelope = await runAgent(intent, query, payload);
        const hasResult = envelope && typeof envelope === 'object' && ('result' in envelope);
        return { result: hasResult ? envelope.result : envelope, envelope, source: 'agent' };
    } catch (agentError) {
        if (typeof fallbackCall !== 'function') throw agentError;
        console.warn(`[Agent fallback] ${operation}: ${agentError?.message || agentError}`);
        const fallbackData = await fallbackCall(agentError);
        return { result: fallbackData, envelope: null, source: 'fallback', agentError };
    }
}

function unwrapAgentResult(result) {
    let current = result;
    for (let i = 0; i < 3; i += 1) {
        if (!current || typeof current !== 'object') break;
        if (!('result' in current)) break;
        const looksLikeWrapper =
            ('ok' in current)
            || ('mode' in current)
            || ('error' in current)
            || ('errors' in current)
            || ('warnings' in current);
        if (!looksLikeWrapper) break;
        current = current.result;
    }
    return current;
}

// ─── Init ──────────────────────────────────────────────────
(async function init() {
    loadProgress();
    checkApiStatus();
    initWhatsAppTools();
    loadDiskStats();
    setupHistoryAccordion();
    loadSessionHistory();
    setupWordCounter();
    initAdaptiveFlashcards();
    initYoutubeKaraoke();
    animateStaggerElements($$('#tab-practice .card'), 'is-revealing', 24);
    $('#prog-date').value = new Date().toISOString().split('T')[0];
})();

async function checkApiStatus() {
    try {
        const res = await fetch('/api/status');
        state.apiStatus = await res.json();
        renderApiBadges();
    } catch {}
}

function renderApiBadges() {
    const el = $('#api-badges');
    el.innerHTML = `
        <span class="badge ${state.apiStatus.lmnt ? 'badge-ok' : 'badge-off'}">
            🎙️ LMNT ${state.apiStatus.lmnt ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.piper ? 'badge-ok' : 'badge-off'}">
            🖥️ Piper ${state.apiStatus.piper ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.deepseek ? 'badge-ok' : 'badge-off'}">
            🐋 DeepSeek ${state.apiStatus.deepseek ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.openrouter ? 'badge-ok' : 'badge-off'}">
            🤖 OpenRouter ${state.apiStatus.openrouter ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.openai_chat ? 'badge-ok' : 'badge-off'}">
            🧠 OpenAI Chat ${state.apiStatus.openai_chat ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.ollama ? 'badge-ok' : 'badge-off'}">
            🦙 Ollama ${state.apiStatus.ollama ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.ai_text ? 'badge-ok' : 'badge-off'}">
            🧠 IA texto ${state.apiStatus.ai_text ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.deepgram ? 'badge-ok' : 'badge-off'}">
            🎯 Deepgram ${state.apiStatus.deepgram ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.youtube_transcript ? 'badge-ok' : 'badge-off'}">
            🎬 YouTube CC ${state.apiStatus.youtube_transcript ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.yt_dlp ? 'badge-ok' : 'badge-off'}">
            🧰 yt-dlp ${state.apiStatus.yt_dlp ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.local_whisper ? 'badge-ok' : 'badge-off'}">
            🎧 Local Whisper ${state.apiStatus.local_whisper ? '✓' : '✗'}
        </span>
        <span class="badge ${state.apiStatus.openai_transcribe ? 'badge-ok' : 'badge-off'}">
            🎙️ OpenAI STT ${state.apiStatus.openai_transcribe ? '✓' : '✗'}
        </span>
    `;
}

// ─── WhatsApp Tools ───────────────────────────────────────
function initWhatsAppTools() {
    if (!$('#btn-wa-status')) return;

    $('#btn-wa-status').addEventListener('click', async () => {
        await refreshWhatsAppStatus({ showSuccess: true });
    });

    $('#btn-wa-students').addEventListener('click', async () => {
        await loadWhatsAppStudents();
    });

    $('#btn-wa-setup').addEventListener('click', async () => {
        await setupWhatsAppInstance();
    });

    $('#btn-wa-qrcode').addEventListener('click', async () => {
        await loadWhatsAppQrCode();
    });

    refreshWhatsAppStatus({ showSuccess: false });
}

function setWhatsAppFeedback(message, type = 'info') {
    const el = $('#wa-feedback');
    if (!el) return;
    el.textContent = message || '';
    el.classList.remove('is-error', 'is-success');
    if (type === 'error') el.classList.add('is-error');
    if (type === 'success') el.classList.add('is-success');
}

function setWhatsAppBusy(isBusy) {
    ['#btn-wa-status', '#btn-wa-students', '#btn-wa-setup', '#btn-wa-qrcode'].forEach(sel => {
        const btn = $(sel);
        if (btn) btn.disabled = isBusy;
    });
}

function prettyJson(value) {
    if (value === undefined) return '';
    try {
        return JSON.stringify(value, null, 2);
    } catch {
        return String(value ?? '');
    }
}

function renderWhatsAppStatusBadges(status) {
    const el = $('#wa-status-badges');
    if (!el) return;

    const enabled = Boolean(status?.enabled);
    const schedulerRunning = Boolean(status?.scheduler_running);
    const students = status?.students || {};
    const totalStudents = Number(students.total || 0);
    const activeStudents = Number(students.active || 0);
    const instanceOk = enabled && status?.instance_status && !status.instance_status.error;

    el.innerHTML = `
        <span class="badge ${enabled ? 'badge-ok' : 'badge-off'}">WhatsApp ${enabled ? 'ON' : 'OFF'}</span>
        <span class="badge ${instanceOk ? 'badge-ok' : 'badge-off'}">Instância ${instanceOk ? 'OK' : 'Pendente'}</span>
        <span class="badge ${schedulerRunning ? 'badge-ok' : 'badge-off'}">Agendador ${schedulerRunning ? 'ON' : 'OFF'}</span>
        <span class="badge ${enabled ? 'badge-ok' : 'badge-off'}">Alunos ${activeStudents}/${totalStudents}</span>
    `;
}

async function refreshWhatsAppStatus({ showSuccess = false } = {}) {
    const statusEl = $('#wa-status-json');
    if (!statusEl) return null;

    setWhatsAppBusy(true);
    try {
        const data = await getJson('/whatsapp/status');
        statusEl.textContent = prettyJson(data);
        renderWhatsAppStatusBadges(data);

        if (data?.enabled === false) {
            setWhatsAppFeedback('WhatsApp desativado. Defina WHATSAPP_ENABLED=1 no .env e reinicie a aplicação.', 'error');
        } else if (showSuccess) {
            setWhatsAppFeedback('Status do WhatsApp atualizado.', 'success');
        } else {
            setWhatsAppFeedback('');
        }

        return data;
    } catch (err) {
        statusEl.textContent = `Erro ao carregar status: ${err.message}`;
        renderWhatsAppStatusBadges({ enabled: false });
        setWhatsAppFeedback(`Falha no status: ${err.message}`, 'error');
        return null;
    } finally {
        setWhatsAppBusy(false);
    }
}

async function setupWhatsAppInstance() {
    const webhookInput = $('#wa-webhook-url');
    const statusEl = $('#wa-status-json');
    if (!statusEl) return;

    const webhookUrl = (webhookInput?.value || '').trim();
    const payload = webhookUrl ? { webhook_url: webhookUrl } : {};

    setWhatsAppBusy(true);
    setWhatsAppFeedback('Configurando instância no Evolution API...');
    try {
        const data = await postJson('/whatsapp/setup', payload);
        statusEl.textContent = prettyJson(data);

        if (data?.webhook_url && webhookInput) {
            webhookInput.value = data.webhook_url;
        }

        setWhatsAppFeedback('Instância configurada. Agora carregue o QR Code para conectar o aparelho.', 'success');
        await refreshWhatsAppStatus({ showSuccess: false });
    } catch (err) {
        setWhatsAppFeedback(`Falha ao configurar instância: ${err.message}`, 'error');
    } finally {
        setWhatsAppBusy(false);
    }
}

function getQrImageSource(payload) {
    const imageCandidates = [
        payload?.qrcode,
        payload?.base64,
        payload?.qr,
        payload?.qrcode?.base64,
        payload?.data?.qrcode,
        payload?.data?.base64,
    ];

    for (const raw of imageCandidates) {
        if (typeof raw !== 'string') continue;
        const value = raw.trim();
        if (!value) continue;

        if (/^data:image\//i.test(value)) return value;
        if (/^https?:\/\//i.test(value)) return value;

        const compact = value.replace(/\s+/g, '');
        if (compact.length > 220 && /^[A-Za-z0-9+/=]+$/.test(compact)) {
            return `data:image/png;base64,${compact}`;
        }
    }

    const qrCodeTextCandidates = [
        payload?.code,
        payload?.qrcode?.code,
        payload?.qrcode?.qrcode,
        payload?.data?.code,
        payload?.data?.qrcode,
        payload?.qrcode,
    ];
    for (const raw of qrCodeTextCandidates) {
        if (typeof raw !== 'string') continue;
        const value = raw.trim();
        if (!value) continue;
        // Código do QR textual (como a Evolution Manager usa).
        if (!/^data:image\//i.test(value) && !/^https?:\/\//i.test(value)) {
            return `https://api.qrserver.com/v1/create-qr-code/?size=320x320&data=${encodeURIComponent(value)}`;
        }
    }

    return '';
}

async function loadWhatsAppQrCode() {
    const section = $('#wa-qr-section');
    const img = $('#wa-qr-image');
    const rawEl = $('#wa-qr-raw');
    if (!section || !img || !rawEl) return;

    setWhatsAppBusy(true);
    setWhatsAppFeedback('Buscando QR Code...');
    try {
        const data = await getJson('/whatsapp/qrcode');
        const imageSrc = getQrImageSource(data);

        section.classList.remove('hidden');
        rawEl.classList.remove('hidden');
        rawEl.textContent = prettyJson(data);

        if (imageSrc) {
            img.src = imageSrc;
            img.classList.remove('hidden');
            setWhatsAppFeedback('QR Code carregado. Escaneie pelo seu WhatsApp.', 'success');
        } else {
            img.src = '';
            img.classList.add('hidden');
            const count = Number(data?.count || data?.qrcode?.count || 0);
            const managerUrl = String(data?.manager_url || '').trim();
            if (count === 0) {
                setWhatsAppFeedback(
                    `A Evolution retornou count=0 (sem QR ativo no momento). Tente "Configurar instância" e depois "Carregar QR Code"${managerUrl ? `, ou abra ${managerUrl}` : ''}.`,
                    'error'
                );
            } else if (data?.pairingCode) {
                setWhatsAppFeedback(`Código de pareamento: ${data.pairingCode}`, 'success');
            } else {
                setWhatsAppFeedback('QR indisponível neste formato. Veja o payload bruto abaixo.', 'error');
            }
        }

        await refreshWhatsAppStatus({ showSuccess: false });
    } catch (err) {
        section.classList.remove('hidden');
        img.src = '';
        img.classList.add('hidden');
        rawEl.classList.remove('hidden');
        rawEl.textContent = `Falha ao obter QR Code: ${err.message}`;
        setWhatsAppFeedback(`Falha ao carregar QR Code: ${err.message}`, 'error');
    } finally {
        setWhatsAppBusy(false);
    }
}

async function loadWhatsAppStudents() {
    const studentsEl = $('#wa-students-json');
    if (!studentsEl) return;

    setWhatsAppBusy(true);
    try {
        const data = await getJson('/whatsapp/students');
        studentsEl.textContent = prettyJson(data);
        const total = Number(data?.count?.total || 0);
        setWhatsAppFeedback(`Lista de alunos atualizada (${total} aluno(s)).`, 'success');
    } catch (err) {
        studentsEl.textContent = `Falha ao carregar alunos: ${err.message}`;
        setWhatsAppFeedback(`Falha ao carregar alunos: ${err.message}`, 'error');
    } finally {
        setWhatsAppBusy(false);
    }
}

// ─── Tabs ──────────────────────────────────────────────────
function scrollAppToTop() {
    const activeTab = document.querySelector('.tab-content.active');
    const targetTop = activeTab
        ? Math.max(0, activeTab.getBoundingClientRect().top + window.scrollY - 16)
        : 0;
    const behavior = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
        ? 'auto'
        : 'smooth';
    const performScroll = () => {
        window.scrollTo({ top: targetTop, behavior });
        document.documentElement?.scrollTo?.({ top: targetTop, behavior });
        document.body?.scrollTo?.({ top: targetTop, behavior });
        activeTab?.scrollIntoView?.({ behavior, block: 'start' });
    };

    requestAnimationFrame(() => {
        performScroll();
    });

    setTimeout(performScroll, 180);
}

$$('.tab').forEach(tab => {
    tab.addEventListener('click', async () => {
        $$('.tab').forEach(t => t.classList.remove('active'));
        $$('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const activeTab = $(`#tab-${tab.dataset.tab}`);
        activeTab.classList.add('active');
        animateStaggerElements(activeTab.querySelectorAll('.card'), 'is-revealing', 24);
        scrollAppToTop();
        if (tab.dataset.tab === 'progress') {
            await loadProgress();
            scrollAppToTop();
        }
    });
});

// ═══════════════════════════════════════════════════════════//  WORD COUNTER
// ═════════════════════════════════════════════════════════
function setupWordCounter() {
    const ta = $('#input-text');
    const counter = $('#word-count');
    const update = () => {
        const text = ta.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        const chars = text.length;
        const estTime = Math.ceil(words / 150); // ~150 words/min speaking
        counter.textContent = `${words} palavras · ${chars} caracteres · ~${estTime} min áudio`;
    };
    ta.addEventListener('input', update);
    update();
}

// ═════════════════════════════════════════════════════════//  GERAR SESSÃO
// ═══════════════════════════════════════════════════════════
$('#btn-generate').addEventListener('click', async () => {
    const text = $('#input-text').value.trim();
    if (!text) return alert('Cole um texto para praticar!');

    const lang = $('#lang-select').value || undefined;
    const voice = $('#voice-select').value;
    const ttsEngine = getSelectedTtsEngine();
    const piperPayload = buildPiperPracticePayload(text, 'shadowing_practice_session', 'story');

    show('#loading'); hide('#result-section'); hide('#analysis-section');
    $('#loading-text').textContent = getTtsLoadingMessage(ttsEngine);
    $('#btn-generate').disabled = true;

    try {
        const requestPayload = { text, lang, voice, tts_engine: ttsEngine, ...piperPayload };
        const { result } = await runAgentWithFallback({
            intent: 'practice',
            query: 'gerar sessão de prática',
            payload: { ...requestPayload, action: 'generate_session' },
            fallbackCall: () => postJson('/api/generate', requestPayload),
            operation: 'generate_session',
        });
        const sessionData = (result && typeof result === 'object' && result.session)
            ? result.session
            : result;
        if (!sessionData?.audio_url) throw new Error('Resposta inválida ao gerar sessão.');
        state.sessionData = sessionData;
        renderSession(sessionData);
        saveToHistory(sessionData);
    } catch (err) {
        alert(`Erro: ${err.message}`);
    } finally {
        hide('#loading');
        $('#btn-generate').disabled = false;
    }
});

// ═══════════════════════════════════════════════════════════
//  ANALISAR COM IA
// ═══════════════════════════════════════════════════════════
$('#btn-analyze').addEventListener('click', async () => {
    const text = $('#input-text').value.trim();
    if (!text) return alert('Cole um texto primeiro!');

    show('#loading'); hide('#analysis-section');
    $('#loading-text').textContent = '🤖 Analisando com Inteligência Artificial...';
    $('#btn-analyze').disabled = true;

    try {
        const requestPayload = { text, lang: $('#lang-select').value || 'en' };
        const { result } = await runAgentWithFallback({
            intent: 'practice',
            query: 'analisar texto',
            payload: { ...requestPayload, action: 'analyze' },
            fallbackCall: () => postJson('/api/analyze', requestPayload),
            operation: 'analyze_text',
        });
        if (!result?.analysis) throw new Error('Resposta inválida da análise.');
        renderAnalysis(result.analysis);
    } catch (err) {
        alert(`Erro: ${err.message}`);
    } finally {
        hide('#loading');
        $('#btn-analyze').disabled = false;
    }
});

function renderAnalysis(a) {
    show('#analysis-section');
    const el = $('#analysis-content');

    if (a.raw_analysis) {
        el.innerHTML = `<pre class="ai-raw">${escapeHtml(a.raw_analysis)}</pre>`;
        return;
    }

    let html = '';

    // Difficulty
    if (a.difficulty_level) {
        const colors = { beginner: '#00E676', intermediate: '#FFD93D', advanced: '#FF6B6B' };
        html += `<div class="ai-row">
            <span class="ai-label">Nível:</span>
            <span class="badge" style="background:${colors[a.difficulty_level] || '#888'};color:#000">
                ${a.difficulty_level.toUpperCase()} (${a.difficulty_score || '?'}/5)
            </span>
        </div>`;
    }

    // Pronunciation tips
    if (a.pronunciation_tips?.length) {
        html += `<h3>🗣️ Dicas de Pronúncia</h3><div class="ai-chips">`;
        a.pronunciation_tips.forEach(t => {
            html += `<div class="ai-chip">
                <strong>${escapeHtml(t.word)}</strong>
                <span class="phonetic">${escapeHtml(t.phonetic || '')}</span>
                <span class="tip">${escapeHtml(t.tip)}</span>
            </div>`;
        });
        html += '</div>';
    }

    // Linking sounds
    if (a.linking_sounds?.length) {
        html += `<h3>🔗 Linking Sounds</h3><div class="ai-chips">`;
        a.linking_sounds.forEach(l => {
            html += `<div class="ai-chip">
                <strong>"${escapeHtml(l.phrase)}"</strong>
                <span class="phonetic">→ ${escapeHtml(l.how)}</span>
                <span class="tip">${escapeHtml(l.tip)}</span>
            </div>`;
        });
        html += '</div>';
    }

    // Vocabulary
    if (a.key_vocabulary?.length) {
        html += `<h3>📚 Vocabulário Chave</h3><div class="vocab-grid">`;
        a.key_vocabulary.forEach(v => {
            html += `<div class="vocab-item">
                <strong>${escapeHtml(v.word)}</strong>
                <span>${escapeHtml(v.meaning)}</span>
                ${v.example ? `<em>"${escapeHtml(v.example)}"</em>` : ''}
            </div>`;
        });
        html += '</div>';
    }

    // Intonation
    if (a.intonation_notes) {
        html += `<h3>🎵 Entonação e Ritmo</h3><p class="ai-note">${escapeHtml(a.intonation_notes)}</p>`;
    }

    // Focus
    if (a.shadowing_focus?.length) {
        html += `<h3>🎯 Foco desta Sessão</h3><ul class="ai-list">`;
        a.shadowing_focus.forEach(f => { html += `<li>${escapeHtml(f)}</li>`; });
        html += '</ul>';
    }

    // Mistakes
    if (a.common_mistakes_br?.length) {
        html += `<h3>⚠️ Erros Comuns de Brasileiros</h3><ul class="ai-list ai-list-warn">`;
        a.common_mistakes_br.forEach(m => { html += `<li>${escapeHtml(m)}</li>`; });
        html += '</ul>';
    }

    el.innerHTML = html;
    animateStaggerElements($$('#analysis-section .card, #analysis-content > *'), 'is-revealing', 26);
    $('#analysis-section').scrollIntoView({ behavior: 'smooth' });
}

// ═════════════════════════════════════════════════════════
//  COMBO: GERAR + ANALISAR
// ═════════════════════════════════════════════════════════
$('#btn-combo').addEventListener('click', async () => {
    const text = $('#input-text').value.trim();
    if (!text) return alert('Cole um texto para praticar!');

    const lang = $('#lang-select').value || undefined;
    const voice = $('#voice-select').value;
    const ttsEngine = getSelectedTtsEngine();
    const piperPayload = buildPiperPracticePayload(text, 'shadowing_practice_session', 'story');

    show('#loading'); hide('#result-section'); hide('#analysis-section');
    $('#loading-text').textContent = `⚡ ${getTtsLoadingMessage(ttsEngine).replace('...', '')} + análise IA em paralelo...`;
    $('#btn-combo').disabled = true;

    try {
        const sessionPayload = { text, lang, voice, tts_engine: ttsEngine, ...piperPayload };
        const analysisPayload = { text, lang: lang || 'en' };
        const [genOutcome, anaOutcome] = await Promise.allSettled([
            runAgentWithFallback({
                intent: 'practice',
                query: 'gerar sessão de prática',
                payload: { ...sessionPayload, action: 'generate_session' },
                fallbackCall: () => postJson('/api/generate', sessionPayload),
                operation: 'combo_generate_session',
            }),
            runAgentWithFallback({
                intent: 'practice',
                query: 'analisar texto',
                payload: { ...analysisPayload, action: 'analyze' },
                fallbackCall: () => postJson('/api/analyze', analysisPayload),
                operation: 'combo_analyze_text',
            }),
        ]);

        let successCount = 0;
        const errors = [];

        if (genOutcome.status === 'fulfilled') {
            const rawSession = genOutcome.value?.result;
            const resolvedSession = (rawSession && typeof rawSession === 'object' && rawSession.session)
                ? rawSession.session
                : rawSession;
            if (resolvedSession?.audio_url) {
                state.sessionData = resolvedSession;
                renderSession(resolvedSession);
                saveToHistory(resolvedSession);
                successCount += 1;
            } else {
                errors.push('Sessão retornou payload inválido.');
            }
        } else {
            errors.push(genOutcome.reason?.message || 'Falha ao gerar sessão.');
        }

        if (anaOutcome.status === 'fulfilled') {
            const analysisData = anaOutcome.value?.result;
            if (analysisData?.analysis) {
                renderAnalysis(analysisData.analysis);
                successCount += 1;
            } else {
                errors.push('Análise retornou payload inválido.');
            }
        } else {
            errors.push(anaOutcome.reason?.message || 'Falha na análise.');
        }

        if (!successCount) {
            throw new Error(errors.join(' | ') || 'Falha ao gerar sessão e análise.');
        }
        if (errors.length) {
            console.warn('[Combo parcial]', errors.join(' | '));
        }
    } catch (err) {
        alert(`Erro: ${err.message}`);
    } finally {
        hide('#loading');
        $('#btn-combo').disabled = false;
    }
});

// ═══════════════════════════════════════════════════════════
//  RENDERIZAR SESSÃO + KARAOKÊ CONTÍNUO
// ═══════════════════════════════════════════════════════════
function renderSession(data) {
    show('#result-section');

    // Show Mission Control sidebar
    showMissionControl();

    // Engine badge
    const badge = $('#engine-badge');
    if (data.tts_engine === 'lmnt') {
        badge.textContent = '🎙️ LMNT Natural Voice';
        badge.className = 'engine-badge badge-lmnt';
        badge.title = '';
    } else if (data.tts_engine === 'deepgram') {
        badge.textContent = '🧠 Deepgram Aura-2';
        badge.className = 'engine-badge badge-deepgram';
        badge.title = '';
    } else if (data.tts_engine === 'piper') {
        badge.textContent = '🖥️ Piper (Local)';
        badge.className = 'engine-badge badge-local';
        const profileLabel = data.piper_meta?.profile_label || '';
        badge.title = profileLabel ? `Piper · perfil ${profileLabel}` : 'Piper local';
    } else {
        badge.textContent = '🔊 TTS Local';
        badge.className = 'engine-badge badge-local';
        badge.title = '';
    }

    // Audio
    const audio = $('#main-audio');
    audio.src = data.audio_url;
    audio.playbackRate = 1;

    // ─── Build continuous karaoke text ───
    const container = $('#karaoke-text');
    container.innerHTML = '';
    const sentenceEls = [];

    // Build flat word list for mapping LMNT durations
    const allWordEls = [];
    data.sentences.forEach((sentence, i) => {
        const span = document.createElement('span');
        span.className = 'k-sentence';
        span.dataset.index = i;
        const words = sentence.split(/\s+/);
        words.forEach((w, wi) => {
            const ws = document.createElement('span');
            ws.className = 'k-word';
            ws.textContent = w;
            span.appendChild(ws);
            allWordEls.push({ el: ws, text: w, sentenceIdx: i });
            if (wi < words.length - 1) span.appendChild(document.createTextNode(' '));
        });
        // Click sentence to play individually
        span.addEventListener('click', () => playSentence(sentence, data.language, data.voice, span));
        container.appendChild(span);
        // Add space between sentences
        if (i < data.sentences.length - 1) container.appendChild(document.createTextNode(' '));
        sentenceEls.push({ el: span, text: sentence, words, charLen: sentence.length, wordCount: words.length });
    });

    // ─── Build timing data ───
    state.sentenceSync = { els: sentenceEls, ranges: [], activeSentence: -1, wordTimings: null };

    const hasDurations = data.durations && Array.isArray(data.durations) && data.durations.length > 0;

    function buildTimingsFromDurations(durations) {
        // LMNT returns [{text, start, duration}, ...] for every token (words, punctuation, spaces)
        // Filter to actual words only
        const wordDurs = durations.filter(d =>
            d.text && d.text.trim().length > 0 && !/^[\s.,;:!?'"()\-\u2013\u2014]+$/.test(d.text.trim())
        );

        // Map LMNT word durations to our DOM word elements
        const wordTimings = [];
        let durIdx = 0;
        for (let i = 0; i < allWordEls.length && durIdx < wordDurs.length; i++) {
            const wEl = allWordEls[i];
            const dur = wordDurs[durIdx];
            const cleanWord = wEl.text.replace(/[^a-zA-Z0-9\u00C0-\u024F]/g, '').toLowerCase();
            const cleanDur = dur.text.replace(/[^a-zA-Z0-9\u00C0-\u024F]/g, '').toLowerCase();
            if (cleanWord === cleanDur || cleanWord.startsWith(cleanDur) || cleanDur.startsWith(cleanWord)) {
                wordTimings.push({
                    el: wEl.el,
                    sentenceIdx: wEl.sentenceIdx,
                    start: dur.start,
                    end: dur.start + dur.duration,
                    duration: dur.duration,
                });
                durIdx++;
            } else {
                let found = false;
                for (let j = durIdx; j < Math.min(durIdx + 3, wordDurs.length); j++) {
                    const cd = wordDurs[j].text.replace(/[^a-zA-Z0-9\u00C0-\u024F]/g, '').toLowerCase();
                    if (cleanWord === cd || cleanWord.startsWith(cd) || cd.startsWith(cleanWord)) {
                        wordTimings.push({
                            el: wEl.el, sentenceIdx: wEl.sentenceIdx,
                            start: wordDurs[j].start, end: wordDurs[j].start + wordDurs[j].duration,
                            duration: wordDurs[j].duration,
                        });
                        durIdx = j + 1;
                        found = true;
                        break;
                    }
                }
                if (!found) { durIdx++; i--; }
            }
        }

        // Build sentence ranges from word timings
        const sentenceRanges = sentenceEls.map((_, si) => {
            const sentWords = wordTimings.filter(w => w.sentenceIdx === si);
            if (sentWords.length === 0) return null;
            return {
                start: sentWords[0].start,
                end: sentWords[sentWords.length - 1].end,
                duration: sentWords[sentWords.length - 1].end - sentWords[0].start,
                wordTimings: sentWords,
            };
        });

        return { wordTimings, sentenceRanges };
    }

    function hasUsableTimingRanges(ranges) {
        if (!Array.isArray(ranges) || !ranges.length) return false;
        return ranges.some(r =>
            r
            && Number.isFinite(r.start)
            && Number.isFinite(r.end)
            && Number.isFinite(r.duration)
            && r.end > r.start
            && r.duration > 0.08
        );
    }

    function calcTimeRangesFallback(duration) {
        // Improved fallback: syllable-based estimation
        function estimateSyllables(word) {
            const w = word.toLowerCase().replace(/[^a-z]/g, '');
            if (w.length <= 3) return 1;
            let count = w.replace(/(?:[^laeiouy]|ed|[^laeiouy]e)$/g, '')
                         .replace(/^y/, '').match(/[aeiouy]{1,2}/g);
            return count ? Math.max(1, count.length) : 1;
        }
        const sentenceWeights = sentenceEls.map(se => {
            const syllables = se.words.reduce((s, w) => s + estimateSyllables(w), 0);
            const pauseWeight = /[.!?]$/.test(se.text) ? 0.4 : 0.15;
            return { syllables, pauseWeight };
        });
        const totalSyllables = sentenceWeights.reduce((s, w) => s + w.syllables, 0);
        const totalPauseTime = sentenceWeights.reduce((s, w) => s + w.pauseWeight, 0);
        const speechDuration = Math.max(0.5, duration - totalPauseTime);
        let t = 0;
        state.sentenceSync.ranges = sentenceEls.map((se, i) => {
            const w = sentenceWeights[i];
            const proportion = w.syllables / totalSyllables;
            const sentDuration = Math.max(0.2, speechDuration * proportion);
            const start = t;
            t += sentDuration + w.pauseWeight;
            return { start, end: start + sentDuration, duration: sentDuration, wordTimings: null };
        });
    }

    if (hasDurations) {
        try {
            const timingData = buildTimingsFromDurations(data.durations);
            const mappedWords = timingData.wordTimings.length;
            const totalWords = Math.max(1, allWordEls.length);
            const wordCoverage = mappedWords / totalWords;
            const fullSentenceCoverage = timingData.sentenceRanges.every(r => r && r.duration > 0.08);

            if (fullSentenceCoverage && wordCoverage >= 0.55) {
                state.sentenceSync.ranges = timingData.sentenceRanges;
                state.sentenceSync.wordTimings = timingData.wordTimings;
                console.log('[Karaoke] Using LMNT word-level durations for precise sync');
            } else {
                console.warn(
                    '[Karaoke] LMNT durations coverage insuficiente; usando fallback proporcional',
                    { mappedWords, totalWords, wordCoverage }
                );
                state.sentenceSync.ranges = [];
                state.sentenceSync.wordTimings = null;
            }
        } catch (e) {
            console.warn('[Karaoke] Failed to parse durations, using fallback', e);
        }
    }

    // Fallback: proportional ranges when no real timing available
    if (!hasUsableTimingRanges(state.sentenceSync.ranges)) {
        const applyFallbackIfNeeded = () => {
            if (audio.duration && isFinite(audio.duration) && !hasUsableTimingRanges(state.sentenceSync.ranges)) {
                calcTimeRangesFallback(audio.duration);
            }
        };
        audio.addEventListener('loadedmetadata', applyFallbackIfNeeded);
        audio.addEventListener('durationchange', applyFallbackIfNeeded);
        applyFallbackIfNeeded();
    }

    // ─── Smooth sync with requestAnimationFrame ───
    if (state._syncHandler) audio.removeEventListener('timeupdate', state._syncHandler);
    if (state._rafId) cancelAnimationFrame(state._rafId);
    state._rafId = null;

    function syncKaraoke() {
        const sync = state.sentenceSync;
        if (!sync.ranges.length) {
            state._rafId = requestAnimationFrame(syncKaraoke);
            return;
        }
        const ct = audio.currentTime;

        // Global progress bar
        if (audio.duration && isFinite(audio.duration)) {
            $('#karaoke-progress-fill').style.width = `${(ct / audio.duration) * 100}%`;
        }

        // Find active sentence
        let active = -1;
        for (let i = 0; i < sync.ranges.length; i++) {
            const r = sync.ranges[i];
            if (r && ct >= r.start - 0.05 && ct <= r.end + 0.15) { active = i; break; }
        }
        if (active === -1) {
            for (let i = sync.ranges.length - 1; i >= 0; i--) {
                if (sync.ranges[i] && ct >= sync.ranges[i].end) break;
                if (sync.ranges[i] && ct >= sync.ranges[i].start) { active = i; break; }
            }
        }

        if (active !== sync.activeSentence) {
            sync.els.forEach(se => {
                se.el.classList.remove('k-active', 'k-done');
                se.el.querySelectorAll('.k-word').forEach(w => w.classList.remove('kw-active', 'kw-done'));
            });
            for (let i = 0; i < active; i++) sync.els[i].el.classList.add('k-done');
            if (active >= 0) {
                sync.els[active].el.classList.add('k-active');
                sync.els[active].el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            sync.activeSentence = active;
        }

        // Word-level highlighting
        if (active >= 0) {
            const r = sync.ranges[active];
            const wordEls = sync.els[active].el.querySelectorAll('.k-word');

            if (r && r.wordTimings && r.wordTimings.length > 0) {
                // Precise: LMNT durations
                wordEls.forEach((w, wi) => {
                    const wt = r.wordTimings[wi];
                    if (!wt) return;
                    w.classList.toggle('kw-active', ct >= wt.start - 0.03 && ct <= wt.end + 0.05);
                    w.classList.toggle('kw-done', ct > wt.end + 0.05);
                });
            } else if (r) {
                // Fallback: proportional
                const progress = Math.min(1, Math.max(0, (ct - r.start) / r.duration));
                const total = wordEls.length;
                const activeIdx = Math.min(total - 1, Math.floor(progress * total));
                wordEls.forEach((w, wi) => {
                    w.classList.toggle('kw-done', wi < activeIdx);
                    w.classList.toggle('kw-active', wi === activeIdx);
                });
            }
        }

        state._rafId = requestAnimationFrame(syncKaraoke);
    }

    // Start/stop rAF sync with audio playback
    audio.addEventListener('play', () => {
        if (state._rafId) cancelAnimationFrame(state._rafId);
        state._rafId = requestAnimationFrame(syncKaraoke);
    });
    audio.addEventListener('pause', () => {
        if (state._rafId) { cancelAnimationFrame(state._rafId); state._rafId = null; }
    });
    audio.addEventListener('seeked', () => {
        state.sentenceSync.activeSentence = -1;
    });

    // On ended — mark all done + handle loop
    audio.addEventListener('ended', () => {
        if (state._rafId) { cancelAnimationFrame(state._rafId); state._rafId = null; }
        state.sentenceSync.els.forEach(se => {
            se.el.classList.remove('k-active');
            se.el.classList.add('k-done');
            se.el.querySelectorAll('.k-word').forEach(w => { w.classList.remove('kw-active'); w.classList.add('kw-done'); });
        });
        state.sentenceSync.activeSentence = -1;
        $('#karaoke-progress-fill').style.width = '100%';

        // Loop logic
        if (state.loopEnabled) {
            state.loopCount++;
            updateLoopCounter();
            const shouldContinue = state.loopMax === 0 || state.loopCount < state.loopMax;
            if (shouldContinue) {
                setTimeout(() => {
                    audio.currentTime = 0;
                    audio.play();
                    // Reset karaoke
                    state.sentenceSync.els.forEach(se => {
                        se.el.classList.remove('k-done', 'k-active');
                        se.el.querySelectorAll('.k-word').forEach(w => w.classList.remove('kw-active', 'kw-done'));
                    });
                    state.sentenceSync.activeSentence = -1;
                    $('#karaoke-progress-fill').style.width = '0%';
                }, 1500);
            } else {
                // Loop complete
                state.loopEnabled = false;
                $('#btn-loop').textContent = '🔁 Loop: OFF';
                $('#btn-loop').classList.remove('btn-loop-active');
                $('#loop-counter').textContent = '✅ Concluído!';
                setTimeout(() => $('#loop-counter').classList.add('hidden'), 3000);
                playBeep();
            }
        }
    });

    // Videos
    renderVideos(data.videos, data.video_warning);

    // Reset recordings
    $('#recordings-list').innerHTML = '';
    state.recordingCount = 0;

    animateStaggerElements($$('#result-section .card'), 'is-revealing', 26);
    $('#result-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderVideos(videos, warning = '') {
    const grid = $('#videos-grid');
    grid.innerHTML = '';
    if (!videos?.length) {
        const warningHtml = warning ? `<p class="hint">${escapeHtml(warning)}</p>` : '';
        grid.innerHTML = `
            <p class="hint">Nenhum vídeo encontrado.</p>
            ${warningHtml}
            <button class="btn btn-sm btn-ghost" id="btn-retry-videos">🔄 Tentar nova busca</button>
        `;
        grid.querySelector('#btn-retry-videos')?.addEventListener('click', retryVideoSearch);
        return;
    }
    videos.forEach(v => {
        const card = document.createElement('div');
        card.className = 'video-card';
        const thumb = v.thumbnails?.[0] || `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`;
        card.innerHTML = `
            <img class="video-thumb" src="${typeof thumb === 'string' ? thumb : `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`}"
                 onerror="this.src='https://img.youtube.com/vi/${v.id}/hqdefault.jpg'" loading="lazy">
            <div class="video-info">
                <h4>${escapeHtml(v.title)}</h4>
                <div class="video-meta"><span>${v.channel||''}</span><span>${v.duration||''}</span><span>${v.views||''}</span></div>
                <div class="video-actions">
                    <button class="btn btn-sm btn-ghost video-watch-btn">▶ Assistir</button>
                    <button class="btn btn-sm btn-lmnt video-karaoke-btn">🎤 Karaoke</button>
                </div>
            </div>`;
        card.querySelector('.video-watch-btn').addEventListener('click', e => {
            e.stopPropagation();
            openVideoModal(v);
        });
        card.querySelector('.video-karaoke-btn').addEventListener('click', e => {
            e.stopPropagation();
            focusYouTubeKaraokeCard();
            loadYouTubeKaraoke(v.url || v.id);
        });
        card.addEventListener('click', () => openVideoModal(v));
        grid.appendChild(card);
    });
    animateStaggerElements($$('#videos-grid .video-card'), 'is-revealing', 18);
}

async function retryVideoSearch() {
    const current = state.sessionData || {};
    const lang = current.language || $('#lang-select').value || 'en';
    const text = (current.text || $('#input-text').value || '').trim();
    if (!text) {
        alert('Digite ou carregue um texto antes de buscar vídeos.');
        return;
    }

    const baseQuery = text.split(/\s+/).slice(0, 10).join(' ');
    const fallbackQuery =
        lang === 'en'
            ? 'english speaking practice viral'
            : `${lang} speaking practice viral`;

    const queries = [baseQuery, fallbackQuery].map(q => q.trim()).filter(Boolean);
    $('#videos-grid').innerHTML = '<p class="hint">Buscando vídeos...</p>';

    for (const query of queries) {
        try {
            const res = await fetch('/api/videos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, lang }),
            });
            if (!res.ok) continue;
            const data = await res.json();
            if (data?.videos?.length) {
                if (state.sessionData) state.sessionData.videos = data.videos;
                renderVideos(data.videos);
                return;
            }
        } catch {}
    }

    renderVideos([], 'Ainda não foi possível carregar vídeos do YouTube.');
}

function openVideoModal(v) {
    const base = v.embed_url || `https://www.youtube.com/embed/${v.id}`;
    const sep = base.includes('?') ? '&' : '?';
    $('#video-iframe').src = `${base}${sep}autoplay=1`;
    $('#video-title').textContent = v.title;
    show('#video-player-modal');
}

$('#btn-close-modal').addEventListener('click', () => { hide('#video-player-modal'); $('#video-iframe').src = ''; });
$('#video-player-modal').addEventListener('click', e => {
    if (e.target === $('#video-player-modal')) { hide('#video-player-modal'); $('#video-iframe').src = ''; }
});

// ═══════════════════════════════════════════════════════════
//  YOUTUBE KARAOKE LAB
// ═══════════════════════════════════════════════════════════
function initYoutubeKaraoke() {
    if (!$('#btn-load-yt-karaoke')) return;

    $('#btn-load-yt-karaoke').addEventListener('click', () => loadYouTubeKaraoke());
    $('#btn-yt-study')?.addEventListener('click', generateYouTubeTranscriptStudy);
    $('#yt-study-list')?.addEventListener('click', handleYouTubeStudyPlayClick);
    if ($('#btn-yt-study')) $('#btn-yt-study').disabled = true;
    $('#yt-url-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            loadYouTubeKaraoke();
        }
    });
    $('#btn-yt-autoscroll').addEventListener('click', () => {
        state.youtubeKaraoke.autoScroll = !state.youtubeKaraoke.autoScroll;
        $('#btn-yt-autoscroll').textContent = `🧭 Auto-scroll: ${state.youtubeKaraoke.autoScroll ? 'ON' : 'OFF'}`;
    });
    $('#btn-yt-delay-minus').addEventListener('click', () => adjustYouTubeDelay(-0.25));
    $('#btn-yt-delay-plus').addEventListener('click', () => adjustYouTubeDelay(0.25));
    $('#btn-yt-sync-now').addEventListener('click', syncYouTubeKaraokeFromNow);
    $('#btn-yt-delay-reset').addEventListener('click', () => setYouTubeDelay(0));

    const subtitles = $('#yt-karaoke-subtitles');
    if (subtitles) {
        const pauseAutoScroll = () => {
            state.youtubeKaraoke.autoScrollHoldUntil = Date.now() + 1200;
        };
        subtitles.addEventListener('wheel', pauseAutoScroll, { passive: true });
        subtitles.addEventListener('touchstart', pauseAutoScroll, { passive: true });
        subtitles.addEventListener('pointerdown', pauseAutoScroll);
    }

    updateYouTubeDelayUi();
}

function focusYouTubeKaraokeCard() {
    const card = $('.yt-karaoke-card');
    if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function autoMinimizeMissionControlForKaraoke() {
    if (window.innerWidth <= 800) return;
    const panel = $('#mission-control');
    if (!panel) return;
    if (panel.classList.contains('hidden')) return;
    if (panel.classList.contains('mc-minimized')) return;
    panel.classList.add('mc-minimized');
}

async function loadYouTubeKaraoke(videoInput = '') {
    const input = (videoInput || $('#yt-url-input').value || '').trim();
    if (!input) return alert('Cole um link (ou ID) de vídeo do YouTube.');
    autoMinimizeMissionControlForKaraoke();

    stopYouTubeStudyAudio();
    $('#yt-url-input').value = input;
    show('#yt-karaoke-loading');
    hide('#yt-karaoke-panel');
    hide('#yt-karaoke-track-meta');
    hide('#yt-study-panel');
    hide('#yt-study-loading');
    $('#btn-load-yt-karaoke').disabled = true;
    if ($('#btn-yt-study')) $('#btn-yt-study').disabled = true;
    $('#yt-karaoke-progress-fill').style.width = '0%';

    try {
        const requestPayload = {
            video: input,
            preferred_lang: $('#yt-lang-select').value || 'en',
            timing_mode: $('#yt-sync-mode')?.value || 'accuracy',
        };
        const { result: rawData } = await runAgentWithFallback({
            intent: 'youtube',
            query: 'carregar transcrição do youtube',
            payload: { ...requestPayload, action: 'transcript' },
            fallbackCall: () => postJson('/api/youtube-transcript', requestPayload),
            operation: 'youtube_transcript',
        });
        let data = unwrapAgentResult(rawData);
        if (!data?.segments?.length && rawData?.result) {
            data = unwrapAgentResult(rawData.result);
        }
        if (!data?.segments?.length) {
            // Extra safety for mixed backend versions in Docker.
            data = await postJson('/api/youtube-transcript', requestPayload);
        }
        if (!data?.segments?.length) {
            throw new Error('Falha ao carregar transcrição/legendas.');
        }

        await renderYouTubeKaraoke(data);
        hide('#yt-karaoke-empty');
    } catch (err) {
        console.error("Error loading YouTube Karaoke:", err);
        $('#yt-karaoke-empty').textContent = `Não foi possível extrair a transcrição: ${err.message}`;
        show('#yt-karaoke-empty');
    } finally {
        hide('#yt-karaoke-loading');
        $('#btn-load-yt-karaoke').disabled = false;
    }
}

async function renderYouTubeKaraoke(data) {
    const yk = state.youtubeKaraoke;
    const subtitles = $('#yt-karaoke-subtitles');
    stopYouTubeStudyAudio();
    subtitles.innerHTML = '';
    subtitles.scrollTop = 0;
    stopYouTubeSyncLoop();

    yk.segments = normalizeYouTubeSegments(data.segments);
    yk.segmentEls = [];
    yk.activeSegment = -1;
    yk.videoId = data.video_id || '';
    yk.transcriptMeta = {
        video_id: data.video_id || '',
        title: data.title || '',
        channel: data.channel || '',
        source: data.source || 'unknown',
        language_code: data.language_code || ($('#yt-lang-select')?.value || 'en'),
        timing_mode: data.timing_mode || ($('#yt-sync-mode')?.value || 'balanced'),
        timing_offset_sec: Number(data.timing_offset_sec) || 0,
    };
    yk.study = null;
    yk.studyLoading = false;
    yk.autoScrollHoldUntil = 0;
    yk.autoScrollLastAt = 0;
    setYouTubeDelay(0);
    if ($('#yt-study-list')) $('#yt-study-list').innerHTML = '';
    if ($('#yt-study-intro')) {
        $('#yt-study-intro').textContent = '';
        $('#yt-study-intro').classList.add('hidden');
    }
    hide('#yt-study-panel');
    hide('#yt-study-loading');
    if ($('#btn-yt-study')) {
        $('#btn-yt-study').disabled = false;
        $('#btn-yt-study').textContent = '📚 Estudar transcrição';
    }

    if (!yk.segments.length || !yk.videoId) {
        throw new Error('Transcrição vazia para este vídeo.');
    }

    yk.segments.forEach((segment, index) => {
        const start = Number(segment.start) || 0;
        const duration = Math.max(Number(segment.duration) || 0.2, 0.2);
        const end = Number(segment.end) || (start + duration);

        const line = document.createElement('div');
        line.className = 'yt-segment';
        line.dataset.index = index;

        const textWrap = document.createElement('span');
        textWrap.className = 'yt-segment-text';

        let wordTimings = [];
        try {
            wordTimings = estimateWordTimingsForSegment({
                text: segment.text || '',
                start,
                duration,
                end,
                words: Array.isArray(segment.words) ? segment.words : [],
            });
        } catch (err) {
            console.warn('[YT Karaoke] Segmento com erro de timing, aplicando fallback seguro:', err, segment);
            wordTimings = [];
        }
        if (!Array.isArray(wordTimings) || !wordTimings.length) {
            wordTimings = [{ word: String(segment.text || '').trim(), start, end }];
        }

        const wordEls = [];
        wordTimings.forEach((wt, wi) => {
            const word = document.createElement('span');
            word.className = 'yt-word';
            word.textContent = wt.word;
            textWrap.appendChild(word);
            wordEls.push(word);
            if (wi < wordTimings.length - 1) textWrap.appendChild(document.createTextNode(' '));
        });

        const timeTag = document.createElement('span');
        timeTag.className = 'yt-timecode';
        timeTag.textContent = formatTimecode(start);

        line.appendChild(textWrap);
        line.appendChild(timeTag);
        line.addEventListener('click', event => {
            if (event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
                calibrateYouTubeDelayToSegment(index);
                return;
            }
            seekYouTubeKaraoke(start + 0.02);
        });
        line.title = 'Clique para pular. Shift/Ctrl/Cmd+clique para sincronizar com esta linha.';

        subtitles.appendChild(line);
        yk.segmentEls.push({ el: line, start, end, wordTimings, wordEls });
    });

    subtitles.scrollTop = 0;

    const sourceLabel = ({
        youtube_transcript_api: 'YT API',
        yt_dlp_subtitles: 'yt-dlp',
        yt_dlp_auto_captions: 'yt-dlp auto',
        deepgram_stt: 'Deepgram STT',
        local_whisper: 'Local Whisper',
        openrouter_audio_timed: 'OpenRouter timed',
        openrouter_audio: 'OpenRouter audio',
        openai_whisper: 'OpenAI STT',
    })[data.source] || 'fallback';
    const modeLabel = ({
        accuracy: 'Sync preciso',
        balanced: 'Balanceado',
        fast: 'Rápido',
    })[data.timing_mode] || 'Sync preciso';

    const trackMeta = $('#yt-karaoke-track-meta');
    trackMeta.textContent = `${(data.language_code || '??').toUpperCase()} · ${data.is_generated ? 'Auto CC' : 'Manual CC'} · ${sourceLabel}`;
    trackMeta.classList.remove('hidden');

    const infoParts = [
        data.title ? `🎵 ${data.title}` : '',
        data.channel ? `Canal: ${data.channel}` : '',
        (data.timing_offset_sec && Number(data.timing_offset_sec) > 0)
            ? `Offset auto +${Number(data.timing_offset_sec).toFixed(2)}s`
            : '',
        `Modo: ${modeLabel}`,
        `${data.stats?.segments || yk.segments.length} linhas`,
        `${data.stats?.words || 0} palavras`,
        'Dica: Shift/Ctrl+clique na linha para calibrar sync',
    ].filter(Boolean);
    $('#yt-karaoke-info').textContent = infoParts.join(' • ');

    show('#yt-karaoke-panel');
    animateStaggerElements($$('#yt-karaoke-subtitles .yt-segment'), 'is-revealing', 22);
    await ensureYouTubePlayer(yk.videoId);
    autoMinimizeMissionControlForKaraoke();
}

let ytCaptionDecoderEl = null;

function decodeYouTubeCaptionHtml(rawText) {
    const source = String(rawText || '');
    if (!source) return '';
    if (!ytCaptionDecoderEl) ytCaptionDecoderEl = document.createElement('textarea');
    ytCaptionDecoderEl.innerHTML = source;
    return ytCaptionDecoderEl.value || source;
}

function cleanYouTubeSegmentText(rawText) {
    let text = decodeYouTubeCaptionHtml(rawText);
    text = text
        .replace(/<[^>]+>/g, ' ')
        .replace(/[\u200B-\u200D\uFEFF]/g, '')
        .replace(/\u00A0/g, ' ')
        .replace(/^\s*(?:>>+|›+)\s*/g, '')
        .replace(/\s+/g, ' ')
        .trim();

    if (!text) return '';
    if (/^[\[\(][^)\]]{1,24}[\]\)]$/.test(text)) return '';
    if (/^(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d+)?$/.test(text)) return '';
    if (/^[-–—_~.·•\s]+$/.test(text)) return '';

    const alphaNumCount = (text.match(/[A-Za-z0-9À-ÖØ-öø-ÿ]/g) || []).length;
    if (!alphaNumCount) return '';
    return text;
}

function normalizeYouTubeSegmentKey(text) {
    return String(text || '')
        .toLowerCase()
        .replace(/[^a-z0-9À-ÖØ-öø-ÿ]+/g, ' ')
        .trim();
}

function normalizeYouTubeSegments(segments) {
    const prepared = (Array.isArray(segments) ? segments : [])
        .map(item => {
            const text = cleanYouTubeSegmentText(item?.text || '');
            const start = Number(item?.start);
            const durationRaw = Number(item?.duration);
            const endRaw = Number(item?.end);
            if (!text || !Number.isFinite(start)) return null;

            let duration = Number.isFinite(durationRaw) && durationRaw > 0
                ? durationRaw
                : (Number.isFinite(endRaw) ? endRaw - start : 0.18);
            duration = Math.max(0.18, duration);
            const end = Number.isFinite(endRaw) && endRaw > start
                ? endRaw
                : start + duration;

            return {
                ...item,
                text,
                start: Math.max(0, start),
                duration: Math.max(0.18, end - start),
                end: Math.max(start + 0.18, end),
                words: Array.isArray(item?.words) ? item.words : [],
                key: normalizeYouTubeSegmentKey(text),
            };
        })
        .filter(Boolean)
        .sort((a, b) => (a.start - b.start) || (a.end - b.end));

    const deduped = [];
    prepared.forEach(seg => {
        if (!deduped.length) {
            deduped.push(seg);
            return;
        }
        const prev = deduped[deduped.length - 1];
        const startClose = Math.abs(seg.start - prev.start) < 0.08;
        const overlaps = seg.start <= (prev.end + 0.2);
        const sameText = seg.text === prev.text;
        const sameKey = !!(
            seg.key
            && prev.key
            && (
                seg.key === prev.key
                || seg.key.startsWith(prev.key + ' ')
                || prev.key.startsWith(seg.key + ' ')
            )
        );

        if ((startClose || overlaps) && (sameText || sameKey)) {
            const prevScore = prev.text.length + (prev.end - prev.start);
            const segScore = seg.text.length + (seg.end - seg.start);
            if (segScore > prevScore) {
                deduped[deduped.length - 1] = {
                    ...seg,
                    end: Math.max(seg.end, prev.end),
                    duration: Math.max(0.18, Math.max(seg.end, prev.end) - seg.start),
                };
            } else {
                prev.end = Math.max(prev.end, seg.end);
                prev.duration = Math.max(0.18, prev.end - prev.start);
                if (
                    Array.isArray(seg.words)
                    && seg.words.length
                    && (!Array.isArray(prev.words) || seg.words.length > prev.words.length)
                ) {
                    prev.words = seg.words;
                }
            }
            return;
        }
        deduped.push(seg);
    });

    return deduped.map(seg => {
        const normalized = { ...seg };
        delete normalized.key;
        return normalized;
    });
}

function estimateWordTimingsForSegment(segment) {
    const start = Number(segment.start) || 0;
    const duration = Math.max(Number(segment.duration) || 0.2, 0.2);
    const endBound = Number(segment.end) || (start + duration);

    const providedWords = Array.isArray(segment.words) ? segment.words : [];
    const providedTimings = providedWords
        .map(w => {
            const word = String(w?.word ?? w?.text ?? '').trim();
            const wStart = Number(w?.start);
            const wEnd = Number(w?.end);
            if (!word || !Number.isFinite(wStart) || !Number.isFinite(wEnd) || wEnd <= wStart) {
                return null;
            }
            return {
                word,
                start: Math.max(start, Math.min(endBound, wStart)),
                end: Math.max(start, Math.min(endBound, wEnd)),
            };
        })
        .filter(Boolean)
        .sort((a, b) => a.start - b.start);

    if (providedTimings.length) {
        const fixed = [];
        let cursor = start;
        providedTimings.forEach(item => {
            const safeStart = Math.max(cursor, item.start);
            const safeEnd = Math.max(safeStart + 0.02, item.end);
            fixed.push({
                word: item.word,
                start: safeStart,
                end: Math.min(endBound, safeEnd),
            });
            cursor = fixed[fixed.length - 1].end;
        });
        return fixed;
    }

    const words = String(segment.text || '').trim().split(/\s+/).filter(Boolean);
    if (!words.length) return [];

    const weights = words.map(w => {
        const clean = w.replace(/[^a-zA-Z0-9À-ÖØ-öø-ÿ']/g, '');
        const punctuationBonus = /[,.!?;:]$/.test(w) ? 1.4 : 1;
        return Math.max(1, clean.length) * punctuationBonus;
    });
    const totalWeight = weights.reduce((sum, w) => sum + w, 0) || words.length;

    let cursor = start;
    return words.map((word, index) => {
        const isLast = index === words.length - 1;
        const share = duration * (weights[index] / totalWeight);
        const wordStart = cursor;
        const wordEnd = isLast ? (start + duration) : Math.min(start + duration, cursor + Math.max(0.04, share));
        cursor = wordEnd;
        return { word, start: wordStart, end: wordEnd };
    });
}

function loadYouTubeIframeApi() {
    if (window.YT && window.YT.Player) return Promise.resolve();
    if (state.youtubeKaraoke.apiPromise) return state.youtubeKaraoke.apiPromise;

    state.youtubeKaraoke.apiPromise = new Promise((resolve, reject) => {
        const prevCallback = window.onYouTubeIframeAPIReady;
        window.onYouTubeIframeAPIReady = () => {
            if (typeof prevCallback === 'function') {
                try { prevCallback(); } catch {}
            }
            resolve();
        };

        if (!document.querySelector('script[data-yt-api="true"]')) {
            const script = document.createElement('script');
            script.src = 'https://www.youtube.com/iframe_api';
            script.async = true;
            script.dataset.ytApi = 'true';
            script.onerror = () => reject(new Error('Falha ao carregar API do YouTube.'));
            document.head.appendChild(script);
        }

        setTimeout(() => {
            if (window.YT && window.YT.Player) resolve();
        }, 900);
    });

    return state.youtubeKaraoke.apiPromise;
}

async function ensureYouTubePlayer(videoId) {
    await loadYouTubeIframeApi();
    const yk = state.youtubeKaraoke;
    yk.videoId = videoId;

    if (yk.player) {
        if (!yk.playerReady) return;
        yk.player.loadVideoById(videoId);
        try { yk.player.playVideo(); } catch {}
        startYouTubeSyncLoop();
        return;
    }

    yk.playerReady = false;
    yk.player = new window.YT.Player('yt-karaoke-player', {
        videoId,
        playerVars: {
            rel: 0,
            modestbranding: 1,
            playsinline: 1,
            cc_load_policy: 0,
        },
        events: {
            onReady: (event) => {
                yk.playerReady = true;
                try { event.target.loadVideoById(yk.videoId || videoId); } catch {}
                try { event.target.playVideo(); } catch {}
                startYouTubeSyncLoop();
            },
            onStateChange: handleYouTubePlayerStateChange,
        },
    });
}

function handleYouTubePlayerStateChange(event) {
    const PS = window.YT?.PlayerState;
    if (!PS) return;

    if (event.data === PS.PLAYING) {
        startYouTubeSyncLoop();
    } else if (event.data === PS.PAUSED || event.data === PS.BUFFERING) {
        stopYouTubeSyncLoop();
        syncYouTubeKaraoke();
    } else if (event.data === PS.ENDED) {
        stopYouTubeSyncLoop();
        markYouTubeKaraokeComplete();
    }
}

function startYouTubeSyncLoop() {
    const yk = state.youtubeKaraoke;
    stopYouTubeSyncLoop();

    const frame = () => {
        syncYouTubeKaraoke();
        yk.syncRafId = requestAnimationFrame(frame);
    };
    yk.syncRafId = requestAnimationFrame(frame);
}

function stopYouTubeSyncLoop() {
    if (state.youtubeKaraoke.syncRafId) {
        cancelAnimationFrame(state.youtubeKaraoke.syncRafId);
        state.youtubeKaraoke.syncRafId = null;
    }
}

function isYouTubeSegmentActiveAt(segment, timeSec) {
    return timeSec >= segment.start - 0.08 && timeSec <= segment.end + 0.18;
}

function findActiveYouTubeSegmentIndex(timeSec, currentIndex = -1) {
    const segs = state.youtubeKaraoke.segmentEls;
    if (!segs.length) return -1;

    if (currentIndex >= 0 && currentIndex < segs.length && isYouTubeSegmentActiveAt(segs[currentIndex], timeSec)) {
        return currentIndex;
    }

    let lo = 0;
    let hi = segs.length - 1;
    let pivot = -1;
    const lookaheadTime = timeSec + 0.08;

    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (segs[mid].start <= lookaheadTime) {
            pivot = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }

    if (pivot < 0) return -1;

    let best = -1;
    for (let i = Math.max(0, pivot - 2); i <= Math.min(segs.length - 1, pivot + 2); i++) {
        if (isYouTubeSegmentActiveAt(segs[i], timeSec)) {
            if (best === -1 || segs[i].start >= segs[best].start) {
                best = i;
            }
        }
    }

    return best;
}

function findNearestYouTubeSegmentIndex(timeSec, maxDistanceSec = 12) {
    const segs = state.youtubeKaraoke.segmentEls;
    if (!segs.length) return -1;

    let nearest = -1;
    let nearestDist = maxDistanceSec;
    segs.forEach((seg, idx) => {
        const distance = Math.abs(seg.start - timeSec);
        if (distance <= nearestDist) {
            nearest = idx;
            nearestDist = distance;
        }
    });

    return nearest;
}

function scrollActiveYouTubeSegmentWithinSubtitles(activeIndex, force = false) {
    if (activeIndex < 0) return;

    const yk = state.youtubeKaraoke;
    const container = $('#yt-karaoke-subtitles');
    const activeSeg = yk.segmentEls[activeIndex];
    if (!container || !activeSeg?.el) return;
    if (!force && Date.now() < (yk.autoScrollHoldUntil || 0)) return;

    const el = activeSeg.el;
    const now = Date.now();
    if (!force && now - (yk.autoScrollLastAt || 0) < 120) return;

    const containerTop = container.scrollTop;
    const containerBottom = containerTop + container.clientHeight;
    const itemTop = el.offsetTop;
    const itemBottom = itemTop + el.offsetHeight;

    const topPadding = 14;
    const bottomPadding = 18;
    const isAbove = itemTop < (containerTop + topPadding);
    const isBelow = itemBottom > (containerBottom - bottomPadding);
    if (!isAbove && !isBelow) return;

    const desiredTop = itemTop - (container.clientHeight * 0.42) + (el.offsetHeight * 0.5);
    const maxTop = Math.max(0, container.scrollHeight - container.clientHeight);
    const nextTop = Math.max(0, Math.min(maxTop, desiredTop));
    const distance = Math.abs(nextTop - containerTop);
    if (distance < 2) return;

    yk.autoScrollLastAt = now;
    if (distance > container.clientHeight * 0.9) {
        container.scrollTop = nextTop;
        return;
    }
    container.scrollTo({ top: nextTop, behavior: 'smooth' });
}

function syncYouTubeKaraoke() {
    const yk = state.youtubeKaraoke;
    if (!yk.playerReady || !yk.player || !yk.segmentEls.length) return;

    let currentTime = 0;
    let videoDuration = 0;
    try {
        currentTime = yk.player.getCurrentTime() || 0;
        videoDuration = yk.player.getDuration() || 0;
    } catch {
        return;
    }
    // Positive delay means subtitles are advanced (appear earlier).
    const effectiveTime = currentTime + yk.delaySec;

    const fallbackDuration = yk.segmentEls[yk.segmentEls.length - 1]?.end || 0;
    const totalDuration = fallbackDuration || videoDuration;
    if (totalDuration > 0) {
        const progressPct = Math.min(100, Math.max(0, (effectiveTime / totalDuration) * 100));
        $('#yt-karaoke-progress-fill').style.width = `${progressPct}%`;
    }

    const active = findActiveYouTubeSegmentIndex(effectiveTime, yk.activeSegment);

    if (active !== yk.activeSegment) {
        yk.segmentEls.forEach((seg, idx) => {
            seg.el.classList.toggle('yt-active', idx === active);
            seg.el.classList.toggle('yt-done', active >= 0 && idx < active);
            const words = Array.isArray(seg.wordEls) ? seg.wordEls : [];

            if (idx < active) {
                words.forEach(word => {
                    word.classList.remove('ytw-active');
                    word.classList.add('ytw-done');
                });
            } else if (idx > active) {
                words.forEach(word => word.classList.remove('ytw-active', 'ytw-done'));
            } else {
                words.forEach(word => word.classList.remove('ytw-active', 'ytw-done'));
            }
        });

        if (active >= 0 && yk.autoScroll) scrollActiveYouTubeSegmentWithinSubtitles(active);
        yk.activeSegment = active;
    }

    if (active >= 0 && yk.autoScroll) {
        scrollActiveYouTubeSegmentWithinSubtitles(active);
    }

    if (active >= 0) {
        const seg = yk.segmentEls[active];
        const words = Array.isArray(seg?.wordEls) ? seg.wordEls : [];
        const timings = Array.isArray(seg?.wordTimings) ? seg.wordTimings : [];
        words.forEach((wordEl, wi) => {
            const wt = timings[wi];
            if (!wt) return;
            wordEl.classList.toggle('ytw-active', effectiveTime >= wt.start - 0.02 && effectiveTime <= wt.end + 0.06);
            wordEl.classList.toggle('ytw-done', effectiveTime > wt.end + 0.06);
        });
    }
}

function calibrateYouTubeDelayToSegment(segmentIndex) {
    const yk = state.youtubeKaraoke;
    if (!yk.playerReady || !yk.player) return;
    const seg = yk.segmentEls[segmentIndex];
    if (!seg) return;

    let currentTime = 0;
    try {
        currentTime = yk.player.getCurrentTime() || 0;
    } catch {
        return;
    }

    const newDelay = seg.start - currentTime;
    setYouTubeDelay(newDelay);
    yk.activeSegment = -1;
    syncYouTubeKaraoke();
}

function markYouTubeKaraokeComplete() {
    const yk = state.youtubeKaraoke;
    yk.segmentEls.forEach(seg => {
        seg.el.classList.remove('yt-active');
        seg.el.classList.add('yt-done');
        const words = Array.isArray(seg.wordEls) ? seg.wordEls : [];
        words.forEach(word => {
            word.classList.remove('ytw-active');
            word.classList.add('ytw-done');
        });
    });
    yk.activeSegment = -1;
    $('#yt-karaoke-progress-fill').style.width = '100%';
}

function seekYouTubeKaraoke(seconds) {
    const yk = state.youtubeKaraoke;
    if (!yk.playerReady || !yk.player) return;
    try {
        yk.player.seekTo(Math.max(0, seconds - yk.delaySec), true);
        yk.player.playVideo();
        startYouTubeSyncLoop();
    } catch {}
}

function setYouTubeDelay(value) {
    const yk = state.youtubeKaraoke;
    yk.delaySec = Math.max(-120, Math.min(120, Number(value) || 0));
    updateYouTubeDelayUi();
}

function adjustYouTubeDelay(delta) {
    setYouTubeDelay(state.youtubeKaraoke.delaySec + delta);
}

function updateYouTubeDelayUi() {
    const yk = state.youtubeKaraoke;
    const value = `${yk.delaySec >= 0 ? '+' : ''}${yk.delaySec.toFixed(2)}s`;
    const direction = yk.delaySec > 0
        ? ' (legenda adiantada)'
        : (yk.delaySec < 0 ? ' (legenda atrasada)' : '');
    if ($('#yt-delay-value')) $('#yt-delay-value').textContent = `Ajuste ${value}${direction}`;
}

function syncYouTubeKaraokeFromNow() {
    const yk = state.youtubeKaraoke;
    if (!yk.playerReady || !yk.player || !yk.segmentEls.length) return;

    let currentTime = 0;
    try {
        currentTime = yk.player.getCurrentTime() || 0;
    } catch {
        return;
    }

    const effectiveTime = currentTime + yk.delaySec;
    const activeIndex = findActiveYouTubeSegmentIndex(effectiveTime, yk.activeSegment);
    const nearestIndex = activeIndex >= 0 ? activeIndex : findNearestYouTubeSegmentIndex(effectiveTime, 10);
    const anchorStart = nearestIndex >= 0
        ? yk.segmentEls[nearestIndex].start
        : findFirstLyricSegmentStart();
    const newDelay = anchorStart - currentTime;
    setYouTubeDelay(newDelay);
    yk.activeSegment = -1;
    syncYouTubeKaraoke();
}

function findFirstLyricSegmentStart() {
    const yk = state.youtubeKaraoke;
    if (!Array.isArray(yk.segments) || !yk.segments.length) return 0;

    const lyricLike = yk.segments.find(seg => {
        const text = String(seg?.text || '').trim();
        if (!text) return false;
        if (/^[\[\(].{1,24}[\]\)]$/.test(text)) return false; // [Music], (Applause), etc.
        return text.split(/\s+/).length >= 2;
    });

    return Number(lyricLike?.start ?? yk.segments[0]?.start) || 0;
}

function formatTimecode(seconds) {
    const total = Math.max(0, Math.floor(seconds || 0));
    const min = Math.floor(total / 60);
    const sec = total % 60;
    return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

async function generateYouTubeTranscriptStudy() {
    const yk = state.youtubeKaraoke;
    if (yk.studyLoading) return;
    if (!yk.segments?.length) {
        alert('Carregue um vídeo com transcrição antes de gerar o estudo.');
        return;
    }

    stopYouTubeStudyAudio();
    const btn = $('#btn-yt-study');
    yk.studyLoading = true;
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Analisando...';
    }
    show('#yt-study-loading');
    hide('#yt-study-panel');

    const payload = {
        preferred_lang: $('#yt-lang-select')?.value || yk.transcriptMeta?.language_code || 'en',
        target_lang: $('#yt-study-target')?.value || 'pt',
        timing_mode: $('#yt-sync-mode')?.value || yk.transcriptMeta?.timing_mode || 'balanced',
        segments: yk.segments,
        source_lang: yk.transcriptMeta?.language_code || 'en',
        source: yk.transcriptMeta?.source || 'client_segments',
        video_id: yk.videoId || '',
        title: yk.transcriptMeta?.title || '',
        channel: yk.transcriptMeta?.channel || '',
        timing_offset_sec: yk.transcriptMeta?.timing_offset_sec || 0,
        max_phrases: 18,
        max_words: 6,
    };

    try {
        const { result: rawData } = await runAgentWithFallback({
            intent: 'youtube',
            query: 'gerar estudo frase por frase',
            payload: { ...payload, action: 'study' },
            fallbackCall: () => postJson('/api/youtube-transcript-study', payload),
            operation: 'youtube_transcript_study',
        });
        const data = unwrapAgentResult(rawData);
        yk.study = data.study || null;
        renderYouTubeTranscriptStudy(yk.study);
    } catch (err) {
        if ($('#yt-study-intro')) {
            $('#yt-study-intro').textContent = '';
            $('#yt-study-intro').classList.add('hidden');
        }
        $('#yt-study-list').innerHTML = `<p class="hint">Erro ao gerar estudo: ${escapeHtml(err.message || 'desconhecido')}</p>`;
        $('#yt-study-meta').textContent = 'Falha';
        show('#yt-study-panel');
    } finally {
        yk.studyLoading = false;
        hide('#yt-study-loading');
        if (btn) {
            btn.disabled = false;
            btn.textContent = '📚 Estudar transcrição';
        }
    }
}

function renderYouTubeTranscriptStudy(study) {
    const panel = $('#yt-study-panel');
    const list = $('#yt-study-list');
    const meta = $('#yt-study-meta');
    const intro = $('#yt-study-intro');
    const yk = state.youtubeKaraoke;
    const phrases = Array.isArray(study?.phrases) ? study.phrases : [];
    const introText = String(study?.lesson_intro || '').trim();
    const warningText = String(study?.warning || '').trim();
    const fallbackMode = String(study?.ai_provider || '').trim().toLowerCase() === 'fallback';

    if (intro) {
        if (introText) {
            intro.textContent = `👨‍🏫 ${introText}`;
            intro.classList.remove('hidden');
        } else {
            intro.textContent = '';
            intro.classList.add('hidden');
        }
    }

    if (!phrases.length) {
        meta.textContent = 'Sem frases';
        list.innerHTML = '<p class="hint">Nenhuma frase retornada para estudo.</p>';
        show('#yt-study-panel');
        return;
    }

    const sourceLangRaw = String(study?.source_language || yk.transcriptMeta?.language_code || 'en').toLowerCase();
    const sourceLang = sourceLangRaw.toUpperCase();
    const targetLang = String(study?.target_language || 'pt').toUpperCase();
    const providerRaw = String(study?.ai_provider || '').trim().toLowerCase();
    const providerLabelMap = {
        deepseek: 'DeepSeek',
        openrouter: 'OpenRouter',
        openai: 'OpenAI',
        ollama: 'Ollama',
        fallback: 'Fallback Local',
        fallback_local: 'Fallback Local',
    };
    const providerLabel = providerRaw ? (providerLabelMap[providerRaw] || providerRaw.toUpperCase()) : '';
    const modeLabel = fallbackMode ? ' · Modo local' : '';
    const providerMeta = providerLabel ? ` · IA: ${providerLabel}` : '';
    meta.textContent = `${phrases.length} frases · ${sourceLang} → ${targetLang}${providerMeta}${modeLabel}`;
    if (warningText) {
        // Mantém rastreabilidade sem poluir a UI principal.
        console.warn('[YouTube Study warning]', warningText);
    }

    list.innerHTML = phrases.map((phrase, idx) => {
        const words = Array.isArray(phrase.words) ? phrase.words : [];
        const phraseTextEncoded = encodeURIComponent(String(phrase.text || '').trim());
        const teacherExplanation = String(
            phrase.teacher_explanation
            || phrase.notes
            || 'Repita esta frase em voz alta 3 vezes, conectando os sons e mantendo ritmo natural.'
        ).trim();
        const wordsHtml = words.length
            ? words.map(word => {
                const term = escapeHtml(word.word || '');
                const pron = escapeHtml(word.pronunciation || '');
                const meaning = escapeHtml(word.meaning || word.translation || '');
                return `<div class="yt-study-word">
                    <strong>${term}</strong>
                    ${pron ? `<span class="yt-study-word-pron">${pron}</span>` : ''}
                    ${meaning ? `<span class="yt-study-word-meaning">${meaning}</span>` : ''}
                </div>`;
            }).join('')
            : '<p class="hint">Sem vocabulário destacado para esta frase.</p>';

        return `<article class="yt-study-phrase">
            <div class="yt-study-head">
                <span class="yt-study-time">${formatTimecode(phrase.start)} → ${formatTimecode(phrase.end)}</span>
                <span class="badge badge-sm">Frase ${idx + 1}</span>
            </div>
            <p class="yt-study-original">${escapeHtml(phrase.text || '')}</p>
            <div class="yt-study-row">
                <strong>Pronúncia:</strong> <span>${escapeHtml(phrase.pronunciation || '—')}</span>
            </div>
            <div class="yt-study-row">
                <strong>Tradução:</strong> <span>${escapeHtml(phrase.translation || '—')}</span>
            </div>
            <div class="yt-study-actions">
                <button
                    type="button"
                    class="btn btn-sm btn-ghost yt-study-play"
                    data-play-text="${phraseTextEncoded}"
                    data-play-lang="${escapeHtml(sourceLangRaw)}"
                    data-default-label="🔊 Ouvir frase"
                    data-loading-label="⏳ Gerando áudio..."
                    data-playing-label="⏸ Tocando"
                >🔊 Ouvir frase</button>
            </div>
            <div class="yt-study-row yt-study-prof">
                <strong>Professor explica:</strong> <span>${escapeHtml(teacherExplanation)}</span>
            </div>
            ${phrase.notes ? `<div class="yt-study-row"><strong>Dica:</strong> <span>${escapeHtml(phrase.notes)}</span></div>` : ''}
            <div class="yt-study-words">${wordsHtml}</div>
        </article>`;
    }).join('');

    show('#yt-study-panel');
    animateStaggerElements($$('#yt-study-list .yt-study-phrase'), 'is-revealing', 16);
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function decodeYouTubeStudyText(rawText) {
    try {
        return decodeURIComponent(String(rawText || ''));
    } catch {
        return String(rawText || '');
    }
}

const YT_STUDY_AUDIO_RATE = 0.82;

function resetYouTubeStudyAudioButtons() {
    $$('#yt-study-list .yt-study-play').forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('is-loading', 'is-playing');
        btn.textContent = btn.dataset.defaultLabel || '🔊 Ouvir frase';
    });
}

function stopYouTubeStudyAudio() {
    const yk = state.youtubeKaraoke;
    if (yk.studyAudio) {
        try { yk.studyAudio.pause(); } catch {}
    }
    if (yk.studySpeechUtterance && window.speechSynthesis) {
        try { window.speechSynthesis.cancel(); } catch {}
    }
    yk.studyAudio = null;
    yk.studyAudioButton = null;
    yk.studySpeechUtterance = null;
    resetYouTubeStudyAudioButtons();
}

function normalizeStudySpeechLang(lang) {
    const base = String(lang || 'en').trim().toLowerCase();
    if (base.startsWith('pt')) return 'pt-BR';
    if (base.startsWith('es')) return 'es-ES';
    if (base.startsWith('fr')) return 'fr-FR';
    return 'en-US';
}

function playYouTubeStudySpeechFallback(button, text, lang, playingLabel) {
    if (!window.speechSynthesis || typeof SpeechSynthesisUtterance === 'undefined') {
        return false;
    }

    const yk = state.youtubeKaraoke;
    try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = normalizeStudySpeechLang(lang);
        utterance.rate = 0.8;
        utterance.pitch = 1.0;

        yk.studySpeechUtterance = utterance;
        yk.studyAudioButton = button;

        button.disabled = false;
        button.classList.remove('is-loading');
        button.classList.add('is-playing');
        button.textContent = `${playingLabel} (navegador)`;

        const cleanup = () => {
            if (yk.studySpeechUtterance === utterance) {
                yk.studySpeechUtterance = null;
                yk.studyAudioButton = null;
            }
            resetYouTubeStudyAudioButtons();
        };

        utterance.addEventListener('end', cleanup, { once: true });
        utterance.addEventListener('error', cleanup, { once: true });
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
        return true;
    } catch {
        return false;
    }
}

async function playYouTubeStudyAudio(button, text, lang) {
    const phraseText = String(text || '').trim();
    if (!button || !phraseText) return;

    const yk = state.youtubeKaraoke;
    const sameButtonActive = yk.studyAudioButton === button && (
        (yk.studyAudio && !yk.studyAudio.paused) || yk.studySpeechUtterance
    );
    if (sameButtonActive) {
        stopYouTubeStudyAudio();
        return;
    }

    stopYouTubeStudyAudio();

    const defaultLabel = button.dataset.defaultLabel || '🔊 Ouvir frase';
    const loadingLabel = button.dataset.loadingLabel || '⏳ Gerando áudio...';
    const playingLabel = button.dataset.playingLabel || '⏸ Tocando';
    const voice = $('#voice-select')?.value || 'leah';
    const sourceLang = String(lang || yk.transcriptMeta?.language_code || 'en').trim().toLowerCase() || 'en';
    const ttsEngine = getSelectedTtsEngine();
    const piperPayload = buildPiperPracticePayload(phraseText, 'youtube_study_phrase', 'lesson');
    const cacheKey = `ytstudy_${phraseText}_${sourceLang}_${voice}_${ttsEngine}_${piperPayload.piper_profile}_${piperPayload.tts_context}`;

    button.disabled = true;
    button.classList.add('is-loading');
    button.textContent = loadingLabel;

    try {
        let audioUrl = state.ttsCache[cacheKey];
        if (!audioUrl) {
            const res = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: phraseText,
                    lang: sourceLang,
                    voice,
                    tts_engine: ttsEngine,
                    ...piperPayload,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Falha ao gerar áudio da frase.');
            audioUrl = data.audio_url || '';
            if (!audioUrl) throw new Error('Áudio não retornado pela API.');
            state.ttsCache[cacheKey] = audioUrl;
        }

        const audio = new Audio(audioUrl);
        audio.playbackRate = YT_STUDY_AUDIO_RATE;
        yk.studyAudio = audio;
        yk.studyAudioButton = button;
        yk.studySpeechUtterance = null;

        button.disabled = false;
        button.classList.remove('is-loading');
        button.classList.add('is-playing');
        button.textContent = playingLabel;

        const cleanup = () => {
            if (yk.studyAudio === audio) {
                yk.studyAudio = null;
                yk.studyAudioButton = null;
            }
            resetYouTubeStudyAudioButtons();
        };

        audio.addEventListener('ended', cleanup, { once: true });
        audio.addEventListener('error', cleanup, { once: true });
        await audio.play();
    } catch (err) {
        console.error('Erro ao tocar áudio do estudo:', err);
        const fallbackStarted = playYouTubeStudySpeechFallback(
            button,
            phraseText,
            sourceLang,
            playingLabel,
        );
        if (fallbackStarted) return;

        button.disabled = false;
        button.classList.remove('is-loading', 'is-playing');
        button.textContent = `${defaultLabel} (erro)`;
        setTimeout(() => {
            if (!button.classList.contains('is-loading') && !button.classList.contains('is-playing')) {
                button.textContent = defaultLabel;
            }
        }, 1500);
    }
}

function handleYouTubeStudyPlayClick(event) {
    const button = event.target.closest('.yt-study-play');
    if (!button || !button.closest('#yt-study-list')) return;
    event.preventDefault();

    const phraseText = decodeYouTubeStudyText(button.dataset.playText);
    const sourceLang = button.dataset.playLang || state.youtubeKaraoke.transcriptMeta?.language_code || 'en';
    playYouTubeStudyAudio(button, phraseText, sourceLang);
}

// ═══════════════════════════════════════════════════════════//  LOOP CONTROL
// ═════════════════════════════════════════════════════════
$('#btn-loop').addEventListener('click', () => {
    state.loopEnabled = !state.loopEnabled;
    state.loopCount = 0;
    const btn = $('#btn-loop');
    const counter = $('#loop-counter');
    if (state.loopEnabled) {
        btn.textContent = '🔁 Loop: ON';
        btn.classList.add('btn-loop-active');
        state.loopMax = parseInt($('#loop-count').value) || 0;
        counter.classList.remove('hidden');
        updateLoopCounter();
    } else {
        btn.textContent = '🔁 Loop: OFF';
        btn.classList.remove('btn-loop-active');
        counter.classList.add('hidden');
    }
});

$('#loop-count').addEventListener('change', () => {
    state.loopMax = parseInt($('#loop-count').value) || 0;
    state.loopCount = 0;
    updateLoopCounter();
});

function updateLoopCounter() {
    const counter = $('#loop-counter');
    if (state.loopMax === 0) {
        counter.textContent = `${state.loopCount}/∞`;
    } else {
        counter.textContent = `${state.loopCount}/${state.loopMax}`;
    }
}

// ═════════════════════════════════════════════════════════//  SPEED CONTROL
// ═══════════════════════════════════════════════════════════
$$('.speed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        $$('.speed-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        $('#main-audio').playbackRate = parseFloat(btn.dataset.speed);
    });
});

// ═══════════════════════════════════════════════════════════
//  TTS FRASE
// ═══════════════════════════════════════════════════════════
let currentSentenceAudio = null;

async function playSentence(text, lang, voice, el) {
    if (currentSentenceAudio) { currentSentenceAudio.pause(); currentSentenceAudio = null; }
    $$('.k-sentence').forEach(s => s.classList.remove('k-playing'));
    el.classList.add('k-playing');

    // Check cache first
    const ttsEngine = getSelectedTtsEngine();
    const piperPayload = buildPiperPracticePayload(text, 'shadowing_sentence', 'lesson');
    const cacheKey = `${text}_${lang}_${voice}_${ttsEngine}_${piperPayload.piper_profile}_${piperPayload.tts_context}`;
    if (state.ttsCache[cacheKey]) {
        currentSentenceAudio = new Audio(state.ttsCache[cacheKey]);
        currentSentenceAudio.play();
        currentSentenceAudio.addEventListener('ended', () => el.classList.remove('k-playing'));
        return;
    }

    try {
        const res = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                lang,
                voice: voice || $('#voice-select').value,
                tts_engine: ttsEngine,
                ...piperPayload,
            }),
        });
        const data = await res.json();
        if (data.audio_url) {
            state.ttsCache[cacheKey] = data.audio_url;  // Cache it
            currentSentenceAudio = new Audio(data.audio_url);
            currentSentenceAudio.play();
            currentSentenceAudio.addEventListener('ended', () => {
                el.classList.remove('k-playing');
            });
        }
    } catch {
        el.classList.remove('k-playing');
    }
}

// ═══════════════════════════════════════════════════════════
//  GRAVAÇÃO
// ═══════════════════════════════════════════════════════════
$('#btn-record').addEventListener('click', startRecording);
$('#btn-stop-record').addEventListener('click', stopRecording);

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        state.mediaRecorder.ondataavailable = e => { if (e.data.size > 0) state.audioChunks.push(e.data); };
        state.mediaRecorder.onstop = () => {
            const blob = new Blob(state.audioChunks, { type: 'audio/webm' });
            addRecording(blob);
            stream.getTracks().forEach(t => t.stop());
        };
        state.mediaRecorder.start();
        state.isRecording = true;
        $('#btn-record').classList.add('recording');
        $('#btn-record').innerHTML = '<span class="rec-icon">⏺</span> Gravando...';
        show('#btn-stop-record');
        $('#recording-status').textContent = '🔴 Gravando...';
        $('#recording-status').classList.add('active');
    } catch { alert('Permita o acesso ao microfone.'); }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        $('#btn-record').classList.remove('recording');
        $('#btn-record').innerHTML = '<span class="rec-icon">⏺</span> Gravar';
        hide('#btn-stop-record');
        $('#recording-status').textContent = '';
        $('#recording-status').classList.remove('active');
    }
}

function addRecording(blob) {
    state.recordingCount++;
    const url = URL.createObjectURL(blob);
    const item = document.createElement('div');
    item.className = 'recording-item';
    item.innerHTML = `<span class="rec-label">🎙️ #${state.recordingCount}</span><audio controls src="${url}"></audio>`;
    $('#recordings-list').prepend(item);
}

// ═══════════════════════════════════════════════════════════
//  VOZES LMNT
// ═══════════════════════════════════════════════════════════
$('#btn-load-voices').addEventListener('click', loadVoices);
$('#btn-refresh-voices').addEventListener('click', loadVoices);

async function loadVoices() {
    try {
        const res = await fetch('/api/voices');
        const data = await res.json();
        state.voices = data.voices || [];
        renderVoiceSelect(state.voices);
        renderVoicesGrid(state.voices);
    } catch {}
}

function renderVoiceSelect(voices) {
    const sel = $('#voice-select');
    if (!voices.length) return;
    sel.innerHTML = '';
    voices.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = `${v.name} (${v.gender || '?'}) ${v.owner === 'me' ? '⭐' : ''}`;
        sel.appendChild(opt);
    });
}

function renderVoicesGrid(voices) {
    const grid = $('#voices-grid');
    if (!voices.length) {
        grid.innerHTML = '<p class="hint">Nenhuma voz carregada. Clique em 🔄.</p>';
        return;
    }
    grid.innerHTML = '';
    voices.slice(0, 30).forEach(v => {
        const card = document.createElement('div');
        card.className = 'voice-card';
        card.innerHTML = `
            <div class="voice-name">${escapeHtml(v.name)}</div>
            <div class="voice-meta">${v.gender || ''} · ${v.owner === 'me' ? '⭐ minha' : v.owner}</div>
            <div class="voice-desc">${escapeHtml(v.description || '')}</div>
            ${v.preview_url ? `<audio controls src="${v.preview_url}" preload="none"></audio>` : ''}
            <button class="btn btn-sm btn-ghost" data-voice-id="${v.id}">Usar esta voz</button>
        `;
        card.querySelector('button').addEventListener('click', () => {
            $('#voice-select').value = v.id;
            if (!$(`#voice-select option[value="${v.id}"]`)) {
                const opt = document.createElement('option');
                opt.value = v.id;
                opt.textContent = v.name;
                $('#voice-select').appendChild(opt);
                $('#voice-select').value = v.id;
            }
        });
        grid.appendChild(card);
    });
}

// ═══════════════════════════════════════════════════════════
//  IA — GERAR PRÁTICA
// ═══════════════════════════════════════════════════════════
$('#btn-ai-generate').addEventListener('click', async () => {
    const topic = $('#ai-topic').value.trim() || 'everyday conversation';
    const target_lang = $('#ai-lang').value || 'en';
    const level = $('#ai-level').value;
    const text_length = $('#ai-length').value || 'medium';
    const text_type = $('#ai-type').value || 'dialogue';
    const focus = $('#ai-focus').value;

    show('#ai-practice-loading'); hide('#ai-practice-result');
    $('#btn-ai-generate').disabled = true;

    try {
        const requestPayload = {
            topic,
            level,
            focus,
            target_lang,
            text_length,
            text_type,
        };
        const { result: data } = await runAgentWithFallback({
            intent: 'practice',
            query: 'gerar texto de prática',
            payload: { ...requestPayload, action: 'generate_practice_text' },
            fallbackCall: () => postJson('/api/generate-practice', requestPayload),
            operation: 'generate_practice_text',
        });
        if (!data?.practice) throw new Error('Resposta inválida ao gerar prática.');
        renderAiPractice(data.practice);
    } catch (err) {
        alert(`Erro: ${err.message}`);
    } finally {
        hide('#ai-practice-loading');
        $('#btn-ai-generate').disabled = false;
    }
});

function renderAiPractice(p) {
    show('#ai-practice-result');
    $('#ai-practice-title').textContent = p.title || 'Prática gerada';
    $('#ai-practice-text').textContent = p.text || '';

    const focusEl = $('#ai-practice-focus');
    focusEl.innerHTML = '';
    (p.focus_points || []).forEach(f => {
        focusEl.innerHTML += `<span class="ai-tag">${escapeHtml(f)}</span>`;
    });

    const vocabEl = $('#ai-practice-vocab');
    if (p.vocabulary_preview?.length) {
        vocabEl.innerHTML = '<h4>📚 Vocabulário</h4><div class="vocab-grid">' +
            p.vocabulary_preview.map(v =>
                `<div class="vocab-item"><strong>${escapeHtml(v.word)}</strong><span>${escapeHtml(v.meaning)}</span></div>`
            ).join('') + '</div>';
    } else {
        vocabEl.innerHTML = '';
    }
}

$('#btn-use-ai-text').addEventListener('click', () => {
    const text = $('#ai-practice-text').textContent;
    if (text) {
        const aiLang = $('#ai-lang')?.value || '';
        const practiceLang = $('#lang-select');
        if (practiceLang && aiLang) {
            const hasOption = Array.from(practiceLang.options || []).some(opt => opt.value === aiLang);
            practiceLang.value = hasOption ? aiLang : '';
        }
        $('#input-text').value = text;
        $$('.tab')[0].click(); // Switch to practice tab
    }
});

// ═══════════════════════════════════════════════════════════
//  MISSION CONTROL — Floating Sidebar
// ═══════════════════════════════════════════════════════════
const mcState = {
    activePhase: -1,
    completed: new Set(),
    timers: {},        // { phaseNum: { interval, remaining, total, paused } }
};

// Show panel when session is generated
function showMissionControl() {
    const panel = $('#mission-control');
    panel.classList.remove('hidden');
    panel.classList.remove('mc-minimized');
    // Reset all phases
    mcState.activePhase = -1;
    mcState.completed.clear();
    Object.values(mcState.timers).forEach(t => { if (t.interval) clearInterval(t.interval); });
    mcState.timers = {};
    $$('.mc-phase').forEach(ph => {
        ph.classList.remove('mc-active', 'mc-done');
        const timerRow = ph.querySelector('.mc-timer-row');
        timerRow.classList.add('hidden');
        const dur = parseInt(ph.dataset.mcDuration);
        ph.querySelector('.mc-timer-display').textContent = formatTime(dur);
        ph.querySelector('.mc-timer-fill').style.width = '100%';
        ph.querySelector('.mc-timer-ctrl').textContent = '⏸';
        ph.querySelector('.mc-check-icon').textContent = '○';
    });
    updateMcProgress();
    // Mobile body padding
    if (window.innerWidth <= 800) document.body.classList.add('mc-mobile-open');
}

// Toggle minimize
$('#mc-toggle-btn').addEventListener('click', () => {
    const panel = $('#mission-control');
    panel.classList.toggle('mc-minimized');
    if (window.innerWidth <= 800) {
        document.body.classList.toggle('mc-mobile-open', !panel.classList.contains('mc-minimized'));
    }
});

// Reset
$('#mc-reset-btn').addEventListener('click', () => {
    if (confirm('Reiniciar todas as fases?')) showMissionControl();
});

// Phase play buttons
$$('.mc-play-btn').forEach(btn => {
    btn.addEventListener('click', e => {
        e.stopPropagation();
        const phase = btn.closest('.mc-phase');
        const num = parseInt(phase.dataset.mcPhase);
        activatePhase(num);
    });
});

// Checkbox buttons
$$('.mc-check').forEach(btn => {
    btn.addEventListener('click', e => {
        e.stopPropagation();
        const phase = btn.closest('.mc-phase');
        const num = parseInt(phase.dataset.mcPhase);
        togglePhaseComplete(num);
    });
});

// Timer control buttons
$$('.mc-timer-ctrl').forEach(btn => {
    btn.addEventListener('click', e => {
        e.stopPropagation();
        const phase = btn.closest('.mc-phase');
        const num = parseInt(phase.dataset.mcPhase);
        toggleTimerPause(num);
    });
});

function activatePhase(num) {
    const phases = $$('.mc-phase');
    mcState.activePhase = num;

    phases.forEach(ph => {
        const n = parseInt(ph.dataset.mcPhase);
        ph.classList.toggle('mc-active', n === num);
        // Show timer only for active phase
        const timerRow = ph.querySelector('.mc-timer-row');
        if (n === num) {
            timerRow.classList.remove('hidden');
            // Start timer if not already running
            if (!mcState.timers[num]) startPhaseTimer(num);
        }
    });

    // Execute smart action for this phase
    executePhaseAction(num);
}

function executePhaseAction(num) {
    const phase = $$(`.mc-phase[data-mc-phase="${num}"]`)[0];
    if (!phase) return;
    const action = phase.dataset.mcAction;
    const audio = $('#main-audio');
    const karaokeText = $('#karaoke-text');
    const karaokeCard = $('.karaoke-card');
    const recordingCard = $('#btn-record')?.closest('.card');

    // Remove text-hidden class first
    if (karaokeText) karaokeText.classList.remove('mc-text-hidden');

    switch (action) {
        case 'listen-only':
            // Play audio, hide karaoke text
            if (karaokeText) karaokeText.classList.add('mc-text-hidden');
            if (audio?.src) { audio.currentTime = 0; audio.play(); }
            // Enable loop for listening
            if (!state.loopEnabled) $('#btn-loop').click();
            break;

        case 'read-only':
            // Pause audio, show text clearly
            if (audio) audio.pause();
            if (karaokeCard) karaokeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;

        case 'listen-read':
            // Play audio with karaoke synced
            if (audio?.src) { audio.currentTime = 0; audio.play(); }
            if (karaokeCard) karaokeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;

        case 'shadow-with-text':
            // Play audio with loop, show text
            if (audio?.src) { audio.currentTime = 0; audio.play(); }
            if (!state.loopEnabled) $('#btn-loop').click();
            if (karaokeCard) karaokeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;

        case 'shadow-no-text':
            // Play audio with loop, blur/hide text
            if (karaokeText) karaokeText.classList.add('mc-text-hidden');
            if (audio?.src) { audio.currentTime = 0; audio.play(); }
            if (!state.loopEnabled) $('#btn-loop').click();
            break;

        case 'record':
            // Show recording area, pause audio
            if (audio) audio.pause();
            if (state.loopEnabled) $('#btn-loop').click(); // turn off loop
            if (recordingCard) recordingCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            break;
    }
}

function startPhaseTimer(num) {
    const phase = $$(`.mc-phase[data-mc-phase="${num}"]`)[0];
    const total = parseInt(phase.dataset.mcDuration);
    const display = phase.querySelector('.mc-timer-display');
    const fill = phase.querySelector('.mc-timer-fill');
    const ctrl = phase.querySelector('.mc-timer-ctrl');

    const timer = { remaining: total, total, paused: false, interval: null };
    mcState.timers[num] = timer;

    ctrl.textContent = '⏸';

    timer.interval = setInterval(() => {
        if (timer.paused) return;
        timer.remaining--;
        display.textContent = formatTime(timer.remaining);
        fill.style.width = `${(timer.remaining / timer.total) * 100}%`;

        if (timer.remaining <= 0) {
            clearInterval(timer.interval);
            display.textContent = '✅ Concluído!';
            display.style.color = 'var(--success)';
            fill.style.width = '0%';
            ctrl.textContent = '🔄';
            playBeep();
            // Auto-mark as complete
            togglePhaseComplete(num, true);
            // Auto-advance to next phase
            const nextNum = num + 1;
            if (nextNum <= 6 && !mcState.completed.has(nextNum)) {
                setTimeout(() => activatePhase(nextNum), 1500);
            }
        }
    }, 1000);
}

function toggleTimerPause(num) {
    const timer = mcState.timers[num];
    if (!timer) return;

    const phase = $$(`.mc-phase[data-mc-phase="${num}"]`)[0];
    const ctrl = phase.querySelector('.mc-timer-ctrl');

    if (timer.remaining <= 0) {
        // Reset timer
        clearInterval(timer.interval);
        delete mcState.timers[num];
        const display = phase.querySelector('.mc-timer-display');
        const fill = phase.querySelector('.mc-timer-fill');
        display.style.color = '';
        display.textContent = formatTime(parseInt(phase.dataset.mcDuration));
        fill.style.width = '100%';
        phase.classList.remove('mc-done');
        mcState.completed.delete(num);
        updateMcProgress();
        startPhaseTimer(num);
        return;
    }

    timer.paused = !timer.paused;
    ctrl.textContent = timer.paused ? '▶' : '⏸';
}

function togglePhaseComplete(num, forceComplete = false) {
    const phase = $$(`.mc-phase[data-mc-phase="${num}"]`)[0];

    if (forceComplete || !mcState.completed.has(num)) {
        mcState.completed.add(num);
        phase.classList.add('mc-done');
        phase.classList.remove('mc-active');
        // Stop timer if running
        const timer = mcState.timers[num];
        if (timer?.interval && timer.remaining > 0) {
            clearInterval(timer.interval);
            phase.querySelector('.mc-timer-display').textContent = '✅ Feito';
            phase.querySelector('.mc-timer-display').style.color = 'var(--success)';
            phase.querySelector('.mc-timer-fill').style.width = '0%';
        }
    } else {
        mcState.completed.delete(num);
        phase.classList.remove('mc-done');
        // Reset timer
        if (mcState.timers[num]) {
            clearInterval(mcState.timers[num].interval);
            delete mcState.timers[num];
        }
        const dur = parseInt(phase.dataset.mcDuration);
        phase.querySelector('.mc-timer-display').textContent = formatTime(dur);
        phase.querySelector('.mc-timer-display').style.color = '';
        phase.querySelector('.mc-timer-fill').style.width = '100%';
        phase.querySelector('.mc-timer-row').classList.add('hidden');
    }
    updateMcProgress();
}

function updateMcProgress() {
    const total = 6;
    const done = mcState.completed.size;
    const pct = Math.round((done / total) * 100);

    $('#mc-ring-fill').setAttribute('stroke-dasharray', `${pct}, 100`);
    $('#mc-ring-text').textContent = `${done}/${total}`;

    // All done celebration
    if (done === total) {
        $('#mc-ring-text').textContent = '🎉';
        $('#mc-ring-fill').style.stroke = 'var(--success)';
    } else {
        $('#mc-ring-fill').style.stroke = '';
    }
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function playBeep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = 880; gain.gain.value = 0.3;
        osc.start(); setTimeout(() => { osc.stop(); ctx.close(); }, 300);
    } catch {}
}

// ═══════════════════════════════════════════════════════════
//  PROGRESSO
// ═══════════════════════════════════════════════════════════
$('#prog-diff').addEventListener('input', e => { $('#diff-display').textContent = e.target.value; });

$('#progress-form').addEventListener('submit', async e => {
    e.preventDefault();
    const entry = {
        date: $('#prog-date').value,
        material: $('#prog-material').value,
        duration_min: parseInt($('#prog-duration').value),
        repetitions: parseInt($('#prog-reps').value),
        difficulty: parseInt($('#prog-diff').value),
        notes: $('#prog-notes').value,
    };
    try {
        const { result: data } = await runAgentWithFallback({
            intent: 'progress',
            query: 'salvar progresso de estudo',
            payload: { ...entry, action: 'save' },
            fallbackCall: () => postJson('/api/progress', entry),
            operation: 'progress_save',
        });
        if (data?.ok) {
            $('#prog-material').value = '';
            $('#prog-notes').value = '';
            loadProgress();
        }
    } catch (err) { alert('Erro: ' + err.message); }
});

async function loadProgress() {
    try {
        const { result } = await runAgentWithFallback({
            intent: 'progress',
            query: 'mostrar progresso',
            payload: { action: 'summary' },
            fallbackCall: () => getJson('/api/progress'),
            operation: 'progress_get',
        });
        const summary = (result && !Array.isArray(result) && typeof result.summary === 'object')
            ? result.summary
            : null;
        const entries = Array.isArray(result)
            ? result
            : (Array.isArray(result?.entries) ? result.entries : []);
        renderProgress(entries, summary);
    } catch {}
    await loadAdaptiveDashboard();
}

function renderProgress(entries, summary = null) {
    const tbody = $('#progress-tbody');
    const noData = $('#no-progress');
    if (!entries?.length) {
        tbody.innerHTML = '';
        noData.classList.remove('hidden');
        $('#stat-sessions').textContent = '0';
        $('#stat-minutes').textContent = '0';
        $('#stat-avg-diff').textContent = '0.0';
        $('#stat-streak').textContent = '0';
        return;
    }
    noData.classList.add('hidden');
    tbody.innerHTML = entries.map((e, i) => `<tr>
        <td>${e.date}</td><td>${escapeHtml(e.material)}</td><td>${e.duration_min}min</td>
        <td>${e.repetitions}x</td><td><span class="difficulty-stars">${'★'.repeat(e.difficulty)}${'☆'.repeat(5-e.difficulty)}</span></td>
        <td>${escapeHtml(e.notes||'')}</td>
        <td><button class="btn-delete-entry" data-index="${Number(e.id || 0) > 0 ? Number(e.id) : i}" title="Excluir">✖</button></td></tr>`).reverse().join('');

    // Delete buttons
    $$('.btn-delete-entry').forEach(btn => {
        btn.addEventListener('click', async (ev) => {
            ev.stopPropagation();
            const idx = btn.dataset.index;
            if (!confirm('Excluir esta entrada?')) return;
            try {
                const res = await fetch(withLearnerQuery(`/api/progress/${idx}`), {
                    method: 'DELETE',
                    headers: buildLearnerHeaders(),
                });
                if ((await res.json()).ok) loadProgress();
            } catch {}
        });
    });

    const computedTotal = entries.length;
    const computedMinutes = entries.reduce((s, e) => s + (e.duration_min || 0), 0);
    const computedAvg = computedTotal
        ? (entries.reduce((s, e) => s + (e.difficulty || 0), 0) / computedTotal)
        : 0;

    let total = computedTotal;
    let mins = computedMinutes;
    let avgValue = computedAvg;

    if (summary && typeof summary === 'object') {
        const summaryTotal = Number(summary.sessions);
        const summaryMinutes = Number(summary.minutes);
        const summaryAvg = Number(summary.avg_difficulty);
        if (Number.isFinite(summaryTotal) && summaryTotal >= 0) total = summaryTotal;
        if (Number.isFinite(summaryMinutes) && summaryMinutes >= 0) mins = summaryMinutes;
        if (Number.isFinite(summaryAvg) && summaryAvg >= 0) avgValue = summaryAvg;
    }

    const avg = Number(avgValue || 0).toFixed(1);
    const dates = [...new Set(entries.map(e => e.date))].sort().reverse();
    let streak = 0;
    const today = new Date();
    for (let i = 0; i < dates.length; i++) {
        const d = new Date(dates[i] + 'T12:00:00');
        const exp = new Date(today); exp.setDate(exp.getDate() - i);
        if (d.toISOString().split('T')[0] === exp.toISOString().split('T')[0]) streak++;
        else break;
    }
    $('#stat-sessions').textContent = total;
    $('#stat-minutes').textContent = mins;
    $('#stat-avg-diff').textContent = avg;
    $('#stat-streak').textContent = streak;
}

function initAdaptiveFlashcards() {
    $('#adaptive-flashcard')?.addEventListener('click', () => flipAdaptiveFlashcard());
    $('#adaptive-flashcard')?.addEventListener('keydown', event => {
        if (event.key === ' ' || event.key === 'Enter') {
            event.preventDefault();
            flipAdaptiveFlashcard();
        } else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            moveAdaptiveFlashcard(-1);
        } else if (event.key === 'ArrowRight') {
            event.preventDefault();
            moveAdaptiveFlashcard(1);
        }
    });
    $('#btn-adaptive-flip')?.addEventListener('click', () => flipAdaptiveFlashcard());
    $('#btn-adaptive-flashcard-prev')?.addEventListener('click', () => moveAdaptiveFlashcard(-1));
    $('#btn-adaptive-flashcard-next')?.addEventListener('click', () => moveAdaptiveFlashcard(1));
    $('#btn-adaptive-grade-again')?.addEventListener('click', () => submitAdaptiveFlashcardReview('again'));
    $('#btn-adaptive-grade-hard')?.addEventListener('click', () => submitAdaptiveFlashcardReview('hard'));
    $('#btn-adaptive-grade-good')?.addEventListener('click', () => submitAdaptiveFlashcardReview('good'));
    $('#btn-adaptive-grade-easy')?.addEventListener('click', () => submitAdaptiveFlashcardReview('easy'));
}

function filterAdaptiveWordItems(items) {
    return (Array.isArray(items) ? items : []).filter(item => {
        const itemType = String(item?.item_type || '').toLowerCase();
        const skillArea = String(item?.skill_area || '').toLowerCase();
        return itemType.includes('word') || itemType.includes('vocab') || skillArea === 'vocabulary';
    });
}

function buildAdaptiveFlashcardDeck(data) {
    const sortByWeakness = (left, right) => {
        const leftMastery = Number(left?.mastery_score || 0);
        const rightMastery = Number(right?.mastery_score || 0);
        if (leftMastery !== rightMastery) return leftMastery - rightMastery;

        const leftSeen = Number(left?.seen_count || 0);
        const rightSeen = Number(right?.seen_count || 0);
        return leftSeen - rightSeen;
    };
    const sortByDueDate = (left, right) => {
        const leftDue = new Date(String(left?.next_due_at || '')).getTime();
        const rightDue = new Date(String(right?.next_due_at || '')).getTime();
        const safeLeft = Number.isFinite(leftDue) ? leftDue : Number.MAX_SAFE_INTEGER;
        const safeRight = Number.isFinite(rightDue) ? rightDue : Number.MAX_SAFE_INTEGER;
        if (safeLeft !== safeRight) return safeLeft - safeRight;
        return sortByWeakness(left, right);
    };
    const dueItems = filterAdaptiveWordItems(data?.review_queue).sort(sortByDueDate);
    const weakItems = filterAdaptiveWordItems(data?.weak_points).sort(sortByWeakness);
    const strongItems = filterAdaptiveWordItems(data?.strengths).sort(sortByWeakness);
    const source = [...dueItems, ...weakItems, ...strongItems];

    const seen = new Set();
    return source.filter(item => {
        const key = String(item?.id || `${item?.item_type || 'item'}:${item?.source_text || ''}`);
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

function getAdaptiveFlashcardCurrent() {
    const flash = state.adaptiveFlashcards;
    if (!flash.deck.length) return null;
    return flash.deck[flash.index] || null;
}

function formatAdaptiveDueLabel(rawValue) {
    const due = new Date(String(rawValue || ''));
    if (Number.isNaN(due.getTime())) return 'Sem próxima revisão';

    const diffMs = due.getTime() - Date.now();
    if (diffMs <= 0) return 'Vencido';

    const diffHours = Math.round(diffMs / (1000 * 60 * 60));
    if (diffHours < 24) return `Próx. em ${Math.max(1, diffHours)}h`;

    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
    return `Próx. em ${Math.max(1, diffDays)}d`;
}

function formatAdaptiveSkillLabel(item) {
    const area = String(item?.skill_area || '').toLowerCase();
    if (area === 'vocabulary') return 'Vocabulário';
    if (area === 'pronunciation') return 'Pronúncia';
    if (area === 'grammar') return 'Gramática';
    if (area === 'shadowing') return 'Shadowing';
    return area ? area[0].toUpperCase() + area.slice(1) : 'Revisão';
}

function renderAdaptiveFlashcards(data) {
    const flash = state.adaptiveFlashcards;
    const previousId = Number(flash.deck[flash.index]?.id || 0);
    const deck = buildAdaptiveFlashcardDeck(data || {});

    flash.lastData = data || {};
    flash.deck = deck;

    if (!deck.length) {
        flash.index = 0;
        flash.flipped = false;
        refreshAdaptiveFlashcardView();
        return;
    }

    const previousIndex = previousId
        ? deck.findIndex(item => Number(item?.id || 0) === previousId)
        : -1;
    flash.index = previousIndex >= 0
        ? previousIndex
        : Math.max(0, Math.min(flash.index, deck.length - 1));
    flash.flipped = false;
    refreshAdaptiveFlashcardView();
}

function refreshAdaptiveFlashcardView() {
    const flash = state.adaptiveFlashcards;
    const current = getAdaptiveFlashcardCurrent();
    const card = $('#adaptive-flashcard');
    const front = $('#adaptive-flashcard-front');
    const back = $('#adaptive-flashcard-back');
    const meta = $('#adaptive-flashcard-meta');
    const hint = $('#adaptive-flashcard-hint');
    const prev = $('#btn-adaptive-flashcard-prev');
    const next = $('#btn-adaptive-flashcard-next');
    const flip = $('#btn-adaptive-flip');
    const again = $('#btn-adaptive-grade-again');
    const hard = $('#btn-adaptive-grade-hard');
    const good = $('#btn-adaptive-grade-good');
    const easy = $('#btn-adaptive-grade-easy');

    if (!card || !front || !back || !meta || !hint) return;

    if (!current) {
        meta.textContent = '0 cartas';
        hint.textContent = 'Nenhum flashcard de palavras disponível ainda. Gere análises ou aulas com vocabulário salvo no banco.';
        front.innerHTML = `
            <div class="adaptive-flashcard-empty">
                <strong>Sem cartas para revisar.</strong>
                <span>O banco ainda não devolveu palavras rastreadas para este aluno.</span>
            </div>
        `;
        back.innerHTML = '';
        card.classList.remove('is-flipped', 'is-loading');
        card.classList.add('is-empty');
        if (prev) prev.disabled = true;
        if (next) next.disabled = true;
        if (flip) {
            flip.disabled = true;
            flip.textContent = '🔄 Virar';
        }
        [again, hard, good, easy].forEach(btn => {
            if (btn) btn.disabled = true;
        });
        return;
    }

    const mastery = Math.round(Number(current.mastery_score || 0) * 100);
    const seenCount = Number(current.seen_count || 0);
    const successCount = Number(current.success_count || 0);
    const typeLabel = escapeHtml(formatAdaptiveSkillLabel(current));
    const dueLabel = escapeHtml(formatAdaptiveDueLabel(current.next_due_at));
    const translation = escapeHtml(current.translation || 'Sem tradução salva ainda.');
    const context = escapeHtml(current.context_text || 'Sem contexto salvo ainda.');
    const notes = escapeHtml(current.notes || 'Sem observação adicional.');

    meta.textContent = `Carta ${flash.index + 1}/${flash.deck.length}`;
    hint.textContent = flash.submitting
        ? 'Salvando resultado da revisão...'
        : (
            flash.flipped
                ? 'Classifique a lembrança para atualizar o espaçamento no banco.'
                : 'Clique na carta para ver significado, contexto e dica.'
        );

    front.innerHTML = `
        <div class="adaptive-flashcard-kicker">
            <span class="badge badge-sm">${typeLabel}</span>
            <span>${dueLabel}</span>
        </div>
        <div class="adaptive-flashcard-text">${escapeHtml(current.source_text || 'Sem conteúdo')}</div>
        <div class="adaptive-flashcard-foot">
            <span>Maestria ${mastery}%</span>
            <span>${seenCount} revisões</span>
            <span>Toque para virar</span>
        </div>
    `;
    back.innerHTML = `
        <div class="adaptive-flashcard-kicker">
            <span class="badge badge-sm">${typeLabel}</span>
            <span>${current.interval_days || 0}d de intervalo</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">Significado</span>
            <strong>${translation}</strong>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">Contexto</span>
            <span>${context}</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">Dica</span>
            <span>${notes}</span>
        </div>
        <div class="adaptive-flashcard-foot">
            <span>Acertos ${successCount}/${Math.max(1, seenCount)}</span>
            <span>${dueLabel}</span>
            <span>Agora classifique</span>
        </div>
    `;

    card.classList.toggle('is-flipped', flash.flipped);
    card.classList.toggle('is-loading', flash.submitting);
    card.classList.remove('is-empty');

    if (prev) prev.disabled = flash.submitting || flash.index <= 0;
    if (next) next.disabled = flash.submitting || flash.index >= flash.deck.length - 1;
    if (flip) {
        flip.disabled = flash.submitting || !flash.deck.length;
        flip.textContent = flash.flipped ? '↩ Frente' : '🔄 Virar';
    }
    [again, hard, good, easy].forEach(btn => {
        if (btn) btn.disabled = flash.submitting || !flash.flipped;
    });
}

function moveAdaptiveFlashcard(delta) {
    const flash = state.adaptiveFlashcards;
    if (flash.submitting || !flash.deck.length) return;
    flash.index = Math.max(0, Math.min(flash.deck.length - 1, flash.index + delta));
    flash.flipped = false;
    refreshAdaptiveFlashcardView();
}

function flipAdaptiveFlashcard(forceValue = null) {
    const flash = state.adaptiveFlashcards;
    if (flash.submitting || !flash.deck.length) return;
    flash.flipped = typeof forceValue === 'boolean' ? forceValue : !flash.flipped;
    refreshAdaptiveFlashcardView();
}

async function submitAdaptiveFlashcardReview(resultKey) {
    const flash = state.adaptiveFlashcards;
    const current = getAdaptiveFlashcardCurrent();
    if (!current || flash.submitting) return;

    const warningEl = $('#adaptive-warning');
    if (warningEl) {
        warningEl.textContent = '';
        warningEl.classList.add('hidden');
    }

    flash.submitting = true;
    refreshAdaptiveFlashcardView();
    try {
        const response = await postJson('/api/learner/review', {
            item_id: current.id,
            result: resultKey,
            source: 'adaptive_flashcards',
        });
        flash.submitting = false;
        renderAdaptiveDashboard(response?.dashboard || {});
    } catch (err) {
        flash.submitting = false;
        refreshAdaptiveFlashcardView();
        if (warningEl) {
            warningEl.textContent = `Não foi possível atualizar a revisão: ${err.message}`;
            warningEl.classList.remove('hidden');
        }
    }
}

async function loadAdaptiveDashboard() {
    const warningEl = $('#adaptive-warning');
    if (warningEl) {
        warningEl.textContent = '';
        warningEl.classList.add('hidden');
    }
    try {
        const data = await getJson('/api/learner/dashboard');
        renderAdaptiveDashboard(data || {});
    } catch (err) {
        renderAdaptiveDashboard({});
        if (warningEl) {
            warningEl.textContent = `Coach adaptativo indisponível: ${err.message}`;
            warningEl.classList.remove('hidden');
        }
    }
}

function renderAdaptiveDashboard(data) {
    const summary = data?.summary || {};
    $('#adaptive-pron-score').textContent = Number(summary.pronunciation_avg_score || 0).toFixed(1);
    $('#adaptive-review-due').textContent = Number(summary.review_due || 0);
    $('#adaptive-tracked-items').textContent = Number(summary.tracked_items || 0);
    $('#adaptive-active-days').textContent = Number(summary.active_days_7d || 0);

    const learnerMeta = $('#adaptive-learner-meta');
    if (learnerMeta) {
        const learner = data?.learner || {};
        const bits = [
            learner?.target_lang ? `Idioma: ${String(learner.target_lang).toUpperCase()}` : '',
            learner?.level ? `Nível: ${learner.level}` : '',
            summary?.last_activity_at ? `Última atividade: ${new Date(summary.last_activity_at).toLocaleString('pt-BR')}` : '',
        ].filter(Boolean);
        learnerMeta.textContent = bits.join(' · ') || 'Sem atividade adaptativa ainda.';
    }

    const warningEl = $('#adaptive-warning');
    if (warningEl) {
        const warning = data?.adaptive_warning || '';
        warningEl.textContent = warning;
        warningEl.classList.toggle('hidden', !warning);
    }

    renderAdaptiveFlashcards(data || {});

    renderAdaptiveList('#review-queue', data?.review_queue, item => `
        <div class="adaptive-item">
            <div class="adaptive-item-title">${escapeHtml(item.source_text || '')}</div>
            <div class="adaptive-item-meta">
                <span class="badge badge-sm">${escapeHtml(item.skill_area || 'review')}</span>
                <span>Maestria ${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
                ${item.translation ? `<span>${escapeHtml(item.translation)}</span>` : ''}
            </div>
            ${item.notes ? `<div class="adaptive-item-note">${escapeHtml(item.notes)}</div>` : ''}
        </div>
    `, 'Nenhum item vencido para revisão hoje.');

    renderAdaptiveList('#adaptive-recommendations', data?.recommendations, item => `
        <div class="adaptive-item">
            <div class="adaptive-item-title">${escapeHtml(item.title || '')}</div>
            <div class="adaptive-item-note">${escapeHtml(item.reason || '')}</div>
            <div class="adaptive-item-meta">
                <span class="badge badge-sm">${escapeHtml(item.kind || 'coach')}</span>
                <span>${escapeHtml(item.skill_area || 'general')}</span>
            </div>
        </div>
    `, 'As próximas ações vão aparecer assim que houver histórico suficiente.');

    renderAdaptiveList('#adaptive-weak-points', data?.weak_points, item => `
        <div class="adaptive-pill">
            <strong>${escapeHtml(item.source_text || '')}</strong>
            <span>${escapeHtml(item.skill_area || 'general')}</span>
            <span>${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
        </div>
    `, 'Seus pontos fracos aparecem aqui conforme o sistema aprende com você.');

    renderAdaptiveList('#adaptive-strengths', data?.strengths, item => `
        <div class="adaptive-pill adaptive-pill-strong">
            <strong>${escapeHtml(item.source_text || '')}</strong>
            <span>${escapeHtml(item.skill_area || 'general')}</span>
            <span>${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
        </div>
    `, 'Seus pontos fortes aparecem aqui após algumas revisões bem-sucedidas.');
}

function renderAdaptiveList(selector, items, itemRenderer, emptyMessage) {
    const el = $(selector);
    if (!el) return;
    if (!Array.isArray(items) || !items.length) {
        el.innerHTML = `<p class="hint">${escapeHtml(emptyMessage)}</p>`;
        return;
    }
    el.innerHTML = items.map(item => itemRenderer(item || {})).join('');
}

// ═════════════════════════════════════════════════════════
//  EXPORT CSV
// ═════════════════════════════════════════════════════════
if ($('#btn-export-csv')) {
    $('#btn-export-csv').addEventListener('click', () => {
        window.open(withLearnerQuery('/api/progress/export'), '_blank');
    });
}

// ═════════════════════════════════════════════════════════
//  SESSION HISTORY
// ═════════════════════════════════════════════════════════
function setupHistoryAccordion() {
    const section = $('#history-section');
    const button = $('#history-accordion-btn');
    const content = $('#history-content');
    if (!section || !button || !content || button.dataset.bound === '1') return;

    try {
        const saved = localStorage.getItem('historyAccordionOpen');
        if (saved === '0') state.historyAccordionOpen = false;
        if (saved === '1') state.historyAccordionOpen = true;
    } catch {}

    const applyState = (isOpen, { save = true } = {}) => {
        state.historyAccordionOpen = !!isOpen;
        section.classList.toggle('is-collapsed', !isOpen);
        button.setAttribute('aria-expanded', String(isOpen));

        if (isOpen) {
            content.style.maxHeight = `${content.scrollHeight}px`;
            content.style.opacity = '1';
            content.style.marginTop = '8px';
        } else {
            content.style.maxHeight = '0px';
            content.style.opacity = '0';
            content.style.marginTop = '0px';
        }

        if (save) {
            try { localStorage.setItem('historyAccordionOpen', isOpen ? '1' : '0'); } catch {}
        }
    };

    button.addEventListener('click', () => {
        const nextOpen = section.classList.contains('is-collapsed');
        applyState(nextOpen);
    });

    content.addEventListener('transitionend', (event) => {
        if (event.propertyName !== 'max-height') return;
        if (!section.classList.contains('is-collapsed')) {
            content.style.maxHeight = `${content.scrollHeight}px`;
        }
    });

    window.addEventListener('resize', () => {
        if (!section.classList.contains('is-collapsed')) {
            content.style.maxHeight = `${content.scrollHeight}px`;
        }
    });

    button.dataset.bound = '1';
    applyState(state.historyAccordionOpen, { save: false });
}

function refreshHistoryAccordionHeight() {
    const section = $('#history-section');
    const content = $('#history-content');
    if (!section || !content || section.classList.contains('is-collapsed')) return;
    content.style.maxHeight = `${content.scrollHeight}px`;
}

async function saveToHistory(sessionData) {
    try {
        await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: sessionData.text,
                language: sessionData.language,
                engine: sessionData.tts_engine,
            }),
        });
        loadSessionHistory();
    } catch {}
}

async function loadSessionHistory() {
    try {
        const entries = await (await fetch('/api/history')).json();
        const section = $('#history-section');
        const list = $('#history-list');
        if (!section || !list) return;
        if (!entries?.length) { section.classList.add('hidden'); return; }

        section.classList.remove('hidden');
        list.innerHTML = '';
        entries.slice().reverse().slice(0, 20).forEach(e => {
            const item = document.createElement('div');
            item.className = 'history-item';
            const preview = e.text.length > 80 ? e.text.slice(0, 80) + '...' : e.text;
            item.innerHTML = `
                <div class="history-meta"><span>${e.date}</span><span class="badge badge-sm">${e.language}</span><span class="badge badge-sm">${e.engine}</span></div>
                <div class="history-text">${escapeHtml(preview)}</div>
            `;
            item.addEventListener('click', () => {
                $('#input-text').value = e.text;
                setupWordCounter && setupWordCounter();
                // Trigger input event to update word counter  
                $('#input-text').dispatchEvent(new Event('input'));
                $$('.tab')[0].click();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            list.appendChild(item);
        });
        requestAnimationFrame(refreshHistoryAccordionHeight);
    } catch {}
}

// ═══════════════════════════════════════════════════════════//  DISK STATS + CLEANUP
// ═════════════════════════════════════════════════════════
async function loadDiskStats() {
    try {
        const stats = await (await fetch('/api/audio-stats')).json();
        const el = $('#disk-stats');
        if (stats.file_count > 0) {
            el.textContent = `💾 ${stats.file_count} arquivos (${stats.total_size_mb} MB)`;
            el.classList.add('has-files');
        } else {
            el.textContent = '💾 Cache limpo';
            el.classList.remove('has-files');
        }
    } catch {}
}

if ($('#btn-cleanup')) {
    $('#btn-cleanup').addEventListener('click', async () => {
        if (!confirm('Limpar todos os áudios em cache?')) return;
        try {
            const res = await fetch('/api/cleanup', { method: 'POST' });
            const data = await res.json();
            loadDiskStats();
            alert(`✅ ${data.removed} arquivo(s) removidos`);
        } catch { alert('Erro ao limpar cache'); }
    });
}

// ═════════════════════════════════════════════════════════//  UTILS
// ═══════════════════════════════════════════════════════════
function animateStaggerElements(nodeList, className = 'is-revealing', stepMs = 30) {
    const elements = Array.from(nodeList || []);
    elements.forEach((el, index) => {
        el.classList.remove(className);
        // Restart CSS animation in repeated renders.
        void el.offsetWidth;
        setTimeout(() => el.classList.add(className), index * stepMs);
    });
}

function escapeHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function show(s) { $(s).classList.remove('hidden'); }
function hide(s) { $(s).classList.add('hidden'); }

// ─── Conversação por Voz ───────────────────────────────────
const convState = {
    mediaRecorder: null,
    audioChunks:   [],
    isRecording:   false,
    isLoading:     false,
    history:       [],
    silenceWatchInterval: null,
    silenceAudioContext: null,
    silenceSource: null,
    silenceAnalyser: null,
    silenceData: null,
    silenceLastSpeechAt: 0,
    silenceSpeechDetected: false,
};

document.addEventListener('DOMContentLoaded', () => {
    $('#conv-mic-btn')?.addEventListener('click', toggleConvRecording);
    $('#conv-clear-btn')?.addEventListener('click', clearConvChat);
    $('#conv-lesson-btn')?.addEventListener('click', generateLesson);
    $('#lesson-modal-close')?.addEventListener('click', closeLessonModal);
    $('#lesson-modal')?.addEventListener('click', function(e) {
        if (e.target === this) closeLessonModal();
    });
    $('#conv-suggest-toggle')?.addEventListener('change', function() {
        const colinha = document.getElementById('conv-colinha');
        if (!colinha) return;
        if (this.checked) {
            colinha.classList.remove('hidden');
        } else {
            colinha.classList.add('hidden');
        }
    });
});

function toggleConvRecording() {
    if (convState.isLoading) return;
    convState.isRecording ? stopConvRecording() : startConvRecording();
}

async function startConvRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        convState.audioChunks = [];
        convState.mediaRecorder = new MediaRecorder(stream);
        convState.mediaRecorder.ondataavailable = e => { if (e.data.size > 0) convState.audioChunks.push(e.data); };
        convState.mediaRecorder.onstop = handleConvAudioStop;
        convState.mediaRecorder.start();
        convState.isRecording = true;
        const autoSendEnabled = document.getElementById('conv-auto-send-toggle')?.checked || false;
        if (autoSendEnabled) startConvSilenceWatcher(stream);
        setConvUiState('recording');
    } catch (err) {
        setConvStatus('Erro ao acessar microfone: ' + err.message, '');
    }
}

function stopConvRecording() {
    stopConvSilenceWatcher();
    if (!convState.mediaRecorder) return;
    if (convState.mediaRecorder.state !== 'inactive') {
        convState.mediaRecorder.stop();
    }
    convState.mediaRecorder.stream.getTracks().forEach(t => t.stop());
    convState.isRecording = false;
    setConvUiState('loading');
}

function startConvSilenceWatcher(stream) {
    stopConvSilenceWatcher();
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    try {
        const audioContext = new AudioCtx();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.85;
        source.connect(analyser);

        convState.silenceAudioContext = audioContext;
        convState.silenceSource = source;
        convState.silenceAnalyser = analyser;
        convState.silenceData = new Uint8Array(analyser.fftSize);
        convState.silenceLastSpeechAt = Date.now();
        convState.silenceSpeechDetected = false;

        let noiseFloor = 0.0;
        let noiseSamples = 0;
        const pollMs = 120;
        const silenceMs = 5000;

        convState.silenceWatchInterval = setInterval(() => {
            if (!convState.isRecording || !convState.silenceAnalyser || !convState.silenceData) return;
            convState.silenceAnalyser.getByteTimeDomainData(convState.silenceData);

            let sumSq = 0;
            for (let i = 0; i < convState.silenceData.length; i++) {
                const v = (convState.silenceData[i] - 128) / 128;
                sumSq += v * v;
            }
            const rms = Math.sqrt(sumSq / convState.silenceData.length);
            if (noiseSamples < 25) {
                noiseFloor = ((noiseFloor * noiseSamples) + rms) / (noiseSamples + 1);
                noiseSamples += 1;
            } else {
                // Adapt floor slowly to ambient changes.
                noiseFloor = (noiseFloor * 0.97) + (rms * 0.03);
            }

            const dynamicThreshold = Math.max(0.012, noiseFloor + 0.01);
            const now = Date.now();
            if (rms > dynamicThreshold) {
                convState.silenceSpeechDetected = true;
                convState.silenceLastSpeechAt = now;
                return;
            }
            if (convState.silenceSpeechDetected && (now - convState.silenceLastSpeechAt) >= silenceMs) {
                stopConvRecording();
            }
        }, pollMs);
    } catch (_) {
        stopConvSilenceWatcher();
    }
}

function stopConvSilenceWatcher() {
    if (convState.silenceWatchInterval) {
        clearInterval(convState.silenceWatchInterval);
        convState.silenceWatchInterval = null;
    }
    if (convState.silenceSource) {
        try { convState.silenceSource.disconnect(); } catch {}
        convState.silenceSource = null;
    }
    convState.silenceAnalyser = null;
    convState.silenceData = null;
    convState.silenceLastSpeechAt = 0;
    convState.silenceSpeechDetected = false;
    if (convState.silenceAudioContext) {
        try { convState.silenceAudioContext.close(); } catch {}
        convState.silenceAudioContext = null;
    }
}

async function handleConvAudioStop() {
    convState.isLoading = true;
    const blob = new Blob(convState.audioChunks, { type: 'audio/webm' });
    try {
        const buffer = await blob.arrayBuffer();
        // Convert to base64 safely (handles large buffers)
        let binary = '';
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const b64 = btoa(binary);

        const lang  = $('#conv-lang')?.value || 'en';
        const voice = $('#conv-voice')?.value || 'leah';
        const ttsEngine = ($('#conv-tts-engine')?.value || 'lmnt').trim().toLowerCase() || 'lmnt';
        const suggest = document.getElementById('conv-suggest-toggle')?.checked || false;

        // Show loading chips if colinha active
        if (suggest) showColinhaLoading();

        const requestPayload = {
            audio_b64: b64,
            lang,
            voice,
            tts_engine: ttsEngine,
            history: convState.history,
            suggest,
        };
        const { result: data } = await runAgentWithFallback({
            intent: 'conversation',
            query: 'conversa por voz',
            payload: { ...requestPayload, action: 'turn' },
            fallbackCall: () => postJson('/api/conversation', requestPayload),
            operation: 'conversation_turn',
        });
        if (data.error) { appendConvError(data.error); return; }

        // hide empty placeholder
        const empty = document.getElementById('conv-empty');
        if (empty) empty.style.display = 'none';

        // update history
        convState.history.push({ role: 'user',      content: data.user_text });
        convState.history.push({ role: 'assistant', content: data.ai_text });
        if (convState.history.length > 20) convState.history = convState.history.slice(-20);

        // render bubbles
        appendConvBubble('user', data.user_text, null);
        appendConvBubble('ai',   data.ai_text,   data.audio_url);
        if (data.warning) appendConvInfo(data.warning);

        // update colinha suggestions
        if (data.suggestions) updateConvColinha(data.suggestions);
        else clearColinhaLoading();

        // auto-play AI voice
        if (data.audio_url) new Audio(data.audio_url).play().catch(() => {});
    } catch (err) {
        appendConvError('Erro de rede: ' + err.message);
    } finally {
        convState.isLoading = false;
        setConvUiState('idle');
    }
}

function appendConvBubble(role, text, audioUrl) {
    const chat = document.getElementById('conv-chat');
    const wrap = document.createElement('div');
    wrap.className = `conv-bubble conv-bubble-${role}`;
    const label = role === 'user' ? 'Você' : '🤖 IA';
    const audioHtml = (audioUrl && role === 'ai')
        ? `<div class="conv-bubble-audio">
               <button class="conv-bubble-play" onclick="convPlayAudio(this,'${escapeHtml(audioUrl)}')">▶</button>
               <span style="font-size:.78rem;opacity:.7">Ouvir novamente</span>
           </div>`
        : '';
    wrap.innerHTML = `<div class="conv-bubble-label">${label}</div><div>${escapeHtml(text)}</div>${audioHtml}`;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function convPlayAudio(btn, url) {
    const audio = new Audio(url);
    btn.textContent = '⏸';
    audio.play().catch(() => {});
    audio.onended = () => { btn.textContent = '▶'; };
}

function appendConvError(msg) {
    const chat = document.getElementById('conv-chat');
    const wrap = document.createElement('div');
    wrap.className = 'conv-bubble conv-bubble-ai';
    wrap.style.borderColor = 'var(--danger)';
    wrap.innerHTML = `<div class="conv-bubble-label" style="color:var(--danger)">Erro</div><div>${escapeHtml(msg)}</div>`;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function appendConvInfo(msg) {
    const chat = document.getElementById('conv-chat');
    const wrap = document.createElement('div');
    wrap.className = 'conv-bubble conv-bubble-ai';
    wrap.style.borderColor = 'var(--warn)';
    wrap.innerHTML = `<div class="conv-bubble-label" style="color:var(--warn)">Aviso</div><div>${escapeHtml(msg)}</div>`;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function clearConvChat() {
    convState.history = [];
    document.getElementById('conv-chat').innerHTML = `
        <div class="conv-empty" id="conv-empty">
            <span class="conv-empty-icon">🎙️</span>
            <p>Clique no microfone e comece a falar!</p>
        </div>`;
    clearColinhaLoading();
    const chips = document.getElementById('conv-chips');
    if (chips) chips.innerHTML = '';
    const empty = document.getElementById('conv-colinha-empty');
    if (empty) empty.style.display = '';
}

function showColinhaLoading() {
    const chips = document.getElementById('conv-chips');
    const empty = document.getElementById('conv-colinha-empty');
    if (!chips) return;
    if (empty) empty.style.display = 'none';
    chips.innerHTML = [
        '<div class="conv-chip conv-chip-loading">…</div>',
        '<div class="conv-chip conv-chip-loading">…</div>',
        '<div class="conv-chip conv-chip-loading">…</div>',
    ].join('');
}

function clearColinhaLoading() {
    const chips = document.getElementById('conv-chips');
    if (chips) chips.innerHTML = '';
}

function updateConvColinha(suggestions) {
    const chips  = document.getElementById('conv-chips');
    const empty  = document.getElementById('conv-colinha-empty');
    if (!chips) return;
    if (empty) empty.style.display = 'none';
    if (!suggestions || !suggestions.length) {
        chips.innerHTML = '';
        if (empty) empty.style.display = '';
        return;
    }
    chips.innerHTML = suggestions.map(s => `
        <button class="conv-chip" onclick="convChipClick(this, decodeURIComponent('${encodeURIComponent(String(s || ''))}'))">
            <span class="conv-chip-speak">📢</span>${escapeHtml(s)}
        </button>
    `).join('');
}

function convChipClick(btn, text) {
    // Highlight briefly
    btn.style.borderColor = 'var(--accent)';
    btn.style.background  = 'rgba(88,166,255,0.12)';
    setTimeout(() => {
        btn.style.borderColor = '';
        btn.style.background = '';
    }, 1200);
    // Read aloud via Web Speech API (free, no API)
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const lang = document.getElementById('conv-lang')?.value || 'en';
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }
}

// ── Lesson generation ──────────────────────────────────────────
async function generateLesson() {
    if (!convState.history.length) {
        alert('Converse primeiro antes de gerar a aula!');
        return;
    }
    const normalizedFocus = 'smart';
    const btn = document.getElementById('conv-lesson-btn');
    const lang        = document.getElementById('conv-lang')?.value        || 'en';
    const translate_to = document.getElementById('conv-translate-to')?.value || 'pt';
    const loadingLabel = '⏳ Aula inteligente: correções + pronúncia…';
    const defaultLabel = '🎯 Aula Inteligente + Correção';

    if (btn) { btn.disabled = true; btn.textContent = loadingLabel; }
    try {
        const requestPayload = {
            history: convState.history,
            lang,
            translate_to,
            lesson_focus: normalizedFocus,
        };
        const { result: data } = await runAgentWithFallback({
            intent: 'conversation',
            query: 'gerar aula inteligente com correções, sugestões e pronúncia',
            payload: { ...requestPayload, action: 'lesson' },
            fallbackCall: () => postJson('/api/conversation/lesson', requestPayload),
            operation: 'conversation_lesson',
        });
        if (data.error) throw new Error(data.error);
        renderLessonModal(data, lang, translate_to);
    } catch(e) {
        alert('Erro ao gerar aula: ' + e.message);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = defaultLabel; }
    }
}

function closeLessonModal() {
    document.getElementById('lesson-modal')?.classList.add('hidden');
    document.body.style.overflow = '';
}

function renderLessonModal(data, lang, translateTo) {
    const langNames = { en:'English', pt:'Português', es:'Español', fr:'Français', de:'Deutsch', it:'Italiano' };
    const langLabel  = langNames[lang]        || lang.toUpperCase();
    const transLabel = langNames[translateTo] || translateTo.toUpperCase();
    const focusRaw = String(data?.lesson_focus || 'balanced').trim().toLowerCase();
    const focusRequested = String(data?.lesson_focus_requested || '').trim().toLowerCase();
    const focusMap = {
        smart: 'Foco: Inteligente',
        balanced: 'Foco: Equilibrado',
        corrections: 'Foco: Correções',
        vocabulary: 'Foco: Vocabulário',
    };
    const focusBase = focusMap[focusRaw] || '';
    const focusLabel = focusBase
        ? `${focusBase}${focusRequested === 'smart' ? ' (auto)' : ''}`
        : '';
    const focusReason = String(data?.lesson_focus_reason || '').trim();
    const providerRaw = String(data?.ai_provider || '').trim().toLowerCase();
    const providerMap = {
        deepseek: 'DeepSeek',
        openrouter: 'OpenRouter',
        openai: 'OpenAI',
        ollama: 'Ollama',
        fallback: 'Fallback Local',
        fallback_local: 'Fallback Local',
    };
    const providerLabel = providerRaw ? (providerMap[providerRaw] || providerRaw.toUpperCase()) : '';

    const sub = document.getElementById('lesson-modal-sub');
    if (sub) {
        const extras = [providerLabel ? `IA: ${providerLabel}` : '', focusLabel].filter(Boolean).join(' · ');
        sub.textContent = `${langLabel} → ${transLabel}${extras ? ` · ${extras}` : ''}`;
    }

    const body = document.getElementById('lesson-modal-body');
    if (!body) return;
    let html = '';

    if (data.warning) {
        html += `<div class="lesson-section">
            <p class="lesson-summary">⚠ ${escapeHtml(data.warning)}</p>
        </div>`;
    }

    if (focusReason) {
        html += `<div class="lesson-section">
            <p class="lesson-summary">🎯 ${escapeHtml(focusReason)}</p>
        </div>`;
    }

    // Summary
    if (data.lesson?.summary) {
        html += `<div class="lesson-section">
            <h3>📝 Resumo da Conversa</h3>
            <p class="lesson-summary">${escapeHtml(data.lesson.summary)}</p>
        </div>`;
    }

    // Transcript
    if (data.transcript?.length) {
        const rows = data.transcript.map(t => {
            const isUser  = t.role === 'user';
            const roleHtml = isUser
                ? `<span class="lesson-role-user">👤 Você</span>`
                : `<span class="lesson-role-ai">🤖 Alex</span>`;
            return `<tr>
                <td>${roleHtml}</td>
                <td class="lesson-original">${escapeHtml(t.original || '')}</td>
                <td class="lesson-translation">${escapeHtml(t.translation || '—')}</td>
            </tr>`;
        }).join('');
        html += `<div class="lesson-section">
            <h3>💬 Transcrição com Tradução</h3>
            <table class="lesson-transcript">
                <thead><tr>
                    <th>Falante</th>
                    <th>${escapeHtml(langLabel)}</th>
                    <th>${escapeHtml(transLabel)}</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
    }

    // Vocabulary
    if (data.lesson?.vocabulary?.length) {
        const cards = data.lesson.vocabulary.map(v => `
            <div class="lesson-vocab-card">
                <div class="lesson-vocab-word">${escapeHtml(v.word || '')}</div>
                <div class="lesson-vocab-meaning">${escapeHtml(v.meaning || '')}</div>
                ${v.example ? `<div class="lesson-vocab-example">"${escapeHtml(v.example)}"</div>` : ''}
            </div>`).join('');
        html += `<div class="lesson-section">
            <h3>📖 Vocabulário</h3>
            <div class="lesson-vocab-grid">${cards}</div>
        </div>`;
    }

    // Grammar
    if (data.lesson?.grammar?.length) {
        const items = data.lesson.grammar.map(g => `
            <div class="lesson-grammar-item">
                <div class="lesson-grammar-point">${escapeHtml(g.point || '')}</div>
                <div class="lesson-grammar-explanation">${escapeHtml(g.explanation || '')}</div>
                ${g.example ? `<div class="lesson-grammar-example">"${escapeHtml(g.example)}"</div>` : ''}
            </div>`).join('');
        html += `<div class="lesson-section">
            <h3>📐 Gramática</h3>
            <div class="lesson-grammar-list">${items}</div>
        </div>`;
    }

    // Corrections
    if (data.lesson?.corrections?.length) {
        const items = data.lesson.corrections.map(c => `
            <div class="lesson-correction">
                ${
                    (c.original || c.corrected)
                        ? `<div class="lesson-correction-row">
                    <span class="lesson-correction-original">${escapeHtml(c.original || '')}</span>
                    <span>→</span>
                    <span class="lesson-correction-corrected">${escapeHtml(c.corrected || '')}</span>
                </div>`
                        : ''
                }
                <div class="lesson-correction-tip">${escapeHtml(c.tip || '')}</div>
            </div>`).join('');
        html += `<div class="lesson-section">
            <h3>✏️ Correções</h3>
            <div class="lesson-corrections-list">${items}</div>
        </div>`;
    }

    // Tips
    if (data.lesson?.tips?.length) {
        const items = data.lesson.tips.map(t => `
            <div class="lesson-tip">
                <span class="lesson-tip-icon">💡</span>
                <span>${escapeHtml(t)}</span>
            </div>`).join('');
        html += `<div class="lesson-section">
            <h3>💡 Dicas para Você</h3>
            <div class="lesson-tips-list">${items}</div>
        </div>`;
    }

    // Reply suggestions
    if (data.next_reply_suggestions?.length) {
        const items = data.next_reply_suggestions.map(s => `
            <button class="conv-chip" onclick="convChipClick(this, decodeURIComponent('${encodeURIComponent(String(s || ''))}'))">
                <span class="conv-chip-speak">💬</span>${escapeHtml(s)}
            </button>
        `).join('');
        html += `<div class="lesson-section">
            <h3>🗣️ Sugestões do que Responder</h3>
            <div class="conv-chips">${items}</div>
        </div>`;
    }

    // Pronunciation feedback
    const pronunciation = data.pronunciation_feedback || {};
    const pronScoreNum = Number(pronunciation.score);
    const pronHasScore = Number.isFinite(pronScoreNum);
    const pronScore = pronHasScore ? Math.max(1, Math.min(100, Math.round(pronScoreNum))) : null;
    const pronLevel = String(pronunciation.level || '').trim();
    const pronSummary = String(pronunciation.summary || '').trim();
    const pronTips = Array.isArray(pronunciation.tips) ? pronunciation.tips : [];
    const pronDrills = Array.isArray(pronunciation.drill_phrases) ? pronunciation.drill_phrases : [];
    if (pronHasScore || pronLevel || pronSummary || pronTips.length || pronDrills.length) {
        let pronHtml = '';
        if (pronHasScore || pronLevel) {
            const parts = [];
            if (pronHasScore) parts.push(`Score estimado: ${pronScore}/100`);
            if (pronLevel) parts.push(pronLevel);
            pronHtml += `<p class="lesson-summary">🧭 ${escapeHtml(parts.join(' · '))}</p>`;
        }
        if (pronSummary) {
            pronHtml += `<p class="lesson-summary">${escapeHtml(pronSummary)}</p>`;
        }
        if (pronTips.length) {
            const items = pronTips.map(t => `
                <div class="lesson-tip">
                    <span class="lesson-tip-icon">🗣️</span>
                    <span>${escapeHtml(t)}</span>
                </div>
            `).join('');
            pronHtml += `<div class="lesson-tips-list">${items}</div>`;
        }
        if (pronDrills.length) {
            const drills = pronDrills.map(t => `
                <button class="conv-chip" onclick="convChipClick(this, decodeURIComponent('${encodeURIComponent(String(t || ''))}'))">
                    <span class="conv-chip-speak">🎧</span>${escapeHtml(t)}
                </button>
            `).join('');
            pronHtml += `<div class="conv-chips">${drills}</div>`;
        }
        html += `<div class="lesson-section">
            <h3>🧠 Avaliação de Pronúncia</h3>
            ${pronHtml}
        </div>`;
    }

    body.innerHTML = html;
    document.getElementById('lesson-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function setConvUiState(state) {
    const btn  = document.getElementById('conv-mic-btn');
    const icon = btn?.querySelector('.conv-mic-icon');
    const sts  = document.getElementById('conv-status');
    const autoSendEnabled = document.getElementById('conv-auto-send-toggle')?.checked || false;
    if (!btn) return;
    btn.classList.remove('recording', 'loading');
    if (state === 'recording') {
        btn.classList.add('recording');
        if (icon) icon.textContent = '⏹️';
        sts.textContent = autoSendEnabled
            ? 'Gravando… pausa de 5s envia automaticamente'
            : 'Gravando… clique para parar';
        sts.className = 'conv-status recording';
    } else if (state === 'loading') {
        btn.classList.add('loading');
        if (icon) icon.textContent = '⏳';
        sts.textContent = 'Processando…';
        sts.className = 'conv-status loading';
    } else {
        if (icon) icon.textContent = '🎙️';
        sts.textContent = 'Clique para falar';
        sts.className = 'conv-status';
    }
}

function setConvStatus(msg, cls) {
    const el = document.getElementById('conv-status');
    if (!el) return;
    el.textContent = msg;
    el.className = 'conv-status' + (cls ? ' ' + cls : '');
}

// Atalhos
document.addEventListener('keydown', e => {
    if (e.code === 'Space' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        const a = $('#main-audio');
        if (a?.src) a.paused ? a.play() : a.pause();
    }
    if (e.code === 'KeyR' && e.ctrlKey && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        state.isRecording ? stopRecording() : startRecording();
    }
    if (e.code === 'Escape') { hide('#video-player-modal'); $('#video-iframe').src = ''; }
});
