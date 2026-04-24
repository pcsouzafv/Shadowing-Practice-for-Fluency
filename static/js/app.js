/* ═══════════════════════════════════════════════════════════
   Shadowing Practice — Frontend (LMNT + Piper + Multi-IA fallback)
   ═══════════════════════════════════════════════════════════ */

const state = {
    uiLang: 'pt',
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
    karaokeTranslations: {
        cache: {},
        targetLang: '',
        source: '',
        warning: '',
        sentenceEls: [],
    },
    adaptiveFlashcards: {
        deck: [],
        allDeck: [],
        index: 0,
        flipped: false,
        submitting: false,
        lastData: null,
        langFilter: 'all',
        languages: [],
    },
    ttsCache: {},  // Cache TTS per sentence to avoid repeat API calls
    videoDiscovery: {
        query: '',
        source: '',
        warning: '',
        lang: '',
        queryUsed: '',
        videos: [],
    },
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
const UI_LANG_STORAGE = 'shadowingUiLang';
const UI_LANG_FALLBACK = 'pt';
const SUPPORTED_UI_LANGS = ['pt', 'en', 'es', 'fr', 'de', 'it'];
const UI_LANG_HTML = {
    pt: 'pt-BR',
    en: 'en',
    es: 'es',
    fr: 'fr',
    de: 'de',
    it: 'it',
};
const LANGUAGE_FLAGS = {
    en: '🇺🇸',
    pt: '🇧🇷',
    es: '🇪🇸',
    fr: '🇫🇷',
    de: '🇩🇪',
    it: '🇮🇹',
};
const UI_COPY = {
    pt: {
        document: {
            title: 'Shadowing Practice for Fluency',
        },
        lang: {
            native: {
                en: 'English',
                pt: 'Português',
                es: 'Español',
                fr: 'Français',
                de: 'Deutsch',
                it: 'Italiano',
            },
            display: {
                en: 'Inglês',
                pt: 'Português',
                es: 'Espanhol',
                fr: 'Francês',
                de: 'Alemão',
                it: 'Italiano',
            },
        },
        header: {
            uiLanguage: 'Interface',
            subtitle: 'Áudio guiado, voz neural, IA aplicada e exploração de vídeos reais para fluência oral consistente.',
        },
        tabs: {
            practice: 'Laboratório',
            aiTools: 'Ferramentas IA',
            conversation: 'Conversação',
            progress: 'Progresso',
        },
        hero: {
            eyebrowHtml: '<span>01</span> FLUÊNCIA ORAL TECH INTENSIVA',
            title: 'TREINE FLUÊNCIA COM SOM, TEXTO, REPETIÇÃO E VÍDEOS REAIS NO MESMO LOOP',
            text: 'Uma experiência de shadowing pensada para transformar repetição em progresso visível: áudio sincronizado, gravação, comparação, missão guiada e exploração de vídeos do YouTube por assunto.',
            voiceLabel: 'voz neural e fallback local',
            videoLabel: 'temas e vídeos reais para ampliar repertório',
            missionLabel: 'rotina guiada de prática',
            start: 'COMEÇAR SESSÃO',
            openVideos: 'ABRIR EXPLORADOR DE VÍDEOS',
            panelKicker: 'Pilha de Prática Profunda',
            panel1: 'Texto sincronizado em tempo real com o áudio principal',
            panel2: 'Fases de estudo guiadas do aquecimento até a gravação',
            panel3: 'Estudo frase por frase com tradução, pronúncia e vocabulário',
            panel4: 'Busca de vídeos por assunto para ampliar repertório com conteúdo real',
            panelFoot: 'Projetado para manter o backend intacto e elevar a experiência visual.',
        },
        composer: {
            kicker: 'Monte Sua Sessão',
            title: 'Insira o texto para shadowing',
            placeholder: 'Cole aqui o texto que deseja praticar...\n\nEx: The key to fluency is consistent daily practice. Even just two minutes a day over thirty days will show noticeable results.',
            language: 'Idioma:',
            voice: 'Voz:',
            engine: 'Engine:',
            loadVoicesTitle: 'Carregar todas as vozes LMNT',
            generate: '🚀 Gerar Sessão',
            analyze: '🤖 Analisar com IA',
            combo: '⚡ Gerar + Analisar',
            comboTitle: 'Gera áudio + análise IA em paralelo',
        },
        loading: {
            generic: 'Gerando áudio com voz natural...',
            analyzing: '🤖 Analisando com Inteligência Artificial...',
        },
        analysis: {
            title: '🤖 Análise Inteligente do Texto',
            level: 'Nível:',
            pronunciation: '🗣️ Dicas de Pronúncia',
            linking: '🔗 Linking Sounds',
            vocabulary: '📚 Vocabulário Chave',
            intonation: '🎵 Entonação e Ritmo',
            focus: '🎯 Foco desta Sessão',
            mistakes: '⚠️ Erros Comuns de Brasileiros',
        },
        audio: {
            title: '🔊 Áudio para Shadowing',
            speed: 'Velocidade:',
            loopOn: '🔁 Loop: ON',
            loopOff: '🔁 Loop: OFF',
            loopTitle: 'Repetir áudio automaticamente',
        },
        karaoke: {
            title: '📖 Texto Sincronizado',
            translateTitle: 'Idioma da tradução',
            hint: '▶ Dê play no áudio — o texto acompanha a fala em tempo real e a tradução segue a frase ativa.',
            hintWarning: '▶ Dê play no áudio — a tradução acompanha a frase ativa. Aviso: {warning}',
            original: 'Original',
            translation: 'Tradução Guiada',
            placeholderIdle: 'Selecione ou aguarde a tradução do texto desta sessão.',
            placeholderSelect: 'Selecione um idioma para carregar a tradução guiada.',
            placeholderLoading: 'Carregando tradução guiada...',
            unavailable: 'Tradução indisponível no momento.',
            error: 'Não foi possível carregar a tradução: {message}',
            options: {
                pt: 'Tradução em Português',
                en: 'Translation in English',
                es: 'Traducción en Español',
                fr: 'Traduction en Français',
                de: 'Übersetzung auf Deutsch',
                it: 'Traduzione in Italiano',
            },
            provider: {
                ai_backfill: 'IA',
                fallback_local: 'Fallback',
                same_language: 'Espelho',
                error: 'Erro',
                erro: 'Erro',
                empty: 'Vazio',
            },
        },
        record: {
            title: '🎙️ Grave e Compare',
            start: '<span class="rec-icon">⏺</span> Gravar',
            recording: '<span class="rec-icon">⏺</span> Gravando...',
            stop: '⏹ Parar',
            status: '🔴 Gravando...',
            micPermission: 'Permita o acesso ao microfone.',
        },
        videos: {
            title: '🎬 Explorador de Vídeos por Assunto',
            hint: 'Pesquise por tema e explore vídeos reais para praticar. Nesta área a aplicação só lista vídeos relacionados, sem tentar extrair transcrição automaticamente.',
            placeholder: 'Ex.: entrevistas curtas sobre tecnologia em inglês',
            search: '🔎 Buscar vídeos',
            defaultSummary: 'Gere uma sessão para receber sugestões automáticas ou pesquise um assunto diretamente.',
            retry: '🔄 Tentar nova busca',
            watchHere: '▶ Assistir aqui',
            openYoutube: '↗ Abrir no YouTube',
        },
        history: {
            title: '📂 Sessões Anteriores',
            hint: 'Clique para reaproveitar um texto já praticado',
        },
        mission: {
            title: '📋 Sessão',
            toggleTitle: 'Minimizar/Expandir',
            markComplete: 'Marcar como concluído',
            activatePhase: 'Ativar esta fase',
            pauseResume: 'Pausar/Continuar',
            reset: '🔄 Reiniciar',
            resetConfirm: 'Reiniciar todas as fases?',
            done: '✅ Feito',
            completed: '✅ Concluído!',
            phases: {
                1: { name: '🎧 Escuta Passiva', hint: 'Ouça sem repetir · 3 min' },
                2: { name: '📖 Leitura', hint: 'Leia e busque palavras · 3 min' },
                3: { name: '👁️ Escuta + Leitura', hint: 'Som ↔ texto juntos · 3 min' },
                4: { name: '🗣️ Shadow COM Texto', hint: 'Repita junto com áudio · 7 min' },
                5: { name: '⭐ Shadow SEM Texto', hint: 'Imite tudo sem olhar · 7 min' },
                6: { name: '🎙️ Grave e Compare', hint: 'Grave e ouça de volta · 3 min' },
            },
        },
        aiTools: {
            title: '🤖 Gerador de Texto',
            hint: 'A IA gera textos para shadowing com idioma, tamanho e tipo que você escolher',
            topic: 'Tema',
            language: 'Idioma do texto',
            level: 'Nível',
            length: 'Tamanho',
            type: 'Tipo',
            focus: 'Foco',
            generate: '⚡ Gerar Texto para Prática',
            loading: 'A IA está criando seu material...',
            useText: '🎧 Usar este texto para shadowing',
            voicesTitle: '🎙️ Vozes LMNT Disponíveis',
            voicesHint: 'Ouça previews e escolha a voz ideal para sua prática',
            refreshVoices: '🔄 Carregar vozes',
            generatedPractice: 'Prática gerada',
            vocabulary: '📚 Vocabulário',
            useVoice: 'Usar esta voz',
            noVoices: 'Nenhuma voz carregada. Clique em 🔄.',
        },
        conversation: {
            title: '💬 Prática de Conversação',
            hint: 'Converse por voz ou texto com um parceiro nativo por IA, usando cenário, objetivo e apoio guiado.',
            scenarioBadge: 'Cenário: {value}',
            goalBadge: 'Objetivo: {value}',
            noReplies: 'Sem respostas ainda',
            partnerLabel: 'Parceiro',
            partnerNote: 'Voz, engine e tradução ficam nas opções avançadas.',
            partnerStatus: '{lang} · {scenario} · {goal} · tradução para {translate}',
            studio: 'CONVERSATION STUDIO',
            heroTitle: 'Fale com contexto, acompanhe o ritmo da sessão e destrave quando faltar assunto.',
            heroText: 'Escolha um cenário, defina o objetivo e comece por voz ou texto. A colinha e os starters ajudam a manter a conversa viva sem quebrar o foco do idioma.',
            turns: 'Turnos',
            mode: 'Modo',
            language: 'Idioma',
            ready: 'Pronto',
            dialogueTitle: '🗨️ Fluxo da Conversa',
            dialogueHint: 'Use voz para ganhar ritmo e texto quando quiser mais precisão.',
            feedBadge: '{turns} turno(s)',
            compassTitle: '🧭 Bússola da Sessão',
            paceReady: 'Pronto',
            paceRecording: 'Ao vivo',
            paceLoading: 'Pensando',
            paceActive: 'Em fluxo',
            nextStepIdle: 'Escolha um starter ou toque no microfone para abrir a conversa com naturalidade.',
            nextStepRecording: 'Fale naturalmente. Quando terminar, pare a gravação ou espere o envio automático.',
            nextStepLoading: 'A IA está montando a próxima resposta. Prepare uma continuação curta.',
            nextStepActive: 'Reaja ao último ponto, peça um exemplo ou conte a sua experiência para manter a conversa viva.',
            goalMini: 'Objetivo',
            scenarioMini: 'Cenário',
            actionsTitle: '⚡ Próximos Movimentos',
            actionsBadge: 'Ações rápidas',
            actionsCount: '{count} prontas',
            actionsHint: 'Toque em uma opção para jogar uma resposta natural no composer.',
            actionsMeta: 'Resposta curta pronta para adaptar',
            moveOpen: 'Abrir com naturalidade',
            moveFollowUp: 'Pedir mais detalhes',
            movePersonal: 'Trazer para a sua realidade',
            moveGoal: 'Treinar o foco da sessão',
            moveExample: 'Pedir um exemplo',
            advancedTitle: '⚙️ Configuração Avançada',
            advancedHint: 'voz, tradução, envio automático e ferramentas',
            settingsLanguage: 'Idioma',
            settingsScenario: 'Cenário',
            settingsGoal: 'Objetivo',
            settingsVoice: 'Voz IA',
            settingsEngine: 'Engine de voz',
            settingsTranslate: 'Traduzir para',
            coachNotes: '💡 Colinha',
            autoSend: '⏱️ Envio automático (5s silêncio)',
            clear: '🗑️ Limpar',
            lesson: '🎯 Aula Inteligente + Correção',
            startersTitle: '⚡ Começos Rápidos',
            startersBadge: 'Starter prompts',
            startersHint: 'Use um starter para abrir a conversa mais rápido ou jogar uma nova direção no meio da sessão.',
            empty: 'Escolha um starter ou clique no microfone para começar a conversa.',
            notesHint: 'Sugestões do que falar',
            notesEmpty: 'As sugestões aparecerão aqui após a IA responder.',
            composeLabel: 'Mensagem de apoio',
            composePlaceholder: 'Digite em inglês, francês, espanhol... ou use um starter acima.',
            send: '📨 Enviar texto',
            sendHint: 'Pressione Enter para enviar. Use Shift+Enter para quebrar linha.',
            micTitle: 'Clique para falar',
            statusIdle: 'Clique para falar',
            statusRecording: 'Gravando… clique para parar',
            statusRecordingAuto: 'Gravando… pausa de 5s envia automaticamente',
            statusLoading: 'Processando…',
            typePrompt: 'Digite uma frase para enviar.',
            networkError: 'Erro de rede: {message}',
            micError: 'Erro ao acessar microfone: {message}',
            lessonNeedHistory: 'Converse primeiro antes de gerar a aula!',
            lessonLoading: '⏳ Aula inteligente: correções + pronúncia…',
            openScenario: 'Abrir conversa em {scenario}',
            user: 'Você',
            assistant: 'Alex',
            inputVoice: 'voz',
            inputText: 'texto',
            useReply: 'Usar resposta',
            reuseLine: 'Reaproveitar linha',
            error: 'Erro',
            warning: 'Aviso',
            summaryIdle: 'Sessão em {lang} no cenário de {scenario}, com foco em {goal}. Use um starter, fale pelo microfone ou mande uma primeira mensagem para abrir a conversa.',
            summaryActive: 'Sessão em {lang} no cenário de {scenario}, com foco em {goal}. Você já completou {turns} turno(s); continue por voz ou mande uma frase por texto para manter o ritmo.',
            lastResponse: 'Última resposta processada com {engine}.',
            scenarioLabels: {
                casual: 'Casual',
                travel: 'Viagem',
                work: 'Trabalho',
                interview: 'Entrevista',
                tech: 'Tecnologia',
                daily: 'Rotina',
            },
            goalLabels: {
                flow: 'Fluidez',
                confidence: 'Confiança',
                vocabulary: 'Vocabulário',
                opinions: 'Opiniões',
            },
        },
        lesson: {
            title: '🎓 Aula Gerada pela IA',
            close: 'Fechar',
            focusSmart: 'Foco: Inteligente',
            focusBalanced: 'Foco: Equilibrado',
            focusCorrections: 'Foco: Correções',
            focusVocabulary: 'Foco: Vocabulário',
            focusAuto: 'auto',
            aiLabel: 'IA',
            summary: '📝 Resumo da Conversa',
            transcript: '💬 Transcrição com Tradução',
            speaker: 'Falante',
            vocabulary: '📖 Vocabulário',
            grammar: '📐 Gramática',
            corrections: '✏️ Correções',
            tips: '💡 Dicas para Você',
            replySuggestions: '🗣️ Sugestões do que Responder',
            pronunciation: '🧠 Avaliação de Pronúncia',
            you: '👤 Você',
            ai: '🤖 Alex',
            estimatedScore: 'Score estimado: {score}/100',
        },
        progress: {
            log: '📊 Log de Progresso',
            date: 'Data',
            material: 'Material',
            duration: 'Duração (min)',
            repetitions: 'Repetições',
            difficulty: 'Dificuldade (1-5)',
            notes: 'Observações',
            save: '💾 Salvar',
            history: '📈 Histórico',
            none: 'Nenhuma sessão registrada ainda.',
            export: '📥 Exportar CSV',
            sessions: 'Sessões',
            minutes: 'Minutos',
            avgDifficulty: 'Dific. média',
            streak: 'Streak',
            coach: '🧠 Coach Adaptativo',
            adaptiveIdle: 'Sem atividade adaptativa ainda.',
            pronAvg: 'Pronúncia média',
            reviewDue: 'Revisões vencidas',
            trackedItems: 'Itens rastreados',
            activeDays: 'Dias ativos (7d)',
            flashcardsTitle: '🃏 Flashcards do Banco',
            flashcardsHint: 'As cartas agora separam os idiomas estudados e mostram mais contexto para cada item salvo no banco.',
            reviewToday: '🔁 Revisão de Hoje',
            nextActions: '🎯 Próximas Ações',
            weakPoints: '⚠️ Pontos Fracos',
            strengths: '✅ Pontos Fortes',
            all: 'Todos',
            flip: '🔄 Virar',
            again: '🔁 Errei',
            hard: '😐 Quase',
            good: '✅ Acertei',
            easy: '🚀 Fácil',
        },
        api: {
            title: '🧩 Status das APIs',
            badge: 'Diagnóstico',
            hint: 'Painel técnico no rodapé para consulta rápida das integrações ativas.',
            textAi: 'IA texto',
        },
        footer: {
            taglineHtml: '🎧 Shadowing Practice — LMNT + Piper + OpenRouter/Ollama IA — A chave é a <strong>consistência diária</strong>',
            cleanupTitle: 'Limpar áudios em cache',
            cleanupButton: '🗑️ Limpar cache',
        },
        misc: {
            searchIn: 'Buscar em {lang}',
            translateTo: 'Tradução em {lang}',
            uiOption: '{flag} {label}',
            words: '{words} palavras · {chars} caracteres · ~{minutes} min áudio',
            searchLoading: 'Buscando vídeos...',
            sessionInvalid: 'Resposta inválida ao gerar sessão.',
            analysisInvalid: 'Resposta inválida da análise.',
            practiceInvalid: 'Resposta inválida ao gerar prática.',
            pasteText: 'Cole um texto para praticar!',
            pasteTextFirst: 'Cole um texto primeiro!',
            enterTopic: 'Digite um assunto para buscar vídeos.',
            enterTopicOrSession: 'Digite um assunto ou gere uma sessão antes de buscar vídeos.',
            youtubeUnavailable: 'Ainda não foi possível carregar vídeos do YouTube.',
            loadingTranslation: 'Carregando tradução guiada...',
            deleteProgress: 'Excluir esta entrada?',
            cacheClean: '💾 Cache limpo',
            cacheFiles: '💾 {count} arquivos ({size} MB)',
            cleanupConfirm: 'Limpar todos os áudios em cache?',
            cleanupRemoved: '✅ {count} arquivo(s) removidos',
            cleanupError: 'Erro ao limpar cache',
        },
    },
    en: {
        document: {
            title: 'Shadowing Practice for Fluency',
        },
        lang: {
            native: {
                en: 'English',
                pt: 'Português',
                es: 'Español',
                fr: 'Français',
                de: 'Deutsch',
                it: 'Italiano',
            },
            display: {
                en: 'English',
                pt: 'Portuguese',
                es: 'Spanish',
                fr: 'French',
                de: 'German',
                it: 'Italian',
            },
        },
        header: {
            uiLanguage: 'Interface',
            subtitle: 'Guided audio, neural voice, applied AI, and real video discovery for consistent speaking fluency.',
        },
        tabs: {
            practice: 'Practice Lab',
            aiTools: 'AI Tools',
            conversation: 'Conversation',
            progress: 'Progress',
        },
        hero: {
            eyebrowHtml: '<span>01</span> TECH-INTENSIVE ORAL FLUENCY',
            title: 'TRAIN FLUENCY WITH AUDIO, TEXT, REPETITION, AND REAL VIDEOS IN THE SAME LOOP',
            text: 'A shadowing experience designed to turn repetition into visible progress: synced audio, recording, comparison, guided missions, and YouTube video discovery by topic.',
            voiceLabel: 'neural voice and local fallback',
            videoLabel: 'real topics and videos to expand your range',
            missionLabel: 'guided practice routine',
            start: 'START SESSION',
            openVideos: 'OPEN VIDEO EXPLORER',
            panelKicker: 'Deep Practice Stack',
            panel1: 'Real-time synced text alongside the main audio',
            panel2: 'Guided study phases from warm-up to recording',
            panel3: 'Sentence-by-sentence study with translation, pronunciation, and vocabulary',
            panel4: 'Topic-based video discovery to expand your repertoire with real content',
            panelFoot: 'Designed to keep the backend intact while raising the product experience.',
        },
        composer: {
            kicker: 'Build Your Session',
            title: 'Paste text for shadowing',
            placeholder: 'Paste the text you want to practice here...\n\nEx: The key to fluency is consistent daily practice. Even just two minutes a day over thirty days will show noticeable results.',
            language: 'Language:',
            voice: 'Voice:',
            engine: 'Engine:',
            loadVoicesTitle: 'Load all LMNT voices',
            generate: '🚀 Generate Session',
            analyze: '🤖 Analyze with AI',
            combo: '⚡ Generate + Analyze',
            comboTitle: 'Generate audio and AI analysis in parallel',
        },
        loading: {
            generic: 'Generating natural voice audio...',
            analyzing: '🤖 Analyzing with Artificial Intelligence...',
        },
        analysis: {
            title: '🤖 Smart Text Analysis',
            level: 'Level:',
            pronunciation: '🗣️ Pronunciation Tips',
            linking: '🔗 Linking Sounds',
            vocabulary: '📚 Key Vocabulary',
            intonation: '🎵 Intonation and Rhythm',
            focus: '🎯 Session Focus',
            mistakes: '⚠️ Common Mistakes for Brazilian Learners',
        },
        audio: {
            title: '🔊 Shadowing Audio',
            speed: 'Speed:',
            loopOn: '🔁 Loop: ON',
            loopOff: '🔁 Loop: OFF',
            loopTitle: 'Repeat audio automatically',
        },
        karaoke: {
            title: '📖 Synced Text',
            translateTitle: 'Translation language',
            hint: '▶ Press play on the audio — the text follows in real time and the translation tracks the active sentence.',
            hintWarning: '▶ Press play on the audio — the translation tracks the active sentence. Warning: {warning}',
            original: 'Original',
            translation: 'Guided Translation',
            placeholderIdle: 'Select or wait for the translation of this session text.',
            placeholderSelect: 'Select a language to load the guided translation.',
            placeholderLoading: 'Loading guided translation...',
            unavailable: 'Translation is currently unavailable.',
            error: 'Could not load the translation: {message}',
            options: {
                pt: 'Translate to Portuguese',
                en: 'Translation in English',
                es: 'Translate to Spanish',
                fr: 'Translate to French',
                de: 'Translate to German',
                it: 'Translate to Italian',
            },
            provider: {
                ai_backfill: 'AI',
                fallback_local: 'Fallback',
                same_language: 'Mirror',
                error: 'Error',
                erro: 'Error',
                empty: 'Empty',
            },
        },
        record: {
            title: '🎙️ Record and Compare',
            start: '<span class="rec-icon">⏺</span> Record',
            recording: '<span class="rec-icon">⏺</span> Recording...',
            stop: '⏹ Stop',
            status: '🔴 Recording...',
            micPermission: 'Please allow microphone access.',
        },
        videos: {
            title: '🎬 Video Explorer by Topic',
            hint: 'Search by topic and explore real videos for practice. In this area the app only lists related videos, without trying to extract transcripts automatically.',
            placeholder: 'Ex: short interviews about technology in English',
            search: '🔎 Search videos',
            defaultSummary: 'Generate a session to receive automatic suggestions or search for a topic directly.',
            retry: '🔄 Try another search',
            watchHere: '▶ Watch here',
            openYoutube: '↗ Open on YouTube',
        },
        history: {
            title: '📂 Previous Sessions',
            hint: 'Click to reuse a text you have already practiced',
        },
        mission: {
            title: '📋 Session',
            toggleTitle: 'Collapse/Expand',
            markComplete: 'Mark as complete',
            activatePhase: 'Activate this phase',
            pauseResume: 'Pause/Resume',
            reset: '🔄 Reset',
            resetConfirm: 'Reset all phases?',
            done: '✅ Done',
            completed: '✅ Complete!',
            phases: {
                1: { name: '🎧 Passive Listening', hint: 'Listen without repeating · 3 min' },
                2: { name: '📖 Reading', hint: 'Read and look up words · 3 min' },
                3: { name: '👁️ Listening + Reading', hint: 'Audio ↔ text together · 3 min' },
                4: { name: '🗣️ Shadow WITH Text', hint: 'Repeat along with the audio · 7 min' },
                5: { name: '⭐ Shadow WITHOUT Text', hint: 'Imitate everything without looking · 7 min' },
                6: { name: '🎙️ Record and Compare', hint: 'Record and listen back · 3 min' },
            },
        },
        aiTools: {
            title: '🤖 Text Generator',
            hint: 'AI creates shadowing texts with the language, length, and type you choose',
            topic: 'Topic',
            language: 'Text language',
            level: 'Level',
            length: 'Length',
            type: 'Type',
            focus: 'Focus',
            generate: '⚡ Generate Practice Text',
            loading: 'AI is creating your material...',
            useText: '🎧 Use this text for shadowing',
            voicesTitle: '🎙️ Available LMNT Voices',
            voicesHint: 'Listen to previews and choose the ideal voice for your practice',
            refreshVoices: '🔄 Load voices',
            generatedPractice: 'Generated practice',
            vocabulary: '📚 Vocabulary',
            useVoice: 'Use this voice',
            noVoices: 'No voices loaded yet. Click 🔄.',
        },
        conversation: {
            title: '💬 Conversation Practice',
            hint: 'Talk by voice or text with an AI native-style partner, using scenario, goal, and guided support.',
            scenarioBadge: 'Scenario: {value}',
            goalBadge: 'Goal: {value}',
            noReplies: 'No replies yet',
            partnerLabel: 'Partner',
            partnerNote: 'Voice, engine, and translation live in the advanced setup.',
            partnerStatus: '{lang} · {scenario} · {goal} · translate into {translate}',
            studio: 'CONVERSATION STUDIO',
            heroTitle: 'Speak with context, keep the session rhythm, and unblock yourself when ideas run short.',
            heroText: 'Choose a scenario, set the goal, and start by voice or text. The notes and starters help keep the conversation alive without breaking the target-language focus.',
            turns: 'Turns',
            mode: 'Mode',
            language: 'Language',
            ready: 'Ready',
            dialogueTitle: '🗨️ Dialogue Flow',
            dialogueHint: 'Use voice for momentum and text when you want extra precision.',
            feedBadge: '{turns} turn(s)',
            compassTitle: '🧭 Session Compass',
            paceReady: 'Ready',
            paceRecording: 'Live',
            paceLoading: 'Thinking',
            paceActive: 'In flow',
            nextStepIdle: 'Pick a starter or tap the mic to open the conversation naturally.',
            nextStepRecording: 'Speak naturally. When you finish, stop recording or wait for auto-send.',
            nextStepLoading: 'The AI is shaping the next reply. Prepare a short follow-up.',
            nextStepActive: 'React to the last point, ask for an example, or share your own experience to keep momentum.',
            goalMini: 'Goal',
            scenarioMini: 'Scenario',
            actionsTitle: '⚡ Next Moves',
            actionsBadge: 'Quick moves',
            actionsCount: '{count} ready',
            actionsHint: 'Tap an option to drop a natural follow-up into the composer.',
            actionsMeta: 'Short follow-up ready to adapt',
            moveOpen: 'Open naturally',
            moveFollowUp: 'Ask for more detail',
            movePersonal: 'Bring it to your reality',
            moveGoal: 'Train the session focus',
            moveExample: 'Ask for an example',
            advancedTitle: '⚙️ Advanced Setup',
            advancedHint: 'voice, translation, auto-send, and tools',
            settingsLanguage: 'Language',
            settingsScenario: 'Scenario',
            settingsGoal: 'Goal',
            settingsVoice: 'AI voice',
            settingsEngine: 'Voice engine',
            settingsTranslate: 'Translate to',
            coachNotes: '💡 Coach Notes',
            autoSend: '⏱️ Auto-send (5s silence)',
            clear: '🗑️ Clear',
            lesson: '🎯 Smart Lesson + Feedback',
            startersTitle: '⚡ Quick Starters',
            startersBadge: 'Starter prompts',
            startersHint: 'Use a starter to open the conversation faster or shift the direction in the middle of the session.',
            empty: 'Pick a starter or tap the microphone to begin the conversation.',
            notesHint: 'Ideas for what to say',
            notesEmpty: 'Suggestions will appear here after the AI replies.',
            composeLabel: 'Support message',
            composePlaceholder: 'Type in English, French, Spanish... or use a starter above.',
            send: '📨 Send text',
            sendHint: 'Press Enter to send. Use Shift+Enter for a new line.',
            micTitle: 'Tap to speak',
            statusIdle: 'Tap to speak',
            statusRecording: 'Recording... tap to stop',
            statusRecordingAuto: 'Recording... a 5s pause sends it automatically',
            statusLoading: 'Processing...',
            typePrompt: 'Type a sentence to send.',
            networkError: 'Network error: {message}',
            micError: 'Microphone access error: {message}',
            lessonNeedHistory: 'Have a conversation first before generating a lesson!',
            lessonLoading: '⏳ Smart lesson: feedback + pronunciation...',
            openScenario: 'Open a conversation in {scenario}',
            user: 'You',
            assistant: 'Alex',
            inputVoice: 'voice',
            inputText: 'text',
            useReply: 'Use reply',
            reuseLine: 'Reuse line',
            error: 'Error',
            warning: 'Warning',
            summaryIdle: 'Session in {lang}, in the {scenario} scenario, focused on {goal}. Use a starter, speak through the mic, or send a first message to open the conversation.',
            summaryActive: 'Session in {lang}, in the {scenario} scenario, focused on {goal}. You have already completed {turns} turn(s); continue by voice or send a new text line to keep the momentum.',
            lastResponse: 'Last response processed with {engine}.',
            scenarioLabels: {
                casual: 'Casual',
                travel: 'Travel',
                work: 'Work',
                interview: 'Interview',
                tech: 'Tech',
                daily: 'Daily routine',
            },
            goalLabels: {
                flow: 'Flow',
                confidence: 'Confidence',
                vocabulary: 'Vocabulary',
                opinions: 'Opinions',
            },
        },
        lesson: {
            title: '🎓 AI-Generated Lesson',
            close: 'Close',
            focusSmart: 'Focus: Smart',
            focusBalanced: 'Focus: Balanced',
            focusCorrections: 'Focus: Corrections',
            focusVocabulary: 'Focus: Vocabulary',
            focusAuto: 'auto',
            aiLabel: 'AI',
            summary: '📝 Conversation Summary',
            transcript: '💬 Transcript with Translation',
            speaker: 'Speaker',
            vocabulary: '📖 Vocabulary',
            grammar: '📐 Grammar',
            corrections: '✏️ Corrections',
            tips: '💡 Tips for You',
            replySuggestions: '🗣️ Suggested Replies',
            pronunciation: '🧠 Pronunciation Review',
            you: '👤 You',
            ai: '🤖 Alex',
            estimatedScore: 'Estimated score: {score}/100',
        },
        progress: {
            log: '📊 Progress Log',
            date: 'Date',
            material: 'Material',
            duration: 'Duration (min)',
            repetitions: 'Repetitions',
            difficulty: 'Difficulty (1-5)',
            notes: 'Notes',
            save: '💾 Save',
            history: '📈 History',
            none: 'No sessions recorded yet.',
            export: '📥 Export CSV',
            sessions: 'Sessions',
            minutes: 'Minutes',
            avgDifficulty: 'Avg. difficulty',
            streak: 'Streak',
            coach: '🧠 Adaptive Coach',
            adaptiveIdle: 'No adaptive activity yet.',
            pronAvg: 'Average pronunciation',
            reviewDue: 'Reviews due',
            trackedItems: 'Tracked items',
            activeDays: 'Active days (7d)',
            flashcardsTitle: '🃏 Database Flashcards',
            flashcardsHint: 'Cards now separate the studied languages and show more context for each saved item.',
            reviewToday: '🔁 Today\'s Review',
            nextActions: '🎯 Next Actions',
            weakPoints: '⚠️ Weak Points',
            strengths: '✅ Strengths',
            all: 'All',
            flip: '🔄 Flip',
            again: '🔁 Again',
            hard: '😐 Hard',
            good: '✅ Good',
            easy: '🚀 Easy',
        },
        api: {
            title: '🧩 API Status',
            badge: 'Diagnostics',
            hint: 'Technical footer panel for a quick view of active integrations.',
            textAi: 'Text AI',
        },
        footer: {
            taglineHtml: '🎧 Shadowing Practice — LMNT + Piper + OpenRouter/Ollama AI — The key is <strong>daily consistency</strong>',
            cleanupTitle: 'Clear cached audio files',
            cleanupButton: '🗑️ Clear cache',
        },
        misc: {
            searchIn: 'Search in {lang}',
            translateTo: 'Translate to {lang}',
            uiOption: '{flag} {label}',
            words: '{words} words · {chars} characters · ~{minutes} min audio',
            searchLoading: 'Searching videos...',
            sessionInvalid: 'Invalid response while generating the session.',
            analysisInvalid: 'Invalid response from the analysis.',
            practiceInvalid: 'Invalid response while generating practice.',
            pasteText: 'Paste some text to practice!',
            pasteTextFirst: 'Paste some text first!',
            enterTopic: 'Type a topic to search for videos.',
            enterTopicOrSession: 'Type a topic or generate a session before searching for videos.',
            youtubeUnavailable: 'YouTube videos could not be loaded yet.',
            loadingTranslation: 'Loading guided translation...',
            deleteProgress: 'Delete this entry?',
            cacheClean: '💾 Cache cleared',
            cacheFiles: '💾 {count} files ({size} MB)',
            cleanupConfirm: 'Clear all cached audio files?',
            cleanupRemoved: '✅ {count} file(s) removed',
            cleanupError: 'Error clearing cache',
        },
    },
};

function mergeUiCopy(base, overlay) {
    const merged = Array.isArray(base) ? [...base] : { ...(base || {}) };
    Object.entries(overlay || {}).forEach(([key, value]) => {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            merged[key] = mergeUiCopy(merged[key] || {}, value);
        } else {
            merged[key] = value;
        }
    });
    return merged;
}

