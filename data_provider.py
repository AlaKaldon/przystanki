import datetime

import pandas as pd
import requests
import unidecode


class DataProvider():

    def __init__(self):
        # Ścieżki do plików
        stops_file = "./stops.txt"
        # Wczytanie danych do DataFrame
        self.stops_df = pd.read_csv(stops_file)
        # Usunięcie polskich znaków
        self.stops_df["stop_name"] = self.stops_df["stop_name"].apply(unidecode.unidecode)
        # Wybór najważniejszych kolumne
        self.table_data = self.stops_df[["stop_name", "stop_id"]]
        # Posortowanie danych
        self.table_data = self.table_data.sort_values(by=["stop_name"])

    def _get_stop_id_by_name(self, stop_name: str) -> int:
        stop_name_lower = stop_name.lower()  # Convert input to lowercase
        result = self.table_data.loc[self.table_data["stop_name"].str.lower() == stop_name_lower, "stop_id"]
        return result.iloc[0] if not result.empty else None

    def filter_stops_by_name(self, stop_name: str):
        if len(stop_name) == 0:
            return []
        else:
            return [s for s in self.stops_df["stop_name"].unique() if s.lower().startswith(stop_name.lower())]

    def _get_departures(self, stop_id):
        url = f"https://ckan2.multimediagdansk.pl/departures?stopId={stop_id}"

        try:
            response = requests.get(url, timeout=5)  # Timeout to avoid long waiting times
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()  # Parse the JSON response
            return data["departures"]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching departures: {e}")
            return None
        except Exception as e:
            print(f"Error parsing departures: {e}")
            return None

    # Funkcja zwracająca 8 najbliższych odjazdów różnych linii względem aktualnego czasu
    # Linie mogą się powtarzać tylko wtedy, gdy mają różne czasy odjazdu
    def get_next_departures(self, stop_name, count=8):
        now = datetime.datetime.now()
        stop_id = self._get_stop_id_by_name(stop_name)
        departures = self._get_departures(stop_id)
        filtered = pd.DataFrame(departures)

        filtered["departure_datetime"] = filtered["estimatedTime"].apply(
            lambda t: datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ"))

        filtered["minutes_left"] = (filtered["departure_datetime"] - now).dt.total_seconds() // 60
        filtered = filtered[filtered["minutes_left"] >= 0]
        filtered = filtered.sort_values(by="minutes_left")

        return filtered[["routeShortName", "minutes_left"]]

    def contains_stop_with_name(self, stop_name: str) -> bool:
        return self._get_stop_id_by_name(stop_name) is not None
