import pygame


class Screen():
    def __init__(self, provider):
        self.screen = pygame.display.set_mode((600, 400))
        pygame.display.set_caption("Tablica SIP")

        # Wczytanie czcionki LED
        self.led_font = pygame.font.Font("TickingTimebombBB.ttf", 30)
        self.clock = pygame.time.Clock()

        # Pole tekstowe
        self.typed_text = ""
        self.input_box_is_active = False
        self.input_box = pygame.Rect(20, 50, 400, 35)
        self.selected_stop = ""
        self.suggestions = []
        self.suggestion_boxes = []
        self.show_suggestions = False
        self.running = True
        self.data_provider = provider
        self.departures = None

    def is_running(self):
        return self.running

    def tick(self):
        self.clock.tick(30)

    def process_user_input(self, event):
        if self.input_box_is_active:
            if event.key == pygame.K_RETURN:
                if self.data_provider.contains_stop_with_name(self.typed_text):
                    self.selected_stop = self.typed_text
                    self.show_suggestions = False  # Ukrycie podpowiedzi po wyborze
                self.input_box_is_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.typed_text = self.typed_text[:-1]
            else:
                self.typed_text += event.unicode

    def draw(self):
        self._render_screen()
        self.suggestions = self.data_provider.filter_stops_by_name(self.typed_text)

        # Wyświetlanie podpowiedzi, jeśli aktywne
        self.suggestion_boxes = []
        if self.show_suggestions:
            self.suggestion_boxes = self._display_suggestions(self.suggestions)

        if self.selected_stop and not self.show_suggestions:
            if self.departures is None:
                self.departures = self.data_provider.get_next_departures(self.selected_stop)
            self._display_departures(self.departures)

        pygame.display.flip()

    def select_suggestion(self, event):
        if self.input_box.collidepoint(event.pos):
            self.input_box_is_active = True
            self.show_suggestions = True
        else:
            self.input_box_is_active = False
        # Sprawdzenie, czy użytkownik kliknął na jedną z podpowiedzi
        for suggestion, rect in self.suggestion_boxes:
            if rect.collidepoint(event.pos):
                self.typed_text = suggestion
                self.selected_stop = suggestion
                self.input_box_is_active = False
                self.show_suggestions = False  # Ukrycie podpowiedzi po wyborze
                self.departures = None
                break

    def stop(self):
        self.running = False

    def _render_screen(self):
        self.screen.fill((0, 0, 0))
        text = self.led_font.render("Wpisz nazwe przystanku:", True, (255, 140, 0))
        self.screen.blit(text, (20, 20))
        color = (255, 140, 0) if self.input_box_is_active else (100, 100, 100)
        pygame.draw.rect(self.screen, color, self.input_box, 2)
        txt_surface = self.led_font.render(self.typed_text, True, (255, 140, 0))
        self.screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))

    def _display_departures(self, departures):
        for i, (line, minutes_left) in enumerate(zip(departures["routeShortName"], departures["minutes_left"])):
            text = self.led_font.render(f"{line}: {int(minutes_left)} MIN", True, (255, 140, 0))
            self.screen.blit(text, (20, 100 + i * 30))

    def _display_suggestions(self, suggestions):
        suggestion_boxes = []
        for i, suggestion in enumerate(suggestions[:5]):  # Ograniczamy liczbę podpowiedzi do 5
            suggestion_surface = self.led_font.render(suggestion, True, (255, 140, 0))
            suggestion_rect = suggestion_surface.get_rect(topleft=(self.input_box.x + 5, self.input_box.y + 35 + i * 30))
            self.screen.blit(suggestion_surface, suggestion_rect.topleft)
            suggestion_boxes.append((suggestion, suggestion_rect))
        return suggestion_boxes
