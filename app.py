import streamlit as st
import feedparser
import urllib.parse
import re
import time
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=3600, show_spinner=False)
def get_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=2.5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            img = soup.find('meta', property='og:image')
            if img and img.get('content'):
                img_url = img['content']
                # Google Newsの汎用アイコン画像（lh3.googleusercontent.com 等）の場合は無視する
                if 'googleusercontent.com' in img_url or 'gstatic.com' in img_url:
                    return None
                return img_url
    except Exception:
        pass
    return None

# ページの設定
st.set_page_config(
    page_title="AI News Dashboard",
    page_icon="📰",
    layout="wide"
)

# サイドバー：検索機能
st.sidebar.title("🔍 ニュース検索")
st.sidebar.markdown("キーワードを入力してRSSを取得します。")
search_word = st.sidebar.text_input("検索キーワード", value="")

if search_word:
    # メイン画面タイトル
    st.title(f"📰 最新の「{search_word}」ニュース収集ダッシュボード")
    st.markdown(f"**「{search_word}」** に関する最新ニュースをGoogle Newsから取得しています。")
    st.divider()
else:
    st.title("📰 ニュース収集ダッシュボード")
    st.info("👈 左側のサイドバーから検索キーワードを入力してください。（例：「AI」「自動運転」など）")
    st.divider()

if search_word:
    # 検索キーワードをURLエンコード
    encoded_query = urllib.parse.quote(search_word)
    
    # 検索ワードに応じてGoogle NewsのRSS URLを動的に生成
    # 日本語のニュースを取得する場合は 'hl=ja&gl=JP&ceid=JP:ja'、英語の場合は 'hl=en-US&gl=US&ceid=US:en'
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"
    
    # RSSフィードの取得
    with st.spinner("ニュースを取得中..."):
        feed = feedparser.parse(rss_url)
    
    # 記事ごとの表示（Google検索のニュースタブ風レイアウト）
    if hasattr(feed, 'entries') and len(feed.entries) > 0:
        # 画像取得に時間がかかるため、最新20件のみ表示する
        st.info("📰 最新20件の記事を表示しています。（初回アクセス時はサムネイル取得のため数秒〜十数秒かかります）")
        
        for entry in feed.entries[:20]:
            # タイトルからパブリッシャー情報を抽出（例: "記事タイトル - 配信元新聞"）
            title_parts = entry.title.rsplit(" - ", 1)
            headline = title_parts[0]
            publisher = title_parts[1] if len(title_parts) > 1 else ""
            
            # 発行日
            published_date = entry.get('published', '')
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    # タイムゾーンをJST（日本標準時）に設定
                    JST = timezone(timedelta(hours=+9), 'JST')
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    published_date = dt.astimezone(JST).strftime('%Y年%m月%d日 %H:%M')
                except Exception:
                    pass
            
            # 要約のHTMLタグを取り除いて表示
            summary_html = entry.get('summary', '')
            clean_summary = re.sub('<.*?>', '', summary_html)
            
            # サムネイル画像の取得
            img_url = get_og_image(entry.link)
            
            # 文字サイズを全体の2/3(約66%)に縮小させるHTMLを構成（opacityで見やすさとテーマ対応を両立）
            content_html = f'''
            <div style="font-size: 66%; line-height: 1.6;">
                {'<div style="opacity: 0.75; margin-bottom: 2px;"><b>' + publisher + '</b></div>' if publisher else ''}
                <div style="margin-bottom: 4px;">
                    <a href="{entry.link}" target="_blank" style="font-size: 1.4em; font-weight: bold; text-decoration: none;">{headline}</a>
                </div>
                {'<div style="margin-bottom: 4px; opacity: 0.9;">' + clean_summary + '</div>' if clean_summary else ''}
                <div style="opacity: 0.6; font-size: 0.9em; margin-top: 4px;">{published_date}</div>
            </div>
            '''
            
            # Google表示風に情報を配置（サムネイルがあれば右側に配置）
            if img_url:
                col1, col2 = st.columns([5, 1]) # 文字が小さくなるため画像の割合を少し小さく調整
                with col1:
                    st.markdown(content_html, unsafe_allow_html=True)
                with col2:
                    st.image(img_url, use_container_width=True)
            else:
                st.markdown(content_html, unsafe_allow_html=True)
                
            st.divider()
    else:
        st.warning("ニュースが見つかりませんでした。別のキーワードを試してください。")
