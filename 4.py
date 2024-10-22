import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import webbrowser
from concurrent.futures import ThreadPoolExecutor
import time

class YouTubeSubtitleSearch:
    def __init__(self):
        self.links = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

    def search_videos(self, search_query):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # YouTube 검색 URL 생성
                search_url = f"ytsearch20:{search_query}"  # 상위 20개 결과만 검색
                result = ydl.extract_info(search_url, download=False)
                
                if 'entries' in result:
                    return result['entries']
                return []
        except Exception as e:
            st.error(f"검색 오류: {str(e)}")
            return []

    def get_video_subtitles(self, video):
        try:
            video_id = video['id']
            url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
            except:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except:
                    return None, None, None
                    
            return transcript, video['title'], url
        except Exception as e:
            return None, None, None

def initialize_session_state():
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'is_searching' not in st.session_state:
        st.session_state.is_searching = False
    if 'stop_search' not in st.session_state:
        st.session_state.stop_search = False

def stop_search():
    st.session_state.stop_search = True
    st.session_state.is_searching = False

def start_search():
    st.session_state.is_searching = True
    st.session_state.stop_search = False

def main():
    st.set_page_config(
        page_title="영어 수업을 위한 유튜브 자막 검색",
        page_icon="🎥",
        layout="wide"
    )

    st.title("영어 수업을 위한 유튜브 자막 검색 🎥")
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # 검색 엔진 초기화
    searcher = YouTubeSubtitleSearch()
    
    # 검색 인터페이스
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        search_text = st.text_input("검색어를 입력하세요", key="search_input")
    with col2:
        search_button = st.button(
            "검색", 
            type="primary", 
            use_container_width=True,
            disabled=st.session_state.is_searching
        )
    with col3:
        stop_button = st.button(
            "중단",
            type="secondary",
            use_container_width=True,
            disabled=not st.session_state.is_searching,
            on_click=stop_search
        )
    
    if search_button and search_text:
        start_search()
        
    if st.session_state.is_searching and search_text:
        with st.spinner("검색 중..."):
            videos = searcher.search_videos(search_text)
            
            if not videos:
                st.warning("검색 결과가 없습니다.")
                st.session_state.is_searching = False
                return
            
            video_count = 0
            subtitle_count = 0
            results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, video in enumerate(videos):
                if st.session_state.stop_search:
                    st.warning("검색이 중단되었습니다.")
                    break
                
                progress = (i + 1) / len(videos)
                progress_bar.progress(progress)
                
                subtitles, title, url = searcher.get_video_subtitles(video)
                
                if subtitles:
                    found = False
                    for subtitle in subtitles:
                        if st.session_state.stop_search:
                            break
                            
                        if search_text.lower() in subtitle['text'].lower():
                            if not found:
                                found = True
                                video_count += 1
                            
                            timestamp = int(subtitle['start'])
                            minutes = timestamp // 60
                            seconds = timestamp % 60
                            time_url = f"{url}&t={timestamp}"
                            
                            results.append({
                                'title': title,
                                'subtitle': subtitle['text'],
                                'time_url': time_url,
                                'timestamp': f"{minutes}:{seconds:02d}"
                            })
                            subtitle_count += 1
                            
                            status_text.text(f"검색 중... 찾은 동영상: {video_count}, 자막: {subtitle_count}개")
            
            st.session_state.search_results = results
            progress_bar.empty()
            status_text.empty()
            
            if st.session_state.stop_search:
                st.warning(f"검색이 중단됨 - 찾은 동영상: {video_count}, 자막: {subtitle_count}개")
            else:
                st.success(f"검색 완료 - 찾은 동영상: {video_count}, 자막: {subtitle_count}개")
            
            st.session_state.is_searching = False
            st.session_state.stop_search = False
    
    # 검색 결과 표시
    if st.session_state.search_results:
        for result in st.session_state.search_results:
            with st.container():
                st.markdown(f"### {result['title']}")
                st.markdown(f"**▶ {result['timestamp']}**")
                st.text(result['subtitle'])
                st.markdown(f"[바로가기]({result['time_url']})")
                st.divider()

if __name__ == "__main__":
    main()