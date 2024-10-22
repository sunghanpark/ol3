import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import Search, YouTube
from concurrent.futures import ThreadPoolExecutor
import time

class YouTubeSubtitleSearch:
    def __init__(self):
        self.links = {}
        self.executor = ThreadPoolExecutor(max_workers=3)

    def search_videos(self, search_query):
        try:
            s = Search(search_query)
            videos = []
            for result in s.results[:20]:  # 상위 20개 결과만 가져옴
                video = {
                    'id': result.video_id,
                    'title': result.title,
                    'url': f"https://www.youtube.com/watch?v={result.video_id}"
                }
                videos.append(video)
            return videos
        except Exception as e:
            st.error(f"검색 오류: {str(e)}")
            return []

    def get_video_subtitles(self, video):
        try:
            url = video['url']
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video['id'], languages=['ko'])
            except:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video['id'], languages=['en'])
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
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

def stop_search():
    st.session_state.stop_search = True
    st.session_state.is_searching = False

def start_search():
    if st.session_state.search_query.strip():
        st.session_state.is_searching = True
        st.session_state.stop_search = False
        return True
    return False

def create_loop_url(base_url, start_time):
    end_time = start_time + 10
    return f"{base_url}&start={start_time}&end={end_time}&loop=1"

def format_percentage(progress):
    return f"{progress:.1f}%"

def on_search_input_change():
    if st.session_state.search_input != st.session_state.search_query:
        st.session_state.search_query = st.session_state.search_input
        start_search()

def main():
    st.set_page_config(
        page_title="영어 수업을 위한 유튜브 자막 검색",
        page_icon="🎥",
        layout="wide"
    )

    st.title("영어 수업을 위한 유튜브 자막 검색 🎥")
    
    initialize_session_state()
    searcher = YouTubeSubtitleSearch()
    
    # 검색 인터페이스
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        search_text = st.text_input(
            "검색어를 입력하세요", 
            key="search_input",
            value=st.session_state.search_query,
            on_change=on_search_input_change
        )
    with col2:
        search_button = st.button(
            "검색", 
            type="primary", 
            use_container_width=True,
            disabled=st.session_state.is_searching,
            on_click=lambda: start_search() if search_text else None
        )
    
    with col3:
        stop_button = st.button(
            "중단",
            type="secondary",
            use_container_width=True,
            disabled=not st.session_state.is_searching,
            on_click=stop_search
        )
    
    if st.session_state.is_searching:
        with st.spinner("검색 중..."):
            videos = searcher.search_videos(st.session_state.search_query)
            
            if not videos:
                st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
                st.session_state.is_searching = False
                return
            
            video_count = 0
            subtitle_count = 0
            results = []
            
            # 진행률 표시를 위한 컨테이너들
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                progress_text = st.empty()
                status_text = st.empty()
            
            total_videos = len(videos)
            
            for i, video in enumerate(videos):
                if st.session_state.stop_search:
                    st.warning("검색이 중단되었습니다.")
                    break
                
                progress = (i + 1) / total_videos
                progress_percentage = progress * 100
                progress_bar.progress(progress)
                progress_text.markdown(f"### 진행률: {format_percentage(progress_percentage)}")
                
                subtitles, title, url = searcher.get_video_subtitles(video)
                
                if subtitles:
                    found = False
                    for subtitle in subtitles:
                        if st.session_state.stop_search:
                            break
                            
                        if st.session_state.search_query.lower() in subtitle['text'].lower():
                            if not found:
                                found = True
                                video_count += 1
                            
                            timestamp = int(subtitle['start'])
                            minutes = timestamp // 60
                            seconds = timestamp % 60
                            time_url = create_loop_url(url, timestamp)
                            
                            results.append({
                                'title': title,
                                'subtitle': subtitle['text'],
                                'time_url': time_url,
                                'timestamp': f"{minutes}:{seconds:02d}",
                                'raw_url': url,
                                'start_time': timestamp
                            })
                            subtitle_count += 1
                            
                            status_text.text(f"검색된 동영상: {video_count}, 자막: {subtitle_count}개")
            
            st.session_state.search_results = results
            progress_container.empty()
            
            if len(results) == 0:
                st.warning("검색어를 포함한 자막을 찾을 수 없습니다. 다른 검색어를 시도해보세요.")
            elif st.session_state.stop_search:
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
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    normal_url = f"{result['raw_url']}&t={result['start_time']}"
                    st.markdown(f"[일반 재생]({normal_url})")
                with col2:
                    st.markdown(f"[10초 반복 재생]({result['time_url']})")
                
                st.divider()

if __name__ == "__main__":
    main()
