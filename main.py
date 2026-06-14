from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import hex_colormap, colormap
from kivy.animation import Animation
from kivy.metrics import sp, dp
from kivy.uix.image import Image
from kivy import platform
from kivy.properties import NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader


class Menu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def go_game(self, *args):
        self.manager.current = "game"
        self.manager.transition.direction = "left"

    def go_settings(self, *args):
        self.manager.current = "settings"
        self.manager.transition.direction = "up"

    def exit_app(self, *args):
        app.stop()


class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def go_menu(self, *args):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"


class Fish(Image):
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.5
    fish_current = None
    fish_index = 0
    hp_current = NumericProperty(0)
    angle = NumericProperty(0)

    # ЗМІНИЛИ ТУТ: Замість bubble01.mp3 тепер завантажується uron.mp3
    click_music = SoundLoader.load('assets/audios/uron.mp3')
    defeate_music = SoundLoader.load('assets/audios/fish_def.ogg')

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        if self.fish_index < len(app.LEVELS[app.LEVEL]):
            self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
            self.source = app.FISHES[self.fish_current]['source']
            self.hp_current = app.FISHES[self.fish_current]['hp']

            if self.fish_current == 'fish4':
                self.GAME_SCREEN.boss_hp_text = "150 HP"
                self.GAME_SCREEN.ids.boss_hp_label.opacity = 1
            elif self.fish_current == 'fish5':
                self.GAME_SCREEN.boss_hp_text = "300 HP"
                self.GAME_SCREEN.ids.boss_hp_label.opacity = 1
            elif self.fish_current == 'fish6':
                self.GAME_SCREEN.boss_hp_text = "500 HP"
                self.GAME_SCREEN.ids.boss_hp_label.opacity = 1
            else:
                self.GAME_SCREEN.ids.boss_hp_label.opacity = 0

            self.swim()

    def swim(self):
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2)
        self.opacity = 1
        swim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, duration=1)
        swim.start(self)
        swim.bind(on_complete=lambda w, a: setattr(self, "interaction_block", False))

    def defeated(self):
        self.interaction_block = True
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        old_size = self.size.copy()
        old_pos = self.pos.copy()
        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2, self.pos[1] - (new_size[0] - self.size[1]) / 2)

        anim &= Animation(size=(new_size), t='in_out_bounce') + Animation(size=(old_size), duration=0)
        anim &= Animation(pos=(new_pos), t='in_out_bounce') + Animation(pos=(old_pos), duration=0)
        anim &= Animation(opacity=0)
        anim.start(self)

        self.defeate_music.play()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return
        if not self.anim_play and not self.interaction_block:
            self.hp_current -= 1
            self.GAME_SCREEN.score += 1
            self.click_music.play()

            if self.fish_current == 'fish4':
                displayed_hp = int(self.hp_current * (150 / 70))
                self.GAME_SCREEN.boss_hp_text = f"{displayed_hp} HP"
            elif self.fish_current == 'fish5':
                displayed_hp = int(self.hp_current * 2)
                self.GAME_SCREEN.boss_hp_text = f"{displayed_hp} HP"
            elif self.fish_current == 'fish6':
                displayed_hp = int(self.hp_current * 2.5)
                self.GAME_SCREEN.boss_hp_text = f"{displayed_hp} HP"

            if self.hp_current > 0:
                old_size = self.size.copy()
                old_pos = self.pos.copy()
                new_size = (self.size[0] * self.COEF_MULT, self.size[1] * self.COEF_MULT)
                new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2,
                           self.pos[1] - (new_size[0] - self.size[1]) / 2)

                zoom_anim = Animation(size=(new_size), duration=0.05) + Animation(size=(old_size), duration=0.05)
                zoom_anim &= Animation(pos=(new_pos), duration=0.05) + Animation(pos=(old_pos), duration=0.05)

                zoom_anim.start(self)
                self.anim_play = True
                zoom_anim.bind(on_complete=lambda *args: setattr(self, "anim_play", False))
            else:
                self.defeated()

                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return super().on_touch_down(touch)


class Game(Screen):
    score = NumericProperty(0)
    level_text = StringProperty("Level 1")
    boss_hp_text = StringProperty("150 HP")
    back_sound = SoundLoader.load('assets/audios/Black_Swan_part.mp3')
    back_sound.loop = True
    level_complete_sound = SoundLoader.load('assets/audios/level_complete.ogg')

    def on_pre_enter(self, *args):
        self.score = 0
        app.LEVEL = 0
        self.level_text = f"Level {app.LEVEL + 1}"
        self.boss_hp_text = "150 HP"
        self.ids.level_complete.opacity = 0
        self.ids.boss_hp_label.opacity = 0
        self.ids.fish.fish_index = 0
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.show_level_title()
        self.back_sound.play()
        return super().on_enter(*args)

    def show_level_title(self):
        self.level_text = f"Level {app.LEVEL + 1}"
        self.ids.level_title.y = '130dp'
        self.ids.level_title.opacity = 0

        label_animation = (
                Animation(y=(self.height - self.ids.level_title.height) / 2 + dp(100), duration=1)
                + Animation(opacity=1, duration=1)
                + Animation(y=self.height, duration=1)
        )
        label_animation &= Animation(opacity=1, duration=2) + Animation(opacity=0, duration=1)
        label_animation.start(self.ids.level_title)
        label_animation.bind(on_complete=self.start_game)

    def start_game(self, animation, widget):
        self.ids.fish.new_fish()

    def level_complete(self, *args):
        anim_zoom = Animation(font_size=dp(70), d=0.3)
        anim_zoom &= Animation(opacity=1, d=0.3)

        self.back_sound.volume = 0.5
        self.level_complete_sound.play()

        anim_zoom.start(self.ids.level_complete)
        anim_zoom.bind(on_complete=self.next_level_prep)

    def next_level_prep(self, *args):
        Clock.schedule_once(self.load_next_level, 1.5)

    def load_next_level(self, *args):
        self.ids.level_complete.opacity = 0
        self.ids.level_complete.font_size = dp(50)

        if app.LEVEL + 1 < len(app.LEVELS):
            app.LEVEL += 1
            self.ids.fish.fish_index = 0
            self.show_level_title()
        else:
            self.ids.level_complete.text = "YOU WIN\nTHE GAME!"
            self.ids.level_complete.opacity = 1

    def go_home(self):
        fish_disapear_anim = Animation(opacity=0, duration=0.1)
        fish_disapear_anim.start(self.ids.fish)
        self.back_sound.stop()
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


class ClickerApp(App):
    LEVEL = 0

    FISHES = {
        'fish1': {'source': 'assets/images/Shelly.png', 'hp': 10},
        'fish2': {'source': 'assets/images/zombie.png', 'hp': 20},
        'fish3': {'source': 'assets/images/Mortis.png', 'hp': 50},
        'fish4': {'source': 'assets/images/enderman.png', 'hp': 70},
        'fish5': {'source': 'assets/images/Voron.png', 'hp': 150},
        'fish6': {'source': 'assets/images/Dragon-Boss.png', 'hp': 200}
    }

    LEVELS = [
        ['fish1'],
        ['fish2'],
        ['fish3'],
        ['fish4'],
        ['fish5'],
        ['fish6']
    ]

    def build(self):
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        return sm


if platform != 'android':
    Window.size = (450, 900)

app = ClickerApp()
app.run()