Object.assign(UI_COPY, {
    es: mergeUiCopy(UI_COPY.en, {
        lang: {
            display: { en: 'inglés', pt: 'portugués', es: 'español', fr: 'francés', de: 'alemán', it: 'italiano' },
        },
        header: {
            uiLanguage: 'Interfaz',
            subtitle: 'Audio guiado, voz neuronal, IA aplicada y descubrimiento de videos reales para una fluidez oral constante.',
        },
        tabs: { practice: 'Práctica', aiTools: 'Herramientas IA', conversation: 'Conversación', progress: 'Progreso' },
        hero: {
            eyebrowHtml: '<span>01</span> FLUIDEZ ORAL TECH INTENSIVA',
            title: 'ENTRENA LA FLUIDEZ CON AUDIO, TEXTO, REPETICIÓN Y VIDEOS REALES EN EL MISMO CICLO',
            text: 'Una experiencia de shadowing diseñada para convertir la repetición en progreso visible: audio sincronizado, grabación, comparación, misiones guiadas y descubrimiento de videos de YouTube por tema.',
            voiceLabel: 'voz neuronal y respaldo local',
            videoLabel: 'temas y videos reales para ampliar tu repertorio',
            missionLabel: 'rutina de práctica guiada',
            start: 'INICIAR SESIÓN',
            openVideos: 'ABRIR EXPLORADOR DE VIDEOS',
            panelKicker: 'Sistema de Práctica Profunda',
            panel1: 'Texto sincronizado en tiempo real junto al audio principal',
            panel2: 'Fases de estudio guiadas desde el calentamiento hasta la grabación',
            panel3: 'Estudio frase por frase con traducción, pronunciación y vocabulario',
            panel4: 'Descubrimiento de videos por tema para ampliar tu repertorio con contenido real',
            panelFoot: 'Diseñado para mantener intacto el backend y elevar la experiencia del producto.',
        },
        composer: {
            kicker: 'Crea Tu Sesión',
            title: 'Pega texto para shadowing',
            language: 'Idioma:',
            voice: 'Voz:',
            generate: '🚀 Generar sesión',
            analyze: '🤖 Analizar con IA',
            combo: '⚡ Generar + analizar',
        },
        aiTools: {
            title: '🤖 Generador de texto',
            hint: 'La IA crea textos para shadowing con el idioma, tamaño y tipo que elijas',
            topic: 'Tema',
            language: 'Idioma del texto',
            level: 'Nivel',
            length: 'Tamaño',
            type: 'Tipo',
            focus: 'Foco',
            generate: '⚡ Generar texto de práctica',
        },
        conversation: {
            title: '💬 Práctica de conversación',
            language: 'Idioma',
            settingsLanguage: 'Idioma',
            settingsScenario: 'Escenario',
            settingsGoal: 'Objetivo',
            settingsVoice: 'Voz de IA',
            settingsEngine: 'Motor de voz',
            settingsTranslate: 'Traducir a',
            send: '📨 Enviar texto',
            statusIdle: 'Toca para hablar',
            scenarioLabels: { casual: 'Casual', travel: 'Viaje', work: 'Trabajo', interview: 'Entrevista', tech: 'Tecnología', daily: 'Rutina diaria' },
            goalLabels: { flow: 'Fluidez', confidence: 'Confianza', vocabulary: 'Vocabulario', opinions: 'Opiniones' },
        },
        progress: {
            log: '📊 Registro de progreso',
            date: 'Fecha',
            material: 'Material',
            duration: 'Duración (min)',
            repetitions: 'Repeticiones',
            difficulty: 'Dificultad (1-5)',
            notes: 'Notas',
            save: '💾 Guardar',
            history: '📈 Historial',
            export: '📥 Exportar CSV',
        },
        misc: {
            searchIn: 'Buscar en {lang}',
            translateTo: 'Traducir a {lang}',
            pasteText: 'Pega un texto para practicar.',
            pasteTextFirst: 'Primero pega un texto.',
        },
    }),
    fr: mergeUiCopy(UI_COPY.en, {
        lang: {
            display: { en: 'anglais', pt: 'portugais', es: 'espagnol', fr: 'français', de: 'allemand', it: 'italien' },
        },
        header: {
            uiLanguage: 'Interface',
            subtitle: 'Audio guidé, voix neuronale, IA appliquée et découverte de vraies vidéos pour une aisance orale régulière.',
        },
        tabs: { practice: 'Pratique', aiTools: 'Outils IA', conversation: 'Conversation', progress: 'Progrès' },
        hero: {
            eyebrowHtml: '<span>01</span> AISANCE ORALE TECH INTENSIVE',
            title: 'ENTRAÎNEZ VOTRE AISANCE AVEC AUDIO, TEXTE, RÉPÉTITION ET VRAIES VIDÉOS DANS LA MÊME BOUCLE',
            text: 'Une expérience de shadowing conçue pour transformer la répétition en progrès visible : audio synchronisé, enregistrement, comparaison, missions guidées et découverte de vidéos YouTube par sujet.',
            voiceLabel: 'voix neuronale et secours local',
            videoLabel: 'sujets et vraies vidéos pour enrichir votre répertoire',
            missionLabel: 'routine de pratique guidée',
            start: 'DÉMARRER LA SESSION',
            openVideos: 'OUVRIR L’EXPLORATEUR VIDÉO',
            panelKicker: 'Pile de Pratique Approfondie',
            panel1: 'Texte synchronisé en temps réel avec l’audio principal',
            panel2: 'Phases d’étude guidées de l’échauffement à l’enregistrement',
            panel3: 'Étude phrase par phrase avec traduction, prononciation et vocabulaire',
            panel4: 'Découverte de vidéos par sujet pour progresser avec du contenu réel',
        },
        composer: { kicker: 'Créer Votre Session', title: 'Collez le texte pour le shadowing', language: 'Langue:', voice: 'Voix:', generate: '🚀 Générer la session', analyze: '🤖 Analyser avec l’IA', combo: '⚡ Générer + analyser' },
        aiTools: { title: '🤖 Générateur de texte', hint: 'L’IA crée des textes de shadowing avec la langue, la longueur et le type choisis', topic: 'Sujet', language: 'Langue du texte', level: 'Niveau', length: 'Longueur', type: 'Type', focus: 'Objectif', generate: '⚡ Générer un texte de pratique' },
        conversation: { title: '💬 Pratique de conversation', language: 'Langue', settingsLanguage: 'Langue', settingsScenario: 'Scénario', settingsGoal: 'Objectif', settingsVoice: 'Voix IA', settingsEngine: 'Moteur vocal', settingsTranslate: 'Traduire en', send: '📨 Envoyer le texte', statusIdle: 'Touchez pour parler', scenarioLabels: { casual: 'Informel', travel: 'Voyage', work: 'Travail', interview: 'Entretien', tech: 'Technologie', daily: 'Routine quotidienne' }, goalLabels: { flow: 'Fluidité', confidence: 'Confiance', vocabulary: 'Vocabulaire', opinions: 'Opinions' } },
        progress: { log: '📊 Journal de progrès', date: 'Date', material: 'Support', duration: 'Durée (min)', repetitions: 'Répétitions', difficulty: 'Difficulté (1-5)', notes: 'Notes', save: '💾 Enregistrer', history: '📈 Historique', export: '📥 Exporter CSV' },
        misc: { searchIn: 'Rechercher en {lang}', translateTo: 'Traduire en {lang}', pasteText: 'Collez un texte à pratiquer.', pasteTextFirst: 'Collez d’abord un texte.' },
    }),
    de: mergeUiCopy(UI_COPY.en, {
        lang: {
            display: { en: 'Englisch', pt: 'Portugiesisch', es: 'Spanisch', fr: 'Französisch', de: 'Deutsch', it: 'Italienisch' },
        },
        header: {
            uiLanguage: 'Oberfläche',
            subtitle: 'Geführtes Audio, neuronale Stimme, angewandte KI und echte Videos für stetige Sprechflüssigkeit.',
        },
        tabs: { practice: 'Übung', aiTools: 'KI-Tools', conversation: 'Konversation', progress: 'Fortschritt' },
        hero: {
            eyebrowHtml: '<span>01</span> TECH-INTENSIVE SPRECHFLÜSSIGKEIT',
            title: 'TRAINIERE FLÜSSIGKEIT MIT AUDIO, TEXT, WIEDERHOLUNG UND ECHTEN VIDEOS IM SELBEN LOOP',
            text: 'Eine Shadowing-Erfahrung, die Wiederholung in sichtbaren Fortschritt verwandelt: synchronisiertes Audio, Aufnahme, Vergleich, geführte Missionen und YouTube-Videos nach Thema.',
            voiceLabel: 'neuronale Stimme und lokaler Fallback',
            videoLabel: 'echte Themen und Videos zur Erweiterung deines Repertoires',
            missionLabel: 'geführte Übungsroutine',
            start: 'SESSION STARTEN',
            openVideos: 'VIDEO-EXPLORER ÖFFNEN',
            panelKicker: 'Deep Practice Stack',
            panel1: 'Echtzeit-synchronisierter Text neben dem Hauptaudio',
            panel2: 'Geführte Lernphasen vom Warm-up bis zur Aufnahme',
            panel3: 'Satz-für-Satz-Studium mit Übersetzung, Aussprache und Wortschatz',
            panel4: 'Themenbasierte Videosuche zum Üben mit echtem Inhalt',
        },
        composer: { kicker: 'Session Erstellen', title: 'Text für Shadowing einfügen', language: 'Sprache:', voice: 'Stimme:', generate: '🚀 Session generieren', analyze: '🤖 Mit KI analysieren', combo: '⚡ Generieren + analysieren' },
        aiTools: { title: '🤖 Textgenerator', hint: 'Die KI erstellt Shadowing-Texte mit der gewählten Sprache, Länge und Art', topic: 'Thema', language: 'Textsprache', level: 'Niveau', length: 'Länge', type: 'Typ', focus: 'Fokus', generate: '⚡ Übungstext generieren' },
        conversation: { title: '💬 Konversationsübung', language: 'Sprache', settingsLanguage: 'Sprache', settingsScenario: 'Szenario', settingsGoal: 'Ziel', settingsVoice: 'KI-Stimme', settingsEngine: 'Sprach-Engine', settingsTranslate: 'Übersetzen in', send: '📨 Text senden', statusIdle: 'Tippen zum Sprechen', scenarioLabels: { casual: 'Locker', travel: 'Reise', work: 'Arbeit', interview: 'Interview', tech: 'Technologie', daily: 'Alltag' }, goalLabels: { flow: 'Fluss', confidence: 'Selbstvertrauen', vocabulary: 'Wortschatz', opinions: 'Meinungen' } },
        progress: { log: '📊 Fortschrittsprotokoll', date: 'Datum', material: 'Material', duration: 'Dauer (Min.)', repetitions: 'Wiederholungen', difficulty: 'Schwierigkeit (1-5)', notes: 'Notizen', save: '💾 Speichern', history: '📈 Verlauf', export: '📥 CSV exportieren' },
        misc: { searchIn: 'Suchen auf {lang}', translateTo: 'Übersetzen in {lang}', pasteText: 'Füge einen Text zum Üben ein.', pasteTextFirst: 'Füge zuerst einen Text ein.' },
    }),
    it: mergeUiCopy(UI_COPY.en, {
        lang: {
            display: { en: 'inglese', pt: 'portoghese', es: 'spagnolo', fr: 'francese', de: 'tedesco', it: 'italiano' },
        },
        header: {
            uiLanguage: 'Interfaccia',
            subtitle: 'Audio guidato, voce neurale, IA applicata e scoperta di video reali per una fluidità orale costante.',
        },
        tabs: { practice: 'Pratica', aiTools: 'Strumenti IA', conversation: 'Conversazione', progress: 'Progressi' },
        hero: {
            eyebrowHtml: '<span>01</span> FLUIDITÀ ORALE TECH INTENSIVA',
            title: 'ALLENA LA FLUIDITÀ CON AUDIO, TESTO, RIPETIZIONE E VIDEO REALI NELLO STESSO CICLO',
            text: 'Un’esperienza di shadowing pensata per trasformare la ripetizione in progresso visibile: audio sincronizzato, registrazione, confronto, missioni guidate e scoperta di video YouTube per argomento.',
            voiceLabel: 'voce neurale e fallback locale',
            videoLabel: 'temi e video reali per ampliare il repertorio',
            missionLabel: 'routine di pratica guidata',
            start: 'AVVIA SESSIONE',
            openVideos: 'APRI ESPLORATORE VIDEO',
            panelKicker: 'Sistema di Pratica Profonda',
            panel1: 'Testo sincronizzato in tempo reale con l’audio principale',
            panel2: 'Fasi di studio guidate dal riscaldamento alla registrazione',
            panel3: 'Studio frase per frase con traduzione, pronuncia e vocabolario',
            panel4: 'Scoperta di video per argomento per allenarsi con contenuti reali',
        },
        composer: { kicker: 'Crea La Tua Sessione', title: 'Incolla il testo per lo shadowing', language: 'Lingua:', voice: 'Voce:', generate: '🚀 Genera sessione', analyze: '🤖 Analizza con IA', combo: '⚡ Genera + analizza' },
        aiTools: { title: '🤖 Generatore di testo', hint: 'L’IA crea testi per shadowing con lingua, lunghezza e tipo scelti', topic: 'Argomento', language: 'Lingua del testo', level: 'Livello', length: 'Lunghezza', type: 'Tipo', focus: 'Focus', generate: '⚡ Genera testo di pratica' },
        conversation: { title: '💬 Pratica di conversazione', language: 'Lingua', settingsLanguage: 'Lingua', settingsScenario: 'Scenario', settingsGoal: 'Obiettivo', settingsVoice: 'Voce IA', settingsEngine: 'Motore vocale', settingsTranslate: 'Traduci in', send: '📨 Invia testo', statusIdle: 'Tocca per parlare', scenarioLabels: { casual: 'Informale', travel: 'Viaggio', work: 'Lavoro', interview: 'Colloquio', tech: 'Tecnologia', daily: 'Routine quotidiana' }, goalLabels: { flow: 'Fluidità', confidence: 'Fiducia', vocabulary: 'Vocabolario', opinions: 'Opinioni' } },
        progress: { log: '📊 Registro progressi', date: 'Data', material: 'Materiale', duration: 'Durata (min)', repetitions: 'Ripetizioni', difficulty: 'Difficoltà (1-5)', notes: 'Note', save: '💾 Salva', history: '📈 Cronologia', export: '📥 Esporta CSV' },
        misc: { searchIn: 'Cerca in {lang}', translateTo: 'Traduci in {lang}', pasteText: 'Incolla un testo da praticare.', pasteTextFirst: 'Incolla prima un testo.' },
    }),
});

