/* --- スコア管理用 --- */
let correctCount = 0;
let answeredCount = 0;
let currentQuizData = []; 

/* =========================
    データ処理系
========================= */

/**
 * クイズの1問から、表示・印刷に必要な選択肢を生成・抽出する共通関数
 */
function prepareChoices(q, nChoice) {
  const actualCorrects = q.corrects || [];
  const actualWrongs = q.wrongs || [];

  // 必要な誤答の数
  const neededW = nChoice - actualCorrects.length;
  // 誤答をシャッフルしてから必要数だけ取り出す
  const selectedWrongs = shuffle([...actualWrongs]).slice(0, Math.max(0, neededW));

  // 正解と選択された誤答を合体
  const allChoices = [
    ...actualCorrects.map(c => ({ text: c, isCorrect: true })),
    ...selectedWrongs.map(w => ({ text: w, isCorrect: false }))
  ];

  // 全体をシャッフルして返す
  return shuffle(allChoices);
}

// 生の配列データ（CSVなど）から、正解・誤答を安全に配列化する関数
function convertToQuizData(csvData) {
  if (!Array.isArray(csvData)) return [];
  return csvData.map(row => {
    if (!row) return null;

    const getSafeValRaw = (names) => {
      for (let name of names) {
        const matchKey = Object.keys(row).find(k => k.trim().toLowerCase() === name.toLowerCase());
        if (matchKey && row[matchKey] !== undefined && row[matchKey] !== null) return row[matchKey];
      }
      return null;
    };

    // 問題文の取得（ここが null だと filter(Boolean) で消えます）
    const questionRaw = getSafeValRaw(["question", "Question", "問題文"]);
    if (!questionRaw) return null; 

    // --- 正解・誤答の集約ロジック (前述の通り) ---
    let corrects = [];
    const mainC = getSafeValRaw(["correct", "corrects", "正解"]);
    if (Array.isArray(mainC)) corrects = [...mainC];
    else if (mainC) corrects.push(mainC);
    for (let i = 1; i <= 5; i++) {
      const c = getSafeValRaw([`correct${i}`]);
      if (c) corrects.push(c);
    }

    let wrongs = [];
    const mainW = getSafeValRaw(["wrong", "wrongs", "不正解"]);
    if (Array.isArray(mainW)) wrongs = [...mainW];
    else if (mainW) wrongs.push(mainW);
    for (let i = 1; i <= 10; i++) {
      const w = getSafeValRaw([`wrong${i}`]);
      if (w) wrongs.push(w);
    }

    const finalize = (arr) => [...new Set(arr.map(v => v.toString().trim()))].filter(Boolean);

    // ★ ここで返すプロパティ名を renderQuiz と完全に合わせる
    return {
      category: (getSafeValRaw(["category", "カテゴリ"]) || "未分類").toString().trim(),
      question: questionRaw.toString().trim(),
      corrects: finalize(corrects),
      wrongs: finalize(wrongs),
      explanation: (getSafeValRaw(["explanation", "解説"]) || "").toString().trim()
    };
  }).filter(Boolean);
}

// 外部ファイル（CSV/JSON）読み込み関数
async function loadData(url) {
  const separator = url.includes('?') ? '&' : '?';
  const fullUrl = `${url}${separator}v=${new Date().getTime()}`;

  const res = await fetch(fullUrl);
  if (!res.ok) throw new Error("ファイルの取得に失敗しました");

  if (url.toLowerCase().endsWith(".json")) {
    const jsonData = await res.json();
    return convertToQuizData(jsonData);
  } 
  
  const text = await res.text();
  const csvResult = Papa.parse(text, { header: true, skipEmptyLines: true }).data;
  return convertToQuizData(csvResult);
}

/* =========================
    判定・UI制御系
========================= */

function toggleSelection(btn) {
  if (btn.parentElement.parentElement.querySelector(".submit-btn").disabled) return;
  btn.classList.toggle("selected");
}

