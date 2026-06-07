from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy import platform
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

# Встановлення розміру вікна для ПК ТУТ (до створення віджетів)
if platform != 'android':
    Window.size = (450, 900)


class Menu(Screen):
    def go_game(self, *args):
        self.manager.transition.direction = "left"
        self.manager.current = "game"

    def go_settings(self, *args):
        self.manager.transition.direction = "up"
        self.manager.current = "settings"

    def exit_app(self, *args):
        App.get_running_app().stop()


class Settings(Screen):
    def go_menu(self, *args):
        self.manager.transition.direction = "down"
        self.manager.current = "menu"


# КЛАС РИБИ: Обробка кліків, створення "нової" риби
class Fish(Image):
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.1  # Зменшено з 1.5 до 1.1, щоб риба не вилазила за межі екрана
    fish_current = None
    fish_index = 0
    hp_current = 0
    angle = NumericProperty(0)

    # Безпечне завантаження аудіо (якщо файлів немає, гра не впаде)
    click_music = SoundLoader.load('assets/audios/bubble01.mp3')
    defeat_music = SoundLoader.load('assets/audios/fish_def.ogg')

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent
        super().on_kv_post(base_widget)

    def new_fish(self, *args):
        app = App.get_running_app()
        # Захист від виходу за межі існуючих рівнів
        if app.LEVEL not in app.LEVELS or self.fish_index >= len(app.LEVELS[app.LEVEL]):
            self.fish_index = 0

        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        self.hp_current = app.FISHES[self.fish_current]['hp']
        self.swim()

    def swim(self):
        self.interaction_block = True
        # Початкова позиція за лівою межею екрана
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2 - self.height / 2)
        self.opacity = 1

        # Рух до центру екрана
        swim_anim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, d=1)
        swim_anim.bind(on_complete=lambda w, a: setattr(self, "interaction_block", False))
        swim_anim.start(self)

    # Перемогли рибу
    def defeated(self):
        self.interaction_block = True
        if self.defeat_music:
            self.defeat_music.play()

        old_size = self.size.copy()
        old_pos = self.pos.copy()

        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2, self.pos[1] - (new_size[1] - self.size[1]) / 2)

        # Комбінована анімація зникнення (обертання + розширення + зникання прозорості)
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')
        anim &= (Animation(size=new_size, pos=new_pos, t='in_out_bounce', d=0.5) + Animation(size=old_size, pos=old_pos,
                                                                                             d=0))
        anim &= Animation(opacity=0, d=0.8)

        anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.anim_play or self.interaction_block:
            return True

        if self.hp_current > 0:
            self.hp_current -= 1
            self.GAME_SCREEN.score += 1
            if self.click_music:
                self.click_music.play()

            if self.hp_current > 0:
                old_size = self.size.copy()
                old_pos = self.pos.copy()

                new_size = (self.size[0] * self.COEF_MULT, self.size[1] * self.COEF_MULT)
                new_pos = (
                self.pos[0] - (new_size[0] - self.size[0]) / 2, self.pos[1] - (new_size[1] - self.size[1]) / 2)

                # Послідовна анімація кліку (збільшення і повернення)
                zoom_anim = Animation(size=new_size, pos=new_pos, d=0.05) + Animation(size=old_size, pos=old_pos,
                                                                                      d=0.05)

                self.anim_play = True
                zoom_anim.bind(on_complete=lambda w, a: setattr(self, "anim_play", False))
                zoom_anim.start(self)
            else:
                self.defeated()
                app = App.get_running_app()

                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return True


class Game(Screen):
    score = NumericProperty(0)
    back_sound = SoundLoader.load('assets/audios/Black_Swan_part.mp3')
    level_complete_sound = SoundLoader.load('assets/audios/level_complete.ogg')

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.back_sound:
            self.back_sound.loop = True

    def on_pre_enter(self, *args):
        self.score = 0
        app = App.get_running_app()
        app.LEVEL = 0
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        # Початкова анімація появи і спливання тексту рівня
        label_animation = (
                Animation(y=(self.height - self.ids.level_title.height) / 2 + dp(100), d=1)
                + Animation(opacity=1, d=1)
                + Animation(y=self.height, d=1)
        )
        label_animation &= Animation(opacity=1, d=2) + Animation(opacity=0, d=1)

        label_animation.start(self.ids.level_title)
        label_animation.bind(on_complete=self.start_game)

        if self.back_sound:
            self.back_sound.volume = 1.0
            self.back_sound.play()

        return super().on_enter(*args)

    def start_game(self, animation, widget):
        self.ids.fish.new_fish()

    def level_complete(self, *args):
        app = App.get_running_app()
        app.LEVEL += 1

        if self.back_sound:
            self.back_sound.volume = 0.5
        if self.level_complete_sound:
            self.level_complete_sound.play()

        anim_zoom = Animation(font_size=dp(70), d=0.3)
        anim_zoom &= Animation(opacity=1, d=0.3)
        anim_zoom.start(self.ids.level_complete)

    def go_home(self):
        fish_disappear_anim = Animation(opacity=0, d=0.1)
        fish_disappear_anim.start(self.ids.fish)

        if self.back_sound:
            self.back_sound.stop()

        self.manager.transition.direction = "right"
        self.manager.current = "menu"


class ClickerApp(App):
    LEVEL = 0

    # Обов'язково додано структуру рівнів (LEVELS), яка використовується у вашому класі Fish
    LEVELS = {
        0: ['fish1', 'fish2'],
        1: ['fish3']
    }

    FISHES = {
        'fish1': {'source': 'assets/images/fish_01.png', 'hp': 10},
        'fish2': {'source': 'assets/images/fish_02.png', 'hp': 20},
        'fish3': {'source': 'assets/images/clown-fish.png', 'hp': 50}
    }

    def build(self):
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        return sm


if __name__ == '__main__':
    ClickerApp().run()
