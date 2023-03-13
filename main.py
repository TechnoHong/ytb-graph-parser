import json
import re

import requests
from datetime import timedelta
from bs4 import BeautifulSoup


def millis_to_hhmmss(millis):
    print(timedelta(milliseconds=millis))


def get_mr_scraping(url: str, count: int = 5):
    """
    ytInitialData Scraping 방식
    브라우저를 통한 접속과 requests의 response에 차이가 있음. (아마 유튜브 측에서 로봇임을 감지해 다른 값을 준듯함)
    requests를 통한 response에서 구간별 most replayed 정규화된 값을 찾을 수 있었음 (heatmap_array)

    heatmap_array
        timeRangeStartMillis: 구간 시작 시간 (millisecond)
        markerDurationMillis: 구간 길이 (millisecond; 아마 동영상 전체 길이의 1/100 millisecond로 설정되어 있는 듯함)
        heatMarkerIntensityScoreNormalized: Replayed 빈도의 normalized 값, 1에 가까울수록 자주 재생된 구간 ( 0 <= x <= 1 )

    따라서 heatMarkerIntensityScoreNormalized 값을 내림차순으로 정렬하여 리턴 갯수(:param: count)만큼 return

    :param url: 대상 유튜브 Video URL
    :param count: 리턴 갯수, default=5
    :return: '동영상 중 replayed 빈도가 높은 순간' millisecond 단위의 list (descending)
    """
    try:
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        data = re.search(r"var ytInitialData = ({.*?});", soup.prettify()).group(1)
        markers_map = json.loads(data)['playerOverlays']['playerOverlayRenderer']['decoratedPlayerBarRenderer'][
            'decoratedPlayerBarRenderer']['playerBar']['multiMarkersPlayerBarRenderer']['markersMap']
        heat_seeker = []

        # 챕터가 나눠진 동영상 대응
        for d in markers_map:
            if d['key'] == 'HEATSEEKER':
                heat_seeker = d

        heatmap_array = \
            heat_seeker['value']['heatmap']['heatmapRenderer']['heatMarkers']
        heatmap_sorted_array = sorted(heatmap_array,
                                      key=(lambda x: x['heatMarkerRenderer']['heatMarkerIntensityScoreNormalized']),
                                      reverse=True)

        result = list(map(lambda x: x['heatMarkerRenderer']['timeRangeStartMillis'], heatmap_sorted_array[0:count]))

        list(map(millis_to_hhmmss, result))

        return result
    except (KeyError, TypeError):  # MostReplayed 정보가 없음
        return 'YT404'
    except AttributeError:  # 요청한 URL이 올바르지 않음
        return 'YT400'
