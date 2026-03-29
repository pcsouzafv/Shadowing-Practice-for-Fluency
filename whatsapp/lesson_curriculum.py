"""
Lesson Curriculum
==================
Currículo de mini-aulas no estilo BeConfident para 5 idiomas.
Cada lição inclui: frase, tradução, IPA, contexto, dica, exemplo e emoji.

Idiomas: Inglês (en), Espanhol (es), Francês (fr), Alemão (de), Italiano (it)
Níveis: A1 → B1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Lesson:
    id: str
    lang: str
    level: str
    phrase: str
    translation: str          # Tradução em Português
    ipa: str                  # Pronúncia em IPA
    context: str              # Quando usar
    example: str              # Frase de exemplo completa
    example_translation: str  # Tradução do exemplo
    tip: str                  # Dica fonética/gramatical
    topic: str = ""           # Tópico temático
    emoji: str = "🎯"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lang": self.lang,
            "level": self.level,
            "phrase": self.phrase,
            "translation": self.translation,
            "ipa": self.ipa,
            "context": self.context,
            "example": self.example,
            "example_translation": self.example_translation,
            "tip": self.tip,
            "topic": self.topic,
            "emoji": self.emoji,
        }


# ═══════════════════════════════════════════════════════════════════════════
# INGLÊS — 30 lições (A1 → B1)
# ═══════════════════════════════════════════════════════════════════════════

EN_LESSONS: list[Lesson] = [
    Lesson("en_001","en","A1","Nice to meet you!","Prazer em conhecê-lo!","/naɪs tə miːt juː/",
           "Ao ser apresentado a alguém pela primeira vez",
           "Hi, I'm Ana. Nice to meet you!","Oi, sou Ana. Prazer em conhecê-lo!",
           "O 'meet' soa como /miːt/ — vogal longa. Não confunda com 'met' /mɛt/.","Cumprimentos","👋"),
    Lesson("en_002","en","A1","How are you doing?","Como você está?","/haʊ ɑːr juː ˈduːɪŋ/",
           "Saudação informal ao ver um amigo ou colega",
           "Hey Mark! How are you doing these days?","Ei Mark! Como você está por esses dias?",
           "Reduzido no fala rápida: 'How ya doin'?' — o 'you' vira 'ya'","Saudação","😊"),
    Lesson("en_003","en","A1","It's been a while!","Faz tempo!","/ɪts bɪn ə waɪl/",
           "Ao reencontrar alguém que não via há muito tempo",
           "Wow, it's been a while! Where have you been?","Nossa, faz tempo! Onde você esteve?",
           "O 'been' se pronuncia /bɪn/, não /biːn/ — vogal curta no inglês falado","Saudação","🙌"),
    Lesson("en_004","en","A1","Can I help you?","Posso te ajudar?","/kæn aɪ hɛlp juː/",
           "Oferecer ajuda em uma loja, escritório ou situação social",
           "Excuse me, can I help you find something?","Com licença, posso te ajudar a encontrar algo?",
           "'Can' é sempre /kæn/ com vogal curta em afirmativas, não /keɪn/","Educação","🤝"),
    Lesson("en_005","en","A1","What do you mean?","O que você quer dizer?","/wɒt duː juː miːn/",
           "Pedir esclarecimento quando não entendeu algo",
           "Sorry, what do you mean exactly?","Desculpe, o que você quer dizer exatamente?",
           "Na fala rápida: 'Whatcha mean?' — informal, comum entre jovens","Comunicação","🤔"),
    Lesson("en_006","en","A1","No worries!","Sem problema! / Não tem problema!","/nəʊ ˈwʌriz/",
           "Resposta relaxada quando alguém pede desculpas ou agradece",
           "A: Sorry I'm late! B: No worries, we just started!","A: Desculpe o atraso! B: Sem problema, acabamos de começar!",
           "Equivalente a 'Don't worry about it' — mais coloquial e natural","Educação","😌"),
    Lesson("en_007","en","A2","I was wondering if...","Eu estava me perguntando se...","/aɪ wəz ˈwʌndərɪŋ ɪf/",
           "Fazer um pedido de forma educada e indireta",
           "I was wondering if you could send me the report.","Eu estava me perguntando se você poderia me mandar o relatório.",
           "Esta estrutura torna o pedido mais educado — muito usada em contextos profissionais","Educação","💼"),
    Lesson("en_008","en","A2","That makes sense.","Isso faz sentido.","/ðæt meɪks sɛns/",
           "Confirmar que entendeu ou que concorda com uma explicação",
           "Oh, that makes sense now. Thanks for explaining!","Ah, isso faz sentido agora. Obrigado por explicar!",
           "Evite dizer 'It makes sense for me' — o correto é simplesmente 'That makes sense'","Concordância","✅"),
    Lesson("en_009","en","A2","I'm looking forward to it.","Estou ansioso por isso.","/aɪm ˈlʊkɪŋ ˈfɔːrwərd tʊ ɪt/",
           "Expressar entusiasmo ou expectativa sobre algo futuro",
           "The conference is on Friday. I'm really looking forward to it!","A conferência é sexta. Estou animado com isso!",
           "Diga 'looking forward TO' + ing ou + pronome. Nunca 'lyking forward'","Emoções","🎉"),
    Lesson("en_010","en","A2","It depends on...","Depende de...","/ɪt dɪˈpɛndz ɒn/",
           "Indicar que a resposta varia de acordo com fatores",
           "A: Should I go? B: It depends on how you feel.","A: Devo ir? B: Depende de como você se sente.",
           "Siga com 'it depends on + substantivo/ing' — nunca 'depends of'","Análise","⚖️"),
    Lesson("en_011","en","A2","Let me think about it.","Deixa eu pensar nisso.","/lɛt miː θɪŋk əˈbaʊt ɪt/",
           "Pedir tempo para considerar uma proposta ou decisão",
           "That's a big decision. Let me think about it and get back to you.","É uma decisão grande. Deixa eu pensar e te aviso.",
           "'Get back to you' = retornar com uma resposta — expressão muito profissional","Comunicação","💭"),
    Lesson("en_012","en","A2","You've got a point.","Você tem razão / Faz sentido o que você disse.","/juːv ɡɒt ə pɔɪnt/",
           "Reconhecer que o argumento de outra pessoa é válido",
           "You've got a point — we should prepare a plan B.","Você tem razão — deveríamos preparar um plano B.",
           "'You've got' = 'You have got' — contração natural. Soa mais autêntico que 'You're right'","Concordância","👍"),
    Lesson("en_013","en","A2","I can't make it.","Não vou conseguir ir / Não posso.","/aɪ kɑːnt meɪk ɪt/",
           "Dizer que não poderá comparecer a algo",
           "Sorry, I can't make it to the party tonight.","Desculpe, não vou conseguir ir à festa esta noite.",
           "'Make it' = conseguir chegar/comparecer. Pronuncie o 't' de 'can't' com parada glotal no AmE","Comunicação","😔"),
    Lesson("en_014","en","A2","What's the catch?","Qual é o porém? / O que tem de errado?","/wɒts ðə kætʃ/",
           "Perguntar qual é a desvantagem ou condição oculta",
           "It's free? What's the catch?","É de graça? Qual é o porém?",
           "Expressão muito coloquial e idiomática — soa 100% nativo","Expressões","🎣"),
    Lesson("en_015","en","B1","I'm swamped right now.","Estou sobrecarregado agora.","/aɪm swɒmpt raɪt naʊ/",
           "Dizer que está muito ocupado com trabalho",
           "Can we reschedule? I'm totally swamped this week.","Podemos remarcar? Estou totalmente sobrecarregado esta semana.",
           "'Swamped' vem da ideia de estar afogado em pântano — intenso, informal, muito usado","Trabalho","😓"),
    Lesson("en_016","en","B1","It slipped my mind.","Saiu da minha cabeça / Esqueci.","/ɪt slɪpt maɪ maɪnd/",
           "Admitir que esqueceu de algo por distração",
           "I forgot to call him — it completely slipped my mind!","Esqueci de ligar para ele — saiu completamente da minha cabeça!",
           "Mais idiomático que 'I forgot'. O 'slip' é como algo escorregando da memória","Expressões","🤦"),
    Lesson("en_017","en","B1","Let's get the ball rolling.","Vamos começar / Vamos colocar a bola para rolar.","/lɛts ɡɛt ðə bɔːl ˈrəʊlɪŋ/",
           "Propor o início de uma ação ou reunião",
           "Everyone's here, so let's get the ball rolling!","Todo mundo chegou, então vamos começar!",
           "Idiom clássico de reuniões de negócios — impressiona muito em contexto profissional","Trabalho","⚽"),
    Lesson("en_018","en","B1","I'll keep you posted.","Vou te manter informado/a.","/aɪl kiːp juː ˈpəʊstɪd/",
           "Prometer atualizar alguém sobre o andamento de algo",
           "No news yet, but I'll keep you posted.","Sem novidades ainda, mas vou te manter informado.",
           "Equivalente formal: 'I'll keep you updated'. Ambos são profissionais e naturais","Trabalho","📬"),
    Lesson("en_019","en","B1","That's out of the question.","Isso está fora de cogitação / Nem pensar.","/ðæts aʊt əv ðə ˈkwɛstʃən/",
           "Recusar algo categoricamente",
           "Quitting? That's out of the question right now.","Desistir? Isso está fora de cogitação agora.",
           "Stronger than 'no'. O 'that's' é muitas vezes protético — 'that-sout-of-the-question' como um bloco","Expressões","🚫"),
    Lesson("en_020","en","B1","Let's touch base later.","Vamos nos falar mais tarde.","/lɛts tʌtʃ beɪs ˈleɪtər/",
           "Propor retomar contato ou conversa em outro momento",
           "I need to run to a meeting. Let's touch base later this afternoon.",
           "Preciso correr para uma reunião. Vamos nos falar mais tarde esta tarde.",
           "Expressão de negócios — 'touch base' vem do baseball, muito comum em e-mails","Trabalho","📞"),
    Lesson("en_021","en","B1","I'm on the fence about it.","Estou indeciso sobre isso.","/aɪm ɒn ðə fɛns əˈbaʊt ɪt/",
           "Expressar indecisão ou hesitação sobre algo",
           "I'm on the fence about accepting the job offer.","Estou indeciso sobre aceitar a oferta de emprego.",
           "'On the fence' = em cima do muro. Imagem de estar sentado na cerca sem escolher um lado","Expressões","🤷"),
    Lesson("en_022","en","B1","I beg to differ.","Com todo respeito, discordo.","/aɪ bɛɡ tə ˈdɪfər/",
           "Discordar educadamente de alguém",
           "I beg to differ — the data doesn't support that conclusion.","Com todo respeito, discordo — os dados não sustentam essa conclusão.",
           "Muito mais educado que 'No, you're wrong'. Ideal em debates formais ou profissionais","Concordância","🎩"),
    Lesson("en_023","en","A2","Could you say that again?","Pode repetir isso?","/kʊd juː seɪ ðæt əˈɡɛn/",
           "Pedir para alguém repetir o que disse",
           "Sorry, could you say that again? I didn't catch that.","Desculpe, pode repetir? Não ouvi direito.",
           "Mais polido que 'What?' ou 'Huh?'. 'I didn't catch that' = não entendi","Comunicação","👂"),
    Lesson("en_024","en","A2","I know what you mean.","Sei o que você quer dizer / Entendo o que sente.","/aɪ nəʊ wɒt juː miːn/",
           "Mostrar empatia e compreensão",
           "A: It's so stressful! B: I know what you mean.","A: É tão estressante! B: Sei o que você quer dizer.",
           "Reduzido na fala: 'I know whatchamean' — treinar a ligação das palavras é essencial","Empatia","💞"),
    Lesson("en_025","en","B1","Take it with a grain of salt.","Leve com reservas / Não acredite 100%.","/teɪk ɪt wɪð ə ɡreɪn əv sɔːlt/",
           "Aconselhar a ser cético sobre informações não verificadas",
           "He says he's an expert, but I'd take his advice with a grain of salt.","Ele diz que é especialista, mas eu levaria o conselho dele com reservas.",
           "Idiom muito frequente em inglês nativo — impossível de deduzir pela tradução literal","Expressões","🧂"),
    Lesson("en_026","en","B1","I'm all ears.","Sou todo ouvidos.","/aɪm ɔːl ɪərz/",
           "Indicar que está prestando atenção total a algo",
           "You said you have news? I'm all ears!","Disse que tem novidades? Sou todo ouvidos!",
           "Soa jovial e animado — melhor que apenas dizer 'I'm listening'","Comunicação","👂"),
    Lesson("en_027","en","B1","Let's call it a day.","Vamos encerrar por hoje.","/lɛts kɔːl ɪt ə deɪ/",
           "Propor terminar o trabalho ou atividade do dia",
           "We've covered a lot — let's call it a day.","Avançamos bastante — vamos encerrar por hoje.",
           "Idiom clássico de fim de expediente — muito natural em contextos informais e profissionais","Trabalho","🏁"),
    Lesson("en_028","en","B1","It's on the tip of my tongue.","Está na ponta da minha língua.","/ɪts ɒn ðə tɪp əv maɪ tʌŋ/",
           "Dizer que lembrou quase de algo mas não consegue puxar",
           "What's her name again? It's on the tip of my tongue!","Qual é o nome dela mesmo? Está na ponta da minha língua!",
           "Fenômeno cognitivo universal — expressão idêntica existe em PT: 'ponta da língua'","Expressões","💬"),
    Lesson("en_029","en","B1","Bear with me.","Tenha paciência comigo / Me aguente um momento.","/bɛr wɪð miː/",
           "Pedir paciência enquanto realiza algo demorado",
           "Bear with me — I just need to find the right file.","Tenha paciência — preciso apenas encontrar o arquivo certo.",
           "'Bear' aqui = aguentar/suportar, não o animal. Pronúncia: /bɛr/ igual a 'bare'","Comunicação","🐻"),
    Lesson("en_030","en","B1","The ball is in your court.","A decisão é sua / A bola está com você.","/ðə bɔːl ɪz ɪn jɔːr kɔːrt/",
           "Dizer que a próxima ação ou decisão é responsabilidade da outra pessoa",
           "I've made my offer. The ball is in your court now.","Fiz minha oferta. A decisão é sua agora.",
           "Metáfora do tênis — a bola está no seu lado da quadra para você jogar","Expressões","🎾"),
]

# ═══════════════════════════════════════════════════════════════════════════
# ESPANHOL — 20 lições (A1 → B1)
# ═══════════════════════════════════════════════════════════════════════════

ES_LESSONS: list[Lesson] = [
    Lesson("es_001","es","A1","¡Mucho gusto!","Muito prazer!","/ˈmutʃo ˈɡusto/",
           "Ao ser apresentado a alguém pela primeira vez",
           "Hola, soy Carlos. ¡Mucho gusto!","Olá, sou Carlos. Muito prazer!",
           "Mais natural que 'encantado' no dia a dia hispânico cotidiano","Cumprimentos","👋"),
    Lesson("es_002","es","A1","¿Qué tal?","Tudo bem? / Como vai?","/ke ˈtal/",
           "Saudação informal, substitui '¿Cómo estás?' no dia a dia",
           "¡Hola! ¿Qué tal todo?","Olá! Tudo bem com tudo?",
           "Muito mais curto e informal — resposta típica: '¡Bien, gracias!'","Saudação","😊"),
    Lesson("es_003","es","A1","No pasa nada.","Não tem problema. / Sem problema.","/no ˈpasa ˈnaða/",
           "Responder quando alguém pede desculpas ou agradece",
           "A: ¡Lo siento! B: ¡No pasa nada, tranquilo!","A: Desculpe! B: Não tem problema, calma!",
           "A 'd' intervocálica em 'nada' é quase inaudível na fala rápida: 'naa'","Educação","😌"),
    Lesson("es_004","es","A1","¿Me puedes ayudar?","Pode me ajudar?","/me ˈpweðes aʝuˈðar/",
           "Pedir ajuda de forma educada",
           "Perdona, ¿me puedes ayudar a encontrar la calle?","Perdão, pode me ajudar a encontrar a rua?",
           "Note: 'puedes' tem ditongo /ue/ — 'PWEH-des', não 'PU-e-des'","Educação","🤝"),
    Lesson("es_005","es","A2","¿Cómo que no?","Como assim não?","/ˈkomo ke no/",
           "Expressar surpresa ou incredulidade com uma negativa",
           "¿Cómo que no vienen? ¡Ya estamos preparados!","Como assim não vêm? Já estamos preparados!",
           "Expressão tipicamente coloquial, muito frequente em conversas naturais","Emoções","😲"),
    Lesson("es_006","es","A2","Tengo muchas ganas.","Estou animado(a) / Não vejo a hora.","/ˈteŋɡo ˈmutʃas ˈɡanas/",
           "Expressar entusiasmo e expectativa sobre algo futuro",
           "Tengo muchas ganas de ver la película nueva.","Não vejo a hora de ver o novo filme.",
           "'Ganas' = vontade/desejo. 'Tener ganas de + infinitivo' é estrutura fundamental","Emoções","🎉"),
    Lesson("es_007","es","A2","A ver...","Vamos ver... / Deixa eu ver...","/a ˈβer/",
           "Ganhar tempo para pensar ou examinar algo — muito frequente na fala",
           "A ver, déjame revisar el documento.","Vamos ver, deixa eu revisar o documento.",
           "Curto, natural, faz parte do ritmo espanhol. Não confunda com 'haber' (verbo)",
           "Fala natural","💭"),
    Lesson("es_008","es","A2","Me alegra escucharlo.","Fico feliz em ouvir isso.","/me aˈleɣɾa eskuˈtʃarlo/",
           "Expressar alegria ao ouvir uma boa notícia",
           "A: ¡Conseguí el trabajo! B: ¡Me alegra mucho escucharlo!","A: Consegui o emprego! B: Fico muito feliz em ouvir isso!",
           "'Alegrar' = fazer alegrar. 'Me alegra' = faz-me feliz — note a estrutura inversa","Empatia","😃"),
    Lesson("es_009","es","B1","No es para tanto.","Não é para tanto. / Não é tão sério assim.","/no es ˈpaɾa ˈtanto/",
           "Diminuir a importância de algo ou acalmar alguém que está exagerando",
           "¡Tranquilo! No es para tanto, se puede solucionar.","Calma! Não é para tanto, tem solução.",
           "Soa mais natural que 'no es tan grave' — muito frequente em espanhol coloquial","Expressões","😅"),
    Lesson("es_010","es","B1","Estar en las nubes.","Estar nas nuvens / Estar distraído.","/esˈtar en las ˈnuβes/",
           "Descrever alguém que está distraído ou sonhando acordado",
           "¡Oye! ¿Me escuchas? Siempre estás en las nubes.","Ei! Você está me ouvindo? Você está sempre nas nuvens.",
           "Idiomatic — tradução quase literal para o PT. Familiar a qualquer falante","Expressões","☁️"),
    Lesson("es_011","es","B1","Ponerse las pilas.","Tomar uma atitude / Colocar as pilhas.","/poˈnerse las ˈpilas/",
           "Dizer a alguém (ou a si mesmo) que precisa se organizar e agir",
           "Tienes que ponerte las pilas si quieres aprobar el examen.","Você precisa tomar uma atitude se quiser passar no exame.",
           "Idiom colorido — como 'recarregar as pilhas' mas com sentido de agir, não descansar","Expressões","🔋"),
    Lesson("es_012","es","A1","Por favor / Con permiso","Por favor / Com licença",
           "/poɾ faˈβoɾ/ /kon peɾˈmiso/",
           "Pedido educado e pedido de passagem — essenciais no dia a dia",
           "Con permiso, ¿puedo pasar? — Por favor, una mesa para dos.","Com licença, posso passar? — Por favor, uma mesa para dois.",
           "'Con permiso' = ao passar por alguém; 'Perdona' = ao interromper","Educação","🙏"),
    Lesson("es_013","es","A2","¿Qué quieres decir?","O que você quer dizer?","/ke ˈkjeɾes deˈθiɾ/",
           "Pedir esclarecimento sobre algo dito",
           "No entiendo. ¿Qué quieres decir con eso?","Não entendo. O que você quer dizer com isso?",
           "Note a 'c/z' em 'decir' /deˈθiɾ/ na Espanha vs /deˈsiɾ/ na América Latina","Comunicação","🤔"),
    Lesson("es_014","es","B1","No me digas.","Não me diz! / Nossa!","/no me ˈdiɣas/",
           "Expressar surpresa ou incredulidade",
           "A: ¡Me caso en junio! B: ¡No me digas! ¿En serio?","A: Vou casar em junho! B: Não me diz! Sério?",
           "Literalmente 'não me diga' — function word de surpresa, não uma ordem real","Emoções","😱"),
    Lesson("es_015","es","B1","Tener mala leche.","Ter má sorte / Estar de mau humor (depende contexto).","/teˈner ˈmala ˈletʃe/",
           "Expressar má sorte ou mau humor — informal e coloquial (Espanha principalmente)",
           "¡Qué mala leche! Se rompió el coche justo hoy.","Que azar! O carro quebrou justamente hoje.",
           "Expressão muito espanhola (Espanha) — pode ter significados diferentes por região","Expressões","🍀"),
    Lesson("es_016","es","A2","Depende de...","Depende de...","/deˈpende de/",
           "Indicar que a resposta varia conforme circunstâncias",
           "¿Vas a ir? Depende de cómo me sienta mañana.","Você vai? Depende de como eu me sentir amanhã.",
           "Sempre seguido de 'de' — nunca 'depende en' (falso cognato com inglês)","Análise","⚖️"),
    Lesson("es_017","es","B1","Echarle ganas.","Se dedicar / Dar o seu melhor.","/eˈtʃarle ˈɡanas/",
           "Encorajar alguém a se esforçar — muito usado no México",
           "¡Échale ganas, tú puedes!","Se dedica, você consegue!",
           "Muito popular no México. Equivalente: 'darle duro', 'esforzarse'","Motivação","💪"),
    Lesson("es_018","es","B1","¿Cómo te fue?","Como foi (para você)?","/ˈkomo te ˈfwe/",
           "Perguntar como foi um evento, dia ou experiência específica",
           "¿Cómo te fue en la entrevista?","Como foi na entrevista?",
           "Pretérito do 'ir/ser' — 'fue' /fwe/ é um dos verbos mais irregulares do espanhol","Conversação","📋"),
    Lesson("es_019","es","B1","Al pan, pan y al vino, vino.","Pão, pão; queijo, queijo. / Chamar as coisas pelo nome.","/al pan pan i al ˈbino ˈbino/",
           "Expressar que se deve ser direto e honesto, sem rodeios",
           "Seré directo: al pan, pan y al vino, vino — esto no funcionó.","Serei direto: pão, pão; queijo, queijo — isso não funcionou.",
           "Provérbio clássico — memorizar a melodia é mais importante que a pronúncia perfeita","Expressões","🍷"),
    Lesson("es_020","es","A1","¡Buen provecho!","Bom apetite!","/bwen proˈβetʃo/",
           "Desejo feito antes ou durante uma refeição",
           "A: Es hora de comer. B: ¡Buen provecho a todos!","A: É hora de comer. B: Bom apetite a todos!",
           "Equivalente italiano: 'Buon appetito'. Em PT brasileiro não há equivalente tão natural","Cotidiano","🍽️"),
]

# ═══════════════════════════════════════════════════════════════════════════
# FRANCÊS — 20 lições (A1 → B1)
# ═══════════════════════════════════════════════════════════════════════════

FR_LESSONS: list[Lesson] = [
    Lesson("fr_001","fr","A1","Enchanté(e)!","Encantado(a)! / Prazer!","/ɑ̃ʃɑ̃te/",
           "Ao ser apresentado a alguém formalmente",
           "Bonjour, je suis Marie. Enchantée!","Bom dia, sou Marie. Prazer!",
           "Homens dizem 'enchanté' (sem e); mulheres 'enchantée' (com e — silencioso na fala)","Cumprimentos","👋"),
    Lesson("fr_002","fr","A1","Ça va?","Tudo bem?","/sa va/",
           "Saudação mais usada no francês cotidiano informal",
           "Salut! Ça va? — Ça va, merci! Et toi?","Oi! Tudo bem? — Tudo bem, obrigado! E você?",
           "Resposta automática é 'Ça va' mesmo. É uma saudação, não pergunta real sobre saúde","Saudação","😊"),
    Lesson("fr_003","fr","A1","S'il vous plaît / S'il te plaît","Por favor (formal/informal)","/sil vu plɛ/ /sil tə plɛ/",
           "Pedido educado — 'vous' (formal) e 'te' (informal/amigos)",
           "Un café, s'il vous plaît.","Um café, por favor.",
           "Na fala rápida 'svp' (abreviado) em mensagens escritas","Educação","🙏"),
    Lesson("fr_004","fr","A1","Je ne comprends pas.","Não entendo.","/ʒə nə kɔ̃pʁɑ̃ pa/",
           "Dizer que não compreendeu algo",
           "Désolé, je ne comprends pas. Pouvez-vous répéter?","Desculpe, não entendo. Pode repetir?",
           "Na fala coloquial o 'ne' cai: 'Je comprends pas' — muito comum","Comunicação","🤔"),
    Lesson("fr_005","fr","A2","C'est pas grave.","Não tem problema. / Não é grave.","/sɛ pa ɡʁav/",
           "Minimizar um erro ou problema — equivalente informal de 'ce n'est pas grave'",
           "A: J'ai oublié! B: C'est pas grave, ça arrive.","A: Esqueci! B: Não tem problema, acontece.",
           "Ausência do 'ne' é característica do francês falado — não é erro, é norma oral","Educação","😌"),
    Lesson("fr_006","fr","A2","On y va?","Vamos?","/ɔ̃ ni va/",
           "Propor partir ou iniciar algo — 'on' = 'a gente' no francês falado",
           "Tout le monde est prêt? On y va!","Todo mundo está pronto? Vamos!",
           "'On' substitui 'nous' no francês coloquial — 'on est', não 'on sommes'","Motivação","🚀"),
    Lesson("fr_007","fr","A2","Je m'en fous.","Não me importo. / Tanto faz.","/ʒə mɑ̃ fu/",
           "Expressar indiferença — atenção: pode soar rude dependendo do contexto",
           "A: Quel film? B: Je m'en fous, choisis toi.","A: Qual filme? B: Tanto faz, você escolhe.",
           "Mais forte: 'je m'en fiche' (suave). Evitar com desconhecidos ou chefes","Expressões","🤷"),
    Lesson("fr_008","fr","A2","C'est sympa!","Que legal! / Que simpático!","/sɛ sɛ̃pa/",
           "Elogiar algo ou alguém de forma casual",
           "C'est vraiment sympa chez toi!","A sua casa é muito legal!",
           "'Sympa' é apócope de 'sympathique' — usado constantemente no francês moderno","Elogios","😍"),
    Lesson("fr_009","fr","B1","Il ne faut pas pousser mémé dans les orties.","Não exagere na medida!",
           "/il nə fo pa puse meme dɑ̃ lez ɔʁti/",
           "Dizer que está indo longe demais — expressão idiomática clássica",
           "Maintenant tu veux mon bureau aussi? Il ne faut pas pousser mémé dans les orties!",
           "Agora você quer meu escritório também? Chega, não exagera!",
           "Literalmente: 'não empurre a vovó nas urtigas' — humorístico e muito francês","Expressões","🌿"),
    Lesson("fr_010","fr","B1","Avoir le cafard.","Estar na fossa / Estar para baixo.","/avwaʁ lə kafaʁ/",
           "Expressar melancolia ou tristeza passageira",
           "Je sais pas pourquoi, mais j'ai vraiment le cafard aujourd'hui.","Não sei por quê, mas estou de fato na fossa hoje.",
           "Literalmente 'ter a barata' — Baudelaire tornou essa expressão famosa","Emoções","🪲"),
    Lesson("fr_011","fr","A1","Merci beaucoup!","Muito obrigado(a)!","/mɛʁsi boku/",
           "Agradecimento com ênfase",
           "C'est très gentil, merci beaucoup!","É muito gentil da sua parte, muito obrigado!",
           "'Beaucoup' = /boku/ — o 'eau' faz som /o/ e o 'p' final é mudo","Educação","🙏"),
    Lesson("fr_012","fr","A2","Ça dépend.","Depende.","/sa depɑ̃/",
           "Resposta comum quando a situação varia",
           "A: Tu viens demain? B: Ça dépend, je dois vérifier mon agenda.",
           "A: Você vem amanhã? B: Depende, preciso verificar minha agenda.",
           "Simples e muito natural — o 'n' nasal de '-end' é a chave","Conversação","⚖️"),
    Lesson("fr_013","fr","B1","Mettre les points sur les i.","Esclarecer as coisas / Colocar os pontos nos is.","/mɛtʁ le pwɛ̃ syʁ lez i/",
           "Ser explícito e direto para evitar ambiguidade",
           "Laisse-moi mettre les points sur les i: ce projet est prioritaire.",
           "Deixa eu esclarecer as coisas: este projeto é prioritário.",
           "Expressão idêntica ao PT 'pôr os pontos nos is' — pontuação como metáfora de precisão","Expressões","✍️"),
    Lesson("fr_014","fr","B1","Avoir d'autres chats à fouetter.","Ter coisas mais importantes a fazer.","/avwaʁ dɔtʁ ʃa a fwɛte/",
           "Dizer que tem coisas mais urgentes para se preocupar",
           "Je n'ai pas le temps pour ça, j'ai d'autres chats à fouetter!","Não tenho tempo para isso, tenho coisas mais importantes!",
           "Literalmente 'ter outros gatos para chicotear' — idiom histórico, muito francês","Expressões","🐱"),
    Lesson("fr_015","fr","A2","C'est quoi l'idée?","Qual é a ideia? / O que você está pensando?","/sɛ kwa l‿ide/",
           "Pedir explicação sobre intenção ou plano",
           "C'est quoi l'idée derrière ce projet?","Qual é a ideia por trás deste projeto?",
           "Forma oral de 'Quelle est l'idée?' — natural e dinâmica","Comunicação","💡"),
    Lesson("fr_016","fr","B1","Avoir le cœur sur la main.","Ser de coração aberto / Ser generoso.","/avwaʁ lə kœʁ syʁ la mɛ̃/",
           "Elogiar a generosidade de alguém",
           "Elle donne toujours à la charité — elle a vraiment le cœur sur la main.",
           "Ela sempre doa pra caridade — ela é realmente de coração aberto.",
           "Bela expressão poética — o coração na mão como símbolo de oferta","Elogios","❤️"),
    Lesson("fr_017","fr","A1","À tout à l'heure!","Até logo! (em breve)","/a tutaˈlœʁ/",
           "Despedida quando vai voltar em breve",
           "Je reviens dans cinq minutes. À tout à l'heure!","Volto em cinco minutos. Até logo!",
           "Cuidado: 'À tout à l'heure' = daqui a pouco; 'À bientôt' = em breve (mais vago)","Despedida","👋"),
    Lesson("fr_018","fr","A2","Je n'en reviens pas!","Não acredito! / Não consigo acreditar!","/ʒə nɑ̃ ʁəvjɛ̃ pa/",
           "Expressar grande surpresa ou espanto",
           "Il a gagné le premier prix? Je n'en reviens pas!","Ele ganhou o primeiro prêmio? Não acredito!",
           "Literalmente 'não consigo voltar de (tanto espanto)' — expressão de choque","Emoções","😱"),
    Lesson("fr_019","fr","B1","Tourner autour du pot.","Enrolar / Não ir direto ao assunto.","/tuʁne otɔʁ dy po/",
           "Criticar alguém que está evitando dizer algo diretamente",
           "Arrête de tourner autour du pot et dis-moi ce qui s'est passé!","Para de enrolar e me diz o que aconteceu!",
           "Literalmente 'girar em torno da panela' — idiom medieval muito vivo","Expressões","🫙"),
    Lesson("fr_020","fr","B1","Avoir le vent en poupe.","Estar com tudo / Estar no sucesso.","/avwaʁ lə vɑ̃ ɑ̃ pup/",
           "Descrever alguém ou algo que está indo muito bem",
           "Son entreprise a le vent en poupe depuis le lancement.","Sua empresa está com tudo desde o lançamento.",
           "Metáfora náutica — vento de popa = propulsão favorável. Eloquente em contexto profissional","Expressões","⛵"),
]

# ═══════════════════════════════════════════════════════════════════════════
# ALEMÃO — 20 lições (A1 → B1)
# ═══════════════════════════════════════════════════════════════════════════

DE_LESSONS: list[Lesson] = [
    Lesson("de_001","de","A1","Guten Morgen!","Bom dia!","/ˈɡuːtən ˈmɔʁɡən/",
           "Saudação pela manhã, até por volta do meio-dia",
           "Guten Morgen! Wie haben Sie geschlafen?","Bom dia! Como dormiu?",
           "O 'G' inicial é sempre /ɡ/ (sonoro), nunca como em inglês. 'gut' rima com 'boot'","Saudação","🌅"),
    Lesson("de_002","de","A1","Wie geht's?","Como vai?","/viː ˈɡeːts/",
           "Saudação informal — abreviação de 'Wie geht es (dir/Ihnen)?'",
           "Hey! Wie geht's? — Gut, danke! Und dir?","Ei! Como vai? — Bem, obrigado! E você?",
           "'Wie geht's' é 'Wie geht es' comprimido — muito mais natural na fala","Saudação","😊"),
    Lesson("de_003","de","A1","Entschuldigung!","Com licença! / Desculpe!","/ɛntˈʃʊldɪɡʊŋ/",
           "Para chamar atenção ou pedir desculpas",
           "Entschuldigung, wo ist der Bahnhof?","Com licença, onde fica a estação de trem?",
           "É a palavra longa que todo aprendiz teme — divida: Ent-shul-di-gung","Educação","🙏"),
    Lesson("de_004","de","A1","Ich verstehe nicht.","Não entendo.","/ɪç fɛɐ̯ˈʃteːə nɪçt/",
           "Dizer que não compreendeu algo",
           "Entschuldigung, ich verstehe nicht. Können Sie das wiederholen?",
           "Com licença, não entendo. Pode repetir isso?",
           "O 'ch' em 'ich' soa /ɪç/ — palatal suave, não 'isch' como alguns dizem","Comunicação","🤔"),
    Lesson("de_005","de","A1","Bitte!","Por favor! / De nada!","/ˈbɪtə/",
           "'Bitte' é multifuncional: pedido, 'de nada', e 'pode falar'",
           "Danke! — Bitte!  /  Einen Kaffee, bitte.","Obrigado! — De nada! / Um café, por favor.",
           "Única palavra alemã com três funções primárias distintas — aprenda o contexto","Educação","🙏"),
    Lesson("de_006","de","A2","Das klingt gut!","Isso soa bem! / Parece ótimo!","/das klɪŋt ɡuːt/",
           "Concordar ou aprovar uma sugestão",
           "A: Essen wir Pizza? B: Das klingt gut!","A: Comemos pizza? B: Isso soa bem!",
           "O verbo 'klingen' = soar. Literal mas muito usado naturalmente no alemão","Concordância","👍"),
    Lesson("de_007","de","A2","Kein Problem.","Sem problema.","/kaɪn pʁoˈbleːm/",
           "Responder que algo não é um problema",
           "A: Kann ich morgen kommen? B: Kein Problem!","A: Posso vir amanhã? B: Sem problema!",
           "'Kein' = nenhum/nenhuma. Contrasta com 'nicht' — fundamental para a negação alemã","Educação","✅"),
    Lesson("de_008","de","A2","Ich bin dabei.","Eu topo / Estou dentro.","/ɪç bɪn daˈbaɪ/",
           "Confirmar participação em algo",
           "A: Kommen wir morgen früh Joggen? B: Ich bin dabei!","A: Corremos cedo amanhã? B: Estou dentro!",
           "'Dabei sein' = estar presente/participar. 'Dabei' = junto a isso","Cotidiano","🤜"),
    Lesson("de_009","de","B1","Das ist nicht mein Bier.","Não é problema meu. / Isso não é da minha conta.",
           "/das ɪst nɪçt maɪn biːɐ̯/",
           "Dizer que algo não é de sua responsabilidade — informal",
           "A: Warum ist das kaputt? B: Keine Ahnung, das ist nicht mein Bier!",
           "A: Por que isso está quebrado? B: Não sei, não é da minha conta!",
           "Literalmente 'não é minha cerveja' — idiom tipicamente alemão e informal","Expressões","🍺"),
    Lesson("de_010","de","B1","Den Nagel auf den Kopf treffen.","Acertar na mosca / Bater o martelo certo.","/den ˈnaːɡəl aʊf den kɔpf ˈtʁɛfən/",
           "Dizer que alguém disse ou fez exatamente certo",
           "Du hast den Nagel auf den Kopf getroffen!","Você acertou na mosca!",
           "Como 'cravar o prego na cabeça' — análogo ao PT 'acertar na mosca'","Expressões","🔨"),
    Lesson("de_011","de","A2","Was ist los?","O que está acontecendo? / O que houve?","/vas ɪst loːs/",
           "Perguntar o que está acontecendo em uma situação",
           "Du siehst traurig aus. Was ist los?","Você parece triste. O que está acontecendo?",
           "'Los' aqui não significa 'losango' — é 'solto/livre/acontecendo' no contexto alemão","Comunicação","❓"),
    Lesson("de_012","de","B1","Ich drücke dir die Daumen.","Estou torcendo por você. (Cruzo os dedos.)",
           "/ɪç ˈdʁʏkə diːɐ̯ diː ˈdaʊmən/",
           "Desejar boa sorte a alguém",
           "Viel Glück beim Vorstellungsgespräch! Ich drücke dir die Daumen!",
           "Boa sorte na entrevista! Estou torcendo por você!",
           "Alemães 'apertam os polegares' em vez de 'cruzar os dedos' — o gesto é diferente","Expressões","👍"),
    Lesson("de_013","de","A1","Sprechen Sie Englisch?","Você fala inglês?","/ˈʃpʁɛçən ziː ˈɛŋlɪʃ/",
           "Pergunta de sobrevivência para turistas ou iniciantes",
           "Entschuldigung, sprechen Sie Englisch? Ich spreche kaum Deutsch.",
           "Com licença, você fala inglês? Falo pouco alemão.",
           "O 'ie' em 'Sie' = /iː/ longo. O verbo 'sprechen' tem o 'e' substituído por 'i' na 2ª/3ª","Comunicação","🌍"),
    Lesson("de_014","de","A2","Auf jeden Fall.","Com certeza. / De qualquer jeito.","/aʊf ˈjeːdən fal/",
           "Afirmar com certeza ou concordar fortemente",
           "A: Kommst du zur Party? B: Auf jeden Fall!","A: Você vem à festa? B: Com certeza!",
           "Mais forte que 'selbstverständlich' no cotidiano jovem — equivale a 'definitely'","Concordância","✅"),
    Lesson("de_015","de","B1","Das geht mir auf den Keks.","Isso me irrita. / Está me enchendo o saco.","/das ɡeːt miːɐ̯ aʊf den keːks/",
           "Expressar irritação com algo de forma informal",
           "Diese Wartezeit geht mir wirklich auf den Keks!","Essa espera está realmente me irritando!",
           "Literalmente 'vai no meu biscoito' — 'Keks' = bolacha. Expressão hilária e típica alemã","Expressões","🍪"),
    Lesson("de_016","de","B1","Unter uns gesagt.","Entre nós. / Só para você saber.","/ˈʊntɐ ʊns ɡəˈzaːkt/",
           "Compartilhar algo em confiança",
           "Unter uns gesagt, ich finde diesen Plan nicht gut.","Entre nós, não acho esse plano bom.",
           "'Unter uns' = entre nós — o particípio 'gesagt' marca que é algo 'dito' confidencialmente","Comunicação","🤫"),
    Lesson("de_017","de","A2","Wie lange dauert das?","Quanto tempo demora isso?","/viː ˈlaŋə ˈdaʊɐ̯t das/",
           "Perguntar a duração de algo — muito útil no cotidiano",
           "Wie lange dauert die Fahrt bis zum Stadtzentrum?","Quanto tempo demora o trajeto até o centro?",
           "'Dauern' = durar. O 'au' em alemão sempre soa /aʊ/ — nunca /oː/","Cotidiano","⏱️"),
    Lesson("de_018","de","B1","Es liegt auf der Hand.","Está claro. / É óbvio.","/ɛs liːkt aʊf deːɐ̯ hant/",
           "Dizer que algo é evidente",
           "Die Lösung liegt doch auf der Hand!","A solução está clara!",
           "Literalmente 'está na mão' — análogo a 'está na palma da mão' em PT","Expressões","✋"),
    Lesson("de_019","de","A2","Ich muss mal.","Preciso ir ao banheiro.","/ɪç mʊs maː/l",
           "Forma muito oral e discreta de pedir licença para ir ao banheiro",
           "Kurze Pause bitte, ich muss mal.","Uma pausa rápida, preciso ir ao banheiro.",
           "'Ich muss mal' é mais educado que dizer explicitamente — 'mal' = 'um momento'","Cotidiano","🚾"),
    Lesson("de_020","de","B1","Alles hat ein Ende, nur die Wurst hat zwei.","Tudo tem um fim, só a salsicha tem dois.",
           "/ˈaləs hat aɪn ˈɛndə nuːɐ̯ diː vʊʁst hat tsvaɪ/",
           "Dizer que as coisas boas (ou ruins) chegam ao fim, com humor",
           "Die Party war toll, aber alles hat ein Ende, nur die Wurst hat zwei!",
           "A festa foi ótima, mas tudo tem um fim, só a salsicha tem dois!",
           "O humor alemão — autoirônico e filosófico. Dizer isso em voz alta causa risos garantidos","Humor","🌭"),
]

# ═══════════════════════════════════════════════════════════════════════════
# ITALIANO — 20 lições (A1 → B1)
# ═══════════════════════════════════════════════════════════════════════════

IT_LESSONS: list[Lesson] = [
    Lesson("it_001","it","A1","Piacere!","Prazer!","/pjaˈtʃeːre/",
           "Ao ser apresentado a alguém pela primeira vez",
           "Ciao, sono Luca. Piacere!","Oi, sou Luca. Prazer!",
           "'Piacere' literalmente = 'prazer'. O 'c' antes de 'e/i' soa /tʃ/ como 'ch'","Cumprimentos","👋"),
    Lesson("it_002","it","A1","Come stai?","Como você está?","/ˈkoːme ˈstaɪ/",
           "Saudação informal para perguntar como alguém está",
           "Ciao! Come stai? — Bene, grazie! E tu?","Oi! Como você está? — Bem, obrigado! E você?",
           "'Stai' vem de 'stare' (estar) — diferente de 'essere' (ser). Crucial no italiano","Saudação","😊"),
    Lesson("it_003","it","A1","Non capisco.","Não entendo.","/non kaˈpisko/",
           "Dizer que não compreendeu",
           "Scusa, non capisco. Puoi ripetere?","Desculpe, não entendo. Pode repetir?",
           "'Capisco' vem de 'capire' — verbo irregular, mas 'capisco' é forma básica frequentíssima","Comunicação","🤔"),
    Lesson("it_004","it","A1","Grazie mille!","Muito obrigado(a)! (literalmente: mil obrigados)",
           "/ˈɡrattsje ˈmille/",
           "Agradecimento enfático e afetivo",
           "Mi hai salvato! Grazie mille!","Você me salvou! Muito obrigado!",
           "'Mille' = mil — idiom idêntico ao PT 'mil vezes obrigado'. O 'll' italiano é geminado /ll/",
           "Educação","🙏"),
    Lesson("it_005","it","A1","Per favore / Per piacere","Por favor","/peɾ faˈvoːɾe/ /peɾ pjaˈtʃeːɾe/",
           "Pedido educado — ambas são corretas, 'per favore' é mais comum",
           "Un cappuccino, per favore.","Um cappuccino, por favor.",
           "Ambas funcionam — 'per piacere' soa levemente mais formal/sul-italiano","Educação","☕"),
    Lesson("it_006","it","A2","Che bello!","Que lindo! / Que ótimo!","/ke ˈbɛllo/",
           "Expressar admiração ou entusiasmo — muito versátil",
           "Guarda quel tramonto! Che bello!","Olha aquele pôr do sol! Que lindo!",
           "'Che' + adjetivo é estrutura central do italiano expressivo. 'Che peccato!' = Que pena!","Elogios","😍"),
    Lesson("it_007","it","A2","Dai!","Vai! / Vamos! / Não acredito!","/ˈdaɪ/",
           "Palavra super versátil: incentivo, surpresa, impaciência",
           "Dai, non essere timido!","Vai, não seja tímido!",
           "Invariável e expressiva — 'Dai!' pode expressar 5 emoções diferentes pelo tom de voz","Expressões","💪"),
    Lesson("it_008","it","A2","Figurati!","Imagina! / De nada! / Não tem problema!","/fiˈɡuːɾati/",
           "Resposta casual a agradecimentos ou pedido de desculpas",
           "A: Grazie per l'aiuto! B: Figurati, è stato un piacere!","A: Obrigado pela ajuda! B: Imagina, foi um prazer!",
           "Também: 'Immagina come ti sento!' = para expressar empatia. Muito versátil no sul","Educação","😌"),
    Lesson("it_009","it","A2","Mamma mia!","Nossa! / Minha nossa!","/ˈmamma ˈmiːa/",
           "Expressar surpresa, admiração ou frustração",
           "Mamma mia, che caldo oggi!","Nossa, que calor hoje!",
           "Uma das expressões italianas mais internacionalmente conhecidas — usada genuinamente","Emoções","😲"),
    Lesson("it_010","it","B1","In bocca al lupo!","Boa sorte! (literalmente: Na boca do lobo!)",
           "/in ˈbokka al ˈluːpo/",
           "Desejo de boa sorte antes de algo importante",
           "A: Ho un esame domani. B: In bocca al lupo! A: Crepi!",
           "A: Tenho prova amanhã. B: Boa sorte! A: Obrigado! (Que o lobo morra!)",
           "Resposta OBRIGATÓRIA é 'Crepi (il lupo)!' = que o lobo morra — nunca diga 'grazie'!","Expressões","🐺"),
    Lesson("it_011","it","A2","Non c'è male.","Não está mal. / Poderia ser pior.","/non tʃɛ ˈmaːle/",
           "Resposta cotidiana a 'Come stai?' — modesta e natural",
           "A: Come stai? B: Non c'è male, grazie. E tu?","A: Como você está? B: Não está mal, obrigado. E você?",
           "Equivale ao PT 'mais ou menos' mas com tom levemente mais positivo","Saudação","🙂"),
    Lesson("it_012","it","B1","Avere la testa tra le nuvole.","Estar nas nuvens / Estar distraído.",
           "/aˈvɛːre la ˈtɛsta tra le ˈnuːvole/",
           "Descrever alguém distraído ou sonhador",
           "Marco ha sempre la testa tra le nuvole!","Marco está sempre nas nuvens!",
           "Literalmente 'ter a cabeça entre as nuvens' — análogo perfeito ao PT","Expressões","☁️"),
    Lesson("it_013","it","B1","Essere al settimo cielo.","Estar no sétimo céu.","/ˈɛːssere al ˈsɛttimo ˈtʃɛːlo/",
           "Expressar felicidade extrema",
           "Ho superato l'esame! Sono al settimo cielo!","Passei na prova! Estou no sétimo céu!",
           "Expressão bíblica/dantesca — o sétimo céu é o paraíso. Idiom compartilhado em muitas línguas","Emoções","😇"),
    Lesson("it_014","it","A1","Dov'è...?","Onde fica...?","/doˈvɛ/",
           "Perguntar localização de algo",
           "Scusa, dov'è il bagno?","Com licença, onde fica o banheiro?",
           "'Dove' + 'è' → 'dov'è' por elisão. Fundamental para qualquer turista na Itália","Cotidiano","📍"),
    Lesson("it_015","it","A2","Che cosa vuoi dire?","O que você quer dizer?","/ke ˈkɔːza vwɔɪ ˈdiːɾe/",
           "Pedir esclarecimento",
           "Non ho capito. Che cosa vuoi dire esattamente?","Não entendi. O que você quer dizer exatamente?",
           "'Vuoi' = tu vuoi = você quer. O ditongo /wɔɪ/ é bem diferente do PT","Comunicação","🤔"),
    Lesson("it_016","it","B1","Costa un occhio della testa.","Custa os olhos da cara.","/ˈkɔːsta un ˈɔkkjo ˈdɛlla ˈtɛːsta/",
           "Dizer que algo é muito caro",
           "Quella borsa è bella, ma costa un occhio della testa!","Aquela bolsa é linda, mas custa os olhos da cara!",
           "Literalmente 'custa um olho da cabeça' — análogo quase perfeito ao PT","Expressões","👁️"),
    Lesson("it_017","it","A2","Andiamo!","Vamos!","/anˈdjaːmo/",
           "Propor partir ou iniciar algo",
           "Sono tutti pronti? Andiamo!","Todos prontos? Vamos!",
           "Primeira pessoa do plural de 'andare' — literalmente 'nós vamos'. Energia!","Motivação","🚶"),
    Lesson("it_018","it","B1","Essere pieno come un uovo.","Estar cheio como um ovo / Estar empanturrado.",
           "/ˈɛːssere ˈpjɛːno kome un ˈwɔːvo/",
           "Dizer que comeu demais",
           "Non posso mangiare altro. Sono pieno come un uovo!","Não posso comer mais. Estou empanturrado!",
           "Ovos são completamente cheios — a metáfora é visual e divertida","Expressões","🥚"),
    Lesson("it_019","it","B1","Tra il dire e il fare c'è di mezzo il mare.","Entre o dizer e o fazer há um oceano.",
           "/tra il ˈdiːre e il ˈfaːre tʃɛ di ˈmɛttso il ˈmaːre/",
           "Dizer que prometido nem sempre é cumprido",
           "Ha detto che si iscrive, ma tra il dire e il fare c'è di mezzo il mare.",
           "Ele disse que se inscreve, mas entre dizer e fazer há um oceano.",
           "Provérbio clássico — fácil de memorizar pelo ritmo. Equivale a 'do dito ao feito há um grande degrau'","Expressões","🌊"),
    Lesson("it_020","it","A1","Buona fortuna!","Boa sorte!","/ˈbwɔːna forˈtuːna/",
           "Desejar boa sorte (mais neutro que 'in bocca al lupo')",
           "Buona fortuna per il colloquio!","Boa sorte na entrevista!",
           "Nota: italianos preferem 'in bocca al lupo' — 'buona fortuna' soa mais às vezes como tradução do inglês","Educação","🍀"),
]

# ═══════════════════════════════════════════════════════════════════════════
# Mapa central de idiomas → lições
# ═══════════════════════════════════════════════════════════════════════════

_CURRICULUM: dict[str, list[Lesson]] = {
    "en": EN_LESSONS,
    "es": ES_LESSONS,
    "fr": FR_LESSONS,
    "de": DE_LESSONS,
    "it": IT_LESSONS,
}


class LessonCurriculum:
    """Interface de acesso ao currículo de lições."""

    def get(self, lang: str, index: int) -> Lesson | None:
        lessons = _CURRICULUM.get(lang, [])
        if not lessons:
            return None
        return lessons[index % len(lessons)]

    def total(self, lang: str) -> int:
        return len(_CURRICULUM.get(lang, []))

    def all_for(self, lang: str) -> list[Lesson]:
        return list(_CURRICULUM.get(lang, []))

    def supported_langs(self) -> list[str]:
        return list(_CURRICULUM.keys())

    def format_lesson_message(self, lesson: Lesson, streak: int = 0) -> str:
        """Formata a lição como mensagem WhatsApp (texto rico com emojis)."""
        flag = {"en":"🇬🇧","es":"🇪🇸","fr":"🇫🇷","de":"🇩🇪","it":"🇮🇹"}.get(lesson.lang, "🌍")
        level_bar = {"A1":"⬜⬜⬜⬜","A2":"🟩⬜⬜⬜","B1":"🟩🟩⬜⬜","B2":"🟩🟩🟩⬜"}.get(lesson.level,"⬜⬜⬜⬜")
        streak_line = f"🔥 Sequência: *{streak} dias!*\n\n" if streak > 1 else ""

        return (
            f"{flag} *Mini Aula — {lesson.level}*\n"
            f"{level_bar} Nível {lesson.level}\n"
            f"{streak_line}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{lesson.emoji} *Frase do dia:*\n"
            f"_{lesson.phrase}_\n\n"
            f"🇧🇷 *Tradução:*\n"
            f"{lesson.translation}\n\n"
            f"🔊 *Pronúncia (IPA):*\n"
            f"`{lesson.ipa}`\n\n"
            f"💡 *Quando usar:*\n"
            f"{lesson.context}\n\n"
            f"📝 *Exemplo real:*\n"
            f"_{lesson.example}_\n"
            f"_{lesson.example_translation}_\n\n"
            f"🎯 *Dica fonética:*\n"
            f"{lesson.tip}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎤 *Exercício de Shadowing:*\n"
            f"Repita em voz alta 3x:\n"
            f"*\"{lesson.phrase}\"*\n\n"
            f"📩 Envie um áudio repetindo a frase!\n"
            f"Ou responda: *PRÓXIMA* | *REPETIR* | *AJUDA*"
        )
