from datetime import datetime
import os
import zipfile
from gui import Logger

VERSION = "2.9.0"

class Formatter():
    def __init__(self, input_path, logger: Logger = None,
                 output_path_dir = os.path.join(os.getcwd(), "output", "formatter"),
                 gen_output_file_path = None, 
                 include_input_files = True, 
                 include_output_files = True, 
                 extension_input_files = "inp",
                 extension_output_files = "out",
                 problem_output_name = ""):

        self.input_path = input_path
        self.output_path_dir = output_path_dir
        self.gen_output_file_path = gen_output_file_path
        self.include_input_files = include_input_files
        self.include_output_files = include_output_files
        self.extension_input_files = extension_input_files.strip().lower()
        self.extension_output_files = extension_output_files.strip().lower()
        self.problem_output_name = problem_output_name.strip()
        self.problem_input_name = ""
        self.output_file_name = ""
        self.logger = logger
        self.can_execute = False
        self.sum_size = 0
        self.count_valid_folder = 0

        self.input_files = []
        self.output_files = []

        self.test_folders = {}

    def check_input_directory(self, verbose = True):
        # Themis type
        # Test structures: <input_path>/<test_subfolders>/problem_name.<extension_input>, problem_name.<extension_output>
        # Approach:
        # Find all files in the directory that have the extension <extension_input> and <extension_output>
        # Find the name of the problem by finding the common prefix of the files
        # Count the number of directory that has the exact structure as above, and also the data size in MB

        if not os.path.isdir(self.input_path):
            self.logger.log_and_status("Đường dẫn thư mục không hợp lệ!", "err")
            return (False, 0)

        self.input_files = []
        self.output_files = []

        filename_list = []
        
        # Find all files in the directory that have the extension <extension_input> and <extension_output>
        for root, dirs, files in os.walk(self.input_path):
            if root == self.input_path: # Skip the root directory, only check the subdirectories
                continue
            
            # name of the current directory
            folder_name = os.path.basename(root)

            # filter numbers in the folder name
            folder_name_number = ''.join(filter(str.isdigit, folder_name))
            if len(folder_name_number) > 0 and folder_name_number.isnumeric():
                folder_name = folder_name_number

            valid_folder = 0

            for file in files:
                filename_list.append(file)
                file_split = str(file).split('.')
                file_extension = (file_split[-1]).lower() if len(file_split) > 1 else None
                path_file = os.path.join(root,file)
                
                if file_extension == self.extension_input_files or (file_extension == None and self.extension_input_files == ""):
                    self.input_files.append((path_file, folder_name))
                    self.sum_size += os.path.getsize(path_file)
                    valid_folder = 1

                elif file_extension == self.extension_output_files  or (file_extension == None and self.extension_output_files == ""):
                    self.output_files.append((path_file, folder_name))
                    self.sum_size += os.path.getsize(path_file)
                    valid_folder = 1
                
            self.count_valid_folder += valid_folder

        # Find the name of the problem
        self.problem_input_name = os.path.commonprefix(filename_list).removeprefix("\\").removesuffix(".")
        if self.problem_output_name == "":
            self.problem_output_name = self.problem_input_name
        
        self.output_file_name = self.problem_output_name + "_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".zip"

        self.output_path = os.path.join(self.output_path_dir, self.output_file_name)

        sum_size_mb = round(self.sum_size / 1024 / 1024, 3)
        
        if verbose:
            self.logger.log("===== TỔNG QUAN =====")
            self.logger.log(f"Folder test đầu vào: {self.input_path}")
            self.logger.log(f"Tên bài đầu ra: {self.problem_output_name}")
            self.logger.log(f"File ZIP đầu ra: {self.output_file_name}")
            self.logger.log(f"Số thư mục hợp lệ: {self.count_valid_folder} thư mục")
            self.logger.log(f"Số file đã phát hiện: {len(self.input_files)} file input, {len(self.output_files)} file output")
            self.logger.log(f"Tổng dung lượng: {sum_size_mb} MB")

        if self.problem_output_name == "":
            self.logger.log_and_status("Không nhận dạng được tên bài!", "err")
            self.logger.log("Vui lòng kiểm tra lại tên bài đầu ra hoặc cấu trúc thư mục!\n")
            self.can_execute = False
            return (False, 0)

        if self.count_valid_folder == 0:
            self.logger.log_and_status("Cấu trúc thư mục không hợp lệ!", "err")
            self.logger.log("Vui lòng kiểm tra lại cấu trúc thư mục!\n")
            self.can_execute = False
            return (False, 0)
        if len(self.input_files) == 0 and len(self.output_files) == 0:
            self.logger.log_and_status("Không phát hiện file input và output!", "err")
            self.logger.log("Vui lòng kiểm tra lại đuôi file hoặc cấu trúc thư mục!\n")
            self.can_execute = False
            return (False, 0)
        
        if len(self.input_files) != len(self.output_files) or len(self.input_files) != self.count_valid_folder or len(self.output_files) != self.count_valid_folder:
            self.logger.log("Lưu ý: Số lượng file input, output và số lượng test đang không trùng khớp.")

        # recommend compression level
        if sum_size_mb < 4:
            level = 0
        elif sum_size_mb < 40:
            level = 5
        else:
            self.logger.log("Lưu ý: Dung lượng lớn hơn 40 MB, nên xem xét giảm kích cỡ bộ test. Khuyến nghị nén ở mức 8.")
            level = 8
        
        self.logger.log_and_status("Không phát hiện lỗi. Nhấn 'Thực thi' để thực hiện chuyển đổi!\n", "ok")
        self.can_execute = True
        self.logger.set_total_steps(self.sum_size)
        return (True, level)

    def format_to_zip(self, level = 0):
        if not self.can_execute:
            return False
        
        # create output directory if not exist
        try:
            os.makedirs(self.output_path_dir, exist_ok=True)
        except FileExistsError:
            pass

        self.logger.log("===== THỰC THI =====")
        self.logger.log_and_status("Đang tạo file ZIP...")
        zip_object = zipfile.ZipFile(self.output_path, 'w')
        if self.include_input_files:
            for cnt, (path_file, folder_name) in enumerate(self.input_files):
                output_zip_file_name = self.problem_output_name + "." + folder_name + ".inp"
                self.logger.status(f"[{cnt+1}/{len(self.input_files)}] Đang xử lý: ${output_zip_file_name}", type="info", force_update=False)
                zip_object.write(path_file, output_zip_file_name, zipfile.ZIP_DEFLATED, level)
                self.logger.step(step=os.path.getsize(path_file), force_update=False)
        if self.include_output_files:
            for cnt, (path_file, folder_name) in enumerate(self.output_files):
                output_zip_file_name = self.problem_output_name + "." + folder_name + ".out"
                self.logger.status(f"[{cnt+1}/{len(self.output_files)}] Đang xử lý: ${output_zip_file_name}", type="info", force_update=False)
                zip_object.write(path_file, output_zip_file_name, zipfile.ZIP_DEFLATED, level)
                self.logger.step(step=os.path.getsize(path_file), force_update=False)
        
        comment = f"Accepted! From Loli with love <3||{VERSION}||{self.problem_output_name}||{self.count_valid_folder}||{self.extension_input_files}||{self.extension_output_files}||{len(self.input_files)}||{len(self.output_files)}"
        zip_object.comment = bytes(comment, 'utf-8')
        zip_object.close()
        self.logger.log_and_status(f"Xử lý thành công {self.count_valid_folder} test vào file ZIP!", "ok")
        self.logger.log(f"File ZIP được lưu tại: {self.output_path}")
        self.logger.log(f"Dung lượng: {round(os.path.getsize(self.output_path) / 1024 / 1024, 3)} MB")
        self.logger.step(step = 0.001)

    def check_input_zip_file(self, verbose = True):

        if not os.path.isfile(self.input_path) or not self.input_path.endswith(".zip"):
            self.logger.log_and_status("Đường dẫn file ZIP không hợp lệ!", "err")
            return False

        self.test_folders = {}

        zip_object = zipfile.ZipFile(self.input_path, 'r')
        
        filename_zip = os.path.basename(self.input_path)
        # get file list
        filename_list = sorted(zip_object.namelist())

        # get comment
        comment = zip_object.comment.decode('utf-8')

        zip_object.close()

        # Parse comment
        found_format = False
        recount_tests = True

        # 3.0+ format
        comment_split = comment.split("||")
        if not found_format and comment_split[0] == "Accepted! From Loli with love <3" and len(comment_split) == 8:
            found_format = True
            self.zip_version = comment_split[1]
            self.problem_input_name = comment_split[2]
            self.count_valid_folder = int(comment_split[3])
            self.extension_input_files = comment_split[4]
            self.extension_output_files = comment_split[5]
            self.count_input_files = int(comment_split[6])
            self.count_output_files = int(comment_split[7])

        # 2.0+ format
        comment_split = comment.split("+-23412vdvdw+")
        if not found_format and comment_split[0] == "LOLICONVERTER" and len(comment_split) == 6:
            found_format = True
            self.zip_version = comment_split[1]
            self.problem_input_name = comment_split[2]
            self.count_valid_folder = int(comment_split[3])
            self.extension_input_files = comment_split[4]
            self.extension_output_files = comment_split[5]
        
        # 1.1 format
        name_split = filename_zip.split("_")

        # also check for last 2 parts, it has to be date and time in the format of %d-%m-%Y_%H-%M-%S
        if not found_format and len(name_split) == 3 and len(name_split[1]) == 10 and len(name_split[2]) == 8:
            found_format = True
            self.zip_version = "1.1"
            self.problem_input_name = name_split[0]
            self.extension_input_files = "inp"
            self.extension_output_files = "out"
        
        # Codeforces format
        if not found_format:
            invalid_format = False
            for filename in filename_list:
                filename_split = filename.split(".")
                if len(filename_split) == 2 and filename_split[1] == "a":
                    self.count_output_files += 1
                    self.test_folders.update({filename_split[0]: {}})
                    self.test_folders[filename_split[0]].update({"o": filename})
                elif len(filename_split) == 1:
                    self.count_input_files += 1
                    self.test_folders[filename_split[0]].update({"i": filename})
                else:
                    invalid_format = True
                    break
            if not invalid_format and self.count_input_files + self.count_output_files > 0:
                found_format = True
                self.zip_version = "Codeforces"
                self.problem_input_name = "Unknown" + datetime.now().strftime("%d%m%y%H%M%S")
                self.extension_input_files = "inp"
                self.extension_output_files = "out"
                self.count_valid_folder = len(self.test_folders)
                recount_tests = False
        
        if not found_format:
            self.logger.log_and_status("Không nhận dạng được định dạng file ZIP!", "err")
            self.logger.log("Vui lòng kiểm tra lại file ZIP!\n")
            return False
            
        # calculate the number of input and output files
        if recount_tests:
            self.count_input_files = 0
            self.count_output_files = 0

            # set of test folder name
            test_folder_set = set()
            for filename in filename_list:
                filename_split = filename.split(".")
                if len(filename_split) == 3 and filename_split[0] == self.problem_input_name:
                    test_folder_set.add(filename_split[1])
                    self.test_folders.update({filename_split[1]: {}})
                    if filename_split[2] == self.extension_input_files or filename_split[2] == "inp":
                        self.count_input_files += 1
                        self.test_folders[filename_split[1]].update({"i": filename})
                    elif filename_split[2] == self.extension_output_files or filename_split[2] == "out":
                        self.count_output_files += 1
                        self.test_folders[filename_split[1]].update({"o": filename})

        if self.count_input_files == 0 and self.count_output_files == 0:
            self.logger.log_and_status("Không phát hiện file input và output!", "err")
            self.logger.log("Vui lòng kiểm tra lại file ZIP!\n")
            return False
        
        if verbose:
            self.logger.log("===== TỔNG QUAN =====")
            self.logger.log(f"File ZIP đầu vào: {self.input_path}")
            self.logger.log(f"Định dạng file ZIP: {self.zip_version}")
        
        if self.problem_output_name == "":
            self.problem_output_name = self.problem_input_name
            if self.zip_version == "Codeforces":
                self.logger.log("Lưu ý: File ZIP này có thể có định dạng Codeforces/IOI, cần bổ sung thêm tên bài đầu ra.")
    
        if verbose:
            self.logger.log(f"Tên bài đầu ra: {self.problem_output_name}")
            self.logger.log(f"Đuôi file input/output đầu ra: {self.extension_input_files}/{self.extension_output_files}")
            self.logger.log(f"Số test hợp lệ: {self.count_valid_folder} test")
            self.logger.log(f"Số file đã phát hiện: {self.count_input_files} file input, {self.count_output_files} file output")
            self.logger.log(f"Dung lượng: {round(os.path.getsize(self.input_path) / 1024 / 1024, 3)} MB")
    
        if self.count_valid_folder > 0 and len(test_folder_set) != self.count_valid_folder:
            self.logger.log("Lưu ý: Số lượng thư mục test dò được và số lượng test đã lưu không trùng khớp.")
        self.count_valid_folder = len(test_folder_set)

        if self.count_input_files != self.count_output_files or self.count_input_files != self.count_valid_folder or self.count_output_files != self.count_valid_folder:
                self.logger.log("Lưu ý: Số lượng file input, output và số lượng test đang không trùng khớp.")
        
        self.logger.log_and_status("Không phát hiện lỗi. Nhấn 'Thực thi' để thực hiện chuyển đổi!\n", "ok")
        self.can_execute = True
        self.logger.set_total_steps(self.sum_size)
        return True
    
    def format_to_folder(self, level = 0):
        pass

if __name__ == "__main__":
    # Formatter("").check_input_directory()
    pass