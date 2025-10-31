import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

API_KEY = "__apikey__"
youtube = build("youtube", "v3", developerKey=API_KEY)

st.set_page_config(page_title="YouTube Dashboard", layout="wide")

st.markdown("""
    <style>
    div.block-container { padding-top: 1.8rem !important; }
    .project-title { font-size: 1.5rem; font-weight: 600; color: #c084fc; margin-bottom: 0.5rem; }
    .css-ffhzg2, .css-1d391kg { padding-top: 0rem !important; padding-bottom: 0rem !important; margin-bottom: 0.3rem !important; }
    .js-plotly-plot { margin: 0px !important; padding: 0px !important; }
    .stDataFrame > div:first-child { padding: 0px; }
    body, .stApp { background-color: #0e1117; color: #e5e5e5; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1c1f26, #14161c); border-right: 2px solid #2a2d3a; }
    h1, h2, h3 { color: #c084fc; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, #1e1f29, #2d2f3b); border-radius: 12px; padding: 8px; box-shadow: 0px 0px 8px rgba(120,0,255,0.5); }
    .stDataFrame { background-color: #1c1f26 !important; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

def get_channel_id_from_name(channel_name: str):
    request = youtube.search().list(part="snippet", q=channel_name, type="channel", maxResults=1)
    response = request.execute()
    if "items" in response and len(response["items"]) > 0:
        return response["items"][0]["snippet"]["channelId"]
    return None

def get_channel_stats(channel_id: str):
    request = youtube.channels().list(part="snippet,statistics", id=channel_id)
    response = request.execute()
    if "items" not in response or len(response["items"]) == 0:
        return None
    item = response["items"][0]
    return {
        "Channel Title": item["snippet"]["title"],
        "Subscribers": int(item["statistics"].get("subscriberCount", 0)),
        "Views": int(item["statistics"].get("viewCount", 0)),
        "Total Videos": int(item["statistics"].get("videoCount", 0)),
    }

def get_latest_videos(channel_id: str, max_results=10):
    request = youtube.search().list(part="snippet", channelId=channel_id, order="date", type="video", maxResults=max_results)
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        publish_date = item["snippet"]["publishedAt"]
        stats_req = youtube.videos().list(part="statistics", id=video_id)
        stats_res = stats_req.execute()
        stats = stats_res["items"][0]["statistics"]
        videos.append({
            "Title": title,
            "Video ID": video_id,
            "Publish Date": publish_date,
            "Views": int(stats.get("viewCount", 0)),
            "Likes": int(stats.get("likeCount", 0)) if "likeCount" in stats else 0,
            "Comments": int(stats.get("commentCount", 0)) if "commentCount" in stats else 0
        })
    return pd.DataFrame(videos)

def get_channel_playlists(channel_id: str):
    request = youtube.playlists().list(
        part="snippet,contentDetails",
        channelId=channel_id,
        maxResults=25
    )
    response = request.execute()
    playlists = {}
    for item in response.get("items", []):
        playlists[item["snippet"]["title"]] = item["id"]
    return playlists

def get_videos_from_playlist(playlist_id: str, max_results=10):
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=max_results
    )
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        publish_date = item["snippet"]["publishedAt"]
        stats_req = youtube.videos().list(part="statistics", id=video_id)
        stats_res = stats_req.execute()
        stats = stats_res["items"][0]["statistics"]
        videos.append({
            "Title": title,
            "Video ID": video_id,
            "Publish Date": publish_date,
            "Views": int(stats.get("viewCount", 0)),
            "Likes": int(stats.get("likeCount", 0)) if "likeCount" in stats else 0,
            "Comments": int(stats.get("commentCount", 0)) if "commentCount" in stats else 0
        })
    return pd.DataFrame(videos)

def multi_line_area_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Publish Date'], y=df['Views'],
                             mode='lines+markers', name='Views',
                             line=dict(color='#c84fcf'), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=df['Publish Date'], y=df['Likes'],
                             mode='lines+markers', name='Likes',
                             line=dict(color='#384df0')))
    fig.update_layout(template='plotly_dark', title="📉 Views & Likes Over Time", height=450)
    return fig

def bar_line_combo_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Title'], y=df['Views'], name='Views', marker_color='rgba(0,123,255,0.7)'))
    avg_likes = df['Likes'].mean()
    fig.add_trace(go.Scatter(x=df['Title'], y=[avg_likes]*len(df), mode='lines', name='Avg Likes',
                             line=dict(color='lime', dash='dash')))
    fig.update_layout(template='plotly_dark', title="📊 Views with Avg Likes Line", height=450)
    return fig

def radial_progress_chart(percentage, title):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percentage,
            title={'text': title},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#c084fc"},
                   'bgcolor': "rgba(30, 30, 50, 0.2)"}
        )
    )
    fig.update_layout(template='plotly_dark', height=450)
    return fig

def horizontal_progress_bars(data_dict):
    fig = go.Figure()
    years = list(data_dict.keys())
    values1 = [v[0] for v in data_dict.values()]
    values2 = [v[1] for v in data_dict.values()]
    fig.add_trace(go.Bar(y=years, x=values1, orientation='h',
                         name='Metric 1', marker_color='rgba(192,82,188,0.7)'))
    fig.add_trace(go.Bar(y=years, x=values2, orientation='h',
                         name='Metric 2', marker_color='rgba(100,150,255,0.7)'))
    fig.update_layout(template='plotly_dark', barmode='stack', title="📊 Yearly Metrics", height=450)
    return fig

def donut_chart_summary(label_values_dict):
    labels = list(label_values_dict.keys())
    values = list(label_values_dict.values())
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.55)])
    fig.update_layout(template='plotly_dark', title="Summary Donut Chart", height=450)
    return fig

st.sidebar.title("⚙ Dashboard Filters")

channel_name = st.sidebar.text_input("🔎 Channel Name", "Google Developers")
max_videos = st.sidebar.slider("🎥 Number of Latest Videos", 5, 100, 50)
date_range = st.sidebar.date_input(
    "🗓 Select Publish Date Range",
    [],
    help="Filter videos published within this date range"
)

fetch_data = st.sidebar.button("Fetch Data")
st.markdown('<h1 class="project-title"> ▶️YouTube Analytics Dashboard</h1>', unsafe_allow_html=True)

if fetch_data or st.session_state.get("channel_fetched", False):
    if fetch_data:
        channel_id = get_channel_id_from_name(channel_name)
        if not channel_id:
            st.error("❌ Channel not found!")
        else:
            st.session_state["channel_id"] = channel_id
            st.session_state["channel_fetched"] = True

    channel_id = st.session_state.get("channel_id")
    if channel_id:
        stats = get_channel_stats(channel_id)
        playlists = get_channel_playlists(channel_id)

        selected_playlist = None
        if playlists:
            selected_playlist = st.sidebar.selectbox(
                "🎵 Select Playlist",
                options=["All Playlists"] + list(playlists.keys()),
                key="playlist_select"
            )

        if selected_playlist and selected_playlist != "All Playlists":
            playlist_id = playlists[selected_playlist]
            videos_df = get_videos_from_playlist(playlist_id, max_videos)
        else:
            videos_df = get_latest_videos(channel_id, max_videos)

        if stats and not videos_df.empty:
            st.success(f"✅ Showing analytics for: **{selected_playlist or 'All Playlists'}**")

            kpi1, kpi2, kpi3 = st.columns(3, gap="small")
            kpi1.metric("👥 Subscribers", f"{stats['Subscribers']:,}")
            kpi2.metric("👁️ Views", f"{stats['Views']:,}")
            kpi3.metric("🎥 Videos", f"{stats['Total Videos']:,}")

            videos_df["Publish Date"] = pd.to_datetime(videos_df["Publish Date"])

            if date_range and len(date_range) == 2:
                start_date = pd.to_datetime(date_range[0])
                end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
                videos_df["Publish Date"] = pd.to_datetime(videos_df["Publish Date"], utc=True).dt.tz_localize(None)
                filtered_df = videos_df[
                    (videos_df["Publish Date"] >= start_date) & (videos_df["Publish Date"] < end_date)
                ]
                if filtered_df.empty:
                    st.warning("⚠ No videos found in the selected date range.")
                else:
                    videos_df = filtered_df
            else:
                st.info("ℹ Showing data for all available videos (no date range selected).")

            # After date filtering and playlist selection...
            videos_df["Publish Date"] = pd.to_datetime(videos_df["Publish Date"])
            # Create 'YearMonth' column in format YYYY-MM
            videos_df["YearMonth"] = videos_df["Publish Date"].dt.strftime("%Y-%m")

            # Build all available months for the dropdown (from earliest to latest video released)
            month_options = sorted(videos_df["YearMonth"].unique())

            if month_options:
                # Dropdown to select month
                selected_month = st.selectbox(
                    "Select Month for Bubble Chart Progress",
                    month_options,
                    index=len(month_options)-1  # Default to latest month
                )
                # Filter videos for the selected month only
                month_df = videos_df[videos_df["YearMonth"] == selected_month]
            else:
                selected_month = None
                month_df = pd.DataFrame([])

            fig_mix = go.Figure()
            fig_mix.add_trace(go.Bar(x=videos_df["Title"], y=videos_df["Views"], name="Views", marker=dict(color="rgba(0, 200, 255, 0.7)")))
            fig_mix.add_trace(go.Scatter(x=videos_df["Title"], y=videos_df["Likes"], mode="lines+markers", name="Likes", line=dict(color="#c084fc", width=2)))
            fig_mix.add_trace(go.Scatter(x=videos_df["Title"], y=videos_df["Comments"], mode="lines", name="Comments", line=dict(color="lime", dash="dot")))
            fig_mix.update_layout(template="plotly_dark", title="📊 Views vs Likes vs Comments", height=450)

            pie_values = [
                videos_df["Views"].sum() if not videos_df.empty else 0,
                videos_df["Likes"].sum() if not videos_df.empty else 0,
                videos_df["Comments"].sum() if not videos_df.empty else 0
            ]
            fig_pie = px.pie(
                names=["Views", "Likes", "Comments"],
                values=pie_values,
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_pie.update_layout(template="plotly_dark", title="📌 Filtered Videos Breakdown", height=450)

            fig_time = px.area(videos_df, x="Publish Date", y="Views", title="📈 Views Over Time",
                               markers=True, color_discrete_sequence=["#38bdf8"])
            fig_time.update_layout(template="plotly_dark", height=450)

            # Bubble chart for selected month progress
            fig_bubble_month = px.scatter(
                month_df,
                x="Views",
                y="Likes",
                size="Comments",
                color="Comments",
                hover_name="Title",
                title=f"💬 Engagement Progress for {selected_month}" if selected_month else "💬 Engagement (Month)",
                color_continuous_scale="Plasma"
            )
            fig_bubble_month.update_layout(template="plotly_dark", height=450)

            df_radar = pd.DataFrame({
                "Metrics": ["Views", "Likes", "Comments"],
                "Value": [
                    videos_df["Views"].sum() if not videos_df.empty else 0,
                    videos_df["Likes"].sum() if not videos_df.empty else 0,
                    videos_df["Comments"].sum() if not videos_df.empty else 0
                ]
            })
            df_radar["Value"] = np.log1p(df_radar["Value"])
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=df_radar["Value"], theta=df_radar["Metrics"], fill="toself", line=dict(color="#c084fc")))
            fig_radar.update_layout(template="plotly_dark", polar=dict(radialaxis=dict(visible=True, gridcolor="gray")), title="🌐 Radar Overview", height=450)

            table_df = videos_df[["Title", "Views", "Likes", "Comments", "Publish Date"]]

            fig_multi_area = multi_line_area_chart(videos_df)
            fig_bar_line = bar_line_combo_chart(videos_df)

            total_views = videos_df["Views"].sum() if not videos_df.empty else 1
            total_likes = videos_df["Likes"].sum() if not videos_df.empty else 0
            total_comments = videos_df["Comments"].sum() if not videos_df.empty else 0

            engagement_pct = ((total_likes + total_comments) / total_views) * 100 if total_views > 0 else 0
            engagement_pct = round(engagement_pct, 2)

            fig_radial = radial_progress_chart(engagement_pct, "Engagement %")

            sample_year_data = {'2023': (70, 30), '2024': (50, 50), '2025': (90, 10)}
            fig_horizontal = horizontal_progress_bars(sample_year_data)
            donut_data = {
                "Subscribers": stats["Subscribers"],
                "Views": stats["Views"],
                "Videos": stats["Total Videos"]
            }
            fig_donut = donut_chart_summary(donut_data)

            row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4, gap="small")
            row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4, gap="small")
            row3_col1, row3_col2, row3_col3, row3_col4 = st.columns(4, gap="small")

            row1_col1.plotly_chart(fig_mix, use_container_width=True)
            row1_col2.plotly_chart(fig_pie, use_container_width=True)
            row1_col3.plotly_chart(fig_time, use_container_width=True)
            row1_col4.plotly_chart(fig_bubble_month, use_container_width=True)

            row2_col1.plotly_chart(fig_radar, use_container_width=True)
            row2_col2.plotly_chart(fig_radial, use_container_width=True)
            row2_col3.plotly_chart(fig_multi_area, use_container_width=True)

            row2_col4.plotly_chart(fig_horizontal, use_container_width=True)
