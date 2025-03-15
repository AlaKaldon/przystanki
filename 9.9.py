import pygame
import pandas as pd
import datetime
import unidecode


# Ścieżki do plików
stops_file = "./stops.txt"
stop_times_file = "./stop_times.txt"
trips_file = "./trips.txt"
routes_file = "./routes.txt"

# Wczytanie danych do DataFrame
stops_df = pd.read_csv(stops_file)
stop_times_df = pd.read_csv(stop_times_file)
trips_df = pd.read_csv(trips_file)
routes_df = pd.read_csv(routes_file)


# Usunięcie polskich znaków
stops_df["stop_name"] = stops_df["stop_name"].apply(unidecode.unidecode)

# Połączenie danych
merged_df = (stop_times_df
             .merge(trips_df, on="trip_id")
             .merge(routes_df, on="route_id")
             .merge(stops_df, on="stop_id"))

# Wybór najważniejszych kolumn
table_data = merged_df[["stop_name", "stop_id", "route_short_name", "departure_time"]]

# Posortowanie danych
table_data = table_data.sort_values(by=["stop_name", "departure_time"])


# Konwersja kolumny departure_time na format datetime
def convert_time(time_str):
    try:
        return datetime.datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        return None


table_data["departure_time"] = table_data["departure_time"].apply(convert_time)


# Funkcja zwracająca 8 najbliższych odjazdów różnych linii względem aktualnego czasu
# Linie mogą się powtarzać tylko wtedy, gdy mają różne czasy odjazdu
def get_next_departures(stop_name, count=8):
    now = datetime.datetime.now()
    filtered = table_data[(table_data["stop_name"] == stop_name)]
    filtered["departure_datetime"] = filtered["departure_time"].apply(
        lambda t: datetime.datetime.combine(now.date(), t) if t else None)
    filtered = filtered[filtered["departure_datetime"] > now]
    filtered["minutes_left"] = (filtered["departure_datetime"] - now).dt.total_seconds() // 60

    # Usunięcie duplikatów tych samych linii o tych samych godzinach
    filtered = filtered.drop_duplicates(subset=["route_short_name", "departure_datetime"])

    # Wybór pierwszych 8 odjazdów
    filtered = filtered.sort_values(by="departure_datetime").head(count)

    return filtered[["route_short_name", "minutes_left"]]


# Inicjalizacja pygame
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Tablica SIP")

# Wczytanie czcionki LED
led_font = pygame.font.Font("TickingTimebombBB.ttf", 30)
clock = pygame.time.Clock()

# Pole tekstowe
typed_text = ""
active = False
input_box = pygame.Rect(20, 50, 400, 30)
selected_stop = ""
suggestions = []
show_suggestions = True


def draw_screen():
    screen.fill((0, 0, 0))

    text = led_font.render("Wpisz nazwe przystanku:", True, (255, 140, 0))
    screen.blit(text, (20, 20))

    color = (255, 140, 0) if active else (100, 100, 100)
    pygame.draw.rect(screen, color, input_box, 2)

    txt_surface = led_font.render(typed_text, True, (255, 140, 0))
    screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))

    # Wyświetlanie podpowiedzi, jeśli aktywne
    suggestion_boxes = []
    if show_suggestions:
        for i, suggestion in enumerate(suggestions[:5]):  # Ograniczamy liczbę podpowiedzi do 5
            suggestion_surface = led_font.render(suggestion, True, (255, 140, 0))
            suggestion_rect = suggestion_surface.get_rect(topleft=(input_box.x + 5, input_box.y + 35 + i * 30))
            screen.blit(suggestion_surface, suggestion_rect.topleft)
            suggestion_boxes.append((suggestion, suggestion_rect))

    if selected_stop and not show_suggestions:
        stop_surface = led_font.render(selected_stop, True, (255, 140, 0))
        screen.blit(stop_surface, (20, 100))
        departures = get_next_departures(selected_stop)
        for i, (line, minutes_left) in enumerate(zip(departures["route_short_name"], departures["minutes_left"])):
            text = led_font.render(f"{line}: {int(minutes_left)} MIN", True, (255, 140, 0))
            screen.blit(text, (20, 150 + i * 30))

    pygame.display.flip()
    return suggestion_boxes


running = True
while running:
    suggestion_boxes = draw_screen()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = True
                show_suggestions = True
            else:
                active = False

            # Sprawdzenie, czy użytkownik kliknął na jedną z podpowiedzi
            for suggestion, rect in suggestion_boxes:
                if rect.collidepoint(event.pos):
                    typed_text = suggestion
                    selected_stop = suggestion
                    active = False
                    show_suggestions = False  # Ukrycie podpowiedzi po wyborze
                    break
        elif event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:
                    if typed_text in stops_df["stop_name"].values:
                        selected_stop = typed_text
                        show_suggestions = False  # Ukrycie podpowiedzi po wyborze
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]
                else:
                    typed_text += event.unicode

                # Generowanie podpowiedzi na podstawie wpisanego tekstu
                suggestions = [s for s in stops_df["stop_name"].unique() if s.lower().startswith(typed_text.lower())]

    clock.tick(30)  # Aktualizacja co 30 klatek na sekundę

pygame.quit()
