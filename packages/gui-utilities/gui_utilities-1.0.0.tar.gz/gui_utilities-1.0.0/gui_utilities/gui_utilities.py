from PyQt6.QtCore import Qt, QObject, QEvent, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QDialog, QToolButton, QWidgetAction
from PyQt6.QtGui import QIcon
import re
import requests
import importlib.resources

main_dir = importlib.resources.files("gui_utilities")
icons_dir = main_dir / "icons"
tlds_path = main_dir / "tlds"

def create_window(title, background_color = "#1e1e1e"):
    window = QWidget()
    window.setObjectName("window")
    window.setWindowTitle(title)
    window.setStyleSheet(f"#window {{background-color: {background_color};}}")
    main_layout = QVBoxLayout(window)
    window.setLayout(main_layout)
    return window

def create_label(
        message,
        font_family = "Segoe UI",
        font_size = 14,
        font_color = "#ffffff",
        font_weight = "normal",
        background_color = "#1e1e1e",
        padding = 15,
        border_width = 0,
        border_color = "#ffffff",
        border_radius = 0
):
    label = QLabel(message)
    style = f"""
        font-family: {font_family};
        font-size: {font_size}px;
        color: {font_color};
        font-weight: {font_weight};
        background-color: {background_color};
        padding: {padding}px;
        border: {border_width}px solid {border_color};
        border-radius: {border_radius}px;
    """
    label.setStyleSheet(style)
    return label

def create_button(
    message,
    font_family = "Segoe UI",
    font_size = 14,
    font_color = "#ffffff",
    font_weight = "bold",
    background_color = "#1e1e1e",
    padding = 15,
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    hover_background_color = "#333333",
    hover_border_width = 3,
    hover_border_color = "#777777",
    pressed_background_color = "#4a4a4a",
    pressed_border_width = 3,
    pressed_border_color = "#0078d7",
    disabled_font_color = "#888888",
    disabled_background_color = "#2d2d2d",
    disabled_border_width = 2,
    disabled_border_color = "#4a4a4a"
):
    button = QPushButton(message)
    style_sheet = f"""
        QPushButton {{
            font-family: {font_family};
            font-size: {font_size}px;
            color: {font_color};
            font-weight: {font_weight};
            background-color: {background_color};
            padding: {padding}px;
            border: {border_width}px solid {border_color};
            border-radius: {border_radius}px;
        }}
        QPushButton:hover {{
            background-color: {hover_background_color};
            border: {hover_border_width}px solid {hover_border_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_background_color};
            border: {pressed_border_width}px solid {pressed_border_color};
        }}
        QPushButton:disabled {{
            color: {disabled_font_color};
            background-color: {disabled_background_color};
            border: {disabled_border_width}px solid {disabled_border_color};
        }}
    """
    button.setStyleSheet(style_sheet)
    return button