const STATIC_TEXT_BINDINGS = [
    ['#ui-lang-label', 'header.uiLanguage'],
    ['.subtitle', 'header.subtitle'],
    ['.tabs [data-tab="practice"]', 'tabs.practice'],
    ['.tabs [data-tab="ai-tools"]', 'tabs.aiTools'],
    ['.tabs [data-tab="conversation"]', 'tabs.conversation'],
    ['.tabs [data-tab="progress"]', 'tabs.progress'],
    ['.section-heading .section-kicker', 'composer.kicker'],
    ['.section-heading h2', 'composer.title'],
    ['#practice-composer .control-group:nth-child(1) label', 'composer.language'],
    ['#practice-composer .control-group:nth-child(2) label', 'composer.voice'],
    ['#practice-composer .control-group:nth-child(3) label', 'composer.engine'],
    ['#btn-generate', 'composer.generate'],
    ['#btn-analyze', 'composer.analyze'],
    ['#btn-combo', 'composer.combo'],
    ['#loading-text', 'loading.generic'],
    ['#analysis-section h2', 'analysis.title'],
    ['#result-section > .card:first-child h2', 'audio.title'],
    ['.speed-controls > span', 'audio.speed'],
    ['.karaoke-card .card-header-row h2', 'karaoke.title'],
    ['#karaoke-translation-hint', 'karaoke.hint'],
    ['.karaoke-pane:first-child .karaoke-pane-header span:first-child', 'karaoke.original'],
    ['.karaoke-translation-pane .karaoke-pane-header span:first-child', 'karaoke.translation'],
    ['#result-section > .card:last-child h2', 'record.title'],
    ['#yt-lab-anchor .card-header-row h2', 'videos.title'],
    ['#yt-lab-anchor > .hint', 'videos.hint'],
    ['#btn-video-topic-search', 'videos.search'],
    ['#videos-summary', 'videos.defaultSummary'],
    ['#history-accordion-btn .history-accordion-title', 'history.title'],
    ['#history-content .history-hint', 'history.hint'],
    ['#mission-control .mc-header h3', 'mission.title'],
    ['#mc-reset-btn', 'mission.reset'],
    ['#tab-ai-tools .card:first-child h2', 'aiTools.title'],
    ['#tab-ai-tools .card:first-child > .hint', 'aiTools.hint'],
    ['label[for="ai-topic"]', 'aiTools.topic'],
    ['label[for="ai-lang"]', 'aiTools.language'],
    ['label[for="ai-level"]', 'aiTools.level'],
    ['label[for="ai-length"]', 'aiTools.length'],
    ['label[for="ai-type"]', 'aiTools.type'],
    ['label[for="ai-focus"]', 'aiTools.focus'],
    ['#btn-ai-generate', 'aiTools.generate'],
    ['#ai-practice-loading p', 'aiTools.loading'],
    ['#btn-use-ai-text', 'aiTools.useText'],
    ['#tab-ai-tools .card:last-child h2', 'aiTools.voicesTitle'],
    ['#tab-ai-tools .card:last-child .hint', 'aiTools.voicesHint'],
    ['#btn-refresh-voices', 'aiTools.refreshVoices'],
    ['#tab-conversation .conv-header h2', 'conversation.title'],
    ['#tab-conversation .conv-header .hint', 'conversation.hint'],
    ['#tab-conversation .conv-kicker', 'conversation.studio'],
    ['#tab-conversation .conv-hero-copy h3', 'conversation.heroTitle'],
    ['#conv-summary-text', 'conversation.heroText'],
    ['#tab-conversation .conv-mini-stat:nth-child(1) .conv-mini-label', 'conversation.turns'],
    ['#tab-conversation .conv-mini-stat:nth-child(2) .conv-mini-label', 'conversation.mode'],
    ['#tab-conversation .conv-mini-stat:nth-child(3) .conv-mini-label', 'conversation.language'],
    ['#tab-conversation .conv-starters-card h3', 'conversation.startersTitle'],
    ['#tab-conversation .conv-starters-card .badge', 'conversation.startersBadge'],
    ['#tab-conversation .conv-starters-card .hint', 'conversation.startersHint'],
    ['#conv-primary-status-label', 'conversation.partnerLabel'],
    ['#conv-dialogue-title', 'conversation.dialogueTitle'],
    ['#conv-dialogue-hint', 'conversation.dialogueHint'],
    ['#conv-compass-title', 'conversation.compassTitle'],
    ['#conv-guide-goal-label', 'conversation.goalMini'],
    ['#conv-guide-scene-label', 'conversation.scenarioMini'],
    ['#conv-actions-title', 'conversation.actionsTitle'],
    ['#conv-actions-hint', 'conversation.actionsHint'],
    ['#conv-advanced-title', 'conversation.advancedTitle'],
    ['#conv-advanced-hint', 'conversation.advancedHint'],
    ['#conv-empty p', 'conversation.empty'],
    ['#conv-colinha-card .conv-colinha-header span:first-child', 'conversation.coachNotes'],
    ['#conv-colinha-card .conv-colinha-hint', 'conversation.notesHint'],
    ['#conv-colinha-empty p', 'conversation.notesEmpty'],
    ['.conv-compose-main label', 'conversation.composeLabel'],
    ['#conv-clear-btn', 'conversation.clear'],
    ['#conv-lesson-btn', 'conversation.lesson'],
    ['#conv-send-btn', 'conversation.send'],
    ['.conv-compose-actions .hint', 'conversation.sendHint'],
    ['#conv-status', 'conversation.statusIdle'],
    ['#conv-engine-status', 'conversation.noReplies'],
    ['#tab-progress .card:nth-child(1) h2', 'progress.log'],
    ['label[for="prog-date"]', 'progress.date'],
    ['label[for="prog-material"]', 'progress.material'],
    ['label[for="prog-duration"]', 'progress.duration'],
    ['label[for="prog-reps"]', 'progress.repetitions'],
    ['label[for="prog-diff"]', 'progress.difficulty'],
    ['label[for="prog-notes"]', 'progress.notes'],
    ['#progress-form button[type="submit"]', 'progress.save'],
    ['#tab-progress .card:nth-child(2) h2', 'progress.history'],
    ['#tab-progress .progress-table thead th:nth-child(1)', 'progress.date'],
    ['#tab-progress .progress-table thead th:nth-child(2)', 'progress.material'],
    ['#tab-progress .progress-table thead th:nth-child(3)', 'progress.duration'],
    ['#tab-progress .progress-table thead th:nth-child(4)', 'progress.repetitions'],
    ['#tab-progress .progress-table thead th:nth-child(5)', 'progress.difficulty'],
    ['#tab-progress .progress-table thead th:nth-child(6)', 'progress.notes'],
    ['#no-progress', 'progress.none'],
    ['#btn-export-csv', 'progress.export'],
    ['#tab-progress .stats-grid .stat-card:nth-child(1) .stat-label', 'progress.sessions'],
    ['#tab-progress .stats-grid .stat-card:nth-child(2) .stat-label', 'progress.minutes'],
    ['#tab-progress .stats-grid .stat-card:nth-child(3) .stat-label', 'progress.avgDifficulty'],
    ['#tab-progress .stats-grid .stat-card:nth-child(4) .stat-label', 'progress.streak'],
    ['#tab-progress .card:nth-child(3) h2', 'progress.coach'],
    ['#adaptive-learner-meta', 'progress.adaptiveIdle'],
    ['#adaptive-stats-grid .stat-card:nth-child(1) .stat-label', 'progress.pronAvg'],
    ['#adaptive-stats-grid .stat-card:nth-child(2) .stat-label', 'progress.reviewDue'],
    ['#adaptive-stats-grid .stat-card:nth-child(3) .stat-label', 'progress.trackedItems'],
    ['#adaptive-stats-grid .stat-card:nth-child(4) .stat-label', 'progress.activeDays'],
    ['.adaptive-review-lab h3', 'progress.flashcardsTitle'],
    ['#adaptive-flashcard-hint', 'progress.flashcardsHint'],
    ['.adaptive-columns:nth-of-type(1) .adaptive-column:nth-child(1) h3', 'progress.reviewToday'],
    ['.adaptive-columns:nth-of-type(1) .adaptive-column:nth-child(2) h3', 'progress.nextActions'],
    ['.adaptive-columns:nth-of-type(2) .adaptive-column:nth-child(1) h3', 'progress.weakPoints'],
    ['.adaptive-columns:nth-of-type(2) .adaptive-column:nth-child(2) h3', 'progress.strengths'],
    ['#btn-adaptive-flip', 'progress.flip'],
    ['#btn-adaptive-grade-again', 'progress.again'],
    ['#btn-adaptive-grade-hard', 'progress.hard'],
    ['#btn-adaptive-grade-good', 'progress.good'],
    ['#btn-adaptive-grade-easy', 'progress.easy'],
    ['.api-status-footer h2', 'api.title'],
    ['.api-status-footer .badge', 'api.badge'],
    ['.api-status-footer .hint', 'api.hint'],
    ['#btn-cleanup', 'footer.cleanupButton'],
    ['.lesson-modal-header h2', 'lesson.title'],
];

const STATIC_HTML_BINDINGS = [
    ['.hero-eyebrow', 'hero.eyebrowHtml'],
    ['.practice-hero-title', 'hero.title'],
    ['.practice-hero-text', 'hero.text'],
    ['.hero-stat:nth-child(1) .hero-stat-label', 'hero.voiceLabel'],
    ['.hero-stat:nth-child(2) .hero-stat-label', 'hero.videoLabel'],
    ['.hero-stat:nth-child(3) .hero-stat-label', 'hero.missionLabel'],
    ['.practice-hero-actions .btn-primary', 'hero.start'],
    ['.practice-hero-actions .btn-ghost', 'hero.openVideos'],
    ['.hero-panel-kicker', 'hero.panelKicker'],
    ['.hero-panel-list li:nth-child(1)', 'hero.panel1'],
    ['.hero-panel-list li:nth-child(2)', 'hero.panel2'],
    ['.hero-panel-list li:nth-child(3)', 'hero.panel3'],
    ['.hero-panel-list li:nth-child(4)', 'hero.panel4'],
    ['.hero-panel-foot', 'hero.panelFoot'],
    ['#btn-record', 'record.start'],
    ['#btn-stop-record', 'record.stop'],
    ['.footer-main > p:first-child', 'footer.taglineHtml'],
];

const STATIC_ATTR_BINDINGS = [
    ['#ui-lang-select', 'aria-label', 'header.uiLanguage'],
    ['#input-text', 'placeholder', 'composer.placeholder'],
    ['#btn-load-voices', 'title', 'composer.loadVoicesTitle'],
    ['#btn-combo', 'title', 'composer.comboTitle'],
    ['#btn-loop', 'title', 'audio.loopTitle'],
    ['#karaoke-translate-to', 'title', 'karaoke.translateTitle'],
    ['#video-topic-input', 'placeholder', 'videos.placeholder'],
    ['#ai-topic', 'placeholder', 'aiTools.topic'],
    ['#video-topic-lang', 'title', 'conversation.settingsLanguage'],
    ['#mc-toggle-btn', 'title', 'mission.toggleTitle'],
    ['.lesson-modal-close', 'title', 'lesson.close'],
    ['#btn-cleanup', 'title', 'footer.cleanupTitle'],
    ['#conv-text-input', 'placeholder', 'conversation.composePlaceholder'],
    ['#prog-material', 'placeholder', 'progress.material'],
    ['#prog-notes', 'placeholder', 'progress.notes'],
    ['#conv-mic-btn', 'title', 'conversation.micTitle'],
];

