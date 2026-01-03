import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# --- 設定 ---
# アプリのタイトル
APP_TITLE = "My AI Tool"
# AIへの命令（Google AI Studioで作ったプロンプトをここに貼ることもできます）
SYSTEM_PROMPT = "あなたは優秀なアシスタントです。ユーザーの入力に対して的確に答えてください。"

# ページ設定
st.set_page_config(page_title=APP_TITLE, page_icon="⚡")
st.title(f"⚡ {APP_TITLE}")

# 1. APIキーの設定
try:
    # エラー対策：モデルを安定版のgemini-1.5-flashに変更
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("設定エラー: Secretsの設定を確認してください。")
    st.stop()

# 2. データ読み込み（履歴表示用）
def load_data():
    try:
        return conn.read(worksheet="Sheet1", ttl="0")
    except:
        return pd.DataFrame(columns=["date", "input", "output"])

df = load_data()
if df.empty:
    df = pd.DataFrame(columns=["date", "input", "output"])

# 3. 入力フォーム
with st.form("main_form"):
    # 日記ではなく汎用的な入力欄に変更
    input_text = st.text_area("入力データ（質問やテキスト）", height=150)
    submitted = st.form_submit_button("実行・保存")

    if submitted and input_text:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with st.spinner("実行中..."):
            try:
                # --- ここでAIを動かす ---
                # 安定して動く無料枠モデル（1.5 Flash）を使用
                model = genai.GenerativeModel('gemini-1.5-flash') 
                
                # システムプロンプトとユーザー入力を結合して送信
                full_prompt = f"{SYSTEM_PROMPT}\n\nユーザー入力: {input_text}"
                response = model.generate_content(full_prompt)
                ai_output = response.text
                
                # --- 結果を表示 ---
                st.success("完了")
                st.markdown("### 🔹 AIの回答")
                st.write(ai_output)

                # --- データを保存 ---
                new_data = pd.DataFrame([{
                    "date": now_str, 
                    "input": input_text,     # 元の「content」列の代わりにinputとして保存
                    "output": ai_output      # 元の「ai_comment」列の代わりにoutputとして保存
                }])
                
                # スプレッドシートの列名に合わせて調整（既存シートを使うための処理）
                # もし列名エラーが出たら、シートの1行目を date, input, output に書き換えてください
                new_data.columns = df.columns[:3] 

                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# 4. 過去の履歴（保存データ）
st.divider()
st.subheader("📂 保存されたデータ")

if not df.empty:
    # 新しい順に表示
    df_rev = df.iloc[::-1]
    dataframe_display = st.checkbox("表形式で見る", value=True)
    
    if dataframe_display:
        st.dataframe(df_rev, use_container_width=True)
    else:
        for index, row in df_rev.iterrows():
            st.caption(row.iloc[0]) # 日付
            st.info(f"入: {row.iloc[1]}")
            st.success(f"出: {row.iloc[2]}")
            st.divider()