def create_text_box(
    placeholder_text,
    font_family = "Segoe UI",
    font_size = 14,
    font_color = "#ffffff",
    font_weight = "normal",
    background_color = "#1e1e1e",
    padding = 15,
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    hover_background_color = "#333333",
    hover_border_width = 3,
    hover_border_color = "#777777",
    focus_font_color = "#000000",
    focus_background_color = "#ffffff",
    focus_border_width = 3,
    focus_border_color = "#0078d7",
    disabled_background_color = "#2d2d2d",
    disabled_border_width = 2,
    disabled_border_color = "#4a4a4a",
    hide_text = False
):
    text_box = QLineEdit()
    text_box.setPlaceholderText(placeholder_text)
    style_sheet = f"""
        QLineEdit {{
            font-family: {font_family};
            font-size: {font_size}px;
            color: {font_color};
            font-weight: {font_weight};
            background-color: {background_color};
            padding: {padding}px;
            border: {border_width}px solid {border_color};
            border-radius: {border_radius}px;
        }}
        QLineEdit:hover {{
            background-color: {hover_background_color};
            border: {hover_border_width}px solid {hover_border_color};
        }}
        QLineEdit:focus {{
            color: {focus_font_color};
            background-color: {focus_background_color};
            border: {focus_border_width}px solid {focus_border_color};
        }}
        QLineEdit:disabled {{
            background-color: {disabled_background_color};
            border: {disabled_border_width}px solid {disabled_border_color};
        }}
    """
    text_box.setStyleSheet(style_sheet)
    if hide_text:
        show_text_icon = QIcon(str(icons_dir / "show_text_icon.png"))
        hide_text_icon = QIcon(str(icons_dir / "hide_text_icon.png"))
        focused_show_text_icon = QIcon(str(icons_dir / "focused_show_text_icon.png"))
        focused_hide_text_icon = QIcon(str(icons_dir / "focused_hide_text_icon.png"))
        text_box.setEchoMode(QLineEdit.EchoMode.Password)
        toggle_text_visibility_button = QToolButton(text_box)
        toggle_text_visibility_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_text_visibility_button.setAutoRaise(True)
        toggle_text_visibility_button.setIcon(hide_text_icon)
        toggle_text_visibility_button.setIconSize(QSize(25, 25))
        toggle_text_visibility_action = QWidgetAction(text_box)
        toggle_text_visibility_action.setDefaultWidget(toggle_text_visibility_button)
        style_sheet = f"""
            QToolButton {{
                border: none;
                margin-right: 10px;
            }}
            QToolButton:hover, QToolButton:pressed {{
                background-color: transparent;
                border: none;
            }}
        """
        toggle_text_visibility_button.setStyleSheet(style_sheet)
        text_box.addAction(toggle_text_visibility_action, QLineEdit.ActionPosition.TrailingPosition)

        def update_icon():
            is_password = text_box.echoMode() == QLineEdit.EchoMode.Password
            if text_box.hasFocus(): icon = focused_hide_text_icon if is_password else focused_show_text_icon
            else: icon = hide_text_icon if is_password else show_text_icon
            toggle_text_visibility_button.setIcon(icon)

        def toggle_visibility():
            if text_box.echoMode() == QLineEdit.EchoMode.Password: text_box.setEchoMode(QLineEdit.EchoMode.Normal)
            else: text_box.setEchoMode(QLineEdit.EchoMode.Password)
            update_icon()

        toggle_text_visibility_button.clicked.connect(toggle_visibility)

        class FocusWatcher(QObject):
            def eventFilter(self, watched, event):
                if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut): update_icon()
                return super().eventFilter(watched, event)

        focus_watcher = FocusWatcher(text_box)
        text_box.installEventFilter(focus_watcher)
        setattr(text_box, "focus_watcher", focus_watcher)
        update_icon()
    return text_box

def create_combo_box(
    placeholder_text,
    items,
    font_family = "Segoe UI",
    font_size = 14,
    placeholder_font_color = "#888888",
    font_color = "#ffffff",
    background_color = "#1e1e1e",
    padding = 15,
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    hover_background_color = "#333333",
    hover_border_width = 3,
    hover_border_color = "#777777",
    on_font_color = "#000000",
    on_background_color = "#ffffff",
    on_border_width = 3,
    on_border_color = "#0078d7",
    dropdown_font_color = "#ffffff",
    dropdown_background_color = "#1e1e1e",
    dropdown_selection_background_color = "#0078d7",
    dropdown_border_width = 1,
    dropdown_border_color = "#5c5c5c"
):
    combo_box = QComboBox()
    combo_box.setPlaceholderText(f"{placeholder_text}")
    combo_box.addItems(items)
    combo_box.setCurrentIndex(-1)
    
    def get_stylesheet(font_color):
        return f"""
            QComboBox {{
                font-family: {font_family};
                font-size: {font_size}px;
                color: {font_color};
                background-color: {background_color};
                padding: {padding}px;
                border: {border_width}px solid {border_color};
                border-radius: {border_radius}px;
            }}
            QComboBox:hover {{
                background-color: {hover_background_color};
                border: {hover_border_width}px solid {hover_border_color};
            }}
            QComboBox:on {{
                color: {on_font_color};
                background-color: {on_background_color};
                border: {on_border_width}px solid {on_border_color};
            }}
            QComboBox QAbstractItemView {{
                color: {dropdown_font_color};
                background-color: {dropdown_background_color};
                selection-background-color: {dropdown_selection_background_color};
                border: {dropdown_border_width}px solid {dropdown_border_color};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """

    def change_color(index):
        if index == -1: combo_box.setStyleSheet(get_stylesheet(placeholder_font_color))
        else: combo_box.setStyleSheet(get_stylesheet(font_color))
    
    combo_box.currentIndexChanged.connect(change_color)
    change_color(-1)
    return combo_box

