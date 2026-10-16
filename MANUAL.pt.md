# CUA-LIBRE STUDIO — Manual de uso (v2.0)

Guia completo de comandos e fluxos para a análise qualitativa.

## 1. Abrir e sair

| Como | O que faz |
|------|----------|
| Clique duplo no aplicativo instalado, ou `./start.sh` / `start.bat` | Abre o Cua-libre em **janela própria** |
| Fechar a janela (ou ⌘Q no Mac) | Encerra o aplicativo. Seu trabalho já está salvo |
| `./start.sh --navegador` | Usa o navegador em vez da janela própria (botão **⏻ SAIR** no cabeçalho para encerrá-lo) |

Se a janela própria não puder abrir (por exemplo, num Windows antigo sem o componente WebView2), o Cua-libre usa o seu navegador automaticamente. Na janela própria, exportar um arquivo abre o diálogo **Salvar como** do sistema, e o relatório acadêmico abre no seu navegador para imprimi-lo em PDF.

Se o aplicativo já estava rodando e você o abre de novo, ele simplesmente reutiliza a instância.

## 2. Projetos (cabeçalho)

- **Seletor PROJETO**: alterna entre suas pesquisas; cada projeto isola corpus, códigos, memos e relações.
- **+ NOVO** / **✎ RENOMEAR**: criar um projeto ou renomear o ativo.
- **⤒ IMPORTAR**: abre um projeto a partir de um **backup .zip** (o gerado em ⇄ Exportar →
  🗄 Backup completo) ou de um arquivo `.json` de projeto, ou de um `.qdpx` do NVivo, ATLAS.ti, MAXQDA ou
  QualCoder (ver ⇄ Exportar). Entra como projeto novo, sem
  sobrescrever nada: serve para levar seu trabalho a outro computador (Mac ↔ Windows) ou
  para compartilhar um projeto com colegas.
- **🗑** (ao lado de IMPORTAR): exclui o projeto ativo, após confirmação. Ele não é apagado
  do disco: vai para a pasta `papelera/` (lixeira) dos seus dados, de onde pode ser
  recuperado.
- **🎓 DEMO**: cria um projeto de exemplo (entrevista fictícia já codificada, com
  relações e exclusões) para explorar todas as funções sem risco.
- **💾 SALVAR**: força um salvamento e confirma o horário. O ponto ao lado **pulsa em vermelho** a cada salvamento automático (que acontece sozinho, após cada ação).
- **🕐 HISTÓRICO**: abre o histórico de backups do projeto. O Cua-libre guarda uma cópia
  completa a cada 10 minutos de trabalho (no máximo) e uma cópia extra cada vez que você
  aperta 💾 SALVAR. Escolha qualquer ponto da lista e aperte **↺** para restaurar o
  projeto àquele momento; o estado imediatamente anterior à restauração também é copiado,
  então você nunca perde trabalho por engano.
- **ℹ SOBRE**: filosofia do projeto, contato e agradecimentos.
- **❓ MANUAL**: abre este manual dentro do aplicativo. **◐**: alterna modo escuro/claro.
- **Seletor de idioma** (Español · English · Português): muda toda a interface na hora,
  sem recarregar. Seus dados não são traduzidos: um projeto aparece igual em qualquer
  idioma (só mudam os rótulos das Categorias Básicas e dos tipos de relação). A demo, o
  manual, o relatório acadêmico e os arquivos exportados saem no idioma escolhido.
