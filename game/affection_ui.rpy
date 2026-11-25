################################################################################
## 好感度バー＆名前色による微細表現システム (affection_ui.rpy)
##
## ・テキストボックス自体は一切装飾せずクリアな読みやすさを保ちます。
## ・画面左上（立ち絵やテキストと被らない位置）に「数値を見せない好感度バー」を配置し、
##   好感度の値に応じてバー自体の色・枠の装飾（ツタ・花 ／ ひび割れ）が変化します。
## ・対象キャラクターの名前の文字色も、好感度に応じて「冷たい青 → 暖色」へ変化します。
##
## 【シナリオ（script.rpy）での使い方】
##   $ unlock_affection("k")    # 鎌倉詩乃の好感度バーを解禁して表示開始
##   $ unlock_affection("m")    # 真鶴千景の好感度バーを解禁して表示開始
##   $ add_affection("k", 15)   # 鎌倉詩乃の好感度を +15
##   $ add_affection("k", -20)  # 鎌倉詩乃の好感度を -20
##   $ add_affection("m", 25)   # 真鶴千景の好感度を +25
##   $ set_affection("k", 80)   # 鎌倉詩乃の好感度を 80 に直接設定
##
## ※ 開発・動作確認用として、ゲーム中に [F8] キーを押すと調整パネルを開閉できます。
################################################################################

init offset = -1

## ヒロインごとの好感度（-100 〜 +100、初期値は 0）
default affection = {
    "k": 0,  # 鎌倉詩乃
    "m": 0,  # 真鶴千景
}

## ヒロインごとの好感度バー解禁フラグ（最初は False＝誰も表示されない状態）
default unlocked_heroines = {
    "k": False,  # 鎌倉詩乃（$ unlock_affection("k") で True になる）
    "m": False,  # 真鶴千景（$ unlock_affection("m") で True になる）
}

## 現在好感度バーに表示する対象ヒロインID（未解禁時は None）
default active_heroine = None

## 好感度バー全体の表示オン／オフフラグ
default show_affection_bar = True

## 開発・確認用プレビューパネルの表示フラグ（通常プレイ時は False で非表示）
default show_affection_debug = False