def create_information_message_box(
    message,
    top_margin = 25,
    bottom_margin = 25,
    left_margin = 25,
    right_margin = 25,
    spacing = 10,
    background_color = "#1e1e1e",
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    label_font_family = "Segoe UI",
    label_font_size = 14,
    label_font_color = "#ffffff",
    label_padding = 15,
    label_border_width = 0,
    label_border_color = "#ffffff",
    label_border_radius = 0,
    button_message = "Aceptar",
    button_font_family = "Segoe UI",
    button_font_size = 14,
    button_font_color = "#ffffff",
    button_background_color = "#1e1e1e",
    button_padding = 15,
    button_border_width = 2,
    button_border_color = "#5c5c5c",
    button_border_radius = 0,
    button_hover_background_color = "#333333",
    button_hover_border_width = 3,
    button_hover_border_color = "#777777",
    button_pressed_background_color = "#4a4a4a",
    button_pressed_border_width = 3,
    button_pressed_border_color = "#0078d7",
    button_disabled_font_color = "#888888",
    button_disabled_background_color = "#2d2d2d",
    button_disabled_border_width = 2,
    button_disabled_border_color = "#4a4a4a"
):
    message_box = QDialog()
    message_box.setObjectName("message_box")
    message_box.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    message_box.setMaximumWidth(480)
    style_sheet = f"""
        QDialog#message_box {{
            background-color: {background_color};
            border: {border_width}px solid {border_color};
            border-radius: {border_radius}px;
        }}
    """
    message_box.setStyleSheet(style_sheet)
    main_layout = QVBoxLayout(message_box)
    message_box.setLayout(main_layout)
    main_layout.setContentsMargins(left_margin, top_margin, right_margin, bottom_margin)
    main_layout.setSpacing(spacing)
    message_label = create_label(
        message = message,
        font_family = label_font_family,
        font_size = label_font_size,
        font_color=  label_font_color,
        background_color = "transparent",
        padding = label_padding,
        border_width = label_border_width,
        border_color = label_border_color,
        border_radius = label_border_radius
    )
    main_layout.addWidget(message_label)

    accept_button = create_button(
        message = button_message,
        font_family = button_font_family,
        font_size = button_font_size,
        font_color = button_font_color,
        background_color = button_background_color,
        padding = button_padding,
        border_width = button_border_width,
        border_color = button_border_color,
        border_radius = button_border_radius,
        hover_background_color = button_hover_background_color,
        hover_border_width = button_hover_border_width,
        hover_border_color = button_hover_border_color,
        pressed_background_color = button_pressed_background_color,
        pressed_border_width = button_pressed_border_width,
        pressed_border_color = button_pressed_border_color,
        disabled_font_color = button_disabled_font_color,
        disabled_background_color = button_disabled_background_color,
        disabled_border_width = button_disabled_border_width,
        disabled_border_color = button_disabled_border_color
    )
    main_layout.addWidget(accept_button)
    accept_button.clicked.connect(message_box.accept)
    return message_box
    
