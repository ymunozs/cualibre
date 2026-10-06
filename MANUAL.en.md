# CUA-LIBRE STUDIO — User manual (v1.13)

A complete guide to the commands and workflows for qualitative analysis.

## 1. Starting and quitting

| How | What it does |
|------|----------|
| Double-click the installed app, or `./start.sh` / `start.bat` | Opens Cua-libre in **its own window** |
| Close the window (or ⌘Q on a Mac) | Shuts the application down. Your work is already saved |
| `./start.sh --navegador` | Uses the browser instead of its own window (**⏻ QUIT** button in the header to shut it down) |

If its own window cannot open (for example, on an old Windows without the WebView2 component), Cua-libre falls back to your browser automatically. In its own window, exporting a file opens the system's **Save as** dialog, and the academic report opens in your browser so you can print it to PDF.

If the app is already running and you open it again, it simply reuses that instance.

## 2. Projects (header)

- **PROJECT selector**: switch between your studies; each project keeps its own corpus, codes, memos and relationships.
- **+ NEW** / **✎ RENAME**: create a project or rename the active one.
- **⤒ IMPORT**: opens a project from a **.zip backup** (the one produced by ⇄ Export →
  🗄 Full backup) or from a project `.json` file, or a `.qdpx` from NVivo, ATLAS.ti, MAXQDA or QualCoder
  (see ⇄ Export). It comes in as a new project and never
  overwrites anything: use it to move your work to another computer (Mac ↔ Windows) or to
  share a project with colleagues.
- **🗑** (next to IMPORT): deletes the active project after confirmation. It is not erased
  from the disk: it is moved to the `papelera/` (bin) folder of your data, from which you
  can recover it.
- **🎓 DEMO**: creates an example project (a fictional interview, already coded, with
  relationships and exclusions) so you can explore every feature without risk.
- **💾 SAVE**: forces a save and confirms the time. The dot beside it **pulses red** with every automatic save (which happens by itself after every action).
- **🕐 HISTORY**: opens your project's backup history. Cua-libre keeps a full copy every
  10 minutes of work (at most) and an extra copy each time you press 💾 SAVE. Pick any
  point in the list and press **↺** to restore the project to that moment; the state just
  before restoring is also backed up, so a mistake never costs you work.
- **ℹ ABOUT**: the project's philosophy, contact details and acknowledgements.
- **❓ MANUAL**: opens this manual inside the app. **◐**: toggles dark/light mode.
- **Language selector** (Español · English · Português): switches the whole interface
  instantly, without reloading. Your data is never translated: a project looks the same
  in any language (only the labels of the Basic Categories and relationship types change).
  The demo, the manual, the academic report and exported files use the chosen language.