init python:

    # キャラクター名からヒロインIDへの対応辞書
    HEROINE_NAME_TO_ID = {
        "鎌倉詩乃": "k",
        "真鶴千景": "m",
    }

    # ヒロインIDから表示名への対応辞書
    HEROINE_ID_TO_NAME = {
        "k": "鎌倉詩乃",
        "m": "真鶴千景",
    }

    # ヒロインごとの名前カラーパレット定義
    # (好感度, "#RRGGBB") のリスト。間の値は滑らかにRGB補間されます。
    HEROINE_COLOR_STOPS = {
        "k": [
            (-100, "#2b4478"),  # 氷のように冷たい濃紺（最低好感度）
            ( -50, "#3b62a6"),  # 冷たい青
            (   0, "#5b86d6"),  # クールな青（初期状態）
            (  30, "#8f94dc"),  # 少し柔らかみを帯びたラベンダーブルー
            (  60, "#df7da2"),  # 温かみのある桜色・ローズピンク
            ( 100, "#ff625c"),  # 情熱的で温かい茜色・コーラルレッド（最大好感度）
        ],
        "m": [
            (-100, "#293d70"),  # 凍てつく群青（最低好感度）
            ( -50, "#3f58a3"),  # 冷たい青紫
            (   0, "#5c7ad6"),  # クールな青（初期状態）
            (  30, "#9c7edc"),  # 淡い藤色・バイオレット
            (  60, "#eb73be"),  # 華やかなマゼンタピンク
            ( 100, "#ff7b54"),  # 陽だまりのようなウォームコーラル（最大好感度）
        ],
    }

    def _hex_to_rgb(hex_str):
        h = hex_str.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _rgb_to_hex(rgb):
        r = max(0, min(255, int(round(rgb[0]))))
        g = max(0, min(255, int(round(rgb[1]))))
        b = max(0, min(255, int(round(rgb[2]))))
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _interpolate_color(stops, value):
        """好感度 value に応じてカラーストップ間を線形補間した #RRGGBB を返す"""
        if not stops:
            return "#ffffff"
        if value <= stops[0][0]:
            return stops[0][1]
        if value >= stops[-1][0]:
            return stops[-1][1]

        for i in range(len(stops) - 1):
            v0, c0 = stops[i]
            v1, c1 = stops[i + 1]
            if v0 <= value <= v1:
                if v1 == v0:
                    return c1
                t = float(value - v0) / float(v1 - v0)
                rgb0 = _hex_to_rgb(c0)
                rgb1 = _hex_to_rgb(c1)
                mixed = (
                    rgb0[0] + (rgb1[0] - rgb0[0]) * t,
                    rgb0[1] + (rgb1[1] - rgb0[1]) * t,
                    rgb0[2] + (rgb1[2] - rgb0[2]) * t,
                )
                return _rgb_to_hex(mixed)
        return stops[-1][1]

    def get_affection(char_id):
        """指定ヒロインの現在の好感度を取得（-100 〜 100）"""
        if char_id not in store.affection:
            return 0
        return max(-100, min(100, store.affection[char_id]))

    def unlock_affection(char_id):
        """
        指定ヒロインの好感度バーを解禁（表示開始）し、現在の表示対象にする。
        例: $ unlock_affection("k") / $ unlock_affection("m")
        """
        if char_id not in store.affection:
            store.affection[char_id] = 0
        store.unlocked_heroines[char_id] = True
        store.active_heroine = char_id
        store.show_affection_bar = True
        renpy.restart_interaction()

    def lock_affection(char_id):
        """指定ヒロインの好感度バーを非表示（未解禁状態）に戻す"""
        store.unlocked_heroines[char_id] = False
        if store.active_heroine == char_id:
            store.active_heroine = None
            for cid, is_open in store.unlocked_heroines.items():
                if is_open:
                    store.active_heroine = cid
                    break
        renpy.restart_interaction()

    def add_affection(char_id, delta):
        """好感度を増減させ、対象ヒロインを解禁＆アクティブにする"""
        if char_id not in store.affection:
            store.affection[char_id] = 0
        store.unlocked_heroines[char_id] = True
        store.affection[char_id] = max(-100, min(100, store.affection[char_id] + delta))
        store.active_heroine = char_id
        renpy.restart_interaction()

    def set_affection(char_id, value):
        """好感度を直接設定し、対象ヒロインを解禁＆アクティブにする"""
        store.unlocked_heroines[char_id] = True
        store.affection[char_id] = max(-100, min(100, value))
        store.active_heroine = char_id
        renpy.restart_interaction()

    def set_affection_target(char_id):
        """好感度バーに表示する対象ヒロインを切り替える（解禁も同時に行う）"""
        store.unlocked_heroines[char_id] = True
        store.active_heroine = char_id
        renpy.restart_interaction()

    def get_character_name_color(who):
        """
        発話者名 who が好感度対象ヒロインであれば、好感度に応じた文字色を返す。
        対象外であれば None を返す（元のCharacter設定色を使用）。
        """
        if who is None:
            return None
        char_id = HEROINE_NAME_TO_ID.get(str(who))
        if not char_id:
            return None
        val = get_affection(char_id)
        stops = HEROINE_COLOR_STOPS.get(char_id, HEROINE_COLOR_STOPS["k"])
        return _interpolate_color(stops, val)

    def affection_speaker_callback(event, interact=True, cb_char_id=None, **kwargs):
        """
        すでに好感度バーが解禁されているヒロインが発話した際、自動的にバーの対象をそのヒロインに切り替える
        """
        if event == "begin" and cb_char_id:
            if store.unlocked_heroines.get(cb_char_id, False):
                store.active_heroine = cb_char_id

    def get_affection_bar_visuals(who=None):
        """
        現在の好感度バーの表示に必要な情報を辞書で返す。
        まだ誰も解禁されていない場合は None を返す（バー非表示）。
        """
        char_id = None
        if who is not None:
            cand = HEROINE_NAME_TO_ID.get(str(who))
            if cand and store.unlocked_heroines.get(cand, False):
                char_id = cand

        if not char_id:
            if store.active_heroine and store.unlocked_heroines.get(store.active_heroine, False):
                char_id = store.active_heroine
            else:
                # まだ対象ヒロインが解禁されていない場合は None を返してバーを隠す
                return None

        val = get_affection(char_id)
        stops = HEROINE_COLOR_STOPS.get(char_id, HEROINE_COLOR_STOPS["k"])
        name_color = _interpolate_color(stops, val)
        display_name = HEROINE_ID_TO_NAME.get(char_id, "鎌倉詩乃")

        # 値に応じてバーの表現（背景プレート・ゲージ色・枠のツタ/花/ひび割れ装飾）を切り替え
        if val >= 70:
            stage = "vine_lv3"
        elif val >= 35:
            stage = "vine_lv2"
        elif val > 0:
            stage = "vine_lv1"
        elif val == 0:
            stage = "neutral"
        elif val > -35:
            stage = "crack_lv1"
        elif val > -70:
            stage = "crack_lv2"
        else:
            stage = "crack_lv3"

        return {
            "char_id": char_id,
            "name": display_name,
            "name_color": name_color,
            "bar_value": val + 100,  # -100〜+100 を 0〜200 のゲージ範囲に変換（初期値0＝50%）
            "plate_img": "gui/affection_bar/plate_{}.png".format(stage),
            "fill_img": "gui/affection_bar/fill_{}.png".format(stage),
            "overlay_img": "gui/affection_bar/overlay_{}.png".format(stage),
        }

    config.overlay_screens.append("affection_debug_overlay")