def create_confirmation_message_box(
    message,
    top_margin = 25,
    bottom_margin = 25,
    left_margin = 25,
    right_margin = 25,
    main_spacing = 10,
    button_spacing = 10,
    background_color = "#1e1e1e",
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    label_font_family = "Segoe UI",
    label_font_size = 14,
    label_font_color = "#ffffff",
    label_padding = 15,
    label_border_width = 0,
    label_border_color = "#ffffff",
    label_border_radius = 0,
    button_font_family = "Segoe UI",
    button_font_size = 14,
    button_font_color = "#ffffff",
    button_background_color = "#1e1e1e",
    button_padding = 15,
    button_border_width = 2,
    button_border_color = "#5c5c5c",
    button_border_radius = 0,
    button_hover_background_color = "#333333",
    button_hover_border_width = 3,
    button_hover_border_color = "#777777",
    button_pressed_background_color = "#4a4a4a",
    button_pressed_border_width = 3,
    button_pressed_border_color = "#0078d7",
    button_disabled_font_color = "#888888",
    button_disabled_background_color = "#2d2d2d",
    button_disabled_border_width = 2,
    button_disabled_border_color = "#4a4a4a"
):
    confirm_message_box = QDialog()
    confirm_message_box.setObjectName("confirm_message_box")
    confirm_message_box.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    confirm_message_box.setMaximumWidth(480)
    style_sheet = f"""
        QDialog#confirm_message_box {{
            background-color: {background_color};
            border: {border_width}px solid {border_color};
            border-radius: {border_radius}px;
        }}
    """
    confirm_message_box.setStyleSheet(style_sheet)
    main_layout = QVBoxLayout(confirm_message_box)
    confirm_message_box.setLayout(main_layout)
    main_layout.setContentsMargins(left_margin, top_margin, right_margin, bottom_margin)
    main_layout.setSpacing(main_spacing)
    message_layout = QHBoxLayout()
    main_layout.addLayout(message_layout)
    message_label = create_label(
        message = message,
        font_family = label_font_family,
        font_size = label_font_size,
        font_color = label_font_color,
        background_color = "transparent",
        padding = label_padding,
        border_width = label_border_width,
        border_color = label_border_color,
        border_radius = label_border_radius
    )
    message_layout.addWidget(message_label)
    buttons_layout = QHBoxLayout()
    main_layout.addLayout(buttons_layout)
    buttons_layout.setSpacing(button_spacing)
    confirm_button = create_button(
        message = "Sí",
        font_family = button_font_family,
        font_size = button_font_size,
        font_color = button_font_color,
        background_color = button_background_color,
        padding = button_padding,
        border_width = button_border_width,
        border_color = button_border_color,
        border_radius = button_border_radius,
        hover_background_color = button_hover_background_color,
        hover_border_width = button_hover_border_width,
        hover_border_color = button_hover_border_color,
        pressed_background_color = button_pressed_background_color,
        pressed_border_width = button_pressed_border_width,
        pressed_border_color = button_pressed_border_color,
        disabled_font_color = button_disabled_font_color,
        disabled_background_color = button_disabled_background_color,
        disabled_border_width = button_disabled_border_width,
        disabled_border_color = button_disabled_border_color
    )
    buttons_layout.addWidget(confirm_button)
    confirm_button.clicked.connect(confirm_message_box.accept)
    decline_button = create_button(
        message = "No",
        font_family = button_font_family,
        font_size = button_font_size,
        font_color = button_font_color,
        background_color = button_background_color,
        padding = button_padding,
        border_width = button_border_width,
        border_color = button_border_color,
        border_radius = button_border_radius,
        hover_background_color = button_hover_background_color,
        hover_border_width = button_hover_border_width,
        hover_border_color = button_hover_border_color,
        pressed_background_color = button_pressed_background_color,
        pressed_border_width = button_pressed_border_width,
        pressed_border_color = button_pressed_border_color,
        disabled_font_color = button_disabled_font_color,
        disabled_background_color = button_disabled_background_color,
        disabled_border_width = button_disabled_border_width,
        disabled_border_color = button_disabled_border_color
    )
    buttons_layout.addWidget(decline_button)
    decline_button.clicked.connect(confirm_message_box.reject)
    return confirm_message_box

def confirm_exit(
    window,
    background_color = "#1e1e1e",
    border_width = 2,
    border_color = "#5c5c5c",
    border_radius = 0,
    label_font_family = "Segoe UI",
    label_font_size = 14,
    label_font_color = "#ffffff",
    label_padding = 15,
    label_border_width = 0,
    label_border_color = "#ffffff",
    label_border_radius = 0,
    button_font_family = "Segoe UI",
    button_font_size = 14,
    button_font_color = "#ffffff",
    button_background_color = "#1e1e1e",
    button_padding = 15,
    button_border_width = 2,
    button_border_color = "#5c5c5c",
    button_border_radius = 0,
    button_hover_background_color = "#333333",
    button_hover_border_width = 3,
    button_hover_border_color = "#777777",
    button_pressed_background_color = "#4a4a4a",
    button_pressed_border_width = 3,
    button_pressed_border_color = "#0078d7",
    button_disabled_font_color = "#888888",
    button_disabled_background_color = "#2d2d2d",
    button_disabled_border_width = 2,
    button_disabled_border_color = "#4a4a4a"
):
    confirmation_message_box = create_confirmation_message_box(
        message = "¿Está seguro de querer salir del programa?",
        background_color = background_color,
        border_width = border_width,
        border_color = border_color,
        border_radius = border_radius,
        label_font_family = label_font_family,
        label_font_size = label_font_size,
        label_font_color = label_font_color,
        label_padding = label_padding,
        label_border_width = label_border_width,
        label_border_color = label_border_color,
        label_border_radius = label_border_radius,
        button_font_family = button_font_family,
        button_font_size = button_font_size,
        button_font_color = button_font_color,
        button_background_color = button_background_color,
        button_padding = button_padding,
        button_border_width = button_border_width,
        button_border_color = button_border_color,
        button_border_radius = button_border_radius,
        button_hover_background_color = button_hover_background_color,
        button_hover_border_width = button_hover_border_width,
        button_hover_border_color = button_hover_border_color,
        button_pressed_background_color = button_pressed_background_color,
        button_pressed_border_width = button_pressed_border_width,
        button_pressed_border_color = button_pressed_border_color,
        button_disabled_font_color = button_disabled_font_color,
        button_disabled_background_color = button_disabled_background_color,
        button_disabled_border_width = button_disabled_border_width,
        button_disabled_border_color = button_disabled_border_color
    )
    result = confirmation_message_box.exec()
    if result == QDialog.DialogCode.Accepted: window.close()