function checkAnswerMulti(quizIndex, explanation) {
  const items = document.querySelectorAll(".quiz-item");
  const itemDiv = items[quizIndex];
  const result = itemDiv.querySelector(".result");
  const exp = itemDiv.querySelector(".explanation");
  const submitBtn = itemDiv.querySelector(".submit-btn");
  const choiceButtons = itemDiv.querySelectorAll(".choice-btn");

  const selectedButtons = Array.from(choiceButtons).filter(btn => btn.classList.contains("selected"));
  if (selectedButtons.length === 0) {
    alert("選択肢を1つ以上選んでください。");
    return;
  }

  submitBtn.disabled = true;
  choiceButtons.forEach(b => b.style.cursor = "default");
  answeredCount++;

  const selectedCorrectCount = selectedButtons.filter(btn => btn.dataset.correct === "true").length;
  const totalCorrectCount = Array.from(choiceButtons).filter(btn => btn.dataset.correct === "true").length;
  const isPerfect = (selectedCorrectCount === selectedButtons.length) && (selectedCorrectCount === totalCorrectCount);

  if (isPerfect) {
    result.textContent = "正解！";
    result.className = "result correct-text";
    correctCount++;
  } else {
    result.textContent = "不正解";
    result.className = "result wrong-text";
  }

  choiceButtons.forEach(btn => {
    if (btn.dataset.correct === "true") btn.classList.add("reveal-correct");
    if (btn.classList.contains("selected") && btn.dataset.correct === "false") btn.classList.add("reveal-wrong");
  });

  if (typeof updateScoreDisplay === "function") updateScoreDisplay();

  let html = marked.parse(explanation || "（解説なし）");
  if (typeof rubyConverter !== "undefined" && typeof rubyConverter.convert === "function") {
      html = rubyConverter.convert(html);
  }
  
  exp.innerHTML = DOMPurify.sanitize(html, { ADD_TAGS: ["ruby", "rt", "rp"] });
  exp.style.display = "block";
}

/* =========================
    表示・レンダリング系
========================= */

function renderQuiz(quizData, containerId = "quiz") {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "読み込み中...";

  // 1. データの正規化（入れ子構造の解消）
  let raw = Array.isArray(quizData) ? quizData : (quizData.quizData || []);
  
  // 2. convertToQuizData を通っていない生データの場合のみ成形する
  // (すでに convertToQuizData を通っているならこの map はスキップされるように組むのが理想)
  let formattedData = raw.map(q => {
    if (q.corrects && q.wrongs) return q; // すでに成形済みならそのまま
    // ... (ここに前述の getVal 等を用いた成形ロジックを入れる)
    return q; 
  }).filter(Boolean);

  // 3. 【重要】quizConfig によるフィルタリング
  let displayData = formattedData;
  if (window.quizConfig && Object.keys(window.quizConfig).length > 0) {
    // カテゴリごとにグループ化
    const groups = formattedData.reduce((acc, obj) => {
      const key = obj.category || "未分類";
      if (!acc[key]) acc[key] = [];
      acc[key].push(obj);
      return acc;
    }, {});

    // 設定に基づいて各カテゴリから抽出
    displayData = Object.keys(groups).flatMap(catName => {
      // quizConfig のキーと完全一致するか確認
      const limit = parseInt(window.quizConfig[catName], 10);
      
      if (!isNaN(limit) && limit > 0) {
        // 設定がある場合はシャッフルして制限数だけ取る
        return shuffle([...groups[catName]]).slice(0, limit);
      }
      // 設定がないカテゴリは、全件出すか除外するか？ 
      // 一般的には設定がないカテゴリは 0問（除外）にするのが「Config」の挙動です
      return []; 
    });
  }

  // シャッフル設定がある場合は全体を混ぜる（任意）
  if (window.noShuffleQuestions === false) {
    displayData = shuffle(displayData);
  }

  currentQuizData = displayData; 
  container.innerHTML = ""; // 描画開始

  if (displayData.length === 0) {
    container.innerHTML = "条件に一致する問題がありません。";
    return;
  }

  // 4. 描画ループ
  let currentCategory = "";
  // ... renderQuiz のフィルタリング処理の後 ...

  displayData.forEach((q, index) => {
    // カテゴリ見出しの描画
    if (q.category && q.category !== currentCategory) {
      currentCategory = q.category;
      const categoryTitle = document.createElement("h3");
      categoryTitle.className = "category-title";
      categoryTitle.textContent = currentCategory;
      container.appendChild(categoryTitle);
    }
  
    // --- 問題ごとに div を作成 ---
    const div = document.createElement("div");
    div.classList.add("quiz-item");
  
    // 【重要】prepareChoices に渡す q が正しい構造か確認
    const nChoice = window.kakomonNChoice || 5;
    const choices = prepareChoices(q, nChoice);
  
    // Markdown変換とルビ処理
    const qText = (typeof rubyConverter !== "undefined") ? rubyConverter.convert(mdInline(q.question)) : mdInline(q.question);
    
    // HTML組み立て
    let html = `<p><strong>Q${index + 1}. ${qText}</strong></p>`;
    html += `<div class="choices-container">`;
    
    choices.forEach(choice => {
      const cText = (typeof rubyConverter !== "undefined") ? rubyConverter.convert(mdInline(choice.text)) : mdInline(choice.text);
      html += `<button type="button" class="choice-btn" data-correct="${choice.isCorrect}" onclick="toggleSelection(this)">${cText}</button>`;
    });
    
    html += `</div>`;
    
    // 解説の安全なエスケープ
    const safeExp = q.explanation ? q.explanation.replace(/'/g, "\\'").replace(/"/g, '&quot;') : "";
    
    html += `
      <button class="submit-btn" onclick="checkAnswerMulti(${index}, '${safeExp}')">回答を確定</button>
      <p class="result"></p>
      <div class="explanation" style="display:none;"></div>
    `;
  
    div.innerHTML = html;
    container.appendChild(div);
  });
}