function getNestedTranslation(source, key) {
    return String(key || '')
        .split('.')
        .reduce((current, part) => (current && typeof current === 'object' ? current[part] : undefined), source);
}

function interpolateTranslation(template, vars = {}) {
    return String(template || '').replace(/\{(\w+)\}/g, (_, key) => {
        const value = vars[key];
        return value === undefined || value === null ? '' : String(value);
    });
}

function detectPreferredUiLang() {
    const browserLang = String(navigator.language || navigator.userLanguage || '').trim().toLowerCase();
    const baseLang = browserLang.split('-')[0];
    return SUPPORTED_UI_LANGS.includes(baseLang) ? baseLang : 'en';
}

function normalizeUiLang(value) {
    const lang = String(value || '').trim().toLowerCase();
    return SUPPORTED_UI_LANGS.includes(lang) ? lang : UI_LANG_FALLBACK;
}

function getStoredUiLang() {
    try {
        return normalizeUiLang(localStorage.getItem(UI_LANG_STORAGE) || detectPreferredUiLang() || UI_LANG_FALLBACK);
    } catch {
        return normalizeUiLang(detectPreferredUiLang() || UI_LANG_FALLBACK);
    }
}

function storeUiLang(lang) {
    try {
        localStorage.setItem(UI_LANG_STORAGE, normalizeUiLang(lang));
    } catch {}
}

function t(key, vars = {}) {
    const lang = normalizeUiLang(state.uiLang || UI_LANG_FALLBACK);
    const value = getNestedTranslation(UI_COPY[lang], key)
        ?? getNestedTranslation(UI_COPY.en, key)
        ?? getNestedTranslation(UI_COPY[UI_LANG_FALLBACK], key);
    if (value === undefined) return key;
    if (typeof value === 'string') return interpolateTranslation(value, vars);
    return value;
}

function setTranslatedText(selector, key, vars = {}) {
    const el = $(selector);
    if (el) el.textContent = t(key, vars);
}

function setTranslatedHtml(selector, key, vars = {}) {
    const el = $(selector);
    if (el) el.innerHTML = t(key, vars);
}

function setTranslatedAttr(selector, attr, key, vars = {}) {
    const el = $(selector);
    if (el) el.setAttribute(attr, t(key, vars));
}

function setSelectOptionText(selectSelector, value, label) {
    const select = $(selectSelector);
    if (!select) return;
    const option = Array.from(select.options || []).find(opt => opt.value === value);
    if (option) option.textContent = label;
}

function getLanguageLabel(code, { mode = 'native', withFlag = false } = {}) {
    const normalized = String(code || '').trim().toLowerCase();
    if (!normalized) return '';
    const name = t(`lang.${mode}.${normalized}`);
    if (!name || name === `lang.${mode}.${normalized}`) {
        return withFlag && LANGUAGE_FLAGS[normalized]
            ? `${LANGUAGE_FLAGS[normalized]} ${normalized.toUpperCase()}`
            : normalized.toUpperCase();
    }
    return withFlag && LANGUAGE_FLAGS[normalized]
        ? `${LANGUAGE_FLAGS[normalized]} ${name}`
        : name;
}

function getConversationScenarioLabel(value) {
    return t(`conversation.scenarioLabels.${String(value || '').trim().toLowerCase()}`) || String(value || '');
}

function getConversationGoalLabel(value) {
    return t(`conversation.goalLabels.${String(value || '').trim().toLowerCase()}`) || String(value || '');
}

function formatUiLoopLabel(enabled) {
    return t(enabled ? 'audio.loopOn' : 'audio.loopOff');
}

function updateLoopButtonLabel() {
    const btn = $('#btn-loop');
    if (!btn) return;
    btn.textContent = formatUiLoopLabel(Boolean(state.loopEnabled));
    btn.title = t('audio.loopTitle');
}

function updatePracticeRecordingUi() {
    const startBtn = $('#btn-record');
    const stopBtn = $('#btn-stop-record');
    const status = $('#recording-status');
    if (startBtn) {
        startBtn.innerHTML = state.isRecording ? t('record.recording') : t('record.start');
    }
    if (stopBtn) stopBtn.textContent = t('record.stop');
    if (status && state.isRecording) status.textContent = t('record.status');
}

function updateUiSelectOptions() {
    const uiSelect = $('#ui-lang-select');
    if (uiSelect) {
        SUPPORTED_UI_LANGS.forEach(code => {
            setSelectOptionText('#ui-lang-select', code, t('misc.uiOption', { flag: LANGUAGE_FLAGS[code], label: t(`lang.native.${code}`) }));
        });
    }

    ['#lang-select', '#ai-lang', '#video-topic-lang', '#conv-lang'].forEach(selector => {
        ['en', 'pt', 'es', 'fr', 'de', 'it'].forEach(code => {
            setSelectOptionText(selector, code, t('misc.uiOption', { flag: LANGUAGE_FLAGS[code], label: getLanguageLabel(code, { mode: 'native' }) }));
        });
    });

    ['#karaoke-translate-to', '#conv-translate-to'].forEach(selector => {
        ['pt', 'en', 'es', 'fr', 'de', 'it'].forEach(code => {
            const language = getLanguageLabel(code, { mode: 'display' });
            const key = selector === '#karaoke-translate-to'
                ? `karaoke.options.${code}`
                : 'misc.translateTo';
            const label = key.startsWith('karaoke.')
                ? t(key)
                : t(key, { lang: language });
            setSelectOptionText(selector, code, `${LANGUAGE_FLAGS[code]} ${label}`);
        });
    });

    ['#video-topic-lang'].forEach(selector => {
        ['en', 'pt', 'es', 'fr', 'de', 'it'].forEach(code => {
            setSelectOptionText(selector, code, `${LANGUAGE_FLAGS[code]} ${t('misc.searchIn', { lang: getLanguageLabel(code, { mode: 'display' }).toLowerCase() })}`);
        });
    });

    const usePortugueseOptionCopy = state.uiLang === 'pt';
    const aiLevelOptions = !usePortugueseOptionCopy
        ? { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }
        : { beginner: 'Iniciante', intermediate: 'Intermediário', advanced: 'Avançado' };
    Object.entries(aiLevelOptions).forEach(([value, label]) => setSelectOptionText('#ai-level', value, label));

    const aiLengthOptions = !usePortugueseOptionCopy
        ? {
            micro: 'Micro (1-2 sentences)',
            short: 'Short (3-4 sentences)',
            medium: 'Medium (5-6 sentences)',
            long: 'Long (7-9 sentences)',
        }
        : {
            micro: 'Micro (1-2 frases)',
            short: 'Curto (3-4 frases)',
            medium: 'Médio (5-6 frases)',
            long: 'Longo (7-9 frases)',
        };
    Object.entries(aiLengthOptions).forEach(([value, label]) => setSelectOptionText('#ai-length', value, label));

    const aiTypeOptions = !usePortugueseOptionCopy
        ? {
            dialogue: 'Dialogue',
            monologue: 'Monologue',
            story: 'Mini story',
            interview: 'Interview',
            presentation: 'Presentation',
            casual_chat: 'Casual chat',
        }
        : {
            dialogue: 'Diálogo',
            monologue: 'Monólogo',
            story: 'Mini história',
            interview: 'Entrevista',
            presentation: 'Apresentação',
            casual_chat: 'Conversa casual',
        };
    Object.entries(aiTypeOptions).forEach(([value, label]) => setSelectOptionText('#ai-type', value, label));

    const aiFocusOptions = !usePortugueseOptionCopy
        ? {
            'general fluency': 'General fluency',
            pronunciation: 'Pronunciation',
            'linking sounds': 'Linking sounds',
            intonation: 'Intonation',
            'formal speech': 'Formal speech',
            'casual speech': 'Casual speech',
        }
        : {
            'general fluency': 'Fluência geral',
            pronunciation: 'Pronúncia',
            'linking sounds': 'Linking sounds',
            intonation: 'Entonação',
            'formal speech': 'Fala formal',
            'casual speech': 'Fala casual',
        };
    Object.entries(aiFocusOptions).forEach(([value, label]) => setSelectOptionText('#ai-focus', value, label));

    const convScenarioOptions = {
        casual: !usePortugueseOptionCopy ? '☕ Casual small talk' : '☕ Small talk casual',
        travel: !usePortugueseOptionCopy ? '✈️ Travel' : '✈️ Viagem',
        work: !usePortugueseOptionCopy ? '💼 Work' : '💼 Trabalho',
        interview: !usePortugueseOptionCopy ? '🎯 Interview' : '🎯 Entrevista',
        tech: !usePortugueseOptionCopy ? '🧠 Technology' : '🧠 Tecnologia',
        daily: !usePortugueseOptionCopy ? '🏠 Daily routine' : '🏠 Rotina diária',
    };
    Object.entries(convScenarioOptions).forEach(([value, label]) => setSelectOptionText('#conv-scenario', value, label));

    const convGoalOptions = {
        flow: !usePortugueseOptionCopy ? '🌊 Flow' : '🌊 Fluidez',
        confidence: !usePortugueseOptionCopy ? '🧩 Confidence' : '🧩 Confiança',
        vocabulary: !usePortugueseOptionCopy ? '📚 Vocabulary' : '📚 Vocabulário',
        opinions: !usePortugueseOptionCopy ? '💬 Opinions' : '💬 Opiniões',
    };
    Object.entries(convGoalOptions).forEach(([value, label]) => setSelectOptionText('#conv-goal', value, label));
}

function updateConversationSettingsLabels() {
    const labels = [
        ['#conv-lang', 'conversation.settingsLanguage'],
        ['#conv-scenario', 'conversation.settingsScenario'],
        ['#conv-goal', 'conversation.settingsGoal'],
        ['#conv-voice', 'conversation.settingsVoice'],
        ['#conv-tts-engine', 'conversation.settingsEngine'],
        ['#conv-translate-to', 'conversation.settingsTranslate'],
    ];
    labels.forEach(([selector, key]) => {
        const input = $(selector);
        const label = input?.closest('.form-group')?.querySelector('label');
        if (label) label.textContent = t(key);
    });

    const toggleTexts = $$('.conv-toggle-label span:last-child');
    if (toggleTexts[0]) toggleTexts[0].textContent = t('conversation.coachNotes');
    if (toggleTexts[1]) toggleTexts[1].textContent = t('conversation.autoSend');
}

function updateMissionControlCopy() {
    setTranslatedText('#mission-control .mc-header h3', 'mission.title');
    setTranslatedAttr('#mc-toggle-btn', 'title', 'mission.toggleTitle');
    setTranslatedText('#mc-reset-btn', 'mission.reset');
    $$('.mc-check').forEach(button => { button.title = t('mission.markComplete'); });
    $$('.mc-play-btn').forEach(button => { button.title = t('mission.activatePhase'); });
    $$('.mc-timer-ctrl').forEach(button => { button.title = t('mission.pauseResume'); });
    $$('.mc-phase').forEach(phase => {
        const num = phase.dataset.mcPhase;
        const title = phase.querySelector('.mc-phase-name');
        const hint = phase.querySelector('.mc-phase-hint');
        if (title) title.textContent = t(`mission.phases.${num}.name`);
        if (hint) hint.textContent = t(`mission.phases.${num}.hint`);
    });
}

function applyStaticUiTranslations() {
    document.documentElement.lang = UI_LANG_HTML[normalizeUiLang(state.uiLang)] || UI_LANG_HTML[UI_LANG_FALLBACK];
    document.title = t('document.title');

    STATIC_TEXT_BINDINGS.forEach(([selector, key]) => setTranslatedText(selector, key));
    STATIC_HTML_BINDINGS.forEach(([selector, key]) => setTranslatedHtml(selector, key));
    STATIC_ATTR_BINDINGS.forEach(([selector, attr, key]) => setTranslatedAttr(selector, attr, key));

    updateUiSelectOptions();
    updateMissionControlCopy();
    updateConversationSettingsLabels();
    updateLoopButtonLabel();
    updatePracticeRecordingUi();
}

function setupUiLanguage() {
    state.uiLang = getStoredUiLang();
    const select = $('#ui-lang-select');
    if (select) {
        select.value = state.uiLang;
        select.addEventListener('change', async event => {
            const nextLang = normalizeUiLang(event.target.value);
            if (state.uiLang === nextLang) return;
            state.uiLang = nextLang;
            storeUiLang(nextLang);
            applyStaticUiTranslations();
            $('#input-text')?.dispatchEvent(new Event('input'));
            renderApiBadges();
            loadDiskStats();
            loadSessionHistory();
            await loadProgress();
            renderConvStarterChips();
            updateConversationSessionUi();
            if (!state.sessionData?.sentences?.length) {
                renderKaraokeTranslationPlaceholder(t('karaoke.placeholderIdle'));
            } else {
                setKaraokeTranslationMeta({
                    sourceLang: state.sessionData?.language || 'en',
                    targetLang: state.karaokeTranslations.targetLang || defaultKaraokeTranslationTarget(state.sessionData?.language),
                    provider: state.karaokeTranslations.source || '',
                    warning: state.karaokeTranslations.warning || '',
                });
            }
            if (state.videoDiscovery.videos?.length || state.videoDiscovery.query || state.videoDiscovery.warning) {
                renderVideos(state.videoDiscovery.videos || [], state.videoDiscovery.warning || '', state.videoDiscovery);
            } else {
                setVideosSummary(t('videos.defaultSummary'));
            }
        });
    }
    applyStaticUiTranslations();
}

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
    if (engine === 'lmnt') {
        return state.uiLang === 'en'
            ? '🎙️ Generating audio with LMNT natural voice...'
            : '🎙️ Gerando áudio com voz natural LMNT...';
    }
    if (engine === 'deepgram') {
        return state.uiLang === 'en'
            ? '🧠 Generating audio with Deepgram Aura-2 natural voice...'
            : '🧠 Gerando áudio com voz natural Deepgram Aura-2...';
    }
    return state.uiLang === 'en'
        ? '🖥️ Generating local audio with Piper...'
        : '🖥️ Gerando áudio local com Piper...';
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
    setupUiLanguage();
    loadProgress();
    checkApiStatus();
    initWhatsAppTools();
    loadDiskStats();
    setupHistoryAccordion();
    loadSessionHistory();
    setupWordCounter();
    initAdaptiveFlashcards();
    initVideoExplorer();
    initKaraokeTranslationPanel();
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
    const textAiLabel = t('api.textAi');
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
            🧠 ${textAiLabel} ${state.apiStatus.ai_text ? '✓' : '✗'}
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
        counter.textContent = t('misc.words', { words, chars, minutes: estTime });
    };
    ta.addEventListener('input', update);
    update();
}