- Your data lives in `~/Library/Application Support/cualibre/` (Mac) or `%APPDATA%\cualibre\` (Windows). Copying that folder = a complete backup.

## 3. Importing the corpus (top strip)

Choose **PDF, DOCX, DOC or TXT** files (you can select several). Each document is added to the corpus with its name as a heading. Errors (a damaged file, a scanned PDF without text) are reported without touching what has already been imported.

- **Word (DOCX and DOC)**: paragraphs are read, and so are **tables** (many transcripts
  come as speaker | turn tables), in the order in which they appear. **Notes** (footnotes
  and endnotes) and **text boxes** are placed at the end of the document. Headers, footers
  and comments are not imported.
- **DOC** is the Word 97-2003 format: it is read directly, without Word installed and
  without converting anything by hand. A `.doc` that is really RTF inside is accepted too.
  If the file has pending **tracked changes**, accept or reject them in Word before
  importing: in a `.doc`, deleted text still appears. Password-protected documents and
  those older than Word 97 must first be saved as `.docx`.
- **TXT**: UTF-8 (with or without BOM) and Windows Notepad's "ANSI" format are accepted;
  Windows line breaks are normalised automatically.
- **Scanned PDFs (OCR)**: if a page is only an image, Cua-libre recognises its text with the
  system's own OCR (Vision on macOS, Windows OCR), offline and without sending anything
  off the computer. It takes a few seconds per page. The document is marked **OCR** (in
  the document list and in its Canvas heading) showing which pages were read this way:
  OCR can make mistakes, so check those pages against the original before quoting them.

## 4. Coding in the Stave

### The Black Cloud (main workflow)

1. **Select** a passage (3+ characters) in the Canvas.
2. The Cloud appears next to the selection, with the cursor ready in the name field.
3. Choose the **category**: click the selector to open the menu, or use keys **1–9** to pick a Basic Category directly.
4. Type the code name and press **↵ Enter**.

The passage is painted in the category's colour, the code goes into the bank and Analytics are updated.

### Categories: Basic and custom

Cua-libre comes with **9 Basic Categories** (Emotional, Descriptive, In Vivo,
Tension/CHAT, Process, Theoretical, Relational, Critical, Method), always available and
with fixed colours. When you open the category selector in the Cloud:

- The **custom categories** you have created appear first, ready to choose.
- **"Basic Categories ▸"** opens the 9 built-in ones in a side submenu when you hover
  over it (like iOS/Windows menus), or with a click if you prefer not to use hover.
- **"✚ New category…"** opens a small form: name + a colour (clicking the colour square
  opens the system picker) + **✓** to create it (or Enter in the name). It is available
  immediately in this project, in the menu and in the Palette.

To **delete** a custom category: "Custom categories" panel in the Palette, ✕ button on
its chip. If codes are using it, you are told how many before confirming; the code keeps
its category name and only loses its own colour.

| Key in the Cloud | Action |
|------------------|--------|
| `↵` | Save the code |
| `⌘↵` (Mac) / `Ctrl+↵` | Repeat the **last** coding (same name and category) on this selection |
| `Esc` or click outside | Cancel without saving |
| `1`–`9` | Choose a Basic Category directly |

### Other ways to code

- **Drag onto an existing code**: select text and drag it onto a code in the compact
  bank in the Palette (right-hand column of the Stave) → another quote is created with
  that same code. The full bank (with search) lives in the ▤ Codes tab, but this compact
  copy in the Palette exists precisely so you can drag while reading the Canvas.
- **Manual code** (Palette → CONTROL PALETTE): category + label + memo, without a textual quote. For theoretical or emerging codes.

### Correcting

- **✎** in the bank: edit the name, category (the highlight colour changes) and memo.
- **🗑** in the bank: delete a code (its highlight disappears).
- **⌘Z / Ctrl+Z** (outside a text field): undoes the **last** coding.

## 5. Navigating and reading

| Command | Action |
|---------|--------|
| Tabs above the Canvas (`ALL`, file names) | Read one document at a time or the whole corpus |
| **⌘F / Ctrl+F** | Search the corpus: matches get a dotted red border, **‹ ›** navigation with a counter; `Esc` in the search box clears it |
| **HIGHLIGHT FILTER** chips | Turn each category's highlights off/on; **◻ CLEAN READING** turns them all off (codes are not deleted, only hidden) |
| **⛶** (next to "Analysis Canvas") | **Immersion mode**: only the Canvas, centred. `Esc` exits |
| **Aa** | Switches the corpus typeface: serif ↔ typewriter (Courier) |
| **№** | Shows/hides **line numbers** (numbers are not copied when you select text) |
| Click a **code name** (bank) | **All its quotes** in a panel, with «GO TO CANVAS →» to jump to each one |
| Scrolling | Your reading position is remembered per document, across sessions, and is not lost when you code |

## 6. Corpus documents (Palette)

A list with the number of codes in each document. **🗑** deletes a document: if it has codes, you are told how many will be lost before confirming.

## 7. ⚡ NLP — lexical analysis

- **Corpus language** (Spanish, English or Portuguese): applies the right stop words and
  grammatical model. It is a project setting shared with Sentiment; it is suggested
  automatically when the first document is imported and you can change it at any time.
  It is independent of the interface language.
- **Minimum length**: discards short words.
- **Grammatical focus**: counts **all words**, **verbs only**, **nouns only** or **adjectives only**; when filtering, inflected forms are grouped under their lemma (*sang* and *singing* count as *sing*). Works offline, in Spanish, English and Portuguese.
- **Words to exclude**: type terms separated by commas and press **＋ EXCLUDE**; they are **added** to the current list (chips under the field; ✕ removes one). Ideal for transcription markers such as `Interviewee`. They are saved per project.
- Three simultaneous views: **concept cloud** (exportable with **⬇ PNG**), top bars and an exact count table.
- **Concordances (KWIC)**: click any word (in the cloud, the bars or the table) to see
  **every occurrence in the corpus**, each with its surrounding text. With grammatical
  focus on, it searches by **lemma**: asking for "sing" also finds "sang" and "singing",
  showing the actual form in the text. Each occurrence has a **«GO TO CANVAS →»** button
  that jumps straight to it in its full context.

## 8. ◫ Analytics

- A **pie chart** by category and **bars** showing the density of each code.
- **Co-occurrence**: a code × code matrix counting quotes that **overlap** on the same passage (appears with 2+ anchored codes; darker = more co-occurrences).
- **Codes by document**: how each code is distributed across your documents.

Everything updates by itself with every coding.

## 9. ◑ Sentiment

Analyses the **emotional tone** of the corpus with the open NRC EmoLex lexicon in the
corpus language (research use, citing Mohammad & Turney 2013).

- **One-off lexicon installation**: the NRC's terms of use do not allow redistributing the
  lexicon inside Cua-libre, so each computer obtains it **once** from the official
  website: **⬇ DOWNLOAD FROM THE NRC** (≈ 25 MB; installs Spanish, English and
  Portuguese). Without internet, **CHOOSE OFFICIAL .ZIP** accepts the
  NRC-Emotion-Lexicon.zip file downloaded on another computer. After that it always
  works offline.
- The Spanish and Portuguese versions are **machine translations** from English made by
  the lexicon's authors: check charged words in context.

Everything is **auditable**: each score comes with the words that produced it.

- **Tone and emotional arc by document**: overall valence (−1 to +1) and its trajectory
  paragraph by paragraph, showing where the account darkens or brightens.
- **Tone by category and by code**: are your "Tension/CHAT" quotes more negative than the
  "Relational" ones? Diverging bars from the zero axis.
- **Emotions detected** (NRC's 8: joy, sadness, fear, anger, trust, anticipation,
  surprise, disgust) and a **ranking of charged words** (± with counts).
- **Audit each classification**: click an **emotion** to see exactly which words
  triggered it in your corpus; click a **charged word** (positive or negative) for the
  same. From there, click any word to open its **concordances** (all its mentions in
  context, with a direct jump to the Canvas) and check with your own eyes whether the
  automatic classification makes sense in your corpus.
- Handles **negation**: "no siento alegría" (I don't feel joy) reverses the polarity of *alegría*.
- Honest limits: irony and sarcasm escape it; use it as an exploratory compass, not as a
  verdict. Always use the lexicon of the corpus language: an English
  corpus analysed with the Spanish lexicon cannot be interpreted.
- **Negators** (*not, no, never*…) only reverse the following word; they never count
  as charged words themselves.
- **Large corpora**: the first time you open Sentiment (or grammatical focus) on a large
  corpus, Cua-libre analyses each document once and shows its progress ("Analysing the
  corpus: 12 of 60 documents…"). The result is stored: later queries, even in another
  session, are immediate.

### How the analysis is produced (rationale and method)

Cua-libre is designed to **promote 100% human decisions**: sentiment analysis does not
interpret for you and never writes anything into your code bank. It is an exploratory
compass that points to areas of the corpus where your close reading may pay off.

**Rationale.** The analysis uses a **lexicon-based** method: a fixed, public list of
words, each with its polarity and associated emotions, compiled and validated by
researchers. This method was chosen (rather than neural networks) for three reasons that
matter in qualitative research:

1. **Auditability**: every score can be rebuilt by hand. If a document scores −0.4, the
   view shows you exactly which words produced it and how many times; you can go and see
   them in context and judge whether the number says anything. Nothing stays inside a
   black box.
2. **Replicability**: with the same text and the same lexicon, the result is always the
   same, on any machine, without an internet connection. Another researcher can repeat
   your analysis and obtain identical values.
3. **Methodological defensibility**: in a methods section you can describe the whole
   procedure in one paragraph and cite the source of the lexicon. With a neural model you
   could only say "the model classified it that way".

The cost of this transparency is well known: the lexicon does not capture irony, sarcasm
or double meanings. That is why scores are **input for your interpretation**, never its
replacement.

**Processing, step by step.**
1. Each text is tokenised and **lemmatised** with spaCy (*lloraba* → *llorar*), so that
   inflected forms find their entry in the lexicon.
2. Each word (by its form or its lemma) is looked up in the lexicon: if it is there, it
   contributes its polarity (+1 or −1) and its associated emotions.
3. **Negation**: if one of the 3 preceding words is a negator (*no, nunca, sin, jamás,
   ni, tampoco, nada, nadie, ninguno/a*), that word's polarity is reversed.
4. A text's **valence** is the average of the contributions: (positive − negative) /
   total charged words → a value between −1 and +1.
5. The **emotional arc** repeats the calculation paragraph by paragraph (up to 40
   sections), following the idea of M. Jockers' *syuzhet* package for narrative
   trajectories.

**Sources.** The lexicon is the **NRC Word–Emotion Association Lexicon (EmoLex)** by Saif
Mohammad and Peter Turney (National Research Council Canada): ~14,000 words annotated by
crowdsourcing with polarity and 8 emotions (joy, sadness, fear, anger, trust,
anticipation, surprise, disgust), with machine translations into more than a hundred
languages. Cua-libre uses the single-word entries in Spanish, English and Portuguese,
converted on your computer from the official file. Free for research use; **cite**: Mohammad, S. & Turney,
P. (2013). *Crowdsourcing a Word–Emotion Association Lexicon*. Computational
Intelligence, 29(3), 436–465.

**Further reading.** Liu, B. (2012), *Sentiment Analysis and Opinion Mining* (the classic
handbook of the field); Jockers, M., vignette of the *syuzhet* package (narrative arcs);
and saifmohammad.com for the NRC lexicon and its updates.

## 10. ▤ Codes

The complete code bank, with search and merging.

- **Search the bank**: filters by code name, category or quote text, without touching
  the Canvas or the server.
- **⇄ Merge codes** (axial coding): choose a source code, type the target name (an
  existing one or a new one) and confirm. If the target already existed, all merged
  quotes take its category; if it is a new name, each quote keeps its own. Relationships
  involving the source code move to the new name by themselves; they are never lost by
  merging.
- Edit (✎) and delete (🗑) work just as in the Palette: it is the same bank, with more
  room.
- With thousands of codes, the bank is drawn in batches: **Show more** at the end of the
  list loads the next batch.

## 11. ◈ Relationships

1. Choose a source code → **type** → target code → **◉ CREATE RELATIONSHIP**.
2. Types: **hierarchy** (contains), **association**, **causality** (influences), **contradiction** (is in tension with).
3. **Organiser (graph)**: nodes coloured by category, edges with a style and letter per type (H/A/C/T). Exportable with **⬇ PNG** (to insert in documents) or **⬇ SVG** (editable in Illustrator/Inkscape).
4. **Hierarchy tree**: built automatically from the "contains" relationships.
5. If a code disappears from the project, its relationships are cleaned up automatically.

## 12. ⚖ Intercoder agreement

Compares how two people coded the same corpus, to support the team's methodological
discussion.

1. Whoever prepares the corpus exports the **🗄 Full backup (.zip)**.
2. The other person opens it with **⤒ IMPORT** and codes their own copy.
3. Whoever compares imports their colleague's project (or its .zip), returns to their own
   project (A), opens **⚖ AGREEMENT**, chooses the colleague's project (B) and presses
   **⚖ CALCULATE AGREEMENT**.

Documents are matched by their **text** (even if the file has another name). For each
code the **percentage agreement**, **Cohen's kappa** and **Krippendorff's alpha** are
reported, with the **character** as the unit of analysis (NVivo's criterion), plus the
mean kappa and overall values. The Landis and Koch (1977) bands are for guidance only.
Clicking a code shows the **passages in disagreement** (who coded them and where), with a
jump to the Canvas to discuss them. **⬇ CSV** exports the table. None of this changes the
code bank: the decisions remain the team's.

## 13. ⇄ Export

The full table of the bank and a **CSV download** in UTF-8 with BOM: it opens in Excel with accents intact. Columns: id, date, document, category, code, quote, memo.

**📄 Academic report**: generates a self-contained HTML document with the WHOLE project:
a methodological note with formal citations (and the statement of 100% human analysis),
the codebook, quotes grouped by category and code with their memos, charts,
co-occurrence matrices, the relationship organiser and the sentiment analysis. It opens
in a new tab: **⌘P** to save it as PDF (an appendix ready for a thesis or paper) or
**⌘S** to save the HTML.

**⇆ REFI-QDA (.qdpx)**: the project in the open exchange standard for qualitative
analysis software. Open it in **NVivo, ATLAS.ti, MAXQDA or QualCoder** to work with
colleagues who use other software. Categories become parent codes (with their colour),
each code keeps its quotes and memos, and relationships become links. The selector next
to the button chooses the target: **Standard** (ATLAS.ti, MAXQDA, QualCoder) or
**NVivo**, because NVivo for Windows counts text positions differently. **⤒ IMPORT** also
opens .qdpx files from those programs: the code hierarchy is kept as categories and
hierarchy relationships, the position convention is detected automatically, and you are
told if any non-text sources (image, audio, video) were left out.

**🗄 Full backup (.zip)**: a self-contained file with the entire project:
`proyecto.json` (full fidelity: corpus, codes, relationships, memos, custom categories;
reopen it with **⤒ IMPORT**), `codes.csv` and the text of every document as `.txt`.
Designed to be deposited as reproducibility evidence when publishing, or as a portable
copy independent of the app.

## 14. 📚 Literature

Concept search in **OpenAlex** (title, year, citations, DOI link). Together with the one-off download of the sentiment lexicon, the only thing that needs the internet; without a connection, the rest of the app works as usual.

## 15. ◷ Focus session

When you open the app (or by clicking **◷ session** in the bottom bar) you can set a
**goal** ("code interview 3") and a block of **15/25/50/90 minutes**, or **SKIP**. The
indicator shows the time left and how many codes you have made in the session; when it
ends, a gentle notice suggests a break (no alarms).

## 16. ♫ Focus music (bottom bar)

Put your audio files (mp3, m4a, ogg, wav, flac) in the `musica/` folder next to your data; **clicking the bar's title** shows you the exact path. `▶` plays on a loop, `⏭` skips a track, and the volume is remembered.

## 17. Quick shortcut table

| Shortcut | Action |
|-------|--------|
| `↵` (in the Cloud) | Save code |
| `⌘↵` (in the Cloud) | Repeat the last coding |
| `Esc` | Cancel the Cloud / leave immersion / clear search |
| `1`–`9` (in the Cloud) | Choose a category |
| `⌘F` / `Ctrl+F` | Search the corpus |
| `⌘Z` / `Ctrl+Z` | Undo the last coding |
| Drag selection → code in the bank | Reapply that code |

## 18. Troubleshooting

- **The Mac says the app cannot be opened**: this happens only the first time, because the app is not signed with an Apple certificate. On macOS 15 (Sequoia) or later: *System Settings → Privacy & Security → Open Anyway*. On macOS 14 or earlier: right-click the app → Open.
- **It does not open on another Mac / nothing happens**: most likely it is the **wrong DMG for its chip**. There are two installers: one for **Intel** Macs and one for **Apple Silicon (M1/M2/M3/M4)** Macs, and they are not interchangeable (unlike Rosetta, which only translates Intel → Apple Silicon, never the reverse). On that Mac, go to the  menu → *About This Mac* to see which chip it has, and download the matching DMG. **macOS 10.15 (Catalina) or later** is also required.
- **Windows SmartScreen shows a warning**: "More info → Run anyway".
- **The browser does not open by itself**: go to `http://127.0.0.1:8734` manually.
- **"Could not connect to the server"**: the app is not running; launch it again.
- **Recovering work**: everything is in `.../cualibre/projects/*.json`; that file is your complete project, readable and easy to back up. A deleted project stays in `.../cualibre/papelera/`: import it with **⤒ IMPORT** to recover it.
- **Sentiment takes a while the first time with a very large corpus**: that is the
  initial analysis of each document (done only once and stored in `.../cualibre/cache/`,
  a folder that can be deleted safely).
- **Windows**: shortcuts use `Ctrl` wherever this manual says `⌘`.
- **Its own window does not open on Windows**: the WebView2 component is missing (it comes
  with Windows 11 and with updated Windows 10). Cua-libre then opens in the browser; you
  can install WebView2 from Microsoft's website. Technical messages are written to
  `%APPDATA%\cualibre\logs\cualibre.log`.
- **A scanned PDF cannot be read**: OCR is not available on this computer (Windows with no
  OCR language installed, or macOS older than 10.15). On macOS, Spanish and Portuguese
  OCR requires macOS 11 or later.
