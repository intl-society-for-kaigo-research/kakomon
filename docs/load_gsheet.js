
window.addEventListener("DOMContentLoaded", async () => {

  // ==========================================
  // GASのウェブアプリURL
  // ==========================================
  const gasUrl =
    "https://script.google.com/macros/s/AKfycbzEsnGKR0mNzRc_ECKgN4H0WHQ1x4j-djwKHCNZ9Hx4kgf3YDqrZc9YQ4cJ0y4-ML4DYw/exec";

  const schoolName = window.schoolName || "";
  const kakomonName = window.kakomonName || "";

  if (!kakomonName) {
    console.error(
      "❌ エラー: kakomonName が未設定のため処理を中断します。"
    );
    return;
  }

  // ==========================================
  // クイズ読み込み
  // ==========================================
  async function loadQuiz(passcode = "") {
    const loading = document.getElementById("quiz-loading");
  
    if (loading) {
      loading.style.display = "block";
    }
  
    try {
      // 現在のfetch処理

      // ------------------------------
      // 1. パラメータの構築
      // ------------------------------
      const params = new URLSearchParams({
        kakomonName: kakomonName
      });

      if (schoolName) {
        params.append("schoolName", schoolName);
      }

      if (passcode) {
        params.append("passcode", passcode);
      }

      const url = `${gasUrl}?${params.toString()}`;

      console.log("▶ GASリクエスト:", url);

      // ------------------------------
      // 2. GASへリクエスト
      // ------------------------------
      const res = await fetch(url);

      if (!res.ok) {
        throw new Error(
          `GAS通信エラー: HTTP ${res.status}`
        );
      }

      const result = await res.json();

      console.log("◀ GASレスポンス:", result);
      console.log("◀ GAS status:", result.status);

      // ==========================================
      // ADMIN設定 from Google Spreadsheet/GAS
      // ==========================================
      if (result.config) {

        console.log("NCHOICE:", result.config.NCHOICE);
        console.log("NCHOICE Number:", Number(result.config.NCHOICE));
        
        window.kakomonNChoice = Number(result.config.NCHOICE);
        
        console.log("window.kakomonNChoice:", window.kakomonNChoice);

      }

      // ==========================================
      // 3. パスコード要求
      // ==========================================
      if (result.status === "auth_required") {
        if (loading) {
          loading.style.display = "none";
        }
        const input = prompt(
          `${result.message}\nパスコードを入力してください:`
        );
        if (input) {
          loadQuiz(input);
        }
        return;
      }

      // ==========================================
      // 4. エラー処理
      // ==========================================
      if (result.status === "error") {

        console.error(
          "❌ GASエラー:",
          result.message
        );

        // パスコード間違い
        if (
          result.message &&
          result.message.includes("パスコード")
        ) {

          const input = prompt(
            `${result.message}\nパスコードを入力してください:`
          );

          if (!input) {
            console.log(
              "パスコード入力がキャンセルされました。"
            );
            return;
          }

          await loadQuiz(input);

          return;
        }

        alert(result.message);
        return;
      }

      // ==========================================
      // 5. 正常レスポンス
      // ==========================================
      if (result.status !== "success") {

        console.error(
          "❌ 想定外のGASレスポンス:",
          result
        );

        alert(
          "GASから想定外のレスポンスが返されました。"
        );

        return;
      }
      // ==========================================
      // 6. クイズデータ格納
      // ==========================================
      
      // GASの CATEGORY / NUM を
      // renderQuiz() が期待する {カテゴリ名: 件数} に変換
      window.quizConfig = {};
      
      (result.categories || []).forEach(cat => {
        const category = cat.CATEGORY || "";
        const num = Number(cat.NUM) || 0;
      
        if (category) {
          window.quizConfig[category] = num;
        }
      });
      
      const rawQuizData = result.data || [];
      
      console.log("✅ GASから取得した問題数:", rawQuizData.length);
      console.log("✅ GASカテゴリ設定:", window.quizConfig);
      
      // 既存の変換関数を使用
      window.currentQuizData = convertToQuizData(rawQuizData);
      
      console.log(
        "🔄 convertToQuizData後の問題数:",
        window.currentQuizData.length
      );
      
      // ==========================================
      // 7. クイズ描画
      // ==========================================
      
      if (typeof renderQuiz === "function") {
        renderQuiz(window.currentQuizData, "quiz");
        if (loading) {
          loading.style.display = "none";
        }
      } else {
        console.error("❌ renderQuiz 関数が見つかりません。");
      }





    } catch (err) {

      console.error(
        "❌ 通信エラーが発生しました:",
        err
      );

      alert(
        "問題データの読み込み中にエラーが発生しました。"
      );
    }
  }

  // ==========================================
  // 初期読み込み
  // ==========================================
  await loadQuiz();

});