- Seus dados ficam em `~/Library/Application Support/cualibre/` (Mac) ou `%APPDATA%\cualibre\` (Windows). Copiar essa pasta = backup completo.

## 3. Importar o corpus (faixa superior)

Escolha arquivos **PDF, DOCX, DOC ou TXT** (você pode selecionar vários). Cada documento é somado ao corpus com seu nome como título. Erros (arquivo danificado, PDF digitalizado sem texto) são avisados sem mexer no que já foi importado.

- **Word (DOCX e DOC)**: são lidos os parágrafos e também as **tabelas** (muitas
  transcrições vêm em tabelas falante | fala), na ordem em que aparecem. As **notas** (de
  rodapé e de fim) e as **caixas de texto** ficam no final do documento. Cabeçalhos,
  rodapés e comentários não são importados.
- **DOC** é o formato do Word 97-2003: é lido diretamente, sem ter o Word instalado e sem
  converter nada à mão. Também são aceitos os `.doc` que por dentro são RTF. Se o arquivo
  tiver **controle de alterações** pendente, aceite ou rejeite as alterações no Word antes
  de importar: em um `.doc`, o texto excluído ainda aparece. Documentos com senha e
  anteriores ao Word 97 precisam ser salvos antes como `.docx`.
- **TXT**: são aceitos UTF-8 (com ou sem BOM) e o formato "ANSI" do Bloco de Notas do
  Windows; as quebras de linha do Windows são normalizadas automaticamente.
- **PDFs digitalizados (OCR)**: se uma página é só imagem, o Cua-libre reconhece o texto
  com o OCR do próprio sistema (Vision no macOS, OCR do Windows), sem internet e sem
  enviar nada para fora do computador. Leva alguns segundos por página. O documento fica
  marcado com **OCR** (na lista de documentos e no título no Canvas) indicando quais
  páginas foram lidas assim: o OCR pode errar, então confira essas páginas com o
  original antes de citá-las.

## 4. Codificar no Pentagrama

### A Nuvem Negra (fluxo principal)

1. **Selecione** um trecho (3 ou mais caracteres) no Canvas.
2. A Nuvem aparece ao lado da seleção, com o cursor pronto no campo do nome.
3. Escolha a **categoria**: clique no seletor para abrir o menu, ou use as teclas **1–9** para uma Categoria Básica diretamente.
4. Escreva o nome do código e aperte **↵ Enter**.

O trecho fica pintado com a cor da categoria, o código entra no banco e as Análises são atualizadas.

### Categorias: Básicas e personalizadas

O Cua-libre traz **9 Categorias Básicas** de fábrica (Emocional, Descritivo, In Vivo,
Tensão/CHAT, Processo, Teórico, Relacional, Crítico, Método), sempre disponíveis e com
cores fixas. Ao abrir o seletor de categoria na Nuvem:

- As **categorias personalizadas** que você criou aparecem primeiro, prontas para escolher.
- **"Categorias Básicas ▸"** abre as 9 de fábrica num submenu lateral ao passar o cursor
  por cima (como os menus do iOS/Windows), ou com um clique se preferir.
- **"✚ Nova categoria…"** abre um mini-formulário: nome + uma cor (clicar no quadrado
  de cor abre o seletor do sistema) + **✓** para criá-la (ou Enter no nome). Ela fica
  disponível na hora neste projeto, no menu e na Paleta.

Para **excluir** uma categoria personalizada: painel "Categorias personalizadas" na
Paleta, botão ✕ no chip. Se houver códigos usando-a, você é avisado de quantos antes de
confirmar; o código mantém o nome da categoria e só perde a cor própria.

| Tecla na Nuvem | Ação |
|------------------|--------|
| `↵` | Salvar o código |
| `⌘↵` (Mac) / `Ctrl+↵` | Repetir a **última** codificação (mesmo nome e categoria) nesta seleção |
| `Esc` ou clique fora | Cancelar sem salvar |
| `1`–`9` | Escolher uma Categoria Básica diretamente |

### Outras formas de codificar

- **Arrastar até um código existente**: selecione um texto e arraste-o sobre um código
  do banco compacto na Paleta (coluna direita do Pentagrama) → é criada outra citação
  com esse mesmo código. O banco completo (com busca) fica na aba ▤ Códigos, mas esta
  cópia compacta na Paleta existe justamente para arrastar enquanto você lê o Canvas.
- **Código manual** (Paleta → PALETA DE CONTROLE): categoria + rótulo + memo, sem citação textual. Para códigos teóricos ou emergentes.

### Corrigir

- **✎** no banco: editar nome, categoria (a cor do destaque muda) e memo.
- **🗑** no banco: excluir um código (o destaque desaparece).
- **⌘Z / Ctrl+Z** (fora de um campo de texto): desfaz a **última** codificação.

## 5. Navegar e ler

| Comando | Ação |
|---------|--------|
| Abas acima do Canvas (`TODOS`, nomes de arquivo) | Ler um documento por vez ou o corpus completo |
| **⌘F / Ctrl+F** | Buscar texto no corpus: ocorrências com borda pontilhada vermelha, navegação **‹ ›** com contador; `Esc` no campo de busca limpa |
| Chips **FILTRO DE DESTAQUES** | Desligar/ligar os destaques de cada categoria; **◻ LEITURA LIMPA** desliga todos (os códigos não são apagados, só ocultados) |
| **⛶** (ao lado de "Canvas de análise") | **Modo imersão**: só o Canvas, centralizado. `Esc` sai |
| **Aa** | Alterna a tipografia do corpus: serifada ↔ máquina de escrever (Courier) |
| **№** | Mostra/oculta a **numeração de linhas** (os números não são copiados ao selecionar) |
| Clique no **nome de um código** (banco) | **Todas as suas citações** num painel, com «IR AO CANVAS →» para saltar a cada uma |
| Rolagem | Sua posição de leitura é lembrada por documento, entre sessões, e não se perde ao codificar |

## 6. Documentos do corpus (Paleta)

Lista com o número de códigos de cada documento. **🗑** exclui um documento: se ele tiver códigos, você é avisado de quantos serão perdidos antes de confirmar.

## 7. ⚡ PLN — análise lexical

- **Idioma do corpus** (espanhol, inglês ou português): aplica as palavras vazias
  (stopwords) e o modelo gramatical corretos. É um ajuste do projeto, compartilhado com
  Sentimento; é sugerido automaticamente ao importar o primeiro documento e você pode
  mudá-lo quando quiser. É independente do idioma da interface.
- **Comprimento mínimo**: descarta palavras curtas.
- **Foco gramatical**: conta **todas as palavras**, **só verbos**, **só substantivos** ou **só adjetivos**; ao filtrar, as flexões são agrupadas sob o lema (*cantó* e *cantaba* contam como *cantar*). Funciona sem internet, em espanhol, inglês e português.
- **Palavras a omitir**: escreva termos separados por vírgula e aperte **＋ OMITIR**; eles se **somam** à lista atual (chips abaixo do campo; ✕ remove um). Ideal para marcas de transcrição como `Entrevistado`. Ficam salvas por projeto.
- Três visualizações simultâneas: **nuvem de conceitos** (exportável com **⬇ PNG**), barras principais e tabela de contagem exata.
- **Concordâncias (KWIC)**: clique em qualquer palavra (na nuvem, nas barras ou na
  tabela) para ver **todas as suas ocorrências no corpus**, cada uma com o texto ao
  redor. Com o foco gramatical ativo, a busca é pelo **lema**: ao pedir "cantar" também
  aparecem "cantó" e "cantaba", com a forma real do texto. Cada ocorrência tem um botão
  **«IR AO CANVAS →»** que salta direto para lê-la no contexto completo.

## 8. ◫ Análises

- **Pizza** por categoria e **barras** de densidade por código.
- **Coocorrência**: matriz código × código que conta as citações que **se sobrepõem** no mesmo trecho (aparece com 2 ou mais códigos ancorados; mais escuro = mais coocorrências).
- **Códigos por documento**: distribuição de cada código entre os seus documentos.

Tudo se atualiza sozinho a cada codificação.

## 9. ◑ Sentimento

Analisa o **tom emocional** do corpus com o léxico aberto NRC EmoLex no idioma do corpus
(uso em pesquisa citando Mohammad & Turney 2013).

- **Instalação única do léxico**: os termos de uso do NRC não permitem redistribuir o
  léxico dentro do Cua-libre; por isso cada computador o obtém **uma única vez** do site
  oficial: botão **⬇ BAIXAR DO NRC** (≈ 25 MB; instala espanhol, inglês e português).
  Sem internet, **ESCOLHER .ZIP OFICIAL** aceita o arquivo NRC-Emotion-Lexicon.zip
  baixado em outro computador. Depois funciona sempre sem conexão.
- As versões em espanhol e português são **traduções automáticas** do inglês feitas
  pelos autores do léxico: revise em contexto as palavras com carga.

Tudo é **auditável**: cada valor vem acompanhado das palavras que o produziram.

- **Tom e arco emocional por documento**: valência global (−1 a +1) e sua trajetória
  parágrafo a parágrafo, mostrando onde o relato escurece ou se ilumina.
- **Tom por categoria e por código**: suas citações de "Tensão/CHAT" são mais negativas
  que as de "Relacional"? Barras divergentes a partir do eixo zero.
- **Emoções detectadas** (as 8 do NRC: alegria, tristeza, medo, raiva, confiança,
  antecipação, surpresa, nojo) e **ranking de palavras com carga** (± com contagens).
- **Auditar cada classificação**: clique numa **emoção** para ver exatamente quais
  palavras a dispararam no seu corpus; clique numa **palavra com carga** (positiva ou
  negativa) para o mesmo. Dali, clique em qualquer palavra para abrir suas
  **concordâncias** (todas as menções em contexto, com salto direto ao Canvas) e
  verificar com seus próprios olhos se a classificação automática faz sentido no seu
  corpus.
- Trata a **negação**: "no siento alegría" (não sinto alegria) inverte a polaridade de *alegría*.
- Limites honestos: a ironia e o sarcasmo escapam; use-o como bússola exploratória, não
  como veredito. Use sempre o léxico do idioma do corpus: um corpus em
  inglês analisado com o léxico em espanhol não é interpretável.
- Os **negadores** (*não, nada, nunca*…) só invertem a palavra seguinte; nunca contam
  como palavras com carga.
- **Corpus grandes**: na primeira vez que você abre Sentimento (ou o foco gramatical)
  sobre um corpus volumoso, o Cua-libre analisa cada documento uma única vez e mostra o
  avanço ("Analisando o corpus: 12 de 60 documentos…"). O resultado fica salvo: as
  consultas seguintes, mesmo em outra sessão, são imediatas.

### Ajustar o léxico ao seu corpus

O léxico é geral e traduzido: em um corpus concreto algumas palavras não significam o que
o léxico supõe (numa escola, *professor* não é necessariamente "confiança") e outras que
carregam emoção não estão nele. Por isso você pode ajustá-lo, palavra por palavra.

- Em **AJUSTAR O LÉXICO** aparecem as oito emoções e as duas polaridades (positivas e
  negativas), cada uma com seu número de menções. Um clique abre a lista completa das
  suas palavras no seu corpus (também um clique em uma barra de **EMOÇÕES DETECTADAS**).
- **✕ DESCARTAR** tira essa palavra da emoção ou polaridade em toda a análise. Ela fica
  na lista **DESCARTADAS**, com **↺ RESTAURAR** para devolvê-la.
- **＋ SOMAR** acrescenta uma palavra que falta. Ela é buscada no corpus pela forma e pelo
  lema (somar *brigar* encontra também *brigavam*), com a mesma regra de negação do
  léxico. Um particípio usado como adjetivo (*angustiado*) é somado assim mesmo: seu lema
  é ele mesmo. Se não aparecer, o Cua-libre avisa e o ajuste fica salvo mesmo assim.
- Cada ajuste recalcula tudo na hora: valências, arcos, tom por categoria e por código,
  emoções, palavras com carga e o tom mostrado no organizador de Relações.
- **SEUS AJUSTES AO LÉXICO** resume tudo o que mudou e permite desfazer cada ajuste ou
  voltar ao léxico original. Os ajustes são salvos por projeto e por idioma do corpus.
- Transparência: o relatório acadêmico declara os ajustes na nota metodológica e os
  detalha na seção de sentimento. Descartar e somar são decisões analíticas suas: vale a
  pena registrá-las também nos seus memos.

### Como a análise é produzida (racionalidade e método)

O Cua-libre foi projetado para **promover decisões 100% humanas**: a análise de
sentimento não interpreta por você nem escreve nada no seu banco de códigos. É uma
bússola exploratória que aponta zonas do corpus onde sua leitura atenta pode render mais.

**Racionalidade.** A análise usa um método **baseado em léxico**: uma lista fixa e pública
de palavras, cada uma com sua polaridade e suas emoções associadas, elaborada e validada
por pesquisadores. Esse método foi escolhido (e não redes neurais) por três razões que
importam na pesquisa qualitativa:

1. **Auditabilidade**: cada valor pode ser reconstruído à mão. Se um documento marca
   −0,4, a visualização mostra exatamente quais palavras o produziram e quantas vezes;
   você pode vê-las em contexto e julgar se o número diz algo. Nada fica numa caixa-preta.
2. **Replicabilidade**: com o mesmo texto e o mesmo léxico, o resultado é sempre o mesmo,
   em qualquer máquina, sem conexão com a internet. Outro pesquisador pode repetir sua
   análise e obter valores idênticos.
3. **Defesa metodológica**: numa seção de métodos você pode descrever o procedimento
   completo num parágrafo e citar a fonte do léxico. Com um modelo neural você só poderia
   dizer "o modelo classificou assim".

O custo dessa transparência é conhecido: o léxico não capta ironia, sarcasmo nem duplos
sentidos. Por isso os valores são **insumo para a sua interpretação**, nunca seu
substituto.

**Processamento, passo a passo.**
1. Cada texto é tokenizado e **lematizado** com o spaCy (*lloraba* → *llorar*), para que
   as flexões encontrem sua entrada no léxico.
2. Cada palavra (pela forma ou pelo lema) é buscada no léxico: se existir, contribui com
   sua polaridade (+1 ou −1) e suas emoções associadas.
3. **Negação**: se entre as 3 palavras anteriores houver um negador (*no, nunca, sin,
   jamás, ni, tampoco, nada, nadie, ninguno/a*), a polaridade dessa palavra se inverte.
4. A **valência** de um texto é a média das contribuições: (positivas − negativas) /
   total de palavras com carga → um valor entre −1 e +1.
5. O **arco emocional** repete o cálculo parágrafo a parágrafo (até 40 trechos), seguindo
   a ideia do pacote *syuzhet* de M. Jockers para trajetórias narrativas.

**Fontes.** O léxico é o **NRC Word–Emotion Association Lexicon (EmoLex)** de Saif
Mohammad e Peter Turney (National Research Council Canada): ~14.000 palavras anotadas por
crowdsourcing com polaridade e 8 emoções (alegria, tristeza, medo, raiva, confiança,
antecipação, surpresa, nojo), com traduções automáticas para mais de cem idiomas. O
Cua-libre usa as entradas de uma só palavra em espanhol, inglês e português,
convertidas no seu computador a partir do arquivo oficial. Uso livre para pesquisa; **cite**: Mohammad, S. & Turney, P.
(2013). *Crowdsourcing a Word–Emotion Association Lexicon*. Computational Intelligence,
29(3), 436–465.

**Para continuar lendo.** Liu, B. (2012), *Sentiment Analysis and Opinion Mining* (o
manual clássico da área); Jockers, M., vinheta do pacote *syuzhet* (arcos narrativos); e
saifmohammad.com para o léxico NRC e suas atualizações.

## 10. ▤ Códigos

O banco de códigos completo, com busca e mesclagem.

- **Buscar no banco**: filtra por nome do código, categoria ou texto da citação, sem
  mexer no Canvas nem no servidor.
- **⇄ Mesclar códigos** (codificação axial): escolha um código de origem, escreva o nome
  de destino (um existente ou um novo) e confirme. Se o destino já existia, todas as
  citações mescladas adotam a categoria dele; se é um nome novo, cada citação mantém a
  sua. As relações que envolviam o código de origem migram sozinhas para o novo nome;
  nunca se perdem ao mesclar.
- Editar (✎) e excluir (🗑) funcionam igual à Paleta: é o mesmo banco, com mais espaço.
- Com milhares de códigos, o banco é desenhado em partes: **Mostrar mais** no fim da
  lista carrega a parte seguinte.

## 11. ▥ Livro de códigos

O lugar para dar conteúdo a cada código e a cada categoria: o que na pesquisa
qualitativa se chama livro de códigos (*codebook*).

- À esquerda, o **índice**: cada categoria com seus códigos, a quantidade de citações e
  uma marca ● (já descrito) ou ○ (sem descrição). Acima, a busca e o avanço
  ("3 de 11 códigos descritos").
- À direita, a **ficha** do código escolhido, com quatro partes: **definição**, **quando
  usar** (critérios de inclusão), **quando não usar** (critérios de exclusão e diferenças
  em relação a códigos próximos) e **exemplo**. O exemplo pode ser tomado diretamente de
  uma das suas citações com o seletor abaixo.
- As categorias (Básicas e próprias) têm sua própria ficha: definição, quando usar e
  quando não usar.
- Salva sozinho enquanto você escreve e ao sair do campo (você verá "✓ Salvo"). Não é
  preciso apertar nada.
- A ficha reúne também o que já existe sobre o código: os memos das suas citações, suas
  relações e as primeiras citações, com **VER AS CITAÇÕES** para ler todas.
- **◀ ANTERIOR / SEGUINTE ▶** percorrem o livro ficha por ficha, como um livro.
- Se um código fica sem citações (você o apagou ou desfez a codificação), sua descrição
  **não se perde**: passa para **DESCRIÇÕES SEM CÓDIGO** e volta sozinha se você codificar
  de novo com esse nome. Ao **fundir** códigos, as duas descrições se somam na do destino.
- **⬇ CSV** baixa o livro completo como tabela. O livro também vai no backup .zip, no
  intercâmbio REFI-QDA (como descrição de cada código) e no relatório acadêmico.

## 12. ◈ Relações

1. Escolha a origem → **tipo** → o destino → **◉ CRIAR RELAÇÃO**. Origem e destino podem
   ser **códigos** ou **categorias** (os seletores mostram os dois grupos): você pode
   relacionar um código com uma categoria ou duas categorias entre si.
2. Tipos: **hierarquia** (contém), **associação**, **causalidade** (influencia), **contradição** (tensiona).
3. **Organizador (grafo)**: os códigos são círculos e as categorias, quadrados; as arestas
   têm estilo e letra por tipo (H/A/C/T). Exportável com **⬇ PNG** (para inserir em
   documentos) ou **⬇ SVG** (editável no Illustrator/Inkscape).
4. **Manipular o esquema**: arraste qualquer nó para organizá-lo; as posições são
   salvas. Para mover vários de uma vez, escolha-os com **Shift + clique** ou arrastando
   um retângulo sobre o fundo vazio, e arraste qualquer um deles: o grupo se move junto.
   **↶ DESFAZER MOVIMENTO** devolve os nós para onde estavam (não mexe em cores nem
   formas). **↺ REORGANIZAR** volta à disposição em círculo. Em Relações, ⌘Z não desfaz
   codificações: use o botão.
   - **Simbologia**: o Cua-libre propõe uma simbologia nativa (● código, ■ CATEGORIA com
     borda grossa e nome em maiúsculas). No painel de um nó, **FORMA** permite escolher
     círculo, quadrado, losango, hexágono ou **caixa com o nome dentro**, para um ou para
     todos os selecionados; **Nativa** a restaura. As categorias mantêm sua borda grossa
     com qualquer forma, e a legenda mostra as formas em uso.
   - **Bloquear**: **🔒 BLOQUEAR** no painel fixa os nós escolhidos (um cadeado indica);
     não são arrastados e REORGANIZAR os respeita. **🔒 BLOQUEAR QUADRO** fixa o quadro
     inteiro, útil antes de exportar ou apresentar: cores e formas ainda podem mudar,
     mas nada se move.
   - **⛶ AMPLIAR** leva o organizador quase à tela cheia, com o criador de relações
     incluído; **Esc** ou **✕ SAIR DO AMPLIADO** volta.
   - **Tipos de linha**: a hierarquia é uma linha grossa com um losango na origem (A
     contém B: ordena categorias e subcódigos), a associação é tracejada (vínculo sem
     afirmar causa), a causalidade é contínua com seta (A produz ou condiciona B) e a
     contradição é pontilhada com uma marca de choque (oposições e tensões). Ao escolher
     o tipo aparece um guia de quando usá-lo, e a legenda os desenha.
5. **Mudar cores**: clique em um nó ou em uma relação (sua letra ou sua linha) para abrir
   um painel abaixo do organizador com o seletor de **COR**. **↺ COR DA CATEGORIA** e
   **↺ PRETO** desfazem a mudança. Em uma relação, **⇄ INVERTER SENTIDO** troca A → B
   por B → A sem perder sua cor. A cor é só do quadro: não muda a cor da categoria no
   resto do aplicativo. O tipo de relação continua sendo distinguido pelo traço e pela
   letra, nunca só pela cor.
6. **Vários quadros por projeto**: **QUADRO** escolhe qual ver. O **geral** mostra sempre
   todas as relações. **+ NOVO** cria um quadro próprio, que começa vazio e mostra só o
   que você colocar nele: **＋ ADICIONAR** coloca um código ou uma categoria, e cada
   relação criada com esse quadro aberto adiciona suas duas pontas. Útil para montar um
   esquema por pergunta de pesquisa ou por capítulo. As relações são do projeto:
   **＋ TRAZER RELAÇÃO** soma ao quadro uma que já existe, e criar com o quadro aberto
   uma relação que já existia também a traz (não se duplica). ✎ renomeia e 🗑 exclui o quadro (as
   relações continuam no projeto).
7. **◑ TOM**: mostra sobre cada nó a valência média das suas citações (de −1 a +1) e
   quantas são, com seus ajustes do léxico (ver ◑ Sentimento). Requer o léxico instalado.
8. **Árvore de hierarquia**: montada automaticamente a partir das relações "contém".
9. Se um código ou uma categoria própria desaparece do projeto, suas relações e seus nós
   nos quadros são limpos automaticamente; ao fundir códigos, migram para o novo nome.

## 13. ⚖ Acordo entre codificadores

Compara a codificação de duas pessoas sobre o mesmo corpus, como apoio à discussão
metodológica da equipe.

1. Quem prepara o corpus exporta o **🗄 Backup completo (.zip)**.
2. A outra pessoa o abre com **⤒ IMPORTAR** e codifica na própria cópia.
3. Quem compara importa o projeto do colega (ou o .zip), volta ao próprio projeto (A),
   abre **⚖ ACORDO**, escolhe o projeto do colega (B) e aperta **⚖ CALCULAR ACORDO**.

Os documentos são pareados pelo **texto** (ainda que o arquivo tenha outro nome). Para
cada código são informados o **percentual de acordo**, o **kappa de Cohen** e o **alfa
de Krippendorff**, com o **caractere** como unidade de análise (o critério do NVivo),
além do kappa médio e dos valores globais. As faixas de Landis e Koch (1977) são apenas
orientativas. Clicar num código mostra os **trechos em desacordo** (quem os codificou e
onde), com salto ao Canvas para discuti-los. **⬇ CSV** exporta a tabela. Nada disso
altera o banco de códigos: as decisões continuam sendo da equipe.

## 14. ⇄ Exportar

Tabela completa do banco e **download em CSV** UTF-8 com BOM: abre no Excel com acentos e ç intactos. Colunas: id, data, documento, categoria, código, citação, memo.

**📄 Relatório acadêmico**: gera um documento HTML autocontido com TODO o projeto: nota
metodológica com citações formais (e a declaração de análise 100% humana), livro de
códigos com suas definições, citações agrupadas por categoria e código com seus memos,
gráficos, matrizes de coocorrência, todos os quadros organizadores e análise de
sentimento com seus ajustes do léxico. Abre numa nova aba:
**⌘P** para salvá-lo como PDF (anexo pronto para tese ou artigo) ou **⌘S** para salvar
o HTML.

**⇆ REFI-QDA (.qdpx)**: o projeto no padrão aberto de intercâmbio entre programas de
análise qualitativa. Abra-o no **NVivo, ATLAS.ti, MAXQDA ou QualCoder** para trabalhar
com colegas que usam outro software. As categorias viram códigos pai (com sua cor), cada
código mantém suas citações e memos, e as relações viram vínculos. O seletor ao lado do
botão escolhe o destino: **Padrão** (ATLAS.ti, MAXQDA, QualCoder) ou **NVivo**, porque o
NVivo para Windows conta as posições do texto de outra forma. **⤒ IMPORTAR** também abre
arquivos .qdpx desses programas: a hierarquia de códigos é mantida como categorias e
relações de hierarquia, a convenção de posições é detectada sozinha, e você é avisado se
fontes que não são texto (imagem, áudio, vídeo) ficaram de fora.

**🗄 Backup completo (.zip)**: um arquivo autocontido com o projeto inteiro:
`proyecto.json` (fidelidade total: corpus, códigos, relações, memos, categorias
próprias; reabra-o com **⤒ IMPORTAR**), `codigos.csv`, `livro_de_codigos.csv` e o texto de cada documento em
`.txt`. Pensado para depositar como evidência de reprodutibilidade ao publicar, ou como
cópia portátil independente do aplicativo.

## 15. 📚 Biblioteca

Sua literatura, **comum a todos os seus projetos**: ler, anotar e codificar sem sair do
Cua-libre. Os arquivos originais nunca são modificados.

- **Adicionar**: **📥 ADICIONAR PDF, DOCX, DOC ou TXT** copia os documentos para a
  biblioteca (o mesmo arquivo não se duplica). Se o documento traz seu **DOI**, a ficha se
  completa sozinha com os dados do Crossref; se não, complete-a à mão em **FICHA**.
- **Ler**: **ABRIR** mostra o PDF com suas páginas reais (− / + para o zoom). Word e TXT
  são lidos como texto contínuo. Um PDF digitalizado sem texto pode ser lido, mas não
  anotado sobre o texto.
- **Anotar**: selecione um trecho e aparece um menu que some ao terminar: quatro cores para
  **destacar**, **sublinhar**, **riscar** e **✎ nota**. Em **ANOTAÇÕES** você vê todas,
  com sua página, para comentar ou excluir; um clique em uma marca do documento a destaca
  no painel. **⬇ CSV** baixa o caderno de leitura.
- **Codificar**: no mesmo menu, **◉ CODIFICAR** usa os códigos e categorias do **projeto
  ativo**. Um nome novo é criado como código manual do projeto. Os trechos da literatura
  são registrados **à parte do corpus**: não contam em Análises, coocorrência, sentimento
  nem acordo. No **▥ LIVRO** de códigos, cada ficha mostra suas **citações da literatura**,
  com um botão para abri-las no leitor.
- **Ficha e referências**: tipo (artigo, livro, capítulo, tese, relatório), autoria, ano,
  revista ou livro, páginas, DOI… com sua referência em **APA 7** à vista. **⟳ COMPLETAR
  PELO DOI** a preenche pela internet. **⬇ BibTeX** e **⬇ RIS** exportam a biblioteca para
  Zotero, Mendeley ou EndNote. O relatório acadêmico acrescenta a literatura codificada e
  a lista de **Referências** do projeto.
- **Busca no OpenAlex**: busca por conceitos (título, ano, citações, link DOI); **＋ À
  BIBLIOTECA** salva a referência com sua ficha completa.
- Na biblioteca, ⌘Z não desfaz codificações do corpus: exclua a marca pelo painel.

A busca no OpenAlex e a consulta de metadados por DOI são, com o download único do léxico
de sentimento, as únicas coisas que exigem internet; sem conexão, todo o resto segue
igual.

## 16. ◷ Sessão de foco

Ao abrir o aplicativo (ou com um clique em **◷ sessão** na barra inferior) você pode
definir uma **meta** ("codificar a entrevista 3") e um bloco de **15/25/50/90 minutos**,
ou **PULAR**. O indicador mostra o tempo restante e quantos códigos você fez na sessão;
ao terminar, um aviso suave sugere a pausa (sem alarmes).

## 17. ♫ Música de foco (barra inferior)

Coloque seus arquivos de áudio (mp3, m4a, ogg, wav, flac) na pasta `musica/` junto aos seus dados; **clicar no título da barra** mostra o caminho exato. `▶` toca em loop, `⏭` pula a faixa, e o volume é lembrado.

## 18. Tabela rápida de atalhos

| Atalho | Ação |
|-------|--------|
| `↵` (na Nuvem) | Salvar código |
| `⌘↵` (na Nuvem) | Repetir a última codificação |
| `Esc` | Cancelar a Nuvem / sair da imersão / limpar a busca |
| `1`–`9` (na Nuvem) | Escolher categoria |
| `⌘F` / `Ctrl+F` | Buscar no corpus |
| `⌘Z` / `Ctrl+Z` | Desfazer a última codificação |
| Arrastar seleção → código do banco | Reaplicar esse código |

## 19. Solução de problemas

- **O Mac diz que o aplicativo não pode ser aberto**: acontece só na primeira vez, porque o aplicativo não está assinado com certificado da Apple. No macOS 15 (Sequoia) ou posterior: *Ajustes do Sistema → Privacidade e Segurança → Abrir Mesmo Assim*. No macOS 14 ou anterior: clique com o botão direito no aplicativo → Abrir.
- **Não abre em outro Mac / não acontece nada**: o mais provável é o **DMG errado para o chip**. Há dois instaladores: um para Mac **Intel** e outro para Mac **Apple Silicon (M1/M2/M3/M4)**, e eles não são intercambiáveis (ao contrário do Rosetta, que só traduz Intel → Apple Silicon, nunca o inverso). Nesse Mac, vá ao menu  → *Sobre Este Mac* para ver qual é o chip, e baixe o DMG correspondente. Também é preciso **macOS 10.15 (Catalina) ou superior**.
- **O Windows SmartScreen mostra um aviso**: "Mais informações → Executar assim mesmo".
- **O navegador não abre sozinho**: acesse manualmente `http://127.0.0.1:8734`.
- **"Não foi possível conectar ao servidor"**: o aplicativo não está rodando; abra-o de novo.
- **Recuperar trabalho**: tudo está em `.../cualibre/projects/*.json`; esse arquivo é o seu projeto completo, legível e fácil de copiar. Um projeto excluído fica em `.../cualibre/papelera/`: importe-o com **⤒ IMPORTAR** para recuperá-lo.
- **Sentimento demora na primeira vez com um corpus muito grande**: é a análise inicial
  de cada documento (feita uma única vez e guardada em `.../cualibre/cache/`, pasta que
  pode ser apagada sem risco).
- **Windows**: os atalhos usam `Ctrl` onde este manual diz `⌘`.
- **A janela própria não abre no Windows**: falta o componente WebView2 (vem com o Windows
  11 e com o Windows 10 atualizado). O Cua-libre abre então no navegador; você pode
  instalar o WebView2 pelo site da Microsoft. As mensagens técnicas ficam em
  `%APPDATA%\cualibre\logs\cualibre.log`.
- **Um PDF digitalizado não é lido**: o computador não tem OCR disponível (Windows sem
  idioma de OCR instalado, ou macOS anterior ao 10.15). No macOS, o OCR em espanhol e
  português exige macOS 11 ou superior.
