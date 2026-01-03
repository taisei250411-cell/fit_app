import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# ページ設定
st.set_page_config(page_title="My AI Diary", page_icon="📝")
st.title("📝 AI交換日記")

# 1. APIキーの設定（StreamlitのSecretsから読み込む）
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("設定エラー: APIキーまたは接続設定が正しくありません。")
    st.stop()

# 2. 過去データの読み込み（キャッシュを使って高速化）
def load_data():
    # ワークシート名を指定（デフォルトはSheet1）
    return conn.read(worksheet="Sheet1", ttl="0")

try:
    df = load_data()
    # データが空の場合の処理
    if df.empty:
        df = pd.DataFrame(columns=["date", "content", "ai_comment"])
except:
    # シートがまだ読み込めない場合の初期化
    df = pd.DataFrame(columns=["date", "content", "ai_comment"])

# 3. 日記の入力フォーム
with st.form("diary_form"):
    input_text = st.text_area("今日はどんな1日でしたか？", height=150)
    submitted = st.form_submit_button("記録してAIに送る")

    if submitted and input_text:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # --- AIへの指示（プロンプト） ---
        prompt = f"""
        あなたは親しい友人であり、専属のメンタルコーチです。
        以下のユーザーの日記に対して、共感し、前向きなフィードバックを返してください。
        
        日記内容: {input_text}
        """
        
        with st.spinner("AIが考え中..."):
            try:
                # Geminiからの応答を取得
                model = genai.GenerativeModel('gemini-1.5-flash') 
                response = model.generate_content(prompt)
                ai_reply = response.text
                
                # データフレームに追加
                new_data = pd.DataFrame([{
                    "date": now_str, 
                    "content": input_text, 
                    "ai_comment": ai_reply
                }])
                
                # スプレッドシートを更新
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success("記録しました！")
                st.rerun() # 画面更新
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# 4. 過去の記録を表示（新しい順）
st.divider()
st.subheader("📚 過去の記録")

if not df.empty:
    # 新しい順に並び替え
    df_rev = df.iloc[::-1]
    
    for index, row in df_rev.iterrows():
        with st.chat_message("user"):
            st.write(f"**{row['date']}**")
            st.write(row['content'])
        
        with st.chat_message("assistant"):
            st.write(row['ai_comment'])
        st.divider()
