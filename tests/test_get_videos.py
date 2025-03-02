import pytest
import requests
from utilities.get_videos import convert_duration, fetch_video_details, fetch_videos_from_channel

def test_convert_duration():
    assert convert_duration('PT1H2M3S') == '1:02:03'
    assert convert_duration('PT15M') == '0:15:00'
    assert convert_duration('PT0S') == '0:00:00'
    assert convert_duration('InvalidDuration') == 'N/A'

def test_fetch_video_details(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'items': [{'id': 'video1', 'statistics': {'viewCount': '1000'}, 'contentDetails': {'duration': 'PT10M'}}]}
    mocker.patch('requests.get', return_value=mock_response)
    api_key = 'test_api_key'
    video_ids = ['video1']
    details = fetch_video_details(video_ids, api_key)
    assert len(details) == 1
    assert details[0]['id'] == 'video1'
    assert details[0]['statistics']['viewCount'] == '1000'

def test_fetch_videos_from_channel(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'items': [{'id': {'videoId': 'video1'}, 'snippet': {'title': 'Test Video', 'publishedAt': '2025-03-01T00:00:00Z'}}]}
    mocker.patch('requests.get', return_value=mock_response)
    api_key = 'test_api_key'
    channel_id = 'test_channel_id'
    data = fetch_videos_from_channel(channel_id, api_key)
    assert 'items' in data
    assert len(data['items']) == 1
    assert data['items'][0]['id']['videoId'] == 'video1'
    assert data['items'][0]['snippet']['title'] == 'Test Video'
