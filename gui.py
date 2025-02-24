import os
import threading
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_ALL
import customtkinter as ctk
from PIL import Image

VERSION = "2.9.0"
COPYRIGHT = "© Loli 2025"

FEATURE_CRAWL_ENABLED = True
FEATURE_GEN_OUTPUT_ENABLED = False

class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class App(Tk):
    def init_resources(self):
        # configure resources images
        self.img_mode_convert = ctk.CTkImage(dark_image=Image.open("resources/dark_img_convert.png"),
                                             light_image=Image.open("resources/light_img_convert.png"),     
                                             size=(24, 24))
        
        self.img_mode_crawl = ctk.CTkImage(dark_image=Image.open("resources/dark_img_crawl.png"),
                                             light_image=Image.open("resources/light_img_crawl.png"),     
                                             size=(24, 24))

    def init_frame_sidebar(self):
        self.frame_sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.frame_sidebar.grid(row=0, column=0, sticky="nsew")

        self.frame_sidebar.grid_rowconfigure(6, weight=1)

        self.lbl_sb_logo = ctk.CTkLabel(self.frame_sidebar, text="Accepted", font=ctk.CTkFont(size=18))
        self.lbl_sb_logo.grid(row=0, column=0, padx=20, pady=(15,0))
        self.lbl_sb_logo_sub = ctk.CTkLabel(self.frame_sidebar, text=f"{VERSION} - {COPYRIGHT}", font=ctk.CTkFont(size=12))
        self.lbl_sb_logo_sub.grid(row=1, column=0, padx=20, pady=(0, 25))
        self.but_sb_mode_convert = ctk.CTkButton(self.frame_sidebar, corner_radius=0, height=40, border_spacing=10, text="Chuyển đổi Test", font=ctk.CTkFont(size=13),
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.img_mode_convert, anchor="w", command=self.event_but_sb_mode_convert)
        self.but_sb_mode_convert.grid(row=2, column=0, padx=0, pady=0, sticky="ew")

        self.but_sb_mode_crawl = ctk.CTkButton(self.frame_sidebar, corner_radius=0, height=40, border_spacing=10, text="Cào bài", font=ctk.CTkFont(size=13),
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   image=self.img_mode_crawl, anchor="w", command=self.event_but_sb_mode_crawl)
        self.but_sb_mode_crawl.grid(row=3, column=0, padx=0, pady=0, sticky="ew")

        self.lbl_sb_submode = ctk.CTkLabel(self.frame_sidebar, text="Chế độ:", anchor="center")
        self.lbl_sb_submode.grid(row=4, column=0, padx = 10, pady = (10,0), sticky="ew")

        self.menu_sb_submode = ctk.CTkOptionMenu(self.frame_sidebar, height=23, command=self.event_menu_sb_submode)
        self.menu_sb_submode.grid(row=5, column=0, padx = 10, sticky="ew")

        self.lbl_sb_shortcutdir = ctk.CTkLabel(self.frame_sidebar, text="Lối tắt thư mục:", anchor="center")
        self.lbl_sb_shortcutdir.grid(row=7, column=0, padx = 10, sticky="ew")

        self.subframe_sb_shortcutdir = ctk.CTkFrame(self.frame_sidebar, corner_radius=0, fg_color="transparent")
        self.subframe_sb_shortcutdir.grid(row=8, column=0, padx=10, pady=(0,20), sticky="ew")
        self.subframe_sb_shortcutdir.grid_columnconfigure((0,1), weight=1)

        self.but_sb_folder_input = ctk.CTkButton(self.subframe_sb_shortcutdir, text="Đầu vào", height=23, width=60, command=self.event_btn_sb_folder_input)
        self.but_sb_folder_input.grid(row=0, column=0, sticky="ew", padx=(0,6))

        self.but_sb_folder_output = ctk.CTkButton(self.subframe_sb_shortcutdir, text="Đầu ra", height=23, width=60, command=self.event_btn_sb_folder_output)
        self.but_sb_folder_output.grid(row=0, column=1, sticky="ew")

        self.subframe_sb_appearmode = ctk.CTkFrame(self.frame_sidebar, corner_radius=0, fg_color="transparent")
        self.subframe_sb_appearmode.grid(row=9, column=0, padx=10, pady=10, sticky="ew")
        self.subframe_sb_appearmode.grid_columnconfigure(1, weight=1)

        self.lbl_sb_appearance_mode = ctk.CTkLabel(self.subframe_sb_appearmode, text="Chủ đề:", anchor="w")
        self.lbl_sb_appearance_mode.grid(row=0, column=0, sticky="w", padx=(0,8))
        self.menu_sb_appearance_mode = ctk.CTkOptionMenu(self.subframe_sb_appearmode, values=["Sáng", "Tối", "Tự động"],
                                                                        command=self.event_menu_sb_appearance_mode, height=23, width=50)
        self.menu_sb_appearance_mode.grid(row=0, column=1, sticky="ew")

    def init_frame_statusbar(self):
        self.frame_statusbar = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray80", "gray15"), height=45)
        self.frame_statusbar.grid(row=1, column=0, columnspan=2, sticky="nsew")
    
        self.frame_statusbar.grid_columnconfigure(1, weight=1)
        self.frame_statusbar.grid_rowconfigure(1, weight=1)

        self.progbar_status = ctk.CTkProgressBar(self.frame_statusbar, mode="determinate", height=6, determinate_speed=1)
        self.progbar_status.grid(row=0, column=0, columnspan = 2, padx=(10, 10), pady=(5, 0), sticky="nsew")

        self.lbl_status = ctk.CTkLabel(self.frame_statusbar, text="Trạng thái: Sẵn sàng!", anchor="w", text_color=("gray25", "gray70"))
        self.lbl_status.grid(row=1, column=0, padx=(10, 0), pady=(0, 0), sticky="nsew")

        self.lbl_percentage = ctk.CTkLabel(self.frame_statusbar, text="100%", anchor="e", text_color=("gray25", "gray70"))
        self.lbl_percentage.grid(row=1, column=1, padx=(0, 10), pady=(0, 0), sticky="e")

    def init_frame_convert(self):
        self.formatter = None

        self.convert_tabview_frame_fz = ctk.CTkFrame(self, border_width=1)

        self.lbl_cv_fz_input = ctk.CTkLabel(self.convert_tabview_frame_fz, text="Test:", anchor="center")
        self.lbl_cv_fz_input.grid(row=0, column=0, padx=8, pady=(5,0))

        self.entry_cv_fz_input = ctk.CTkEntry(self.convert_tabview_frame_fz, placeholder_text="Đường dẫn tới thư mục test... (có thể kéo thả)", height=27)
        self.entry_cv_fz_input.grid(row=0, column=1, columnspan=6, sticky="ew", pady=(5,0))
        self.entry_cv_fz_input.bind("<FocusOut>", self.event_entry_cv_fz_input_path)

        self.but_cv_fz_input = ctk.CTkButton(self.convert_tabview_frame_fz, text="Duyệt...", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray35"), border_width=2, height=27, width=75, command=self.event_btn_cv_fz_inp_choose_dir)
        self.but_cv_fz_input.grid(row=0, column=7, sticky="e", padx=(5,8), pady=(5,0))

        self.check_cv_fz_genoutput = ctk.CTkCheckBox(self.convert_tabview_frame_fz, text="Sinh kết quả", checkbox_height=15, checkbox_width=15, border_width=2)
        self.check_cv_fz_genoutput.grid(row=1, column=0, columnspan=2, padx=(8, 0), sticky="w")

        self.entry_cv_fz_genoutput = ctk.CTkEntry(self.convert_tabview_frame_fz, placeholder_text="File sinh kết quả... (.cpp/.exe, có thể kéo thả)", height=23)
        self.entry_cv_fz_genoutput.grid(row=1, column=2, columnspan=5, sticky="ew")

        self.but_cv_fz_genoutput = ctk.CTkButton(self.convert_tabview_frame_fz, text="Duyệt...", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray35"), border_width=2, height=23, width=75, command=self.event_btn_cv_fz_output_choose_file)
        self.but_cv_fz_genoutput.grid(row=1, column=7, sticky="e", padx=(5,8))

        self.lbl_cv_fz_output_name = ctk.CTkLabel(self.convert_tabview_frame_fz, text="Tên bài đầu ra:", anchor="e")
        self.lbl_cv_fz_output_name.grid(row=2, column=5, padx=(5,8), sticky="e")

        self.entry_cv_fz_output_name = ctk.CTkEntry(self.convert_tabview_frame_fz, placeholder_text="(như cũ)", height=23)
        self.entry_cv_fz_output_name.grid(row=2, column=6, columnspan=2, sticky="ew", padx=(0,8))
        self.entry_cv_fz_output_name.bind("<FocusOut>", self.event_entry_cv_fz_output_name)

        self.subframe_cv_fz_extopts = ctk.CTkFrame(self.convert_tabview_frame_fz, corner_radius=0, fg_color="transparent")
        self.subframe_cv_fz_extopts.grid(row=2, column=0, columnspan=5, sticky="w", padx=4)
        self.subframe_cv_fz_extopts.grid_columnconfigure((1,3), weight=1, pad=10)

        self.lbl_cv_fz_input_ext = ctk.CTkLabel(self.subframe_cv_fz_extopts, text="Đuôi file input:", anchor="w")
        self.lbl_cv_fz_input_ext.grid(row=0, column=0, padx=(14,8), sticky="e")

        self.entry_cv_fz_input_ext = ctk.CTkEntry(self.subframe_cv_fz_extopts, placeholder_text="(inp, ..)", height=23, width=60)
        self.entry_cv_fz_input_ext.grid(row=0, column=1, sticky="w")
        self.entry_cv_fz_input_ext.bind("<FocusOut>", self.event_entry_cv_fz_update_ext)

        self.lbl_cv_fz_output_ext = ctk.CTkLabel(self.subframe_cv_fz_extopts, text="Đuôi file output:", anchor="w")
        self.lbl_cv_fz_output_ext.grid(row=0, column=2, padx=(15,8), sticky="e")

        self.entry_cv_fz_output_ext = ctk.CTkEntry(self.subframe_cv_fz_extopts, placeholder_text="(out, ..)", height=23, width=60)
        self.entry_cv_fz_output_ext.grid(row=0, column=3, sticky="w")
        self.entry_cv_fz_output_ext.bind("<FocusOut>", self.event_entry_cv_fz_update_ext)

        self.subframe_cv_fz_inclopts = ctk.CTkFrame(self.convert_tabview_frame_fz, corner_radius=0, fg_color="transparent", )
        self.subframe_cv_fz_inclopts.grid(row=3, column=0, columnspan=3, sticky="w", padx=(8,0))
        self.subframe_cv_fz_inclopts.grid_columnconfigure((0,1), weight=1)

        self.check_cv_fz_inclinput = ctk.CTkCheckBox(self.subframe_cv_fz_inclopts, text="Chứa input?", checkbox_height=15, checkbox_width=15, border_width=2, command=self.event_check_cv_fz_update_incl)
        self.check_cv_fz_inclinput.grid(row=0, column=0, padx=(0, 0), sticky="e")

        self.check_cv_fz_incloutput = ctk.CTkCheckBox(self.subframe_cv_fz_inclopts, text="Chứa output?", checkbox_height=15, checkbox_width=15, border_width=2, command=self.event_check_cv_fz_update_incl)
        self.check_cv_fz_incloutput.grid(row=0, column=1, padx=(20, 0), sticky="e")

        self.lbl_cv_fz_compress_type = ctk.CTkLabel(self.convert_tabview_frame_fz, text="Kiểu nén:", anchor="e")
        self.lbl_cv_fz_compress_type.grid(row=3, column=3, padx=(0, 5), sticky="e")

        self.menu_cv_fz_compress_type = ctk.CTkOptionMenu(self.convert_tabview_frame_fz, values=["Deflate 5 (mặc định)", "Deflate 8 (chậm, nhẹ)", "Không nén (nhanh, nặng)"], command=self.event_menu_cv_fz_change_compress_type, height=23)
        self.menu_cv_fz_compress_type.grid(row=3, column=4, columnspan=3, padx=(5, 1), sticky="ew")

        self.but_cv_fz_dircheck = ctk.CTkButton(self.convert_tabview_frame_fz, text="Áp dụng", height=23, width=75, command=self.event_btn_cv_check)
        self.but_cv_fz_dircheck.grid(row=3, column=7, padx=(5, 8), sticky="e")

        self.box_cv_fz_logbox = ctk.CTkTextbox(self.convert_tabview_frame_fz, activate_scrollbars=False, border_width=1, font=ctk.CTkFont(size = 12), wrap="word")
        self.box_cv_fz_logbox.grid(row=4, column=0, columnspan=8, padx=(8, 8), pady=(1, 5), sticky="nsew")
        self.box_cv_fz_logbox.configure(state="disabled")

        self.lbl_cv_fz_savedir = ctk.CTkLabel(self.convert_tabview_frame_fz, text="Lưu tại:", anchor="center", width=80)
        self.lbl_cv_fz_savedir.grid(row=5, column=0, padx=(5, 0), pady=(0,5))

        self.entry_cv_fz_savedir = ctk.CTkEntry(self.convert_tabview_frame_fz, placeholder_text="Đường dẫn tới thư mục... (có thể kéo thả)", height=27)
        self.entry_cv_fz_savedir.grid(row=5, column=1, columnspan=5, sticky="ew", pady=(0,5))
        self.entry_cv_fz_savedir.bind("<FocusOut>", self.event_entry_cv_fz_savedir)

        self.but_cv_fz_savedir = ctk.CTkButton(self.convert_tabview_frame_fz, text="Duyệt...", height=27, width=20, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray35"), border_width=2, command=self.event_btn_cv_fz_savedir_choose_dir)
        self.but_cv_fz_savedir.grid(row=5, column=6, padx=(5,0), sticky="ew", pady=(0,5))

        self.but_cv_fz_convert = ctk.CTkButton(self.convert_tabview_frame_fz, text="Thực thi", height=30, width=75, fg_color="firebrick", hover_color="darkred", text_color = "white", text_color_disabled="gray", command=self.event_btn_cv_convert)
        self.but_cv_fz_convert.grid(row=5, column=7, padx=(5, 8), sticky="nse", pady=(0,5))

        self.convert_tabview_frame_fz.drop_target_register(DND_ALL)
        self.convert_tabview_frame_fz.dnd_bind("<<Drop>>", self.event_dnd_convert_input)

        self.entry_cv_fz_genoutput.drop_target_register(DND_ALL)
        self.entry_cv_fz_genoutput.dnd_bind("<<Drop>>", self.event_dnd_convert_output)

        self.entry_cv_fz_savedir.drop_target_register(DND_ALL)
        self.entry_cv_fz_savedir.dnd_bind("<<Drop>>", self.event_dnd_convert_savedir)

    def init_frame_crawl(self):
        self.crawl_tabview_frame = ctk.CTkFrame(self, border_width=1)

        self.lbl_cr_input = ctk.CTkLabel(self.crawl_tabview_frame, text="URL:", anchor="center")
        self.lbl_cr_input.grid(row=0, column=0, padx=8, pady=(5,5))

        self.entry_cr_input = ctk.CTkEntry(self.crawl_tabview_frame, placeholder_text="Link URL tới trang...", height=27)
        self.entry_cr_input.grid(row=0, column=1, columnspan=7, sticky="ew", pady=(5,5), padx=(0,8))

        self.box_cr_logbox = ctk.CTkTextbox(self.crawl_tabview_frame, activate_scrollbars=False, border_width=1, font=ctk.CTkFont(size = 12), wrap="word")
        self.box_cr_logbox.grid(row=4, column=0, columnspan=8, padx=(8, 8), pady=(1, 5), sticky="nsew")
        self.box_cr_logbox.configure(state="disabled")

        self.lbl_cr_savedir = ctk.CTkLabel(self.crawl_tabview_frame, text="Lưu tại:", anchor="center", width=80)
        self.lbl_cr_savedir.grid(row=5, column=0, padx=(5, 0), pady=(0,5))

        self.entry_cr_savedir = ctk.CTkEntry(self.crawl_tabview_frame, placeholder_text="Đường dẫn tới thư mục... (có thể kéo thả)", height=27)
        self.entry_cr_savedir.grid(row=5, column=1, columnspan=5, sticky="ew", pady=(0,5))
        self.entry_cr_savedir.bind("<FocusOut>", self.event_entry_cv_fz_savedir)

        self.but_cr_savedir = ctk.CTkButton(self.crawl_tabview_frame, text="Duyệt...", height=27, width=20, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray35"), border_width=2, command=self.event_btn_cv_fz_savedir_choose_dir)
        self.but_cr_savedir.grid(row=5, column=6, padx=(5,0), sticky="ew", pady=(0,5))

        self.but_cr_crawl = ctk.CTkButton(self.crawl_tabview_frame, text="Thực thi", height=30, width=75, fg_color="firebrick", hover_color="darkred", text_color = "white", text_color_disabled="gray", command=self.event_btn_cv_convert)
        self.but_cr_crawl.grid(row=5, column=7, padx=(5, 8), sticky="nse", pady=(0,5))

    def init_default_state(self):
        self.menu_sb_appearance_mode.set("Tự động")
        self.switch_operation_mode("convert")

        if not FEATURE_CRAWL_ENABLED:
            self.but_sb_mode_crawl.configure(state="disabled")

        if not FEATURE_GEN_OUTPUT_ENABLED:
            self.entry_cv_fz_genoutput.configure(state="disabled")
            self.but_cv_fz_genoutput.configure(state="disabled")
            self.check_cv_fz_genoutput.configure(state="disabled")

        self.progbar_status.set(0)
        self.lbl_percentage.configure(text="")

        self.entry_cv_fz_input_ext.insert(0, "inp")
        self.entry_cv_fz_output_ext.insert(0, "out")
        self.menu_cv_fz_compress_type.set("Deflate 5 (mặc định)")
        self.check_cv_fz_inclinput.select()
        self.check_cv_fz_incloutput.select()
        self.but_cv_fz_convert.configure(state="disabled")

        self.but_cr_crawl.configure(state="disabled")
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # default dir to save is current working directory, in a folder named "output"
        self.entry_cv_fz_savedir.insert(0, os.path.join(os.getcwd(), "output", "formatter"))
        self.entry_cr_savedir.insert(0, os.path.join(os.getcwd(), "output", "crawler"))

    def __init__(self):
        self.current_mode = "init"
        self.current_submode = "init"
        self.prev_submode_convert = "init"
        self.prev_submode_crawl = "init"

        super().__init__()
        self.geometry("810x476")
        self.title(f"Accepted - v{VERSION} - {COPYRIGHT}")

        self.init_resources()
        # configure grid layout (2x2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.init_frame_sidebar()
        self.init_frame_statusbar()
        self.init_frame_convert()
        self.init_frame_crawl()
        self.init_default_state()

    def event_dnd_convert_input(self, event):
        event.data = str(event.data).removeprefix('{').removesuffix('}')
        # check if the input is a directory or a file
        if (self.current_submode == "ZIP → Thư mục" and os.path.isdir(event.data)):
            self.switch_submode("Thư mục → ZIP")
        
        if (self.current_submode == "Thư mục → ZIP" and os.path.isfile(event.data)):
            if event.data.endswith(".zip"):
                self.switch_submode("ZIP → Thư mục")
            else:
                return

        self.entry_cv_fz_input.delete(0, "end")
        self.entry_cv_fz_input.insert(0, event.data)

        self.event_btn_cv_check(compress_level_rcm=True)

    def event_dnd_convert_output(self, event):
        event.data = str(event.data).removeprefix('{').removesuffix('}')
        if os.path.isdir(event.data):
            return
        self.entry_cv_fz_genoutput.delete(0, "end")
        self.entry_cv_fz_genoutput.insert(0, event.data)
    
    def event_dnd_convert_savedir(self, event):
        event.data = str(event.data).removeprefix('{').removesuffix('}')
        if os.path.isfile(event.data):
            return
        self.entry_cv_fz_savedir.delete(0, "end")
        self.entry_cv_fz_savedir.insert(0, event.data)
    
    def event_btn_cv_fz_inp_choose_dir(self):
        if self.current_submode == "Thư mục → ZIP":
            self.path = filedialog.askdirectory()
        elif self.current_submode == "ZIP → Thư mục":
            self.path = filedialog.askopenfilename(filetypes=[("Tệp nén", "*.zip")])
        if str(self.path) == "":
            return
        self.entry_cv_fz_input.delete(0, "end")
        self.entry_cv_fz_input.insert(0, self.path)
        self.event_btn_cv_check(compress_level_rcm=True)
    
    def event_btn_cv_fz_savedir_choose_dir(self):
        self.path = filedialog.askdirectory()
        if str(self.path) == "":
            return
        self.entry_cv_fz_savedir.delete(0, "end")
        self.entry_cv_fz_savedir.insert(0, self.path)

    def event_btn_cv_fz_output_choose_file(self):
        self.path = filedialog.askopenfilename(filetypes=[("File sinh kết quả", "*.cpp *.exe")])
        if str(self.path) == "":
            return
        self.entry_cv_fz_genoutput.delete(0, "end")
        self.entry_cv_fz_genoutput.insert(0, self.path)

    def event_menu_sb_appearance_mode(self, new_appearance_mode: str):
        if new_appearance_mode == "Sáng":
            ctk.set_appearance_mode("Light")
        elif new_appearance_mode == "Tối":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("System")

    def switch_operation_mode(self, new_mode: str):
        if new_mode == self.current_mode:
            return
        
        if self.current_mode == "convert":
            self.prev_submode_convert = self.current_submode
        elif self.current_mode == "crawl":
            self.prev_submode_crawl = self.current_submode
        
        self.current_mode = new_mode
        print(f"Switched to {new_mode} mode")

        MENU_SB_SUBMODE_CONVERT_LIST = ["Thư mục → ZIP", "ZIP → Thư mục"]
        MENU_SB_SUBMODE_CRAWL_LIST = ["Tự nhận diện", "DMOJ", "LQDOJ", "Codeforces", "CSLOJ"]
        
        if new_mode == "crawl":
            self.convert_tabview_frame_fz.grid_forget()
            self.crawl_tabview_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=(5, 5))
            self.crawl_tabview_frame.grid_columnconfigure((2,3,4,5), weight=1)
            self.crawl_tabview_frame.grid_rowconfigure((0,1,2,3,4,5), pad=7)
            self.crawl_tabview_frame.grid_rowconfigure(4, weight=1)
            self.logger = Logger(self.box_cr_logbox, self.progbar_status, self.lbl_status, self.lbl_percentage)
            self.menu_sb_submode.configure(values = MENU_SB_SUBMODE_CRAWL_LIST)
            self.switch_submode("Tự nhận diện" if self.prev_submode_crawl == "init" else self.prev_submode_crawl, notify=False)
        
        elif new_mode == "convert":
            self.crawl_tabview_frame.grid_forget()
            self.convert_tabview_frame_fz.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=(5, 5))
            self.convert_tabview_frame_fz.grid_columnconfigure((2,3,4,5,6), weight=1)
            self.convert_tabview_frame_fz.grid_rowconfigure((0,1,2,3,4,5), pad=7)
            self.convert_tabview_frame_fz.grid_rowconfigure(4, weight=1)
            self.logger = Logger(self.box_cv_fz_logbox, self.progbar_status, self.lbl_status, self.lbl_percentage)
            self.menu_sb_submode.configure(values = MENU_SB_SUBMODE_CONVERT_LIST)
            self.switch_submode("Thư mục → ZIP" if self.prev_submode_convert == "init" else self.prev_submode_convert, notify=False)

        self.but_sb_mode_convert.configure(fg_color=("gray75", "gray23") if self.current_mode == "convert" else "transparent")
        self.but_sb_mode_crawl.configure(fg_color=("gray75", "gray23") if self.current_mode == "crawl" else "transparent")

    def switch_submode(self, new_submode: str, notify=True):
        if new_submode == self.current_submode:
            return
        self.current_submode = new_submode
        print(f"Switched to {new_submode} submode")

        # set menu option
        self.menu_sb_submode.set(new_submode)

        if notify:
            self.logger.log(f"\n===== Chuyển sang chế độ: {new_submode} =====\n")

        self.lbl_status.configure(text="Trạng thái: Sẵn sàng!", text_color=("gray25", "gray70"))
        self.progbar_status.set(0)
        self.lbl_percentage.configure(text="")

        if self.current_mode == "convert":
            # clear input
            self.entry_cv_fz_input.delete(0, "end")
            self.but_cv_fz_convert.configure(state="disabled")
            if new_submode == "Thư mục → ZIP":
                self.lbl_cv_fz_input.configure(text="Thư mục:")
                self.entry_cv_fz_input.configure(placeholder_text="Đường dẫn tới thư mục test... (có thể kéo thả)")
                self.lbl_cv_fz_compress_type.configure(text="Kiểu nén:")
                self.menu_cv_fz_compress_type.grid(row=3, column=4, columnspan=3, padx=(5, 1), sticky="ew")

            elif new_submode == "ZIP → Thư mục":
                self.lbl_cv_fz_input.configure(text="File ZIP:")
                self.entry_cv_fz_input.configure(placeholder_text="Đường dẫn tới file ZIP... (có thể kéo thả)")
                self.lbl_cv_fz_compress_type.configure(text="")
                self.menu_cv_fz_compress_type.grid_forget()

    def event_btn_cv_check(self, verbose=True, compress_level_rcm=True):
        if(self.entry_cv_fz_input.get() == ""):
            return
        if self.current_submode == "Thư mục → ZIP":
            self.event_btn_cv_fz_check_dir(verbose, compress_level_rcm)
        elif self.current_submode == "ZIP → Thư mục":
            self.event_btn_cv_zf_check_zip(verbose)

    def event_btn_cv_fz_check_dir(self, verbose=True, compress_level_rcm = True):
        self.logger.log_and_status("Kiểm tra thư mục...")
        from formatter import Formatter
        self.formatter = Formatter(self.entry_cv_fz_input.get(), self.logger, 
                                   self.entry_cv_fz_savedir.get(), 
                                   self.entry_cv_fz_genoutput.get() if self.check_cv_fz_genoutput.get() == 1 else None,
                                   self.check_cv_fz_inclinput.get(), 
                                   self.check_cv_fz_incloutput.get(), 
                                   self.entry_cv_fz_input_ext.get(),
                                   self.entry_cv_fz_output_ext.get(),
                                   self.entry_cv_fz_output_name.get())
        
        # Run in a separate thread
        (verdict, rcm_level) = self.formatter.check_input_directory(verbose)
        if verdict == False:
            self.but_cv_fz_convert.configure(state="disabled")
            return
        else:
            self.but_cv_fz_convert.configure(state="normal")
            if compress_level_rcm == False:
                return
            if rcm_level == 0:
                self.menu_cv_fz_compress_type.set("Không nén (nhanh, nặng)")
            elif rcm_level == 5:
                self.menu_cv_fz_compress_type.set("Deflate 5 (mặc định)")
            elif rcm_level == 8:
                self.menu_cv_fz_compress_type.set("Deflate 8 (chậm, nhẹ)")
    
    def event_btn_cv_zf_check_zip(self, verbose=True):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log_and_status("Kiểm tra file ZIP...")
        from formatter import Formatter
        self.formatter = Formatter(self.entry_cv_fz_input.get(), self.logger, 
                                   self.entry_cv_fz_savedir.get(), 
                                   self.entry_cv_fz_genoutput.get() if self.check_cv_fz_genoutput.get() == 1 else None,
                                   self.check_cv_fz_inclinput.get(), 
                                   self.check_cv_fz_incloutput.get(), 
                                   self.entry_cv_fz_input_ext.get(),
                                   self.entry_cv_fz_output_ext.get(),
                                   self.entry_cv_fz_output_name.get())
        
        # Run in a separate thread
        verdict = self.formatter.check_input_zip_file(verbose)
        if verdict == False:
            self.but_cv_fz_convert.configure(state="disabled")
            return
        else:
            self.but_cv_fz_convert.configure(state="normal")
    
    def event_btn_cv_convert(self):
        if(self.entry_cv_fz_input.get() == ""):
            return
        if self.current_submode == "Thư mục → ZIP":
            self.event_btn_cv_fz_convert()
        elif self.current_submode == "ZIP → Thư mục":
            self.event_btn_cv_zf_convert()
    
    def event_btn_cv_fz_convert(self):
        self.logger.log_and_status("Bắt đầu chuyển đổi...")
        level = 0
        if self.menu_cv_fz_compress_type.get() == "Deflate 5 (mặc định)":
            level = 5
        elif self.menu_cv_fz_compress_type.get() == "Deflate 8 (chậm, nhẹ)":
            level = 8
        
        # Run in a separate thread
        threading.Thread(target=self.formatter.format_to_zip, args=(level,)).start()
    
    def event_btn_cv_zf_convert(self):
        self.logger.log_and_status("Bắt đầu chuyển đổi...")

        # Run in a separate thread
        threading.Thread(target=self.formatter.format_to_folder).start()

    def event_check_cv_fz_update_incl(self):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: {"Không chứa" if self.check_cv_fz_inclinput.get() == 0 else "Chứa"} file input; {"Không chứa" if self.check_cv_fz_incloutput.get() == 0 else "Chứa"} file output!")
        self.event_btn_cv_check(verbose=False, compress_level_rcm=False)

    def event_entry_cv_fz_output_name(self, event):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: Tên bài đầu ra là '{self.entry_cv_fz_output_name.get()}'!")
        self.event_btn_cv_check(compress_level_rcm=False)
    
    def event_entry_cv_fz_update_ext(self, event):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: Đuôi file input/output là '{self.entry_cv_fz_input_ext.get()}'/'{self.entry_cv_fz_output_ext.get()}'!")
        self.event_btn_cv_check(verbose=False, compress_level_rcm=False)

    def event_menu_cv_fz_change_compress_type(self, new_compress_type: str):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: Kiểu nén mới là '{new_compress_type}'!")
    
    def event_entry_cv_fz_input_path(self, event):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: Folder test đầu vào là '{self.entry_cv_fz_input.get()}'!")
        self.event_btn_cv_check(compress_level_rcm=True)
    
    def event_entry_cv_fz_savedir(self, event):
        if(self.entry_cv_fz_input.get() == ""):
            return
        self.logger.log(f"Đã thay đổi lựa chọn: Folder lưu đầu ra là '{self.entry_cv_fz_savedir.get()}'!")
        self.event_btn_cv_check(compress_level_rcm=False)
    
    def event_but_sb_mode_convert(self):
        self.switch_operation_mode("convert")

    def event_but_sb_mode_crawl(self):
        self.switch_operation_mode("crawl")
    
    def event_btn_sb_folder_input(self):
        if str(self.entry_cv_fz_input.get()) == "":
            self.event_btn_cv_fz_inp_choose_dir()
        
        os.system('explorer.exe /select,' + self.entry_cv_fz_input.get().replace('/', '\\'))
        
    def event_btn_sb_folder_output(self):
        if str(self.entry_cv_fz_savedir.get()) == "":
            self.event_btn_cv_fz_savedir_choose_dir()
        
        os.system('explorer.exe ' + self.entry_cv_fz_savedir.get().replace('/', '\\'))
    
    def event_menu_sb_submode(self, new_submode: str):
        self.switch_submode(new_submode)

class Logger():
    def __init__(self, textbox: ctk.CTkTextbox, progbar_status: ctk.CTkProgressBar, statusbar: ctk.CTkLabel, percentage: ctk.CTkLabel):
        self.textbox = textbox
        self.progbar_status = progbar_status
        self.statusbar = statusbar
        self.percentage = percentage
        self.current_done_step = 0
        self.total_steps = 1

    def log(self, log_text: str):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", log_text + '\n')
        self.textbox.configure(state="disabled")

        # scroll to the bottom
        self.textbox.see("end")

    def clear_log(self):
        self.textbox.configure(state="normal")
        self.textbox.delete(1.0, "end")
        self.textbox.configure(state="disabled")

    queued_status_text = ""
    queued_status_info = ""
    queued_update_ui = False

    def status(self, status_text: str, type="info", force_update=True, resolve_queue=False):
        # if this call is for resolving the queue, update the status with the queued status
        status_text = status_text.strip().strip('\n')
        if resolve_queue:
            if len(self.queued_status_info) == 0:
                return
            status_text = self.queued_status_text
            type = self.queued_status_info
        
        # if the status is not important, and there is a queued status, update the status with the queued status
        if force_update == False:
            self.queued_status_text = status_text
            self.queued_status_info = type
            if self.queued_update_ui == False: # if there has not been a queued update, queue one
                self.queued_update_ui = True
                self.statusbar.after(200, lambda: self.status("", "", force_update=True, resolve_queue=True))
            else:
                return
        else: # this is an important status, clear the queue
            self.queued_status_text = ""
            self.queued_status_info = ""
            self.queued_update_ui = False
        
        # self.update_count += 1
        self.statusbar.configure(text=f"Trạng thái: {status_text}")
        if type == "info":
            self.statusbar.configure(text_color=("gray25", "gray70"))
        elif type == "ok":
            self.statusbar.configure(text_color=("darkgreen", "lightgreen"))
        elif type == "err":
            self.statusbar.configure(text_color=("darkred", "red"))
    
    def log_and_status(self, log_text: str, type="info"):
        self.log(log_text)
        self.status(log_text, type)
    
    def set_total_steps(self, total_steps: int):
        self.total_steps = total_steps
        self.progbar_status.set(0)
        self.percentage.configure(text="")
        self.current_done_step = 0

    queued_step = 0
    queued_update_ui_progbar = False

    def step(self, step = 1, force_update=True, resolve_queue=False, completed=False):
        new_step = step
        # if this call is for resolving the queue, update the status with the queued status
        if resolve_queue:
            new_step = 0
        
        # if the status is not important, and there is a queued status, update the status with the queued status
        if force_update == False:
            if self.queued_update_ui_progbar == False: # if there has not been a queued update, queue one
                self.queued_update_ui_progbar = True
                self.progbar_status.after(200, lambda: self.step(force_update=True, resolve_queue=True))
            else:
                self.queued_step += step
                return
        else: # this is an important status, clear the queue
            new_step += self.queued_step
            self.queued_step = 0
            self.queued_update_ui_progbar = False
        
        if new_step == 0:
            return

        self.current_done_step += new_step
        if completed:
            self.current_done_step = self.total_steps

        perc = min(1,self.current_done_step / self.total_steps)
        self.progbar_status.set(perc)
        self.percentage.configure(text=f"{int(perc * 100)}%")

if __name__ == "__main__":
    root = App()
    root.mainloop()