// ═════════════════════════════════════════════════════════//  GERAR SESSÃO
// ═══════════════════════════════════════════════════════════
$('#btn-generate').addEventListener('click', async () => {
    const text = $('#input-text').value.trim();
    if (!text) return alert(t('misc.pasteText'));

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
        if (!sessionData?.audio_url) throw new Error(t('misc.sessionInvalid'));
        state.sessionData = sessionData;
        renderSession(sessionData);
        saveToHistory(sessionData);
    } catch (err) {
        alert(`${t('conversation.error')}: ${err.message}`);
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
    if (!text) return alert(t('misc.pasteTextFirst'));

    show('#loading'); hide('#analysis-section');
    $('#loading-text').textContent = t('loading.analyzing');
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
        if (!result?.analysis) throw new Error(t('misc.analysisInvalid'));
        renderAnalysis(result.analysis);
    } catch (err) {
        alert(`${t('conversation.error')}: ${err.message}`);
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
            <span class="ai-label">${escapeHtml(t('analysis.level'))}</span>
            <span class="badge" style="background:${colors[a.difficulty_level] || '#888'};color:#000">
                ${a.difficulty_level.toUpperCase()} (${a.difficulty_score || '?'}/5)
            </span>
        </div>`;
    }

    // Pronunciation tips
    if (a.pronunciation_tips?.length) {
        html += `<h3>${escapeHtml(t('analysis.pronunciation'))}</h3><div class="ai-chips">`;
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
        html += `<h3>${escapeHtml(t('analysis.linking'))}</h3><div class="ai-chips">`;
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
        html += `<h3>${escapeHtml(t('analysis.vocabulary'))}</h3><div class="vocab-grid">`;
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
        html += `<h3>${escapeHtml(t('analysis.intonation'))}</h3><p class="ai-note">${escapeHtml(a.intonation_notes)}</p>`;
    }

    // Focus
    if (a.shadowing_focus?.length) {
        html += `<h3>${escapeHtml(t('analysis.focus'))}</h3><ul class="ai-list">`;
        a.shadowing_focus.forEach(f => { html += `<li>${escapeHtml(f)}</li>`; });
        html += '</ul>';
    }

    // Mistakes
    if (a.common_mistakes_br?.length) {
        html += `<h3>${escapeHtml(t('analysis.mistakes'))}</h3><ul class="ai-list ai-list-warn">`;
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
    if (!text) return alert(t('misc.pasteText'));

    const lang = $('#lang-select').value || undefined;
    const voice = $('#voice-select').value;
    const ttsEngine = getSelectedTtsEngine();
    const piperPayload = buildPiperPracticePayload(text, 'shadowing_practice_session', 'story');

    show('#loading'); hide('#result-section'); hide('#analysis-section');
    $('#loading-text').textContent = state.uiLang === 'en'
        ? `⚡ ${getTtsLoadingMessage(ttsEngine).replace('...', '')} + AI analysis in parallel...`
        : `⚡ ${getTtsLoadingMessage(ttsEngine).replace('...', '')} + análise IA em paralelo...`;
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
                errors.push(t('misc.sessionInvalid'));
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
                errors.push(t('misc.analysisInvalid'));
            }
        } else {
            errors.push(anaOutcome.reason?.message || t('misc.analysisInvalid'));
        }

        if (!successCount) {
            throw new Error(errors.join(' | ') || (state.uiLang === 'en' ? 'Failed to generate session and analysis.' : 'Falha ao gerar sessão e análise.'));
        }
        if (errors.length) {
            console.warn('[Combo parcial]', errors.join(' | '));
        }
    } catch (err) {
        alert(`${t('conversation.error')}: ${err.message}`);
    } finally {
        hide('#loading');
        $('#btn-combo').disabled = false;
    }
});

// ═══════════════════════════════════════════════════════════
//  RENDERIZAR SESSÃO + KARAOKÊ CONTÍNUO
// ═══════════════════════════════════════════════════════════
function formatKaraokeTranslationLangLabel(lang) {
    return getLanguageLabel(lang, { mode: 'native', withFlag: true }) || String(lang || '??').toUpperCase();
}

function defaultKaraokeTranslationTarget(sourceLang) {
    const normalized = String(sourceLang || 'en').trim().toLowerCase();
    return normalized === 'pt' ? 'en' : 'pt';
}

function initKaraokeTranslationPanel() {
    $('#karaoke-translate-to')?.addEventListener('change', event => {
        const nextLang = String(event.target.value || '').trim().toLowerCase() || 'pt';
        loadSessionTranslation(nextLang, { force: false });
    });
}

function setKaraokeTranslationMeta({ sourceLang = '', targetLang = '', provider = '', warning = '' } = {}) {
    const sourceTag = $('#karaoke-source-lang');
    const targetTag = $('#karaoke-target-lang');
    const badge = $('#karaoke-translation-badge');
    const hint = $('#karaoke-translation-hint');

    const providerLabel = t(`karaoke.provider.${String(provider || '').trim().toLowerCase()}`) || (provider ? String(provider).toUpperCase() : '—');

    if (sourceTag) sourceTag.textContent = String(sourceLang || '??').toUpperCase();
    if (targetTag) targetTag.textContent = String(targetLang || '??').toUpperCase();
    if (badge) badge.textContent = providerLabel;
    if (hint) {
        hint.textContent = warning
            ? t('karaoke.hintWarning', { warning })
            : t('karaoke.hint');
    }
}

function renderKaraokeTranslationPlaceholder(message = t('karaoke.placeholderSelect')) {
    const container = $('#karaoke-translation-text');
    if (!container) return;
    container.innerHTML = `<div class="adaptive-flashcard-empty"><strong>${escapeHtml(t('karaoke.translation'))}</strong><span>${escapeHtml(message)}</span></div>`;
    state.karaokeTranslations.sentenceEls = [];
}

function renderKaraokeTranslations(translations = [], sessionData = {}) {
    const container = $('#karaoke-translation-text');
    if (!container) return;
    container.innerHTML = '';

    const sentenceEls = [];
    const sourceSentences = Array.isArray(sessionData?.sentences) ? sessionData.sentences : [];
    translations.forEach((item, index) => {
        const span = document.createElement('span');
        span.className = 'k-sentence k-translation-sentence';
        span.dataset.index = index;
        span.textContent = item?.translation || t('karaoke.unavailable');
        const sourceSentence = sourceSentences[index] || item?.text || '';
        span.addEventListener('click', () => playSentence(sourceSentence, sessionData.language, sessionData.voice, span));
        container.appendChild(span);
        if (index < translations.length - 1) container.appendChild(document.createTextNode(' '));
        sentenceEls.push({ el: span, text: span.textContent });
    });

    state.karaokeTranslations.sentenceEls = sentenceEls;
}

async function loadSessionTranslation(targetLang, { force = false } = {}) {
    const session = state.sessionData;
    if (!session?.sentences?.length) return;
    const sessionKey = `${session.session_id || ''}:${session.text || ''}`;

    const normalizedTarget = String(targetLang || '').trim().toLowerCase()
        || defaultKaraokeTranslationTarget(session.language);
    const normalizedSource = String(session.language || 'en').trim().toLowerCase();
    const cacheKey = `${normalizedSource}:${normalizedTarget}:${session.session_id || session.text}`;
    state.karaokeTranslations.targetLang = normalizedTarget;

    const select = $('#karaoke-translate-to');
    if (select && select.value !== normalizedTarget) select.value = normalizedTarget;

    if (!force && state.karaokeTranslations.cache[cacheKey]) {
        const cached = state.karaokeTranslations.cache[cacheKey];
        state.karaokeTranslations.source = cached.provider || '';
        state.karaokeTranslations.warning = cached.warning || '';
        renderKaraokeTranslations(cached.translations || [], session);
        setKaraokeTranslationMeta({
            sourceLang: normalizedSource,
            targetLang: normalizedTarget,
            provider: cached.provider || '',
            warning: cached.warning || '',
        });
        return;
    }

    renderKaraokeTranslationPlaceholder(t('karaoke.placeholderLoading'));
    setKaraokeTranslationMeta({
        sourceLang: normalizedSource,
        targetLang: normalizedTarget,
        provider: '...',
        warning: '',
    });

    try {
        const data = await postJson('/api/session-translation', {
            sentences: session.sentences,
            source_lang: normalizedSource,
            target_lang: normalizedTarget,
        });
        const currentSession = state.sessionData;
        const currentSessionKey = `${currentSession?.session_id || ''}:${currentSession?.text || ''}`;
        if (currentSessionKey !== sessionKey) return;
        state.karaokeTranslations.cache[cacheKey] = {
            translations: Array.isArray(data?.translations) ? data.translations : [],
            provider: data?.provider || 'unknown',
            warning: data?.warning || '',
        };
        state.karaokeTranslations.source = data?.provider || '';
        state.karaokeTranslations.warning = data?.warning || '';
        renderKaraokeTranslations(data?.translations || [], session);
        setKaraokeTranslationMeta({
            sourceLang: normalizedSource,
            targetLang: normalizedTarget,
            provider: data?.provider || '',
            warning: data?.warning || '',
        });
    } catch (err) {
        const currentSession = state.sessionData;
        const currentSessionKey = `${currentSession?.session_id || ''}:${currentSession?.text || ''}`;
        if (currentSessionKey !== sessionKey) return;
        state.karaokeTranslations.source = 'error';
        state.karaokeTranslations.warning = err.message || (state.uiLang === 'en' ? 'Failed to load translation.' : 'Falha ao carregar tradução.');
        renderKaraokeTranslationPlaceholder(t('karaoke.error', { message: err.message }));
        setKaraokeTranslationMeta({
            sourceLang: normalizedSource,
            targetLang: normalizedTarget,
            provider: 'erro',
            warning: err.message || (state.uiLang === 'en' ? 'Failed to load translation.' : 'Falha ao carregar tradução.'),
        });
    }
}

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
        badge.title = profileLabel
            ? (state.uiLang === 'en' ? `Piper · profile ${profileLabel}` : `Piper · perfil ${profileLabel}`)
            : (state.uiLang === 'en' ? 'Local Piper' : 'Piper local');
    } else {
        badge.textContent = state.uiLang === 'en' ? '🔊 Local TTS' : '🔊 TTS Local';
        badge.className = 'engine-badge badge-local';
        badge.title = '';
    }

    // Audio
    const audio = $('#main-audio');
    audio.src = data.audio_url;
    audio.playbackRate = 1;

    state.karaokeTranslations = {
        cache: {},
        targetLang: defaultKaraokeTranslationTarget(data.language),
        source: '',
        warning: '',
        sentenceEls: [],
    };
    const translateSelect = $('#karaoke-translate-to');
    if (translateSelect) {
        translateSelect.value = state.karaokeTranslations.targetLang;
    }
    renderKaraokeTranslationPlaceholder(t('karaoke.placeholderIdle'));
    setKaraokeTranslationMeta({
        sourceLang: data.language || 'en',
        targetLang: state.karaokeTranslations.targetLang,
        provider: '...',
        warning: '',
    });

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
            state.karaokeTranslations.sentenceEls.forEach(se => {
                se.el.classList.remove('k-active', 'k-done');
            });
            for (let i = 0; i < active; i++) sync.els[i].el.classList.add('k-done');
            for (let i = 0; i < active; i++) {
                if (state.karaokeTranslations.sentenceEls[i]) {
                    state.karaokeTranslations.sentenceEls[i].el.classList.add('k-done');
                }
            }
            if (active >= 0) {
                sync.els[active].el.classList.add('k-active');
                sync.els[active].el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                if (state.karaokeTranslations.sentenceEls[active]) {
                    state.karaokeTranslations.sentenceEls[active].el.classList.add('k-active');
                    state.karaokeTranslations.sentenceEls[active].el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
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
        state.karaokeTranslations.sentenceEls.forEach(se => {
            se.el.classList.remove('k-active');
            se.el.classList.add('k-done');
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
                    state.karaokeTranslations.sentenceEls.forEach(se => {
                        se.el.classList.remove('k-done', 'k-active');
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
    syncVideoExplorerFromSession(data);
    renderVideos(data.videos, data.video_warning, {
        query: buildSuggestedVideoTopic(data.text || '', data.language || 'en'),
        source: data.video_source || '',
        lang: data.language || 'en',
        queryUsed: data.video_query_used || '',
    });

    // Reset recordings
    $('#recordings-list').innerHTML = '';
    state.recordingCount = 0;

    animateStaggerElements($$('#result-section .card'), 'is-revealing', 26);
    $('#result-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
    loadSessionTranslation(state.karaokeTranslations.targetLang, { force: true });
}

function initVideoExplorer() {
    const input = $('#video-topic-input');
    const button = $('#btn-video-topic-search');
    const langSelect = $('#video-topic-lang');
    if (!input || !button || !langSelect) return;

    input.addEventListener('input', () => {
        if (input.value.trim()) input.dataset.edited = '1';
        else delete input.dataset.edited;
    });

    input.addEventListener('keydown', event => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        searchVideosByTopic();
    });

    button.addEventListener('click', () => searchVideosByTopic());

    const mainLangSelect = $('#lang-select');
    mainLangSelect?.addEventListener('change', () => {
        if (state.sessionData) return;
        langSelect.value = mainLangSelect.value || 'en';
    });
}

function buildSuggestedVideoTopic(text, lang = 'en') {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    if (!clean) return '';
    const firstSentence = clean.split(/(?<=[.!?。！？])\s+/)[0]?.trim() || clean;
    const snippet = firstSentence.split(/\s+/).slice(0, 8).join(' ');
    const suffixByLang = {
        en: 'dialogue',
        pt: 'dialogo',
        es: 'dialogo',
        fr: 'conversation',
        de: 'Dialog',
        it: 'dialogo',
    };
    const suffix = suffixByLang[String(lang || '').toLowerCase()] || 'dialogue';
    return `${snippet} ${suffix}`.trim();
}

function syncVideoExplorerFromSession(data = {}) {
    const input = $('#video-topic-input');
    const langSelect = $('#video-topic-lang');
    const sessionLang = data.language || $('#lang-select')?.value || 'en';

    if (langSelect) langSelect.value = sessionLang;

    if (input && !input.dataset.edited) {
        const suggestion = buildSuggestedVideoTopic(data.text || '', sessionLang);
        if (suggestion) input.value = suggestion;
    }
}

function videoSourceLabel(source) {
    return ({
        youtube_search: 'youtube-search',
        yt_dlp: 'yt-dlp',
    })[source] || '';
}

function formatVideoSearchLangLabel(lang) {
    return getLanguageLabel(lang, { mode: 'display', withFlag: false }) || String(lang || '').trim();
}

function setVideosSourceBadge(source = '') {
    const badge = $('#videos-source-badge');
    if (!badge) return;
    const label = videoSourceLabel(source);
    if (!label) {
        badge.textContent = '';
        badge.classList.add('hidden');
        return;
    }
    badge.textContent = label;
    badge.classList.remove('hidden');
}

function setVideosSummary(message = '') {
    const summary = $('#videos-summary');
    if (!summary) return;
    summary.textContent = message || t('videos.defaultSummary');
}

async function requestVideoSearch(query, lang) {
    const res = await fetch('/api/videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, lang }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.error || (state.uiLang === 'en' ? 'Failed to search videos.' : 'Falha ao buscar vídeos.'));
    return data;
}

function renderVideos(videos, warning = '', meta = {}) {
    const grid = $('#videos-grid');
    const query = String(meta.query || state.videoDiscovery.query || '').trim();
    const source = String(meta.source || state.videoDiscovery.source || '').trim();
    const lang = String(meta.lang || state.videoDiscovery.lang || '').trim();
    const queryUsed = String(meta.queryUsed || state.videoDiscovery.queryUsed || '').trim();
    const langLabel = formatVideoSearchLangLabel(lang);
    state.videoDiscovery.query = query;
    state.videoDiscovery.source = source;
    state.videoDiscovery.warning = String(warning || '');
    state.videoDiscovery.lang = lang;
    state.videoDiscovery.queryUsed = queryUsed;
    state.videoDiscovery.videos = Array.isArray(videos) ? videos : [];

    grid.innerHTML = '';
    setVideosSourceBadge(source);
    if (!videos?.length) {
        const emptySummary = query
            ? (
                state.uiLang === 'en'
                    ? `No videos found${langLabel ? ` in ${langLabel}` : ''} for "${query}".`
                    : `Nenhum vídeo encontrado${langLabel ? ` em ${langLabel}` : ''} para "${query}".`
            )
            : (
                state.uiLang === 'en'
                    ? 'No videos found yet.'
                    : 'Nenhum vídeo encontrado ainda.'
            );
        const guidedSummary = (
            queryUsed
            && query
            && queryUsed.toLocaleLowerCase() !== query.toLocaleLowerCase()
        ) ? (
            state.uiLang === 'en'
                ? ` Guided query used: "${queryUsed}".`
                : ` Busca guiada usada: "${queryUsed}".`
        ) : '';
        setVideosSummary(
            warning
                ? `${emptySummary}${guidedSummary} ${warning}`
                : `${emptySummary}${guidedSummary}`
        );
        const warningHtml = warning ? `<p class="hint">${escapeHtml(warning)}</p>` : '';
        grid.innerHTML = `
            <p class="hint">${escapeHtml(state.uiLang === 'en' ? 'No videos found.' : 'Nenhum vídeo encontrado.')}</p>
            ${warningHtml}
            <button class="btn btn-sm btn-ghost" id="btn-retry-videos">${escapeHtml(t('videos.retry'))}</button>
        `;
        grid.querySelector('#btn-retry-videos')?.addEventListener('click', retryVideoSearch);
        return;
    }
    const countLabel = state.uiLang === 'en'
        ? `${videos.length} ${videos.length === 1 ? 'video found' : 'videos found'}`
        : `${videos.length} ${videos.length === 1 ? 'vídeo encontrado' : 'vídeos encontrados'}`;
    const summary = query
        ? (
            state.uiLang === 'en'
                ? `${countLabel}${langLabel ? ` in ${langLabel}` : ''} for "${query}". Open one to practice with real content.`
                : `${countLabel}${langLabel ? ` em ${langLabel}` : ''} para "${query}". Abra um deles para praticar com conteúdo real.`
        )
        : (
            state.uiLang === 'en'
                ? `${countLabel}${langLabel ? ` in ${langLabel}` : ''} related to your topic.`
                : `${countLabel}${langLabel ? ` em ${langLabel}` : ''} relacionados ao seu tema.`
        );
    const guidedSummary = (
        queryUsed
        && query
        && queryUsed.toLocaleLowerCase() !== query.toLocaleLowerCase()
    ) ? (
        state.uiLang === 'en'
            ? ` Guided query: "${queryUsed}".`
            : ` Busca guiada: "${queryUsed}".`
    ) : '';
    setVideosSummary(
        warning
            ? `${summary}${guidedSummary} ${state.uiLang === 'en' ? 'Warning' : 'Aviso'}: ${warning}`
            : `${summary}${guidedSummary}`
    );

    videos.forEach(v => {
        const card = document.createElement('div');
        card.className = 'video-card';
        const thumb = v.thumbnails?.[0] || `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`;
        const externalUrl = v.url || `https://www.youtube.com/watch?v=${v.id}`;
        card.innerHTML = `
            <img class="video-thumb" src="${typeof thumb === 'string' ? thumb : `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`}"
                 onerror="this.src='https://img.youtube.com/vi/${v.id}/hqdefault.jpg'" loading="lazy">
            <div class="video-info">
                <h4>${escapeHtml(v.title)}</h4>
                <div class="video-meta"><span>${escapeHtml(v.channel || '')}</span><span>${escapeHtml(v.duration || '')}</span><span>${escapeHtml(v.views || '')}</span></div>
                <div class="video-actions">
                    <button class="btn btn-sm btn-ghost video-watch-btn">${escapeHtml(t('videos.watchHere'))}</button>
                    <button class="btn btn-sm btn-lmnt video-open-btn">${escapeHtml(t('videos.openYoutube'))}</button>
                </div>
            </div>`;
        card.querySelector('.video-watch-btn').addEventListener('click', e => {
            e.stopPropagation();
            openVideoModal(v);
        });
        card.querySelector('.video-open-btn').addEventListener('click', e => {
            e.stopPropagation();
            window.open(externalUrl, '_blank', 'noopener');
        });
        card.addEventListener('click', () => openVideoModal(v));
        grid.appendChild(card);
    });
    animateStaggerElements($$('#videos-grid .video-card'), 'is-revealing', 18);
}

async function retryVideoSearch() {
    const manualQuery = ($('#video-topic-input')?.value || '').trim();
    if (manualQuery) {
        await searchVideosByTopic();
        return;
    }

    const current = state.sessionData || {};
    const lang = current.language || $('#lang-select').value || 'en';
    const text = (current.text || $('#input-text').value || '').trim();
    if (!text) {
        alert(t('misc.enterTopicOrSession'));
        return;
    }

    const baseQuery = text.split(/\s+/).slice(0, 10).join(' ');
    const fallbackQuery =
        lang === 'en'
            ? 'english speaking practice viral'
            : `${lang} speaking practice viral`;

    const queries = [baseQuery, fallbackQuery].map(q => q.trim()).filter(Boolean);
    if ($('#video-topic-input') && !$('#video-topic-input').dataset.edited) {
        $('#video-topic-input').value = queries[0] || '';
    }
    if ($('#video-topic-lang')) $('#video-topic-lang').value = lang;
    setVideosSummary(state.uiLang === 'en' ? 'Searching for related videos...' : 'Buscando vídeos relacionados...');
    $('#videos-grid').innerHTML = `<p class="hint">${escapeHtml(t('misc.searchLoading'))}</p>`;

    for (const query of queries) {
        try {
            const data = await requestVideoSearch(query, lang);
            if (data?.videos?.length) {
                if (state.sessionData) state.sessionData.videos = data.videos;
                renderVideos(data.videos, '', {
                    query,
                    source: data.source,
                    lang,
                    queryUsed: data.query_used || '',
                });
                return;
            }
        } catch {}
    }

    renderVideos([], t('misc.youtubeUnavailable'), {
        query: queries[0] || '',
        lang,
        queryUsed: '',
    });
}

