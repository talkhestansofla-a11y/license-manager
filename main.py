from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp
import hashlib
import os
import jdatetime
import arabic_reshaper
from bidi.algorithm import get_display
import json
from datetime import datetime
import sys
import logging
import traceback
import functools

# ==================== تنظیمات لاگ‌گیری ====================
def setup_logging():
    """تنظیمات اولیه برای سیستم لاگ‌گیری"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"license_manager_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# ایجاد لاگر اصلی
logger = setup_logging()

# ==================== تابع برای لاگ کردن استثناها ====================
def log_exception(exc_type, exc_value, exc_traceback):
    """تابع برای لاگ کردن تمام استثناهای سیستمی"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# تنظیم تابع هندلر برای استثناها
sys.excepthook = log_exception

# ==================== دکوراتور ساده‌شده برای لاگ کردن توابع ====================
def log_function_call(func):
    """دکوراتور ساده‌شده برای لاگ کردن فراخوانی توابع"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            class_name = args[0].__class__.__name__ if args else ''
            logger.debug(f"Calling {class_name}.{func.__name__}")
            result = func(*args, **kwargs)
            logger.debug(f"Function {class_name}.{func.__name__} completed")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

# تنظیمات اولیه پنجره - کوچک کردن ابعاد
MAX_WIDTH = dp(450)
Window.size = (MAX_WIDTH, dp(600))
Window.minimum_width = max(MAX_WIDTH, 1)
Window.minimum_height = max(dp(450), 1)

# تنظیم آیکون برنامه - بهبود بخشیده شده
try:
    # اول PNG را امتحان کن
    icon_path_png = os.path.join(os.path.dirname(__file__), "app-icon.png")
    icon_path_ico = os.path.join(os.path.dirname(__file__), "app-icon.ico")
    
    if os.path.exists(icon_path_png):
        Window.set_icon(icon_path_png)
        logger.info("Application PNG icon set successfully")
    elif os.path.exists(icon_path_ico):
        Window.set_icon(icon_path_ico)
        logger.info("Application ICO icon set successfully")
    else:
        logger.warning("Application icon file not found (app-icon.png or app-icon.ico)")
except Exception as e:
    logger.error(f"Error setting application icon: {e}")

# Register Persian font
try:
    font_path = os.path.join(os.path.dirname(__file__), "Vazir.ttf")
    if os.path.exists(font_path):
        LabelBase.register(name="PersianFont", fn_regular=font_path)
        logger.info("Persian font registered successfully")
    else:
        LabelBase.register(name="PersianFont", fn_regular="Arial")
        logger.warning("Persian font file not found, using Arial as fallback")
except Exception as e:
    logger.error(f"Error registering Persian font: {e}")
    LabelBase.register(name="PersianFont", fn_regular="Arial")

def reshape_bidi(text):
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception as e:
        logger.error(f"Error in reshape_bidi: {e}")
        return text

class PersianLabel(Label):
    """Label امن برای نمایش فارسی (شکل‌دهی و راست‌چین) بدون حلقه بازگشتی."""
    
    def __init__(self, **kwargs):
        logger.debug("Creating PersianLabel")
        raw_text = kwargs.get("text", "")
        kwargs.setdefault("font_name", "PersianFont")
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("color", (0.1, 0.1, 0.1, 1))
        super().__init__(**kwargs)
        self._updating = False
        self._raw_text = raw_text
        self.bind(size=self._update_text_size, text=self._on_text_changed)
        self._update_text_size()
        self._set_reshaped_text(self._raw_text or super().text)

    def _update_text_size(self, *a):
        try:
            self.text_size = (self.width, None)
        except Exception as e:
            logger.error(f"Error updating text size: {e}")

    def _set_reshaped_text(self, raw):
        try:
            reshaped = reshape_bidi(raw)
            self._updating = True
            super(Label, self).__setattr__("text", reshaped)
            self._updating = False
        except Exception as e:
            logger.error(f"Error setting reshaped text: {e}")

    def _on_text_changed(self, instance, value):
        if self._updating:
            return
        self._raw_text = value
        self._set_reshaped_text(value)

class PersianButton(Button):
    """Button با پشتیبانی از متن فارسی"""
    
    def __init__(self, **kwargs):
        logger.debug("Creating PersianButton")
        raw_text = kwargs.get("text", "")
        kwargs.setdefault("font_name", "PersianFont")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(30))
        kwargs.setdefault("color", (1, 1, 1, 1))
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("valign", "middle")
        kwargs.setdefault("background_color", (0.8, 0.8, 0.8, 1))
        super().__init__(**kwargs)
        self._updating = False
        self._raw_text = raw_text
        self.bind(size=self._update_text_size, text=self._on_text_changed)
        self._update_text_size()
        self._set_reshaped_text(self._raw_text or super().text)

    def _update_text_size(self, *a):
        try:
            pad = 0
            if isinstance(self.padding, (list, tuple)) and len(self.padding) >= 2:
                if len(self.padding) >= 4:
                    pad = self.padding[0] + self.padding[2]
                else:
                    pad = self.padding[0] * 2
            elif isinstance(self.padding, (int, float)):
                pad = self.padding * 2
            width_for_text = max(self.width - pad, 10)
            self.text_size = (width_for_text, None)
            self.shorten = False
        except Exception as e:
            logger.error(f"Error updating button text size: {e}")

    def _set_reshaped_text(self, raw):
        try:
            reshaped = reshape_bidi(raw)
            self._updating = True
            super(Button, self).__setattr__("text", reshaped)
            self._updating = False
        except Exception as e:
            logger.error(f"Error setting reshaped button text: {e}")

    def _on_text_changed(self, instance, value):
        if self._updating:
            return
        self._raw_text = value
        self._set_reshaped_text(value)

class PersianTextInput(TextInput):
    """TextInput برای ورود فارسی"""
    
    def __init__(self, **kwargs):
        logger.debug("Creating PersianTextInput")
        hint = kwargs.get("hint_text", "")
        kwargs.setdefault("font_name", "PersianFont")
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("write_tab", False)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(30))
        kwargs.setdefault("padding", [dp(6), dp(4)])
        kwargs.setdefault("foreground_color", (0.1, 0.1, 0.1, 1))
        kwargs.setdefault("background_color", (0.9, 0.9, 0.9, 1))
        super().__init__(**kwargs)
        self._updating = False
        if hint:
            try:
                super(TextInput, self).__setattr__("hint_text", reshape_bidi(hint))
            except Exception as e:
                logger.error(f"Error setting hint text: {e}")
        self.bind(text=self._on_text_changed)

    def _on_text_changed(self, instance, value):
        if self._updating:
            return
        try:
            cursor = self.cursor_index()
        except Exception as e:
            logger.error(f"Error getting cursor index: {e}")
            cursor = None
            
        sel = None
        try:
            sel = self.selection_text
        except Exception as e:
            logger.error(f"Error getting selection text: {e}")
            sel = None
            
        reshaped = reshape_bidi(value)
        if reshaped == value:
            return
            
        self._updating = True
        try:
            super(TextInput, self).__setattr__("text", reshaped)
            if cursor is not None:
                self.cursor = (cursor, 0)
            if sel:
                self.selection_text = sel
        except Exception as e:
            logger.error(f"Error updating text input: {e}")
        finally:
            self._updating = False

class LoginScreen(BoxLayout):
    
    def __init__(self, app_instance, **kwargs):
        logger.info("Initializing LoginScreen")
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(15)
        self.spacing = dp(10)
        self.size_hint = (None, None)
        self.width = MAX_WIDTH - dp(30)
        self.height = dp(200)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        self.app = app_instance
        self.password_file = "admin_pass.hash"

        title_label = PersianLabel(
            text="ورود به سیستم مدیریت لایسنس", 
            font_size=dp(16),
            size_hint_y=None,
            height=dp(25)
        )
        self.add_widget(title_label)

        self.password_input = PersianTextInput(
            password=True, 
            hint_text="رمز عبور را وارد کنید", 
            size_hint_y=None,
            height=dp(25),
            font_size=dp(13)
        )
        self.add_widget(self.password_input)

        login_btn = PersianButton(
            text="ورود به سیستم", 
            size_hint_y=None,
            height=dp(25),
            font_size=dp(14),
            background_color=(0.3, 0.5, 0.7, 1)
        )
        login_btn.bind(on_press=self.check_password)
        self.add_widget(login_btn)

        if not os.path.exists(self.password_file):
            self.setup_password()

    def setup_password(self):
        logger.info("Setting up default password")
        default_password = "admin123"
        try:
            with open(self.password_file, "w") as f:
                f.write(self.hash_password(default_password))
            logger.info("Default password setup completed")
        except Exception as e:
            logger.error(f"Error setting up default password: {e}")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, instance):
        logger.info("Password check initiated")
        password = self.password_input.text
        if not password:
            logger.warning("Empty password entered")
            self.show_popup("خطا", "رمز عبور را وارد کنید")
            return
        try:
            with open(self.password_file, "r") as f:
                stored = f.read().strip()
            if self.hash_password(password) == stored:
                logger.info("Login successful")
                self.app.show_main_screen()
            else:
                logger.warning("Invalid password attempt")
                self.show_popup("خطا", "رمز عبور نامعتبر است")
        except Exception as e:
            logger.error(f"Error during password check: {e}")
            self.show_popup("خطا", str(e))

    def show_popup(self, title, message):
        logger.debug(f"Showing popup: {title} - {message}")
        try:
            content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
            content.add_widget(PersianLabel(text=message, font_size=dp(13), size_hint_y=None, height=dp(35)))
            btn = PersianButton(text="تایید", size_hint=(1, None), height=dp(25))
            popup = Popup(
                title=reshape_bidi(title), 
                content=content, 
                size_hint=(0.7, 0.35),
                title_align='center'
            )
            btn.bind(on_press=popup.dismiss)
            content.add_widget(btn)
            popup.open()
        except Exception as e:
            logger.error(f"Error showing popup: {e}")

class CustomerItem(BoxLayout):
    
    def __init__(self, customer, remove_callback, **kwargs):
        logger.debug("Creating CustomerItem")
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(25)
        self.padding = [dp(4), dp(2)]
        self.spacing = dp(4)
        
        info_text = f"{customer['name']} | {customer['phone']} | {customer['hardware_id']} | {customer['access_code']} | {customer['created_date']}"
        
        info_label = PersianLabel(
            text=info_text,
            font_size=dp(10),
            halign="right",
            size_hint_x=0.85,
            text_size=(None, None),
            size_hint_y=1,
            valign="middle"
        )
        
        delete_btn = PersianButton(
            text="حذف",
            size_hint=(None, None),
            width=dp(45),
            height=dp(25),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        delete_btn.bind(on_press=lambda x: remove_callback(customer))
        
        self.add_widget(info_label)
        self.add_widget(delete_btn)

class MainScreen(BoxLayout):
    
    def __init__(self, **kwargs):
        logger.info("Initializing MainScreen")
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(20)
        self.spacing = dp(8)
        self.size_hint = (1, 1)
        self.width = MAX_WIDTH

        self.data_dir = "license_data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.customers_file = os.path.join(self.data_dir, "customers.json")

        self.customers = self.load_customers()
        
        title_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(35))
                
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                from kivy.uix.image import Image
                logo = Image(source=logo_path, size_hint=(None, None), size=(dp(150), dp(50)))
                title_layout.add_widget(logo)
                logger.info("Logo loaded successfully")
        except Exception as e:
            logger.error(f"Error loading logo: {e}")

        title_label = PersianLabel(
            text="سیستم مدیریت لایسنس انطباق 302", 
            font_size=dp(16),
            size_hint_x=1
        )
        title_layout.add_widget(title_label)
        self.add_widget(title_layout)

        form_layout = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None, height=dp(180))
        
        form_title = PersianLabel(
            text="تولید لایسنس جدید", 
            font_size=dp(15),
            size_hint_y=None,
            height=dp(25)
        )
        form_layout.add_widget(form_title)

        name_phone_layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(35))

        name_layout = BoxLayout(orientation="vertical", spacing=0, size_hint_x=0.5)
        name_label = PersianLabel(
            text="نام شرکت/مشتری:",
            size_hint_y=None,
            height=dp(18),
            font_size=dp(11)
        )
        self.buyer_name = PersianTextInput(
            hint_text="نام را وارد کنید",
            font_size=dp(13),
            size_hint_y=None,
            height=dp(25)
        )
        name_layout.add_widget(name_label)
        name_layout.add_widget(self.buyer_name)

        phone_layout = BoxLayout(orientation="vertical", spacing=0, size_hint_x=0.5)
        phone_label = PersianLabel(
            text="شماره تلفن:",
            size_hint_y=None,
            height=dp(18),
            font_size=dp(11)
        )
        self.phone = PersianTextInput(
            hint_text="تلفن را وارد کنید",
            font_size=dp(13),
            size_hint_y=None,
            height=dp(25)
        )
        phone_layout.add_widget(phone_label)
        phone_layout.add_widget(self.phone)

        name_phone_layout.add_widget(name_layout)
        name_phone_layout.add_widget(phone_layout)
        form_layout.add_widget(name_phone_layout)

        id_layout = BoxLayout(orientation="vertical", spacing=0, size_hint_y=None, height=dp(45))

        id_label = PersianLabel(
            text="شناسه سخت‌افزاری:",
            size_hint_y=None,
            height=dp(18),
            font_size=dp(11)
        )
        self.hardware_id = PersianTextInput(
            hint_text="16 کاراکتر",
            font_size=dp(13),
            size_hint_y=None,
            height=dp(25)
        )

        id_layout.add_widget(id_label)
        id_layout.add_widget(self.hardware_id)

        form_layout.add_widget(id_layout)

        button_layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(25))
        
        generate_btn = PersianButton(
            text="تولید لایسنس", 
            size_hint_x=0.5,
            background_color=(0, 0.4, 0, 1)
        )
        generate_btn.bind(on_press=self.generate_license)
        
        change_pass_btn = PersianButton(
            text="تغییر رمز", 
            size_hint_x=0.5,
            background_color=(0.4, 0.2, 0.6, 1)
        )
        change_pass_btn.bind(on_press=self.show_change_password_popup)
        
        button_layout.add_widget(generate_btn)
        button_layout.add_widget(change_pass_btn)
        form_layout.add_widget(button_layout)

        self.add_widget(form_layout)

        list_title = PersianLabel(
            text="لایسنس‌های تولید شده:", 
            font_size=dp(15),
            size_hint_y=None,
            height=dp(25)
        )
        self.add_widget(list_title)

        self.scroll_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.scroll_layout.bind(minimum_height=self.scroll_layout.setter("height"))
        
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.scroll_layout)
        self.add_widget(scroll)

        manage_buttons = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(35))
        
        export_btn = PersianButton(
            text="خروجی متنی",
            background_color=(0.4, 0.2, 0.6, 1)
        )
        export_btn.bind(on_press=self.export_customers)
        
        exit_btn = PersianButton(
            text="خروج از برنامه", 
            background_color=(0.6, 0, 0, 1)
        )
        exit_btn.bind(on_press=self.exit_app)
        
        manage_buttons.add_widget(export_btn)
        manage_buttons.add_widget(exit_btn)
        self.add_widget(manage_buttons)

        self.refresh_customers_list()

    def load_customers(self):
        """بارگذاری اطلاعات مشتریان"""
        logger.info("Loading customers data")
        if os.path.exists(self.customers_file):
            try:
                with open(self.customers_file, 'r', encoding='utf-8') as f:
                    customers = json.load(f)
                logger.info(f"Loaded {len(customers)} customers")
                return customers
            except Exception as e:
                logger.error(f"Error loading customers: {e}")
                return []
        logger.info("No customers file found, starting with empty list")
        return []

    def save_customers(self):
        """ذخیره اطلاعات مشتریان"""
        logger.info("Saving customers data")
        try:
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(self.customers, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully saved {len(self.customers)} customers")
            return True
        except Exception as e:
            logger.error(f"Error saving customers: {e}")
            self.show_popup("خطا", f"خطا در ذخیره اطلاعات: {e}")
            return False

    def generate_access_code(self, hardware_id):
        """تولید کد دسترسی بر اساس شناسه سخت‌افزاری"""
        logger.debug(f"Generating access code for hardware ID: {hardware_id}")
        try:
            salt = "SIEVE_ANALYSIS_APP_SECURE_SALT_2024"
            combined = hardware_id + salt
            
            hash1 = hashlib.sha512(combined.encode()).hexdigest()
            hash2 = hashlib.md5(hash1.encode()).hexdigest()
            hash3 = hashlib.sha256((hash2 + hardware_id).encode()).hexdigest()
            
            access_code = ""
            for i in range(0, len(hash3), 4):
                if len(access_code) >= 12:
                    break
                segment = hash3[i:i+4]
                access_code += segment.upper() + "-"
            
            access_code = access_code.rstrip("-")
            
            if len(access_code) < 8:
                alternative_code = hashlib.sha384((hardware_id + "BACKUP_SALT").encode()).hexdigest()[:12].upper()
                access_code = '-'.join([alternative_code[i:i+4] for i in range(0, len(alternative_code), 4)])
            
            logger.debug(f"Generated access code: {access_code}")
            return access_code[:15]
        except Exception as e:
            logger.error(f"Error generating access code: {e}")
            raise

    def validate_hardware_id(self, hardware_id):
        """اعتبارسنجی شناسه سخت‌افزاری"""
        logger.debug(f"Validating hardware ID: {hardware_id}")
        if not hardware_id or len(hardware_id) != 16:
            logger.warning(f"Invalid hardware ID length: {hardware_id}")
            return False
        valid = all(c in "0123456789ABCDEF" for c in hardware_id.upper())
        if not valid:
            logger.warning(f"Invalid hardware ID characters: {hardware_id}")
        return valid

    def generate_license(self, instance):
        logger.info("License generation initiated")
        buyer = self.buyer_name.text.strip()
        phone = self.phone.text.strip()
        hardware_id = self.hardware_id.text.strip().upper()

        if not (buyer and phone and hardware_id):
            logger.warning("License generation failed: empty fields")
            self.show_popup("خطا", "تمام فیلدها را پر کنید")
            return

        if not self.validate_hardware_id(hardware_id):
            logger.warning(f"License generation failed: invalid hardware ID {hardware_id}")
            self.show_popup("خطا", "شناسه سخت‌افزاری نامعتبر است (باید 16 کاراکتر و فقط شامل اعداد و حروف A-F باشد)")
            return

        try:
            access_code = self.generate_access_code(hardware_id)
            
            jalali_date = jdatetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            
            customer = {
                "name": buyer,
                "phone": phone,
                "hardware_id": hardware_id,
                "access_code": access_code,
                "created_date": jalali_date
            }
            
            self.customers.append(customer)
            
            if self.save_customers():
                logger.info(f"License generated successfully for {buyer}, hardware ID: {hardware_id}")
                self.show_popup("موفق", f"مشتری با موفقیت اضافه شد\nرمز تولید شده: {access_code}")
                self.refresh_customers_list()
                self.clear_fields()
            else:
                logger.error("Failed to save customer data")
        except Exception as e:
            logger.error(f"Error generating license: {e}")
            self.show_popup("خطا", f"خطا در تولید لایسنس: {e}")

    def clear_fields(self):
        """پاک کردن فیلدهای ورودی"""
        try:
            self.buyer_name.text = ""
            self.phone.text = ""
            self.hardware_id.text = ""
            logger.debug("Input fields cleared")
        except Exception as e:
            logger.error(f"Error clearing fields: {e}")

    def refresh_customers_list(self):
        """به‌روزرسانی لیست مشتریان"""
        logger.debug("Refreshing customers list")
        try:
            self.scroll_layout.clear_widgets()
            self.scroll_layout.height = 0
            
            for customer in self.customers:
                item = CustomerItem(customer, self.confirm_remove_customer)  # تغییر این خط
                self.scroll_layout.add_widget(item)
                self.scroll_layout.height += item.height
            logger.debug("Customers list refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing customers list: {e}")

    def confirm_remove_customer(self, customer):
        """نمایش پاپ‌آپ تایید برای حذف مشتری"""
        logger.info(f"Showing confirmation popup for customer removal: {customer['name']}")
        try:
            content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))
            
            message_label = PersianLabel(
                text=f"آیا از حذف مشتری '{customer['name']}' مطمئن هستید؟",
                font_size=dp(14),
                size_hint_y=None,
                height=dp(50)
            )
            content.add_widget(message_label)
            
            buttons_layout = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(40))
            
            cancel_btn = PersianButton(
                text="انصراف",
                background_color=(0.6, 0.6, 0.6, 1)
            )
            
            confirm_btn = PersianButton(
                text="حذف",
                background_color=(0.8, 0.2, 0.2, 1)
            )
            
            buttons_layout.add_widget(cancel_btn)
            buttons_layout.add_widget(confirm_btn)
            content.add_widget(buttons_layout)
            
            popup = Popup(
                title=reshape_bidi("تایید حذف"),
                content=content,
                size_hint=(0.7, 0.4),
                title_align='center'
            )
            
            def remove_customer_confirmed(instance):
                logger.info(f"Customer removal confirmed for: {customer['name']}")
                popup.dismiss()
                self.remove_customer(customer)
            
            def cancel_removal(instance):
                logger.debug("Customer removal cancelled")
                popup.dismiss()
            
            confirm_btn.bind(on_press=remove_customer_confirmed)
            cancel_btn.bind(on_press=cancel_removal)
            
            popup.open()
        except Exception as e:
            logger.error(f"Error showing confirmation popup: {e}")

    def remove_customer(self, customer):
        """حذف مشتری از لیست"""
        logger.info(f"Removing customer: {customer['name']}")
        if customer in self.customers:
            self.customers.remove(customer)
            self.save_customers()
            self.refresh_customers_list()
            logger.info(f"Customer {customer['name']} removed successfully")
            self.show_popup("موفق", f"مشتری '{customer['name']}' با موفقیت حذف شد")

    def export_customers(self, instance):
        """صدور لیست مشتریان به فایل متنی"""
        logger.info("Exporting customers to text file")
        try:
            filename = f"customers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("     لیست مشتریان انطباق302\n")
                f.write("=" * 60 + "\n\n")
                
                for i, customer in enumerate(self.customers, 1):
                    f.write(f"ردیف: {i}\n")
                    f.write(f"نام: {customer['name']}\n")
                    f.write(f"تلفن: {customer['phone']}\n")
                    f.write(f"شناسه: {customer['hardware_id']}\n")
                    f.write(f"رمز: {customer['access_code']}\n")
                    f.write(f"تاریخ ایجاد: {customer['created_date']}\n")
                    f.write("-" * 40 + "\n")
            
            logger.info(f"Customers exported successfully to {filepath}")
            self.show_popup("موفق", f"لیست مشتریان با موفقیت در فایل ذخیره شد:\n{filepath}")
        except Exception as e:
            logger.error(f"Error exporting customers: {e}")
            self.show_popup("خطا", f"خطا در ذخیره فایل: {e}")

    def show_change_password_popup(self, instance):
        """نمایش پاپ‌آپ برای تغییر رمز عبور"""
        logger.info("Showing change password popup")
        try:
            content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
            
            content.add_widget(PersianLabel(
                text="رمز عبور فعلی:", 
                size_hint_y=None, 
                height=dp(25),
                color=(1, 1, 1, 1)
            ))
            current_password = PersianTextInput(password=True, size_hint_y=None, height=dp(30))
            content.add_widget(current_password)
            
            content.add_widget(PersianLabel(
                text="رمز عبور جدید:", 
                size_hint_y=None, 
                height=dp(25),
                color=(1, 1, 1, 1)
            ))
            new_password = PersianTextInput(password=True, size_hint_y=None, height=dp(30))
            content.add_widget(new_password)
            
            content.add_widget(PersianLabel(
                text="تکرار رمز عبور جدید:", 
                size_hint_y=None, 
                height=dp(25),
                color=(1, 1, 1, 1)
            ))
            confirm_password = PersianTextInput(password=True, size_hint_y=None, height=dp(30))
            content.add_widget(confirm_password)
            
            buttons_layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(35))
            
            cancel_btn = PersianButton(text="انصراف", size_hint_x=0.5, background_color=(0.85, 0.85, 0.85, 0.9))
            change_btn = PersianButton(text="تغییر رمز", size_hint_x=0.5, background_color=(0.85, 0.85, 0.85, 0.9))
            
            buttons_layout.add_widget(cancel_btn)
            buttons_layout.add_widget(change_btn)
            content.add_widget(buttons_layout)
            
            popup = Popup(
                title=reshape_bidi("تغییر رمز عبور"), 
                content=content, 
                size_hint=(0.8, 0.5),
                title_align='center'
            )
            
            def change_password(btn):
                logger.info("Password change initiated")
                if not current_password.text:
                    logger.warning("Password change failed: empty current password")
                    self.show_popup("خطا", "رمز عبور فعلی را وارد کنید")
                    return
                    
                if not new_password.text:
                    logger.warning("Password change failed: empty new password")
                    self.show_popup("خطا", "رمز عبور جدید را وارد کنید")
                    return
                    
                if new_password.text != confirm_password.text:
                    logger.warning("Password change failed: passwords don't match")
                    self.show_popup("خطا", "رمزهای عبور جدید مطابقت ندارند")
                    return
                    
                password_file = "admin_pass.hash"
                try:
                    with open(password_file, "r") as f:
                        stored_hash = f.read().strip()
                    
                    if self.hash_password(current_password.text) != stored_hash:
                        logger.warning("Password change failed: incorrect current password")
                        self.show_popup("خطا", "رمز عبور فعلی نادرست است")
                        return
                        
                    with open(password_file, "w") as f:
                        f.write(self.hash_password(new_password.text))
                        
                    logger.info("Password changed successfully")
                    self.show_popup("موفق", "رمز عبور با موفقیت تغییر یافت")
                    popup.dismiss()
                    
                except Exception as e:
                    logger.error(f"Error changing password: {e}")
                    self.show_popup("خطا", f"خطا در تغییر رمز عبور: {e}")
            
            def cancel_change(btn):
                logger.debug("Password change cancelled")
                popup.dismiss()
            
            change_btn.bind(on_press=change_password)
            cancel_btn.bind(on_press=cancel_change)
            
            popup.open()
        except Exception as e:
            logger.error(f"Error showing change password popup: {e}")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def show_popup(self, title, message):
        logger.debug(f"Showing popup: {title} - {message}")
        try:
            content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
            content.add_widget(PersianLabel(text=message, font_size=dp(13), size_hint_y=None, height=dp(40)))
            btn = PersianButton(text="بستن", size_hint=(1, None), height=dp(30))
            popup = Popup(
                title=reshape_bidi(title), 
                content=content, 
                size_hint=(0.7, 0.35),
                title_align='center'
            )
            btn.bind(on_press=popup.dismiss)
            content.add_widget(btn)
            popup.open()
        except Exception as e:
            logger.error(f"Error showing popup: {e}")

    def exit_app(self, instance):
        """خروج از برنامه"""
        logger.info("Exiting application")
        try:
            App.get_running_app().stop()
            Window.close()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error exiting application: {e}")
            import os
            os._exit(0)

class LicenseManagerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # تنظیم آیکن در سطح کلاس App
        self.icon = 'app-icon.png'  # ابتدا PNG را امتحان کن
    
    def build(self):
        logger.info("Application started")
        
        # تنظیم آیکن برای پنجره (روش جایگزین)
        try:
            icon_path_png = os.path.join(os.path.dirname(__file__), "app-icon.png")
            icon_path_ico = os.path.join(os.path.dirname(__file__), "app-icon.ico")
            icon_path_jpg = os.path.join(os.path.dirname(__file__), "app-icon.jpg")
            
            if os.path.exists(icon_path_png):
                self.icon = icon_path_png
                Window.set_icon(icon_path_png)
                logger.info("Application PNG icon set successfully")
            elif os.path.exists(icon_path_ico):
                self.icon = icon_path_ico
                Window.set_icon(icon_path_ico)
                logger.info("Application ICO icon set successfully")
            elif os.path.exists(icon_path_jpg):
                self.icon = icon_path_jpg
                Window.set_icon(icon_path_jpg)
                logger.info("Application JPG icon set successfully")
            else:
                logger.warning("No application icon file found")
        except Exception as e:
            logger.error(f"Error setting application icon: {e}")
        
        Window.clearcolor = (0.85, 0.85, 0.85, 0.9)
        self.main_layout = BoxLayout(orientation="vertical", padding=dp(12))
        self.show_login_screen()
        return self.main_layout

    def show_login_screen(self):
        logger.debug("Showing login screen")
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(LoginScreen(self))

    def show_main_screen(self):
        logger.debug("Showing main screen")
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(MainScreen())

if __name__ == "__main__":
    try:
        LicenseManagerApp().run()
    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
