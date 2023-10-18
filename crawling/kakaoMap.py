import os
import requests
from dotenv import load_dotenv


class KakaoMap:
    def __init__(self):
        load_dotenv()
        kakao_api_key = os.getenv("KAKAO_API_KEY")
        self.headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
        # print(kakao_api_key)

    def convert_address_to_coords(self, building_address):
        geocode_url = (
            "https://dapi.kakao.com/v2/local/search/address.json"  # 주소로부터 좌표 정보 가져오기
        )
        params = {"query": building_address}
        response = requests.get(geocode_url, headers=self.headers, params=params)
        data = response.json()
        # print(data)

        if data.get("documents"):
            location = data["documents"][0]["address"]
            return (float(location["y"]), float(location["x"]))
        else:
            print(building_address, "주소를 찾을 수 없습니다.")
            return (None, None)

    def get_nearest_station_distance(self, building_address):
        stations_url = (
            "https://dapi.kakao.com/v2/local/search/keyword.json"  # 가장 가까운 역 찾기
        )
        keyword = "역"
        building_coords = self.convert_address_to_coords(building_address)

        if building_coords:
            station_params = {
                "query": keyword,
                "x": building_coords[1],
                "y": building_coords[0],
                "radius": 2000,  # 일정 범위 내에서 검색 (2km)
            }
            station_response = requests.get(
                stations_url, headers=self.headers, params=station_params
            )
            station_data = station_response.json()
            # print('역정보',station_data)

            if station_data.get("documents"):
                return (
                    station_data["documents"][0]["place_name"],
                    float(station_data["documents"][0]["distance"]),
                )
            else:
                return (None, None), print(building_address, "가까운 역을 찾을 수 없습니다.")
        else:
            return (None, None)
