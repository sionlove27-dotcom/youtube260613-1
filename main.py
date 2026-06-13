import streamlit as st
import pandas as pd
import re
from collections import Counter
from googleapiclient.discovery import build
from kiwipiepy import Kiwi
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.express as px
import os

st.set_page_config(
page_title="유튜브 댓글 분석기",
page_icon="📊",
layout="wide"
)

@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

# -----------------------

# URL → Video ID

# -----------------------

def extract_video_id(url):
patterns = [
r"v=([a-zA-Z0-9_-]+)",
r"youtu.be/([a-zA-Z0-9_-]+)",
r"shorts/([a-zA-Z0-9_-]+)"
]

```
for pattern in patterns:
    match = re.search(pattern, url)
    if match:
        return match.group(1)

return None
```

# -----------------------

# 댓글 수집

# -----------------------

def get_comments(youtube, video_id, max_comments):

```
comments = []

try:

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:

        response = request.execute()

        for item in response["items"]:

            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

            comments.append(comment)

            if len(comments) >= max_comments:
                return comments

        request = youtube.commentThreads().list_next(
            request,
            response
        )

except Exception as e:
    st.error(f"댓글 수집 오류: {e}")

return comments
```

# -----------------------

# 키워드 추출

# -----------------------

def extract_keywords(comments):

```
stopwords = {
    "영상","진짜","정말","너무",
    "구독","좋아요","감사",
    "생각","사람","오늘",
    "이거","저거"
}

words = []

for comment in comments:

    try:

        tokens = kiwi.tokenize(comment)

        for token in tokens:

            if token.tag.startswith("N"):

                word = token.form

                if len(word) >= 2 and word not in stopwords:
                    words.append(word)

    except:
        pass

return Counter(words)
```

# -----------------------

# 감성분석

# -----------------------

positive_words = [
"좋다","최고","감동","행복",
"추천","재밌다","훌륭",
"멋지다","대박"
]

negative_words = [
"별로","실망","최악",
"짜증","문제","싫다",
"불편","아쉽다"
]

def sentiment_analysis(comments):

```
positive = 0
negative = 0

for comment in comments:

    for word in positive_words:
        if word in comment:
            positive += 1

    for word in negative_words:
        if word in comment:
            negative += 1

return positive, negative
```

# -----------------------

# UI

# -----------------------

st.title("📊 유튜브 댓글 심층 분석기")

api_key = st.text_input(
"YouTube API Key",
type="password"
)

video_url = st.text_input(
"유튜브 링크 입력"
)

max_comments = st.slider(
"댓글 수",
100,
2000,
1000,
100
)

if st.button("분석 시작"):

```
if not api_key:
    st.warning("YouTube API Key를 입력하세요.")
    st.stop()

video_id = extract_video_id(video_url)

if not video_id:
    st.error("올바른 유튜브 링크가 아닙니다.")
    st.stop()

youtube = build(
    "youtube",
    "v3",
    developerKey=api_key
)

with st.spinner("댓글 수집 중..."):

    comments = get_comments(
        youtube,
        video_id,
        max_comments
    )

if not comments:
    st.error("댓글을 가져오지 못했습니다.")
    st.stop()

st.success(f"{len(comments):,}개 댓글 분석 완료")

df = pd.DataFrame({
    "댓글": comments
})

# 통계

st.header("📈 기본 통계")

lengths = [len(x) for x in comments]

col1, col2, col3 = st.columns(3)

col1.metric("댓글 수", len(comments))
col2.metric("평균 길이", round(sum(lengths)/len(lengths),1))
col3.metric("최대 길이", max(lengths))

# 키워드

st.header("🔥 TOP 키워드")

keywords = extract_keywords(comments)

keyword_df = pd.DataFrame(
    keywords.most_common(30),
    columns=["키워드","빈도"]
)

st.dataframe(keyword_df, use_container_width=True)

fig = px.bar(
    keyword_df.head(20),
    x="키워드",
    y="빈도",
    title="TOP 20 키워드"
)

st.plotly_chart(fig, use_container_width=True)

# 워드클라우드

st.header("☁️ 워드클라우드")

if os.path.exists("NanumGothic.ttf"):

    wc = WordCloud(
        font_path="NanumGothic.ttf",
        width=1600,
        height=800,
        background_color="white"
    )

    wc.generate_from_frequencies(dict(keywords))

    fig2, ax = plt.subplots(figsize=(14,7))
    ax.imshow(wc)
    ax.axis("off")

    st.pyplot(fig2)

else:
    st.warning(
        "NanumGothic.ttf 파일을 프로젝트 폴더에 넣어주세요."
    )

# 감성분석

st.header("😊 감성 분석")

pos, neg = sentiment_analysis(comments)

sentiment_df = pd.DataFrame({
    "감정":["긍정","부정"],
    "개수":[pos,neg]
})

fig3 = px.pie(
    sentiment_df,
    names="감정",
    values="개수"
)

st.plotly_chart(fig3, use_container_width=True)

# 댓글

st.header("💬 원본 댓글")

st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "CSV 다운로드",
    csv,
    "youtube_comments.csv",
    "text/csv"
)
```