def switch_instance(gui_instance, menu_function):
    new_widget = QWidget()
    new_layout = menu_function()
    new_widget.setLayout(new_layout)
    if gui_instance.central_widget is not None:
        gui_instance.window.layout().replaceWidget(gui_instance.central_widget, new_widget)
        gui_instance.central_widget.deleteLater()
    else: gui_instance.window.layout().addWidget(new_widget)
    gui_instance.central_widget = new_widget

def get_responsive_width(window, fraction = 3.0):
    screen_width = window.screen().size().width()
    return round(screen_width / fraction)

def validate_string(string, suffix = "El", field = "campo"):
    if string and string.strip(): return None
    return f"{suffix} {field} no puede dejarse {"vacío" if suffix == "El" else "vacía"}."

def validate_integer(integer, suffix = "El", field = "campo"):
    if not integer or not integer.strip(): return f"{suffix} {field} no puede dejarse {"vacío" if suffix == "El" else "vacía"}."
    pattern = re.compile(r"^\d+$")
    unformatted_integer = integer.replace(".", "")
    if pattern.match(unformatted_integer): return None
    return f"No ha ingresado {"un" if suffix == "El" else "una"} {field} {"válido" if suffix == "El" else "válida"}."

def validate_id(id_str):
    if not id_str or not id_str.strip(): return "El D.N.I. no puede dejarse vacio."
    pattern = re.compile(r"^(?:\d{8}|(?:\d{1,2}\.\d{3}\.\d{3}))$")
    if pattern.match(id_str): return None
    return "No ha ingresado un D.N.I. válido."

def validate_cellphone_number(cellphone_number):
    if not cellphone_number or not cellphone_number.strip(): return "El número telefónico no puede dejarse vacío."
    clean_number = "".join(filter(str.isdigit, cellphone_number))
    if len(clean_number) == 10: return None
    return "No ha ingresado un número telefónico válido."

tlds_list_path = main_dir / tlds_path / "tlds_list.txt"

def export_tlds(tlds_list):
    try:
        with open(tlds_list_path, "w", encoding = "utf-8") as saved_tlds: saved_tlds.write("\n".join(tlds_list))
    except IOError: pass

def import_tlds():
    try:
        with open(tlds_list_path, "r", encoding = "utf-8") as saved_tlds: return [tld.strip() for tld in saved_tlds]
    except FileNotFoundError: return []

def get_tlds():
    url = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
    try:
        response = requests.get(url, timeout = 10)
        response.raise_for_status()
        tlds_list = [tld.lower() for tld in response.text.splitlines()[1:] if tld]
        if tlds_list: export_tlds(tlds_list)
        return tlds_list
    except requests.exceptions.RequestException: return import_tlds()

def build_email_pattern(tlds_list):
    if not tlds_list:
        return re.compile(
            r"^(?P<local>[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+" 
            r"(?:\[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)@" 
            r"(?P<dominio>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
            r"[a-zA-Z]{2,63})$",
            re.IGNORECASE
        )
    tld_pattern = "|".join(re.escape(tld) for tld in sorted(tlds_list, key = len, reverse = True))
    return re.compile(
        r"^(?P<local>[a-zA-Z0-9!#$%&'+/=?^_{|}~-]+"
        r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)@"
        r"(?P<dominio>(?:[a-zA-Z0-9-]+\.)+"
        r"(?:" + tld_pattern + r"))$", re.IGNORECASE
    )

email_pattern = build_email_pattern(get_tlds())

def validate_email(email):
    if not email or not email.strip(): return "El correo electrónico no puede dejarse vacío."
    if email_pattern.match(email): return None
    return "No ha ingresado un correo electrónico válido."

def decimal_format(number):
    if isinstance(number, float) and number.is_integer(): number = int(number)
    return f"{number:,}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_id(id_string):
    clean_id = id_string.replace(".", "")
    if len(clean_id) == 8: return f"{clean_id[0:2]}.{clean_id[2:5]}.{clean_id[5:8]}"
    elif len(clean_id) == 7: return f"{clean_id[0:1]}.{clean_id[1:4]}.{clean_id[4:7]}"
    return id_string

def cellphone_number_format(cellphone_number):
    clean_number = "".join(filter(str.isdigit, cellphone_number))
    if len(clean_number) == 10: return f"{clean_number[0:4]} - {clean_number[4:10]}"
    return cellphone_number