function shuffle(array) {
  if (!Array.isArray(array)) return [];
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array;
}

function mdInline(text) {
  if (!text) return "";
  const html = marked.parse(text.toString().replace(/\\n/g, "\n") || "").replace(/^<p>|<\/p>\n?$/g, "");
  return DOMPurify.sanitize(html, { ADD_TAGS: ["ruby", "rt", "rp"] });
}

/* =========================
    スコア表示
========================= */

function updateScoreDisplay() {
  const scoreDiv = document.getElementById("score");
  if (!scoreDiv) return;
  const rate = answeredCount === 0 ? 0 : Math.round((correctCount / answeredCount) * 100);
  const comments = {
    start: ["まずは一問！", "ここからスタート！"],
    low: ["がんばれ！", "復習しよう"],
    high: ["この調子！", "完璧に近い！"]
  };

  let comment = (answeredCount === 0) ? comments.start[Math.floor(Math.random() * comments.start.length)] : (rate < 60 ? comments.low[Math.floor(Math.random() * comments.low.length)] : comments.high[Math.floor(Math.random() * comments.high.length)]);

  scoreDiv.innerHTML = `
    <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #fdfdfd; border-radius: 10px; border: 1px solid #eee; max-width: fit-content; margin-bottom: 20px;">
      <img src="Baba.png" alt="Baba" width="80" height="80" style="border-radius: 50%; border: 2px solid #007bff; background:white; object-fit: cover;">
      <div>
        <div style="font-weight: bold; font-size: 1.1rem;">スコア: ${correctCount}/${answeredCount} (${rate}%)</div>
        <div style="font-size: 0.9rem; color: #555; margin-top: 4px;">${comment}</div>
      </div>
    </div>
  `;
}

/* =========================
    印刷関連
========================= */
function preparePrint() {
  if (!currentQuizData || currentQuizData.length === 0) {
    alert("データがありません。");
    return;
  }
  renderQuizForPrint(currentQuizData);
}

function renderQuizForPrint(quizData) {
  const container = document.getElementById("quiz");
  if (!container) return;

  container.innerHTML = `
    <h2 style="text-align:center; margin-bottom: 2rem;">確認テスト</h2>
    <p style="text-align:right; margin-bottom: 2rem;">氏名：__________________________</p>
  `;

  const nChoice = window.kakomonNChoice || 5;

  quizData.forEach((q, index) => {
    const div = document.createElement("div");
    div.className = "print-item"; // スタイル調整用
    div.style.marginBottom = "2rem";
    div.style.pageBreakInside = "avoid";

    // 共通関数を利用（isCorrectの情報も含まれるが、印刷ではtextのみ使用）
    const choices = prepareChoices(q, nChoice);

    const qText = (typeof rubyConverter !== "undefined") ? rubyConverter.convert(mdInline(q.question)) : mdInline(q.question);
    let html = `<p><strong>問${index + 1}. ${qText}</strong></p>`;
    
    choices.forEach((c, i) => {
      const cText = (typeof rubyConverter !== "undefined") ? rubyConverter.convert(mdInline(c.text)) : mdInline(c.text);
      html += `<div style="margin-left: 20px; margin-bottom: 0.5rem;">（ ${i + 1} ） ${cText}</div>`;
    });

    div.innerHTML = html;
    container.appendChild(div);
  });

  setTimeout(() => { window.print(); location.reload(); }, 500);
}