async function searchVideosByTopic() {
    const input = $('#video-topic-input');
    const button = $('#btn-video-topic-search');
    const query = (input?.value || '').trim();
    const lang = $('#video-topic-lang')?.value || state.sessionData?.language || $('#lang-select')?.value || 'en';

    if (!query) {
        alert(t('misc.enterTopic'));
        input?.focus();
        return;
    }

    if (input) input.dataset.edited = '1';
    setVideosSummary(
        state.uiLang === 'en'
            ? `Searching videos for "${query}"...`
            : `Buscando vídeos para "${query}"...`
    );
    $('#videos-grid').innerHTML = `<p class="hint">${escapeHtml(t('misc.searchLoading'))}</p>`;
    if (button) button.disabled = true;

    try {
        const data = await requestVideoSearch(query, lang);
        if (state.sessionData) state.sessionData.videos = data.videos || [];
        renderVideos(data.videos || [], '', {
            query,
            source: data.source,
            lang,
            queryUsed: data.query_used || '',
        });
    } catch (err) {
        renderVideos([], err.message || 'Falha ao buscar vídeos.', { query, lang, queryUsed: '' });
    } finally {
        if (button) button.disabled = false;
    }
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
            : `<p class="hint">${escapeHtml(state.uiLang === 'en' ? 'No highlighted vocabulary for this sentence.' : 'Sem vocabulário destacado para esta frase.')}</p>`;

        return `<article class="yt-study-phrase">
            <div class="yt-study-head">
                <span class="yt-study-time">${formatTimecode(phrase.start)} → ${formatTimecode(phrase.end)}</span>
                <span class="badge badge-sm">${escapeHtml(state.uiLang === 'en' ? `Sentence ${idx + 1}` : `Frase ${idx + 1}`)}</span>
            </div>
            <p class="yt-study-original">${escapeHtml(phrase.text || '')}</p>
            <div class="yt-study-row">
                <strong>${escapeHtml(state.uiLang === 'en' ? 'Pronunciation:' : 'Pronúncia:')}</strong> <span>${escapeHtml(phrase.pronunciation || '—')}</span>
            </div>
            <div class="yt-study-row">
                <strong>${escapeHtml(state.uiLang === 'en' ? 'Translation:' : 'Tradução:')}</strong> <span>${escapeHtml(phrase.translation || '—')}</span>
            </div>
            <div class="yt-study-actions">
                <button
                    type="button"
                    class="btn btn-sm btn-ghost yt-study-play"
                    data-play-text="${phraseTextEncoded}"
                    data-play-lang="${escapeHtml(sourceLangRaw)}"
                    data-default-label="${escapeHtml(state.uiLang === 'en' ? '🔊 Listen to sentence' : '🔊 Ouvir frase')}"
                    data-loading-label="${escapeHtml(state.uiLang === 'en' ? '⏳ Generating audio...' : '⏳ Gerando áudio...')}"
                    data-playing-label="${escapeHtml(state.uiLang === 'en' ? '⏸ Playing' : '⏸ Tocando')}"
                >${escapeHtml(state.uiLang === 'en' ? '🔊 Listen to sentence' : '🔊 Ouvir frase')}</button>
            </div>
            <div class="yt-study-row yt-study-prof">
                <strong>${escapeHtml(state.uiLang === 'en' ? 'Teacher note:' : 'Professor explica:')}</strong> <span>${escapeHtml(teacherExplanation)}</span>
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
        btn.textContent = formatUiLoopLabel(true);
        btn.classList.add('btn-loop-active');
        state.loopMax = parseInt($('#loop-count').value) || 0;
        counter.classList.remove('hidden');
        updateLoopCounter();
    } else {
        btn.textContent = formatUiLoopLabel(false);
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
        $('#btn-record').innerHTML = t('record.recording');
        show('#btn-stop-record');
        $('#recording-status').textContent = t('record.status');
        $('#recording-status').classList.add('active');
    } catch { alert(t('record.micPermission')); }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        $('#btn-record').classList.remove('recording');
        $('#btn-record').innerHTML = t('record.start');
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
        grid.innerHTML = `<p class="hint">${escapeHtml(t('aiTools.noVoices'))}</p>`;
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
            <button class="btn btn-sm btn-ghost" data-voice-id="${v.id}">${escapeHtml(t('aiTools.useVoice'))}</button>
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
        if (!data?.practice) throw new Error(t('misc.practiceInvalid'));
        renderAiPractice(data.practice);
    } catch (err) {
        alert(`${t('conversation.error')}: ${err.message}`);
    } finally {
        hide('#ai-practice-loading');
        $('#btn-ai-generate').disabled = false;
    }
});

function renderAiPractice(p) {
    show('#ai-practice-result');
    $('#ai-practice-title').textContent = p.title || t('aiTools.generatedPractice');
    $('#ai-practice-text').textContent = p.text || '';

    const focusEl = $('#ai-practice-focus');
    focusEl.innerHTML = '';
    (p.focus_points || []).forEach(f => {
        focusEl.innerHTML += `<span class="ai-tag">${escapeHtml(f)}</span>`;
    });

    const vocabEl = $('#ai-practice-vocab');
    if (p.vocabulary_preview?.length) {
        vocabEl.innerHTML = `<h4>${escapeHtml(t('aiTools.vocabulary'))}</h4><div class="vocab-grid">` +
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
    if (confirm(t('mission.resetConfirm'))) showMissionControl();
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
    const karaokeTranslationText = $('#karaoke-translation-text');
    const karaokeCard = $('.karaoke-card');
    const recordingCard = $('#btn-record')?.closest('.card');

    // Remove text-hidden class first
    if (karaokeText) karaokeText.classList.remove('mc-text-hidden');
    if (karaokeTranslationText) karaokeTranslationText.classList.remove('mc-text-hidden');

    switch (action) {
        case 'listen-only':
            // Play audio, hide karaoke text
            if (karaokeText) karaokeText.classList.add('mc-text-hidden');
            if (karaokeTranslationText) karaokeTranslationText.classList.add('mc-text-hidden');
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
            if (karaokeTranslationText) karaokeTranslationText.classList.add('mc-text-hidden');
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
            display.textContent = t('mission.completed');
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
            phase.querySelector('.mc-timer-display').textContent = t('mission.done');
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
    } catch (err) { alert(`${t('conversation.error')}: ${err.message}`); }
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
            if (!confirm(t('misc.deleteProgress'))) return;
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
    $('#adaptive-lang-filters')?.addEventListener('click', event => {
        const button = event.target.closest('[data-adaptive-lang]');
        if (!button) return;
        event.preventDefault();
        setAdaptiveFlashcardLanguageFilter(button.dataset.adaptiveLang || 'all');
    });
}

function normalizeAdaptiveLangCode(value, fallback = 'en') {
    const raw = String(value || '').trim().toLowerCase();
    if (!raw) return fallback;
    const base = raw.split(/[-_]/)[0];
    return base || fallback;
}

function formatAdaptiveLanguageLabel(value) {
    const lang = normalizeAdaptiveLangCode(value, 'en');
    return ({
        en: '🇺🇸 English',
        pt: '🇧🇷 Português',
        es: '🇪🇸 Español',
        fr: '🇫🇷 Français',
        de: '🇩🇪 Deutsch',
        it: '🇮🇹 Italiano',
    })[lang] || lang.toUpperCase();
}

function formatAdaptiveItemSourceLabel(item) {
    const itemType = String(item?.item_type || '').toLowerCase();
    if (itemType === 'vocabulary_word') return state.uiLang === 'en' ? 'Text analysis' : 'Análise de texto';
    if (itemType === 'conversation_vocab') return state.uiLang === 'en' ? 'Conversation lesson' : 'Aula de conversa';
    if (itemType === 'pronunciation_word') return state.uiLang === 'en' ? 'Pronunciation training' : 'Treino de pronúncia';
    if (itemType === 'pronunciation_phrase') return state.uiLang === 'en' ? 'Recorded attempt' : 'Tentativa gravada';
    if (itemType === 'drill_phrase') return state.uiLang === 'en' ? 'Guided drill' : 'Drill guiado';
    if (itemType === 'correction_phrase') return state.uiLang === 'en' ? 'Conversation correction' : 'Correção da conversa';
    if (itemType === 'shadow_phrase') return state.uiLang === 'en' ? 'Shadowing focus' : 'Foco de shadowing';

    const skillArea = String(item?.skill_area || '').toLowerCase();
    if (skillArea === 'vocabulary') return state.uiLang === 'en' ? 'Vocabulary' : 'Vocabulário';
    if (skillArea === 'pronunciation') return state.uiLang === 'en' ? 'Pronunciation' : 'Pronúncia';
    if (skillArea === 'grammar') return state.uiLang === 'en' ? 'Grammar' : 'Gramática';
    if (skillArea === 'shadowing') return 'Shadowing';
    return state.uiLang === 'en' ? 'Review' : 'Revisão';
}

function formatAdaptiveDeckBucketLabel(bucket) {
    const normalized = String(bucket || '').toLowerCase();
    if (normalized === 'due') return state.uiLang === 'en' ? 'Review today' : 'Revisar hoje';
    if (normalized === 'weak') return state.uiLang === 'en' ? 'Weak point' : 'Ponto fraco';
    if (normalized === 'strong') return state.uiLang === 'en' ? 'Strong point' : 'Ponto forte';
    return state.uiLang === 'en' ? 'Deck' : 'Banco';
}

function summarizeAdaptiveText(value, maxChars = 140) {
    const text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    if (text.length <= maxChars) return text;
    return `${text.slice(0, maxChars - 1).trimEnd()}…`;
}

function inferAdaptiveDeckBucket(item) {
    const dueTime = new Date(String(item?.next_due_at || '')).getTime();
    if (Number.isFinite(dueTime) && dueTime <= Date.now()) return 'due';

    const mastery = Number(item?.mastery_score || 0);
    const seenCount = Number(item?.seen_count || 0);
    if (mastery >= 0.85 && seenCount >= 2) return 'strong';
    if (mastery <= 0.55 || seenCount <= 1) return 'weak';
    return 'deck';
}

function buildAdaptiveFlashcardDeck(data) {
    const sortByWeakness = (left, right) => {
        const leftMastery = Number(left?.mastery_score || 0);
        const rightMastery = Number(right?.mastery_score || 0);
        if (leftMastery !== rightMastery) return leftMastery - rightMastery;

        const leftSeen = Number(left?.seen_count || 0);
        const rightSeen = Number(right?.seen_count || 0);
        return rightSeen - leftSeen;
    };
    const sortByDueDate = (left, right) => {
        const leftDue = new Date(String(left?.next_due_at || '')).getTime();
        const rightDue = new Date(String(right?.next_due_at || '')).getTime();
        const safeLeft = Number.isFinite(leftDue) ? leftDue : Number.MAX_SAFE_INTEGER;
        const safeRight = Number.isFinite(rightDue) ? rightDue : Number.MAX_SAFE_INTEGER;
        if (safeLeft !== safeRight) return safeLeft - safeRight;
        return sortByWeakness(left, right);
    };

    const flashcardPool = Array.isArray(data?.flashcard_pool) ? data.flashcard_pool : [];
    const fallbackSource = [
        ...(Array.isArray(data?.review_queue) ? data.review_queue : []),
        ...(Array.isArray(data?.weak_points) ? data.weak_points : []),
        ...(Array.isArray(data?.strengths) ? data.strengths : []),
    ];
    const source = (flashcardPool.length ? flashcardPool : fallbackSource)
        .slice()
        .sort(sortByDueDate);

    const seen = new Set();
    return source
        .filter(item => {
            const sourceText = String(item?.source_text || '').trim();
            if (!sourceText) return false;
            const key = String(item?.id || `${item?.item_type || 'item'}:${sourceText}`);
            if (!key || seen.has(key)) return false;
            seen.add(key);
            return true;
        })
        .map(item => ({
            ...item,
            deck_bucket: inferAdaptiveDeckBucket(item),
            target_lang: normalizeAdaptiveLangCode(
                item?.target_lang,
                data?.learner?.target_lang || 'en',
            ),
        }));
}

function buildAdaptiveLanguageOptions(data, deck) {
    const counts = new Map();
    (Array.isArray(deck) ? deck : []).forEach(item => {
        const code = normalizeAdaptiveLangCode(item?.target_lang, '');
        if (!code) return;
        const current = counts.get(code) || {
            lang: code,
            total: 0,
            due: 0,
            avgMastery: 0,
            masterySamples: 0,
        };
        current.total += 1;
        current.due += inferAdaptiveDeckBucket(item) === 'due' ? 1 : 0;
        current.avgMastery += Number(item?.mastery_score || 0);
        current.masterySamples += 1;
        counts.set(code, current);
    });

    return Array.from(counts.values())
        .map(item => ({
            ...item,
            avgMastery: item.masterySamples ? item.avgMastery / item.masterySamples : 0,
        }))
        .sort((left, right) => right.total - left.total || left.lang.localeCompare(right.lang));
}

function getAdaptiveFilteredDeck() {
    const flash = state.adaptiveFlashcards;
    if (flash.langFilter === 'all') return flash.allDeck;
    return flash.allDeck.filter(item => normalizeAdaptiveLangCode(item?.target_lang, '') === flash.langFilter);
}

function renderAdaptiveLanguageFilters() {
    const flash = state.adaptiveFlashcards;
    const container = $('#adaptive-lang-filters');
    if (!container) return;

    const totalCount = Array.isArray(flash.allDeck) ? flash.allDeck.length : 0;
    const buttons = [
        `<button type="button" class="adaptive-lang-chip ${flash.langFilter === 'all' ? 'is-active' : ''}" data-adaptive-lang="all">${escapeHtml(t('progress.all'))} <span>${totalCount}</span></button>`,
        ...flash.languages.map(item => `
            <button type="button" class="adaptive-lang-chip ${flash.langFilter === item.lang ? 'is-active' : ''}" data-adaptive-lang="${escapeHtml(item.lang)}">
                ${escapeHtml(formatAdaptiveLanguageLabel(item.lang))}
                <span>${Number(item.total || 0)}</span>
            </button>
        `),
    ];
    container.innerHTML = buttons.join('');
}

function setAdaptiveFlashcardLanguageFilter(lang) {
    const flash = state.adaptiveFlashcards;
    const normalized = normalizeAdaptiveLangCode(lang, 'all');
    const nextFilter = normalized === 'all' ? 'all' : normalized;
    if (flash.langFilter === nextFilter) return;
    flash.langFilter = nextFilter;
    flash.deck = getAdaptiveFilteredDeck();
    flash.index = 0;
    flash.flipped = false;
    renderAdaptiveLanguageFilters();
    refreshAdaptiveFlashcardView();
}

function getAdaptiveFlashcardCurrent() {
    const flash = state.adaptiveFlashcards;
    if (!flash.deck.length) return null;
    return flash.deck[flash.index] || null;
}

function formatAdaptiveDueLabel(rawValue) {
    const due = new Date(String(rawValue || ''));
    if (Number.isNaN(due.getTime())) return state.uiLang === 'en' ? 'No next review' : 'Sem próxima revisão';

    const diffMs = due.getTime() - Date.now();
    if (diffMs <= 0) return state.uiLang === 'en' ? 'Due now' : 'Vencido';

    const diffHours = Math.round(diffMs / (1000 * 60 * 60));
    if (diffHours < 24) return state.uiLang === 'en'
        ? `Next in ${Math.max(1, diffHours)}h`
        : `Próx. em ${Math.max(1, diffHours)}h`;

    const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
    return state.uiLang === 'en'
        ? `Next in ${Math.max(1, diffDays)}d`
        : `Próx. em ${Math.max(1, diffDays)}d`;
}

function formatAdaptiveSkillLabel(item) {
    const area = String(item?.skill_area || '').toLowerCase();
    if (area === 'vocabulary') return state.uiLang === 'en' ? 'Vocabulary' : 'Vocabulário';
    if (area === 'pronunciation') return state.uiLang === 'en' ? 'Pronunciation' : 'Pronúncia';
    if (area === 'grammar') return state.uiLang === 'en' ? 'Grammar' : 'Gramática';
    if (area === 'shadowing') return 'Shadowing';
    return area ? area[0].toUpperCase() + area.slice(1) : (state.uiLang === 'en' ? 'Review' : 'Revisão');
}

function renderAdaptiveFlashcards(data) {
    const flash = state.adaptiveFlashcards;
    const previousId = Number(getAdaptiveFlashcardCurrent()?.id || 0);
    const deck = buildAdaptiveFlashcardDeck(data || {});
    const languages = buildAdaptiveLanguageOptions(data || {}, deck);

    flash.lastData = data || {};
    flash.allDeck = deck;
    flash.languages = languages;

    const validLangs = new Set(['all', ...languages.map(item => item.lang)]);
    if (!validLangs.has(flash.langFilter)) flash.langFilter = 'all';

    flash.deck = getAdaptiveFilteredDeck();
    renderAdaptiveLanguageFilters();

    if (!flash.deck.length) {
        flash.index = 0;
        flash.flipped = false;
        refreshAdaptiveFlashcardView();
        return;
    }

    const previousIndex = previousId
        ? flash.deck.findIndex(item => Number(item?.id || 0) === previousId)
        : -1;
    flash.index = previousIndex >= 0
        ? previousIndex
        : Math.max(0, Math.min(flash.index, flash.deck.length - 1));
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
        const filteredLabel = flash.langFilter === 'all'
            ? (state.uiLang === 'en' ? 'yet' : 'ainda')
            : state.uiLang === 'en'
                ? `for ${formatAdaptiveLanguageLabel(flash.langFilter)}`
                : `para ${formatAdaptiveLanguageLabel(flash.langFilter)}`;
        meta.textContent = `0 cartas${flash.languages.length ? ` · ${flash.languages.length} idioma(s)` : ''}`;
        meta.textContent = state.uiLang === 'en'
            ? `0 cards${flash.languages.length ? ` · ${flash.languages.length} language(s)` : ''}`
            : `0 cartas${flash.languages.length ? ` · ${flash.languages.length} idioma(s)` : ''}`;
        hint.textContent = state.uiLang === 'en'
            ? `No flashcards available ${filteredLabel}. Generate analyses, lessons, or attempts to feed the database.`
            : `Nenhum flashcard disponível ${filteredLabel}. Gere análises, aulas ou tentativas para alimentar o banco.`;
        front.innerHTML = `
            <div class="adaptive-flashcard-empty">
                <strong>${escapeHtml(state.uiLang === 'en' ? 'No cards to review.' : 'Sem cartas para revisar.')}</strong>
                <span>${escapeHtml(state.uiLang === 'en' ? 'The database has not returned enough items for this language filter yet.' : 'O banco ainda não devolveu itens suficientes para este filtro de idioma.')}</span>
            </div>
        `;
        back.innerHTML = '';
        card.classList.remove('is-flipped', 'is-loading');
        card.classList.add('is-empty');
        if (prev) prev.disabled = true;
        if (next) next.disabled = true;
        if (flip) {
            flip.disabled = true;
            flip.textContent = t('progress.flip');
        }
        [again, hard, good, easy].forEach(btn => {
            if (btn) btn.disabled = true;
        });
        return;
    }

    const itemLang = normalizeAdaptiveLangCode(current.target_lang, 'en');
    const mastery = Math.round(Number(current.mastery_score || 0) * 100);
    const seenCount = Number(current.seen_count || 0);
    const successCount = Number(current.success_count || 0);
    const typeLabel = escapeHtml(formatAdaptiveSkillLabel(current));
    const sourceLabel = escapeHtml(formatAdaptiveItemSourceLabel(current));
    const languageLabel = escapeHtml(formatAdaptiveLanguageLabel(itemLang));
    const bucketLabel = escapeHtml(formatAdaptiveDeckBucketLabel(current.deck_bucket));
    const dueLabel = escapeHtml(formatAdaptiveDueLabel(current.next_due_at));
    const translation = escapeHtml(current.translation || 'Sem tradução salva ainda.');
    const context = escapeHtml(current.context_text || 'Sem contexto salvo ainda.');
    const notes = escapeHtml(current.notes || 'Sem observação adicional.');
    const phoneticRaw = current?.metadata?.phonetic || '';
    const phonetic = escapeHtml(phoneticRaw || 'Sem guia de pronúncia salvo.');
    const preview = escapeHtml(
        summarizeAdaptiveText(
            current.translation || current.context_text || current.notes || '',
            160,
        ) || 'Toque para abrir os detalhes completos da revisão.'
    );
    const retentionLabel = seenCount > 0
        ? (
            state.uiLang === 'en'
                ? `${successCount}/${Math.max(1, seenCount)} successes`
                : `${successCount}/${Math.max(1, seenCount)} acertos`
        )
        : (state.uiLang === 'en' ? 'No history yet' : 'Ainda sem histórico');

    meta.textContent = state.uiLang === 'en'
        ? `Card ${flash.index + 1}/${flash.deck.length} · ${languageLabel}`
        : `Carta ${flash.index + 1}/${flash.deck.length} · ${languageLabel}`;
    hint.textContent = flash.submitting
        ? (state.uiLang === 'en' ? 'Saving review result...' : 'Salvando resultado da revisão...')
        : (
            flash.flipped
                ? (state.uiLang === 'en' ? 'Grade your recall to update spacing in the database.' : 'Classifique a lembrança para atualizar o espaçamento no banco.')
                : (state.uiLang === 'en' ? 'Click the card to see meaning, pronunciation, context, and source.' : 'Clique na carta para ver significado, pronúncia, contexto e origem do item.')
        );

    front.innerHTML = `
        <div class="adaptive-flashcard-kicker">
            <div class="adaptive-flashcard-badges">
                <span class="badge badge-sm">${languageLabel}</span>
                <span class="badge badge-sm">${typeLabel}</span>
                <span class="badge badge-sm">${bucketLabel}</span>
            </div>
            <span>${dueLabel}</span>
        </div>
        <div class="adaptive-flashcard-text">${escapeHtml(current.source_text || 'Sem conteúdo')}</div>
        <div class="adaptive-flashcard-pron">${phoneticRaw ? phonetic : sourceLabel}</div>
        <div class="adaptive-flashcard-preview">${preview}</div>
        <div class="adaptive-flashcard-foot">
            <span>${state.uiLang === 'en' ? 'Mastery' : 'Maestria'} ${mastery}%</span>
            <span>${seenCount} ${state.uiLang === 'en' ? 'reviews' : 'revisões'}</span>
            <span>${sourceLabel}</span>
            <span>${state.uiLang === 'en' ? 'Tap to flip' : 'Toque para virar'}</span>
        </div>
    `;
    back.innerHTML = `
        <div class="adaptive-flashcard-kicker">
            <div class="adaptive-flashcard-badges">
                <span class="badge badge-sm">${languageLabel}</span>
                <span class="badge badge-sm">${typeLabel}</span>
            </div>
            <span>${current.interval_days || 0}${state.uiLang === 'en' ? 'd interval' : 'd de intervalo'}</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">${state.uiLang === 'en' ? 'Meaning' : 'Significado'}</span>
            <strong>${translation}</strong>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">${state.uiLang === 'en' ? 'Pronunciation / clue' : 'Pronúncia / pista'}</span>
            <span>${phonetic}</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">${state.uiLang === 'en' ? 'Context' : 'Contexto'}</span>
            <span>${context}</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">${state.uiLang === 'en' ? 'How to review' : 'Como revisar'}</span>
            <span>${notes}</span>
        </div>
        <div class="adaptive-flashcard-block">
            <span class="adaptive-flashcard-label">${state.uiLang === 'en' ? 'Item source' : 'Origem do item'}</span>
            <span>${sourceLabel}</span>
        </div>
        <div class="adaptive-flashcard-foot">
            <span>${retentionLabel}</span>
            <span>${state.uiLang === 'en' ? 'Mastery' : 'Maestria'} ${mastery}%</span>
            <span>${dueLabel}</span>
            <span>${state.uiLang === 'en' ? 'Grade it now' : 'Agora classifique'}</span>
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
    const languageBreakdown = Array.isArray(data?.language_breakdown) ? data.language_breakdown : [];
    $('#adaptive-pron-score').textContent = Number(summary.pronunciation_avg_score || 0).toFixed(1);
    $('#adaptive-review-due').textContent = Number(summary.review_due || 0);
    $('#adaptive-tracked-items').textContent = Number(summary.tracked_items || 0);
    $('#adaptive-active-days').textContent = Number(summary.active_days_7d || 0);

    const learnerMeta = $('#adaptive-learner-meta');
    if (learnerMeta) {
        const learner = data?.learner || {};
        const studiedLanguages = languageBreakdown.length
            ? (
                state.uiLang === 'en'
                    ? `Languages in deck: ${languageBreakdown.map(item => formatAdaptiveLanguageLabel(item.target_lang || 'en')).join(', ')}`
                    : `Idiomas no banco: ${languageBreakdown.map(item => formatAdaptiveLanguageLabel(item.target_lang || 'en')).join(', ')}`
            )
            : '';
        const bits = [
            learner?.target_lang ? `${state.uiLang === 'en' ? 'Language' : 'Idioma'}: ${String(learner.target_lang).toUpperCase()}` : '',
            learner?.level ? `${state.uiLang === 'en' ? 'Level' : 'Nível'}: ${learner.level}` : '',
            studiedLanguages,
            summary?.last_activity_at ? `${state.uiLang === 'en' ? 'Last activity' : 'Última atividade'}: ${new Date(summary.last_activity_at).toLocaleString(state.uiLang === 'en' ? 'en-US' : 'pt-BR')}` : '',
        ].filter(Boolean);
        learnerMeta.textContent = bits.join(' · ') || t('progress.adaptiveIdle');
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
                <span class="badge badge-sm">${escapeHtml(formatAdaptiveLanguageLabel(item.target_lang || 'en'))}</span>
                <span class="badge badge-sm">${escapeHtml(formatAdaptiveSkillLabel(item))}</span>
                <span>${state.uiLang === 'en' ? 'Mastery' : 'Maestria'} ${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
                ${item.translation ? `<span>${escapeHtml(item.translation)}</span>` : ''}
            </div>
            ${item.notes ? `<div class="adaptive-item-note">${escapeHtml(item.notes)}</div>` : ''}
        </div>
    `, state.uiLang === 'en' ? 'No items are due for review today.' : 'Nenhum item vencido para revisão hoje.');

    renderAdaptiveList('#adaptive-recommendations', data?.recommendations, item => `
        <div class="adaptive-item">
            <div class="adaptive-item-title">${escapeHtml(item.title || '')}</div>
            <div class="adaptive-item-note">${escapeHtml(item.reason || '')}</div>
            <div class="adaptive-item-meta">
                <span class="badge badge-sm">${escapeHtml(formatAdaptiveLanguageLabel(item.target_lang || 'en'))}</span>
                <span class="badge badge-sm">${escapeHtml(item.kind || 'coach')}</span>
                <span>${escapeHtml(item.skill_area || 'general')}</span>
            </div>
        </div>
    `, state.uiLang === 'en' ? 'Next actions will show up once there is enough history.' : 'As próximas ações vão aparecer assim que houver histórico suficiente.');

    renderAdaptiveList('#adaptive-weak-points', data?.weak_points, item => `
        <div class="adaptive-pill">
            <span>${escapeHtml(formatAdaptiveLanguageLabel(item.target_lang || 'en'))}</span>
            <strong>${escapeHtml(item.source_text || '')}</strong>
            <span>${escapeHtml(item.skill_area || 'general')}</span>
            <span>${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
        </div>
    `, state.uiLang === 'en' ? 'Your weak points will show up here as the system learns from you.' : 'Seus pontos fracos aparecem aqui conforme o sistema aprende com você.');

    renderAdaptiveList('#adaptive-strengths', data?.strengths, item => `
        <div class="adaptive-pill adaptive-pill-strong">
            <span>${escapeHtml(formatAdaptiveLanguageLabel(item.target_lang || 'en'))}</span>
            <strong>${escapeHtml(item.source_text || '')}</strong>
            <span>${escapeHtml(item.skill_area || 'general')}</span>
            <span>${Math.round(Number(item.mastery_score || 0) * 100)}%</span>
        </div>
    `, state.uiLang === 'en' ? 'Your strengths will appear here after a few successful reviews.' : 'Seus pontos fortes aparecem aqui após algumas revisões bem-sucedidas.');
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
            el.textContent = t('misc.cacheFiles', { count: stats.file_count, size: stats.total_size_mb });
            el.classList.add('has-files');
        } else {
            el.textContent = t('misc.cacheClean');
            el.classList.remove('has-files');
        }
    } catch {}
}

if ($('#btn-cleanup')) {
    $('#btn-cleanup').addEventListener('click', async () => {
        if (!confirm(t('misc.cleanupConfirm'))) return;
        try {
            const res = await fetch('/api/cleanup', { method: 'POST' });
            const data = await res.json();
            loadDiskStats();
            alert(t('misc.cleanupRemoved', { count: data.removed }));
        } catch { alert(t('misc.cleanupError')); }
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
const CONV_LANG_LABELS = {
    en: '🇺🇸 English',
    pt: '🇧🇷 Português',
    es: '🇪🇸 Español',
    fr: '🇫🇷 Français',
    de: '🇩🇪 Deutsch',
    it: '🇮🇹 Italiano',
};

const CONV_SCENARIO_LABELS = {
    casual: 'Casual',
    travel: 'Viagem',
    work: 'Trabalho',
    interview: 'Entrevista',
    tech: 'Tecnologia',
    daily: 'Rotina',
};

const CONV_GOAL_LABELS = {
    flow: 'Fluidez',
    confidence: 'Confiança',
    vocabulary: 'Vocabulário',
    opinions: 'Opiniões',
};

const CONV_SCENARIO_STARTERS = {
    en: {
        casual: [
            'How has your week been going lately?',
            'What have you been enjoying these days?',
        ],
        travel: [
            'What is the first place I should visit here?',
            'Do you usually travel with a plan or improvise?',
        ],
        work: [
            'What kind of projects are you working on now?',
            'How do you usually organize your day at work?',
        ],
        interview: [
            'Could you tell me a little about your background?',
            'What kind of role are you looking for right now?',
        ],
        tech: [
            'What app or tool do you use every single day?',
            'Which technology are you most curious about lately?',
        ],
        daily: [
            'What does your morning routine look like?',
            'What habit are you trying to improve this month?',
        ],
    },
    pt: {
        casual: [
            'Como tem sido a sua semana ultimamente?',
            'O que voce tem gostado de fazer esses dias?',
        ],
        travel: [
            'Qual e o primeiro lugar que eu deveria visitar aqui?',
            'Voce costuma viajar com plano ou improvisa?',
        ],
        work: [
            'Em que tipo de projeto voce esta trabalhando agora?',
            'Como voce costuma organizar o seu dia no trabalho?',
        ],
        interview: [
            'Voce pode me contar um pouco sobre a sua experiencia?',
            'Que tipo de vaga voce esta buscando agora?',
        ],
        tech: [
            'Qual aplicativo ou ferramenta voce usa todo dia?',
            'Sobre qual tecnologia voce esta mais curioso ultimamente?',
        ],
        daily: [
            'Como e a sua rotina de manha?',
            'Que habito voce esta tentando melhorar este mes?',
        ],
    },
    es: {
        casual: [
            'Como ha ido tu semana ultimamente?',
            'Que has estado disfrutando estos dias?',
        ],
        travel: [
            'Cual es el primer lugar que deberia visitar aqui?',
            'Sueles viajar con un plan o improvisas?',
        ],
        work: [
            'En que tipo de proyecto estas trabajando ahora?',
            'Como organizas normalmente tu dia de trabajo?',
        ],
        interview: [
            'Podrias contarme un poco sobre tu experiencia?',
            'Que tipo de puesto estas buscando ahora?',
        ],
        tech: [
            'Que aplicacion o herramienta usas todos los dias?',
            'Que tecnologia te da mas curiosidad ultimamente?',
        ],
        daily: [
            'Como es tu rutina por la manana?',
            'Que habito intentas mejorar este mes?',
        ],
    },
    fr: {
        casual: [
            'Comment se passe ta semaine en ce moment ?',
            'Qu est-ce que tu aimes faire ces jours-ci ?',
        ],
        travel: [
            'Quel est le premier endroit que je devrais visiter ici ?',
            'Tu voyages plutot avec un plan ou tu improvises ?',
        ],
        work: [
            'Sur quel type de projet travailles-tu en ce moment ?',
            'Comment organises-tu normalement ta journee de travail ?',
        ],
        interview: [
            'Peux-tu me parler un peu de ton parcours ?',
            'Quel type de poste recherches-tu maintenant ?',
        ],
        tech: [
            'Quelle application ou quel outil utilises-tu tous les jours ?',
            'Quelle technologie t interesse le plus en ce moment ?',
        ],
        daily: [
            'A quoi ressemble ta routine du matin ?',
            'Quelle habitude essaies-tu d ameliorer ce mois-ci ?',
        ],
    },
    de: {
        casual: [
            'Wie laeuft deine Woche im Moment?',
            'Was machst du in letzter Zeit besonders gern?',
        ],
        travel: [
            'Welchen Ort sollte ich hier als Erstes besuchen?',
            'Reist du lieber mit Plan oder spontan?',
        ],
        work: [
            'An welcher Art von Projekten arbeitest du gerade?',
            'Wie organisierst du normalerweise deinen Arbeitstag?',
        ],
        interview: [
            'Kannst du mir ein bisschen ueber deinen Hintergrund erzaehlen?',
            'Welche Art von Stelle suchst du gerade?',
        ],
        tech: [
            'Welche App oder welches Tool benutzt du jeden Tag?',
            'Welche Technologie findest du im Moment am spannendsten?',
        ],
        daily: [
            'Wie sieht deine Morgenroutine aus?',
            'Welche Gewohnheit willst du diesen Monat verbessern?',
        ],
    },
    it: {
        casual: [
            'Come sta andando la tua settimana ultimamente?',
            'Che cosa ti sta piacendo fare in questi giorni?',
        ],
        travel: [
            'Qual e il primo posto che dovrei visitare qui?',
            'Di solito viaggi con un piano o improvvisi?',
        ],
        work: [
            'Su che tipo di progetto stai lavorando adesso?',
            'Come organizzi di solito la tua giornata di lavoro?',
        ],
        interview: [
            'Puoi raccontarmi qualcosa del tuo percorso?',
            'Che tipo di ruolo stai cercando in questo momento?',
        ],
        tech: [
            'Quale app o strumento usi ogni giorno?',
            'Quale tecnologia ti incuriosisce di piu ultimamente?',
        ],
        daily: [
            'Com e la tua routine del mattino?',
            'Quale abitudine stai cercando di migliorare questo mese?',
        ],
    },
};

const convState = {
    mediaRecorder: null,
    audioChunks:   [],
    isRecording:   false,
    isLoading:     false,
    history:       [],
    turnCount:     0,
    lastProvider:  '',
    lastTtsEngine: '',
    lastInputMode: 'idle',
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
    $('#conv-send-btn')?.addEventListener('click', sendConvTextMessage);
    $('#conv-lesson-btn')?.addEventListener('click', generateLesson);
    $('#lesson-modal-close')?.addEventListener('click', closeLessonModal);
    $('#lesson-modal')?.addEventListener('click', function(e) {
        if (e.target === this) closeLessonModal();
    });
    $('#conv-suggest-toggle')?.addEventListener('change', function() {
        toggleConversationCoachVisibility(this.checked);
    });
    $('#conv-text-input')?.addEventListener('keydown', event => {
        if (event.key !== 'Enter' || event.shiftKey) return;
        event.preventDefault();
        sendConvTextMessage();
    });
    ['#conv-lang', '#conv-scenario', '#conv-goal', '#conv-voice', '#conv-tts-engine', '#conv-translate-to'].forEach(selector => {
        $(selector)?.addEventListener('change', () => {
            if (selector === '#conv-lang' || selector === '#conv-scenario' || selector === '#conv-goal') {
                renderConvStarterChips();
            }
            updateConversationSessionUi();
        });
    });
    $('#conv-auto-send-toggle')?.addEventListener('change', () => {
        if (convState.isRecording) setConvUiState('recording');
        else updateConversationSessionUi();
    });
    toggleConversationCoachVisibility($('#conv-suggest-toggle')?.checked || false);
    updateConversationSessionUi();
    renderConvStarterChips();
});

function getConversationSelections() {
    return {
        lang: $('#conv-lang')?.value || 'en',
        scenario: $('#conv-scenario')?.value || 'casual',
        goal: $('#conv-goal')?.value || 'flow',
    };
}

function formatConvProviderLabel(provider) {
    const normalized = String(provider || '').trim().toLowerCase();
    return ({
        deepseek: 'DeepSeek',
        openrouter: 'OpenRouter',
        openai: 'OpenAI',
        ollama: 'Ollama',
        fallback: 'Fallback',
        fallback_local: 'Local',
    })[normalized] || (provider || 'IA');
}

function formatConvTtsLabel(engine) {
    const normalized = String(engine || '').trim().toLowerCase();
    return ({
        lmnt: 'LMNT',
        deepgram: 'Deepgram',
        piper: 'Piper',
        local: 'Piper',
    })[normalized] || (engine || '');
}

function getSelectedOptionText(selector, fallback = '') {
    const select = $(selector);
    if (!select || typeof select.selectedIndex !== 'number' || select.selectedIndex < 0) return fallback;
    return select.options?.[select.selectedIndex]?.textContent?.trim() || fallback;
}

function getConversationVoiceLabel() {
    return getSelectedOptionText('#conv-voice', 'Leah').replace(/\s*\([^)]*\)\s*$/, '').trim() || 'Leah';
}

function getConversationTranslateLabel() {
    const value = $('#conv-translate-to')?.value || 'pt';
    return getLanguageLabel(value, { mode: 'display', withFlag: true }) || getSelectedOptionText('#conv-translate-to', 'Português');
}

function getConvStarterPhrases(lang, scenario) {
    const normalizedLang = String(lang || 'en').trim().toLowerCase();
    const normalizedScenario = String(scenario || 'casual').trim().toLowerCase();
    const byLang = CONV_SCENARIO_STARTERS[normalizedLang] || CONV_SCENARIO_STARTERS.en;
    const selected = byLang[normalizedScenario] || byLang.casual || [];
    const generic = {
        en: ['Can you explain that in a simple way?', 'What do you think about that?'],
        pt: ['Pode explicar isso de um jeito simples?', 'O que voce acha disso?'],
        es: ['Puedes explicar eso de una forma simple?', 'Que opinas de eso?'],
        fr: ['Tu peux expliquer cela simplement ?', 'Qu en penses-tu ?'],
        de: ['Kannst du das einfach erklaeren?', 'Was denkst du darueber?'],
        it: ['Puoi spiegarlo in modo semplice?', 'Che cosa ne pensi?'],
    }[normalizedLang] || ['Can you explain that in a simple way?', 'What do you think about that?'];
    return [...selected, ...generic].slice(0, 4);
}

function getConversationPowerPhrases(lang) {
    const normalizedLang = String(lang || 'en').trim().toLowerCase();
    const bank = {
        en: {
            followUp: 'Interesting. Can you tell me a bit more about that?',
            example: 'Can you give me a concrete example?',
            scenarios: {
                casual: 'Lately, I have been enjoying ...',
                travel: 'When I travel, I usually look for ...',
                work: 'At work, I usually focus on ...',
                interview: 'One strength I would highlight is ...',
                tech: 'The tool I rely on most is ...',
                daily: 'In my routine, the hardest part is ...',
            },
            goals: {
                flow: 'That makes sense. In my case, ...',
                confidence: 'I am not completely sure, but I would say ...',
                vocabulary: 'What would be a more natural way to say that?',
                opinions: 'I partly agree, but I also think ...',
            },
        },
        pt: {
            followUp: 'Interessante. Pode me contar um pouco mais sobre isso?',
            example: 'Pode me dar um exemplo mais concreto?',
            scenarios: {
                casual: 'Ultimamente, eu tenho gostado bastante de ...',
                travel: 'Quando eu viajo, eu normalmente procuro ...',
                work: 'No trabalho, eu costumo focar em ...',
                interview: 'Um ponto forte que eu destacaria é ...',
                tech: 'A ferramenta em que eu mais confio é ...',
                daily: 'Na minha rotina, a parte mais difícil é ...',
            },
            goals: {
                flow: 'Faz sentido. No meu caso, ...',
                confidence: 'Não tenho 100% de certeza, mas eu diria que ...',
                vocabulary: 'Qual seria uma forma mais natural de dizer isso?',
                opinions: 'Eu concordo em parte, mas também acho que ...',
            },
        },
        es: {
            followUp: 'Interesante. ¿Puedes contarme un poco más sobre eso?',
            example: '¿Puedes darme un ejemplo más concreto?',
            scenarios: {
                casual: 'Últimamente, he estado disfrutando mucho de ...',
                travel: 'Cuando viajo, suelo buscar ...',
                work: 'En el trabajo, normalmente me enfoco en ...',
                interview: 'Una fortaleza que destacaría es ...',
                tech: 'La herramienta en la que más confío es ...',
                daily: 'En mi rutina, la parte más difícil es ...',
            },
            goals: {
                flow: 'Tiene sentido. En mi caso, ...',
                confidence: 'No estoy cien por cien seguro, pero diría que ...',
                vocabulary: '¿Cuál sería una forma más natural de decir eso?',
                opinions: 'Estoy de acuerdo en parte, pero también creo que ...',
            },
        },
        fr: {
            followUp: 'Intéressant. Tu peux m en dire un peu plus ?',
            example: 'Tu peux me donner un exemple plus concret ?',
            scenarios: {
                casual: 'En ce moment, j aime beaucoup ...',
                travel: 'Quand je voyage, je cherche surtout ...',
                work: 'Au travail, je me concentre surtout sur ...',
                interview: 'Un point fort que je mettrais en avant, c est ...',
                tech: 'L outil sur lequel je compte le plus, c est ...',
                daily: 'Dans ma routine, la partie la plus difficile, c est ...',
            },
            goals: {
                flow: 'Je vois. Dans mon cas, ...',
                confidence: 'Je ne suis pas totalement sûr, mais je dirais que ...',
                vocabulary: 'Quelle serait une façon plus naturelle de dire cela ?',
                opinions: 'Je suis d accord en partie, mais je pense aussi que ...',
            },
        },
        de: {
            followUp: 'Interessant. Kannst du mir noch ein bisschen mehr dazu sagen?',
            example: 'Kannst du mir ein konkreteres Beispiel geben?',
            scenarios: {
                casual: 'In letzter Zeit mache ich besonders gern ...',
                travel: 'Wenn ich reise, suche ich normalerweise nach ...',
                work: 'Bei der Arbeit konzentriere ich mich meistens auf ...',
                interview: 'Eine Stärke, die ich hervorheben würde, ist ...',
                tech: 'Das Tool, auf das ich mich am meisten verlasse, ist ...',
                daily: 'In meiner Routine ist der schwierigste Teil ...',
            },
            goals: {
                flow: 'Das ergibt Sinn. Bei mir ist es so, dass ...',
                confidence: 'Ich bin mir nicht ganz sicher, aber ich würde sagen, dass ...',
                vocabulary: 'Wie könnte man das noch natürlicher sagen?',
                opinions: 'Ich stimme teilweise zu, aber ich denke auch, dass ...',
            },
        },
        it: {
            followUp: 'Interessante. Puoi dirmi qualcosa in più su questo?',
            example: 'Puoi farmi un esempio più concreto?',
            scenarios: {
                casual: 'Ultimamente mi sta piacendo molto ...',
                travel: 'Quando viaggio, di solito cerco ...',
                work: 'Al lavoro di solito mi concentro su ...',
                interview: 'Un punto di forza che metterei in evidenza è ...',
                tech: 'Lo strumento su cui faccio più affidamento è ...',
                daily: 'Nella mia routine, la parte più difficile è ...',
            },
            goals: {
                flow: 'Ha senso. Nel mio caso, ...',
                confidence: 'Non sono del tutto sicuro, ma direi che ...',
                vocabulary: 'Quale sarebbe un modo più naturale per dirlo?',
                opinions: 'Sono d accordo in parte, ma penso anche che ...',
            },
        },
    };
    return bank[normalizedLang] || bank.en;
}

function getConversationPowerActions() {
    const { lang, scenario, goal } = getConversationSelections();
    const turnCount = convState.history.filter(item => item?.role === 'user').length;
    const starters = getConvStarterPhrases(lang, scenario);
    const phrasing = getConversationPowerPhrases(lang);
    const scenarioPhrase = phrasing.scenarios?.[scenario] || starters[0] || '';
    const goalPhrase = phrasing.goals?.[goal] || starters[1] || '';
    const rawActions = turnCount
        ? [
            { text: phrasing.followUp, meta: t('conversation.moveFollowUp') },
            { text: scenarioPhrase, meta: t('conversation.movePersonal') },
            { text: goalPhrase, meta: t('conversation.moveGoal') },
            { text: phrasing.example, meta: t('conversation.moveExample') },
        ]
        : [
            { text: starters[0] || scenarioPhrase, meta: t('conversation.moveOpen') },
            { text: starters[1] || phrasing.followUp, meta: t('conversation.moveOpen') },
            { text: scenarioPhrase, meta: t('conversation.movePersonal') },
            { text: goalPhrase, meta: t('conversation.moveGoal') },
        ];

    const seen = new Set();
    return rawActions.filter(action => {
        const normalizedText = String(action?.text || '').trim();
        if (!normalizedText || seen.has(normalizedText)) return false;
        seen.add(normalizedText);
        action.text = normalizedText;
        return true;
    }).slice(0, 4);
}

function renderConversationPowerActions() {
    const container = $('#conv-power-actions');
    if (!container) return;
    const badge = $('#conv-actions-badge');
    const actions = getConversationPowerActions();
    if (badge) {
        badge.textContent = actions.length
            ? t('conversation.actionsCount', { count: actions.length })
            : t('conversation.actionsBadge');
    }
    container.innerHTML = actions.map(action => `
        <button class="conv-power-btn" type="button" onclick="convPowerActionClick(decodeURIComponent('${encodeURIComponent(action.text)}'))">
            <span class="conv-power-btn-label">${escapeHtml(action.text)}</span>
            <span class="conv-power-btn-meta">${escapeHtml(action.meta || t('conversation.actionsMeta'))}</span>
        </button>
    `).join('');
}

function toggleConversationCoachVisibility(forceChecked = null) {
    const card = $('#conv-colinha-card');
    if (!card) return;
    const checked = typeof forceChecked === 'boolean'
        ? forceChecked
        : ($('#conv-suggest-toggle')?.checked || false);
    card.classList.toggle('hidden', !checked);
}

function convPowerActionClick(text) {
    useConversationDraft(text, { speak: false });
}

function convBubbleActionClick(text) {
    useConversationDraft(text, { speak: false });
}

function renderConvStarterChips() {
    const container = $('#conv-starters');
    if (!container) return;
    const { lang, scenario } = getConversationSelections();
    const label = getConversationScenarioLabel(scenario) || 'Casual';
    const starters = getConvStarterPhrases(lang, scenario);
    container.innerHTML = starters.map(text => `
        <button class="conv-chip conv-starter-chip" type="button" onclick="convStarterClick(decodeURIComponent('${encodeURIComponent(text)}'))">
            <span>${escapeHtml(text)}</span>
            <small>${escapeHtml(t('conversation.openScenario', { scenario: label.toLowerCase() }))}</small>
        </button>
    `).join('');
}

function updateConversationSessionUi() {
    const { lang, scenario, goal } = getConversationSelections();
    const scenarioLabel = getConversationScenarioLabel(scenario) || 'Casual';
    const goalLabel = getConversationGoalLabel(goal) || t('conversation.ready');
    const langLabel = getLanguageLabel(lang, { mode: 'native', withFlag: true }) || String(lang || 'EN').toUpperCase();
    const turnCount = convState.history.filter(item => item?.role === 'user').length;
    convState.turnCount = turnCount;

    const modeLabel = convState.isRecording
        ? (state.uiLang === 'en' ? 'Recording' : 'Gravando')
        : convState.isLoading
            ? (state.uiLang === 'en' ? 'Processing' : 'Processando')
            : convState.lastInputMode === 'voice'
                ? (state.uiLang === 'en' ? 'Voice' : 'Voz')
                : convState.lastInputMode === 'text'
                    ? (state.uiLang === 'en' ? 'Text' : 'Texto')
                    : t('conversation.ready');

    const engineParts = [];
    if (convState.lastProvider) engineParts.push(formatConvProviderLabel(convState.lastProvider));
    if (convState.lastTtsEngine) engineParts.push(formatConvTtsLabel(convState.lastTtsEngine));
    const engineSummary = engineParts.length ? engineParts.join(' · ') : t('conversation.noReplies');
    const paceLabel = convState.isRecording
        ? t('conversation.paceRecording')
        : convState.isLoading
            ? t('conversation.paceLoading')
            : turnCount
                ? t('conversation.paceActive')
                : t('conversation.paceReady');
    const nextStep = convState.isRecording
        ? t('conversation.nextStepRecording')
        : convState.isLoading
            ? t('conversation.nextStepLoading')
            : turnCount
                ? t('conversation.nextStepActive')
                : t('conversation.nextStepIdle');
    const partnerValue = [getConversationVoiceLabel(), formatConvTtsLabel($('#conv-tts-engine')?.value || '')]
        .filter(Boolean)
        .join(' · ');
    const partnerStatus = t('conversation.partnerStatus', {
        lang: langLabel,
        scenario: scenarioLabel,
        goal: goalLabel,
        translate: getConversationTranslateLabel(),
    });

    $('#conv-active-scenario').textContent = t('conversation.scenarioBadge', { value: scenarioLabel });
    $('#conv-active-goal').textContent = t('conversation.goalBadge', { value: goalLabel });
    $('#conv-engine-badge').textContent = engineSummary;
    $('#conv-turn-count').textContent = String(turnCount);
    $('#conv-input-mode').textContent = modeLabel;
    $('#conv-lang-badge').textContent = langLabel;
    $('#conv-primary-status-label').textContent = t('conversation.partnerLabel');
    $('#conv-primary-status-value').textContent = partnerValue || 'Alex';
    $('#conv-primary-status-note').textContent = partnerStatus;
    $('#conv-dialogue-title').textContent = t('conversation.dialogueTitle');
    $('#conv-dialogue-hint').textContent = t('conversation.dialogueHint');
    $('#conv-feed-badge').textContent = t('conversation.feedBadge', { turns: turnCount });
    $('#conv-compass-title').textContent = t('conversation.compassTitle');
    $('#conv-pace-badge').textContent = paceLabel;
    $('#conv-next-step').textContent = nextStep;
    $('#conv-guide-goal-label').textContent = t('conversation.goalMini');
    $('#conv-guide-goal-value').textContent = goalLabel;
    $('#conv-guide-scene-label').textContent = t('conversation.scenarioMini');
    $('#conv-guide-scene-value').textContent = scenarioLabel;
    $('#conv-actions-title').textContent = t('conversation.actionsTitle');
    $('#conv-actions-hint').textContent = t('conversation.actionsHint');
    $('#conv-advanced-title').textContent = t('conversation.advancedTitle');
    $('#conv-advanced-hint').textContent = t('conversation.advancedHint');

    const summary = turnCount
        ? t('conversation.summaryActive', { lang: langLabel, scenario: scenarioLabel.toLowerCase(), goal: goalLabel.toLowerCase(), turns: turnCount })
        : t('conversation.summaryIdle', { lang: langLabel, scenario: scenarioLabel.toLowerCase(), goal: goalLabel.toLowerCase() });
    $('#conv-summary-text').textContent = summary;
    $('#conv-engine-status').textContent = turnCount
        ? t('conversation.lastResponse', { engine: engineSummary })
        : `${t('conversation.noReplies')}.`;
    renderConversationPowerActions();
    toggleConversationCoachVisibility();
}

function useConversationDraft(text, { speak = false } = {}) {
    const input = $('#conv-text-input');
    if (input) {
        input.value = String(text || '').trim();
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
    }
    if (speak && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const lang = $('#conv-lang')?.value || 'en';
        const utterance = new SpeechSynthesisUtterance(String(text || ''));
        utterance.lang = lang;
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }
}

function convStarterClick(text) {
    useConversationDraft(text, { speak: true });
}

function buildConversationRequestPayload({ audio_b64 = '', text = '' } = {}) {
    const { lang, scenario, goal } = getConversationSelections();
    return {
        audio_b64,
        text,
        lang,
        scenario,
        goal,
        voice: $('#conv-voice')?.value || 'leah',
        tts_engine: ($('#conv-tts-engine')?.value || 'lmnt').trim().toLowerCase() || 'lmnt',
        history: convState.history,
        suggest: $('#conv-suggest-toggle')?.checked || false,
    };
}

function applyConversationTurn(data, inputMode) {
    const empty = $('#conv-empty');
    if (empty) empty.style.display = 'none';

    convState.history.push({ role: 'user', content: data.user_text });
    convState.history.push({ role: 'assistant', content: data.ai_text });
    if (convState.history.length > 20) convState.history = convState.history.slice(-20);

    convState.lastProvider = data.provider || '';
    convState.lastTtsEngine = data.tts_engine || '';
    convState.lastInputMode = inputMode;

    appendConvBubble('user', data.user_text, null, { mode: inputMode });
    appendConvBubble('ai', data.ai_text, data.audio_url, {
        provider: data.provider || '',
        ttsEngine: data.tts_engine || '',
    });

    if (data.warning) appendConvInfo(data.warning);

    if (data.suggestions) updateConvColinha(data.suggestions);
    else clearColinhaLoading();

    updateConversationSessionUi();

    if (data.audio_url) {
        new Audio(data.audio_url).play().catch(() => {});
    }
}

async function sendConvTextMessage() {
    if (convState.isLoading || convState.isRecording) return;
    const input = $('#conv-text-input');
    const text = String(input?.value || '').trim();
    if (!text) {
        input?.focus();
        setConvStatus(t('conversation.typePrompt'), 'loading');
        return;
    }

    convState.isLoading = true;
    setConvUiState('loading');
    if ($('#conv-suggest-toggle')?.checked) showColinhaLoading();

    try {
        const requestPayload = buildConversationRequestPayload({ text });
        const { result: data } = await runAgentWithFallback({
            intent: 'conversation',
            query: `conversa por texto: ${text}`,
            payload: { ...requestPayload, action: 'turn' },
            fallbackCall: () => postJson('/api/conversation', requestPayload),
            operation: 'conversation_turn',
        });
        if (data.error) {
            clearColinhaLoading();
            appendConvError(data.error);
            return;
        }
        if (input) input.value = '';
        applyConversationTurn(data, 'text');
    } catch (err) {
        clearColinhaLoading();
        appendConvError(t('conversation.networkError', { message: err.message }));
    } finally {
        convState.isLoading = false;
        setConvUiState('idle');
    }
}

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
        setConvStatus(t('conversation.micError', { message: err.message }), '');
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

        const suggest = document.getElementById('conv-suggest-toggle')?.checked || false;

        // Show loading chips if colinha active
        if (suggest) showColinhaLoading();

        const requestPayload = buildConversationRequestPayload({ audio_b64: b64 });
        const { result: data } = await runAgentWithFallback({
            intent: 'conversation',
            query: 'conversa por voz',
            payload: { ...requestPayload, action: 'turn' },
            fallbackCall: () => postJson('/api/conversation', requestPayload),
            operation: 'conversation_turn',
        });
        if (data.error) {
            clearColinhaLoading();
            appendConvError(data.error);
            return;
        }
        applyConversationTurn(data, 'voice');
    } catch (err) {
        clearColinhaLoading();
        appendConvError(t('conversation.networkError', { message: err.message }));
    } finally {
        convState.isLoading = false;
        setConvUiState('idle');
    }
}

function appendConvBubble(role, text, audioUrl, meta = {}) {
    const chat = document.getElementById('conv-chat');
    const wrap = document.createElement('div');
    wrap.className = `conv-bubble conv-bubble-${role}`;
    const label = role === 'user' ? t('conversation.user') : t('conversation.assistant');
    const metaParts = [];
    if (role === 'user' && meta.mode) {
        metaParts.push(meta.mode === 'voice' ? t('conversation.inputVoice') : t('conversation.inputText'));
    }
    if (role === 'ai' && meta.provider) {
        metaParts.push(formatConvProviderLabel(meta.provider));
    }
    if (role === 'ai' && meta.ttsEngine) {
        metaParts.push(formatConvTtsLabel(meta.ttsEngine));
    }
    const audioHtml = (audioUrl && role === 'ai')
        ? `<div class="conv-bubble-audio">
               <button class="conv-bubble-play" onclick="convPlayAudio(this,'${escapeHtml(audioUrl)}')">▶</button>
               <span style="font-size:.78rem;opacity:.7">${escapeHtml(state.uiLang === 'en' ? 'Listen again' : 'Ouvir novamente')}</span>
           </div>`
        : '';
    const actionLabel = role === 'ai' ? t('conversation.useReply') : t('conversation.reuseLine');
    const actionsHtml = text
        ? `<div class="conv-bubble-actions">
               <button class="conv-bubble-action" type="button" onclick="convBubbleActionClick(decodeURIComponent('${encodeURIComponent(String(text || ''))}'))">
                   ${escapeHtml(actionLabel)}
               </button>
           </div>`
        : '';
    wrap.innerHTML = `
        <div class="conv-bubble-header">
            <div class="conv-bubble-label">${label}</div>
            ${metaParts.length ? `<div class="conv-bubble-meta">${escapeHtml(metaParts.join(' · '))}</div>` : ''}
        </div>
        <div class="conv-bubble-text">${escapeHtml(text)}</div>
        ${audioHtml}
        ${actionsHtml}
    `;
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
    wrap.innerHTML = `
        <div class="conv-bubble-header">
            <div class="conv-bubble-label" style="color:var(--danger)">${escapeHtml(t('conversation.error'))}</div>
        </div>
        <div class="conv-bubble-text">${escapeHtml(msg)}</div>
    `;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function appendConvInfo(msg) {
    const chat = document.getElementById('conv-chat');
    const wrap = document.createElement('div');
    wrap.className = 'conv-bubble conv-bubble-ai';
    wrap.style.borderColor = 'var(--warn)';
    wrap.innerHTML = `
        <div class="conv-bubble-header">
            <div class="conv-bubble-label" style="color:var(--warn)">${escapeHtml(t('conversation.warning'))}</div>
        </div>
        <div class="conv-bubble-text">${escapeHtml(msg)}</div>
    `;
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

function clearConvChat() {
    convState.history = [];
    convState.turnCount = 0;
    convState.lastProvider = '';
    convState.lastTtsEngine = '';
    convState.lastInputMode = 'idle';
    document.getElementById('conv-chat').innerHTML = `
        <div class="conv-empty" id="conv-empty">
            <span class="conv-empty-icon">🎙️</span>
            <p>${escapeHtml(t('conversation.empty'))}</p>
        </div>`;
    clearColinhaLoading();
    const chips = document.getElementById('conv-chips');
    if (chips) chips.innerHTML = '';
    const empty = document.getElementById('conv-colinha-empty');
    if (empty) empty.style.display = '';
    const input = document.getElementById('conv-text-input');
    if (input) input.value = '';
    renderConvStarterChips();
    updateConversationSessionUi();
    setConvStatus(t('conversation.statusIdle'), '');
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
    useConversationDraft(text, { speak: true });
}

// ── Lesson generation ──────────────────────────────────────────
async function generateLesson() {
    if (!convState.history.length) {
        alert(t('conversation.lessonNeedHistory'));
        return;
    }
    const normalizedFocus = 'smart';
    const btn = document.getElementById('conv-lesson-btn');
    const lang        = document.getElementById('conv-lang')?.value        || 'en';
    const translate_to = document.getElementById('conv-translate-to')?.value || 'pt';
    const loadingLabel = t('conversation.lessonLoading');
    const defaultLabel = t('conversation.lesson');

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
        alert(`${t('conversation.error')}: ${e.message}`);
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = defaultLabel; }
    }
}

function closeLessonModal() {
    document.getElementById('lesson-modal')?.classList.add('hidden');
    document.body.style.overflow = '';
}

function renderLessonModal(data, lang, translateTo) {
    const langLabel  = getLanguageLabel(lang, { mode: 'native' }) || String(lang || '').toUpperCase();
    const transLabel = getLanguageLabel(translateTo, { mode: 'native' }) || String(translateTo || '').toUpperCase();
    const focusRaw = String(data?.lesson_focus || 'balanced').trim().toLowerCase();
    const focusRequested = String(data?.lesson_focus_requested || '').trim().toLowerCase();
    const focusMap = {
        smart: t('lesson.focusSmart'),
        balanced: t('lesson.focusBalanced'),
        corrections: t('lesson.focusCorrections'),
        vocabulary: t('lesson.focusVocabulary'),
    };
    const focusBase = focusMap[focusRaw] || '';
    const focusLabel = focusBase
        ? `${focusBase}${focusRequested === 'smart' ? ` (${t('lesson.focusAuto')})` : ''}`
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
        const extras = [providerLabel ? `${t('lesson.aiLabel')}: ${providerLabel}` : '', focusLabel].filter(Boolean).join(' · ');
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
            <h3>${escapeHtml(t('lesson.summary'))}</h3>
            <p class="lesson-summary">${escapeHtml(data.lesson.summary)}</p>
        </div>`;
    }

    // Transcript
    if (data.transcript?.length) {
        const rows = data.transcript.map(t => {
            const isUser  = t.role === 'user';
            const roleHtml = isUser
                ? `<span class="lesson-role-user">${escapeHtml(t('lesson.you'))}</span>`
                : `<span class="lesson-role-ai">${escapeHtml(t('lesson.ai'))}</span>`;
            return `<tr>
                <td>${roleHtml}</td>
                <td class="lesson-original">${escapeHtml(t.original || '')}</td>
                <td class="lesson-translation">${escapeHtml(t.translation || '—')}</td>
            </tr>`;
        }).join('');
        html += `<div class="lesson-section">
            <h3>${escapeHtml(t('lesson.transcript'))}</h3>
            <table class="lesson-transcript">
                <thead><tr>
                    <th>${escapeHtml(t('lesson.speaker'))}</th>
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
            <h3>${escapeHtml(t('lesson.vocabulary'))}</h3>
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
            <h3>${escapeHtml(t('lesson.grammar'))}</h3>
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
            <h3>${escapeHtml(t('lesson.corrections'))}</h3>
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
            <h3>${escapeHtml(t('lesson.tips'))}</h3>
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
            <h3>${escapeHtml(t('lesson.replySuggestions'))}</h3>
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
            if (pronHasScore) parts.push(t('lesson.estimatedScore', { score: pronScore }));
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
            <h3>${escapeHtml(t('lesson.pronunciation'))}</h3>
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
            ? t('conversation.statusRecordingAuto')
            : t('conversation.statusRecording');
        sts.className = 'conv-status recording';
    } else if (state === 'loading') {
        btn.classList.add('loading');
        if (icon) icon.textContent = '⏳';
        sts.textContent = t('conversation.statusLoading');
        sts.className = 'conv-status loading';
    } else {
        if (icon) icon.textContent = '🎙️';
        sts.textContent = t('conversation.statusIdle');
        sts.className = 'conv-status';
    }
    convState.lastInputMode = state === 'recording'
        ? 'voice'
        : convState.lastInputMode;
    updateConversationSessionUi();
}

function setConvStatus(msg, cls) {
    const el = document.getElementById('conv-status');
    if (!el) return;
    el.textContent = msg;
    el.className = 'conv-status' + (cls ? ' ' + cls : '');
    updateConversationSessionUi();
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