## script.rpy の Character 定義が読み込まれた後に、対象ヒロインの自動ターゲット追従を紐付けます
init 10 python:
    def _bind_heroine_character(char_obj, char_id):
        if char_obj is None:
            return
        if hasattr(char_obj, "cb_args"):
            char_obj.cb_args["cb_char_id"] = char_id
        char_obj.callback = affection_speaker_callback

    _bind_heroine_character(getattr(store, "k", None), "k")
    _bind_heroine_character(getattr(store, "m", None), "m")


## 画面左上に配置する「数値を見せない好感度バー」ウィジェット
## $ unlock_affection("k") 等で解禁されるまでは非表示になります。
screen affection_bar_widget(who=None):
    if show_affection_bar:
        $ _vis = get_affection_bar_visuals(who)

        if _vis is not None:
            fixed:
                xpos 28
                ypos 20
                xsize 420
                ysize 96

                # 1. 状態に応じた背景プレート
                add _vis["plate_img"]

                # 2. 対象ヒロイン名（数値は一切出さず、文字色の変化で温度感を表現）
                text _vis["name"]:
                    xalign 0.5
                    ypos 17
                    size 22
                    font gui.name_text_font
                    color _vis["name_color"]
                    outlines [(2, "#0b101acc", 0, 0)]

                # 3. 好感度ゲージ本体（AnimatedValueにより増減時に滑らかに伸縮）
                bar:
                    xpos 60
                    ypos 52
                    xsize 300
                    ysize 18
                    value AnimatedValue(value=_vis["bar_value"], range=200, delay=0.45)
                    left_bar _vis["fill_img"]
                    right_bar "gui/affection_bar/bar_track.png"
                    thumb None
                    thumb_offset 0

                # 4. ゲージ枠に絡まるツタ・花 ／ ひび割れの装飾オーバーレイ
                add _vis["overlay_img"]


## [F8]キーで開発用確認パネルを開閉できるオーバーレイ（通常時は非表示）
screen affection_debug_overlay():
    zorder 200
    key "K_F8" action ToggleVariable("show_affection_debug")

    if show_affection_debug:
        frame:
            xalign 0.98
            yalign 0.03
            padding (18, 14)
            background "#101622d8"
            vbox:
                spacing 8
                text "【開発用】好感度バー動作テスト (F8で閉じる)" size 20 color "#a8c5ff"
                $ _target_id = active_heroine or "k"
                $ _target_name = "鎌倉詩乃 (k)" if _target_id == "k" else "真鶴千景 (m)"
                $ _cur_val = get_affection(_target_id)
                $ _cur_col = get_character_name_color("鎌倉詩乃" if _target_id == "k" else "真鶴千景")
                $ _is_unlocked = unlocked_heroines.get(_target_id, False)
                text "対象: [_target_name] (解禁:[_is_unlocked]) / 内部値: [_cur_val] / 名前色: {color=[_cur_col]}[_cur_col]{/color}" size 18 color "#ffffff"

                hbox:
                    spacing 10
                    textbutton "詩乃を解禁・表示" action Function(unlock_affection, "k") text_size 18
                    textbutton "千景を解禁・表示" action Function(unlock_affection, "m") text_size 18
                    textbutton "バー非表示" action Function(lock_affection, _target_id) text_size 18

                hbox:
                    spacing 8
                    textbutton "ひびLv3(-85)" action Function(set_affection, _target_id, -85) text_size 16
                    textbutton "ひびLv2(-50)" action Function(set_affection, _target_id, -50) text_size 16
                    textbutton "ひびLv1(-20)" action Function(set_affection, _target_id, -20) text_size 16
                    textbutton "初期(0)" action Function(set_affection, _target_id, 0) text_size 16
                    textbutton "ツタLv1(+20)" action Function(set_affection, _target_id, 20) text_size 16
                    textbutton "ツタLv2(+50)" action Function(set_affection, _target_id, 50) text_size 16
                    textbutton "満開Lv3(+85)" action Function(set_affection, _target_id, 85) text_size 16

                hbox:
                    spacing 10
                    textbutton "-10" action Function(add_affection, _target_id, -10) text_size 18
                    textbutton "-5" action Function(add_affection, _target_id, -5) text_size 18
                    textbutton "+5" action Function(add_affection, _target_id, 5) text_size 18
                    textbutton "+10" action Function(add_affection, _target_id, 10) text_size 18
