import json
import os
import re
import traceback
import requests
import markdown
import markdownify
import markdown2latex.mdx_latex as MDXLatex
import warnings
import unicodedata
from gui import Logger

SPECIAL_CHAR_BULLET = "―"
LATEX_HEADER = """
\\documentclass[12pt,a4paper]{article}
\\usepackage[utf8]{vietnam}
\\usepackage[pdftex]{graphicx}
\\usepackage{tabularx}
\\usepackage{array}
\\usepackage{color}
\\usepackage{geometry}
\\usepackage{listings}
\\usepackage{sectsty}
\\usepackage{fancyhdr}
\\usepackage{enumitem}
\\usepackage[dvipsnames]{xcolor}	
\\usepackage{hyperref}
\\usepackage{amsmath}

\\geometry{a4paper,total={170mm,257mm},left=20mm,top=20mm,}
\\allsectionsfont{\\normalfont\\sffamily\\bfseries}

\\setlength{\\parskip}{.25em}
\\setlist[itemize]{topsep=0ex, itemsep=0.05ex}
\\begin{document}

"""

TESTCASE_INDICATOR_LIST = ["Sample", "Example", "Test", "Testcase", "Case", "Input", "Ví dụ", "Dữ liệu vào"]

DMOJ_INDICATOR_LIST = """
dmoj.ca
cyboj.ddns.net
oj.qnoi.info
oj.vnoi.info
tinhoctre.vn
coder.husc.edu.vn
oj.chuyenhalong.edu.vn
dmoj.ctu.edu.vn
hnoj.edu.vn
chvoj.edu.vn
oj.giftedbat.edu.vn
claoj.edu.vn
laptrinhonline.club
ptnkoj.com
laptrinh.ictu.edu.vn
oj.lequydon.net
oj.thptchuyenhatinh.edu.vn
sqrtoj.edu.vn
oj.vku.udn.vn
oj.eiu.edu.vn
"""

LQDOJ_INDICATOR_LIST = """
lqdoj.edu.vn
tleoj.edu.vn
nbk.homes
ltoj.edu.vn
quangtrioj.edu.vn
"""

INSTRUCT_USING_MANUAL_VI = """
Không thể chuyển đổi bài toán. Tuy nhiên có thể thử sử dụng phương pháp Thủ công:

1. Truy cập vào trang web cần chuyển đổi.
2. Nhấn Ctrl + U.
3. Nhấn Ctrl + A (chọn tất cả), và nhấn Ctrl + C (sao chép).
4. Dán nội dung đã copy vào cửa sổ Notepad (chuột phải > Dán hoặc Ctrl + V).
5. Lưu file và đóng cửa sổ Notepad. Chương trình sẽ tiếp tục.
"""

class Crawler():
    def __init__(self, url: str, logger: Logger = Logger(), 
                 output_path_dir = os.path.join(os.getcwd(), "output", "crawler"),
                 problem_site_type = None):
        
        self.url = url
        self.logger = logger
        self.output_path_dir = output_path_dir
        self.problem_site_type = problem_site_type

        self.output_problem_path_dir = str()
        self.html_response = str()
        self.problem = dict()
        self.problem_folder_name = str()
        self.result_latex_general = ""
        self.result_latex_polygon = ""
        self.result_latex_template = ""
        self.result_md_dmoj = ""
        self.result_md_general = ""
        self.result_quick_copy_md_dmoj = ""
        self.result_quick_copy_latex_polygon = ""
        self.result_quick_copy_example_text = ""
        self.result_quick_copy_example_md = ""


    def os_create_folder(self, folder_dir: str):
        """Create a folder with the given name if it does not exist."""
        try:
            os.makedirs(folder_dir, exist_ok=True)
            return True
        except FileExistsError:
            return False

    def get_base_problem_dmoj(self):
        """Return and extract the raw problem content from a DMOJ-themed site."""

        # Problem code is the part after the '/problem/' in the URL
        problem_code = self.url.split("/problem/")[1]

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        # Problem site is the part before the '/problem/' in the URL
        problem_site = self.url.split("/problem/")[0]
        problem_site = problem_site.split("://")[1]

        if self.html_response == str():
            response = requests.get(self.url)
            if(response.status_code != 200):
                self.logger.log_and_status("[DMOJ] Không thể cào bài từ trang đã cho!", "err")
                raise Exception("Failed to get problem from DMOJ-themed site")
            self.html_response = response.text

        # Extract the problem content from the response
        
        # SPECIAL CASE: claoj.edu.vn
        if "claoj.edu.vn" in problem_site:
            self.html_response = self.html_response.split('<div id="content-left" class="split-common-content">')
        else:
            self.html_response = self.html_response.split('<iframe name="raw_problem" id="raw_problem"></iframe>')
        
        if len(self.html_response) == 1:
            self.logger.log("[DMOJ] Không thể phân chia rõ ràng nội dung đã cào, sẽ sử dụng toàn bộ nội dung.")
            
        # First half is the problem details
        html_problem_details = self.html_response[0]

        # Extract the problem title, info entries, types, allowed langs, and content
        problem_title = html_problem_details.split('<h2 ')[1].split('</h2>')[0].split('>')[1].strip()
        html_problem_info_entries = html_problem_details.split('<div class="problem-info-entry">')[1:]

        problem_info_entries = {}
        for entry in html_problem_info_entries:
            entry = entry.split('</div>')[0]
            entry_name = entry.split('pi-name">')[1].split(':</span>')[0].strip().lower()
            entry_value = entry.split('-value">')[1]

            if(entry_value.find('</span>') != -1):
                entry_value = entry_value.split('</span>')[0].strip()
            elif(entry_value.find('</div>') != -1):
                entry_value = entry_value.split('</div>')[0].strip()

            # Remove all HTML tags in the entry value
            entry_value = re.sub(r'<[^>]*>', '', entry_value).strip("\n")
            problem_info_entries[entry_name] = entry_value

        problem_types = []
        try:
            html_problem_types = html_problem_details.split('<div id="problem-types">')[1]
            html_problem_types = html_problem_types.split('class="toggled">')[1]
            html_problem_types = html_problem_types.split('</div>')[0]

            problem_types = html_problem_types.split(',')
            problem_types = [problem_type.strip() for problem_type in problem_types]
        except:
            self.logger.log("[DMOJ] Không tìm được phân loại bài toán.")
            pass

        problem_allowed_langs = []
        try:
            html_problem_allowed_langs = html_problem_details.split('<div id="allowed-langs">')[1]
            html_problem_allowed_langs = html_problem_allowed_langs.split('class="toggled">')[1]
            html_problem_allowed_langs = html_problem_allowed_langs.split('</div>')[0]

            problem_allowed_langs = html_problem_allowed_langs.split(',')
            problem_allowed_langs = [lang for lang in problem_allowed_langs if lang.find('<s title="') == -1]
            problem_allowed_langs = [lang.strip() for lang in problem_allowed_langs]
        except:
            self.logger.log("[DMOJ] Không tìm được danh sách ngôn ngữ cho phép.")
            pass

        # Second half is the problem content using the last part of the split
        html_problem_content = self.html_response[-1].split('src="/static/mathjax_config.js"></script>')[0]
        
        # Alternative method to extract the problem content
        if len(self.html_response) == 1:
            html_problem_content = '<div id="' + html_problem_content.split('<div id="')[-2].strip().strip("\n")
        else:
            html_problem_content = html_problem_content.split('<hr>\n')[0].strip().strip("\n")
        
        self.logger.status("[DMOJ] Đã cào nội dung đề bài thành công!", "info", False)

        details = f"===== NỘI DUNG CHI TIẾT =====\n"
        details += f"[DMOJ] URL: {self.url}\n"
        details += f"[DMOJ] Loại trang: DMOJ\n"
        details += f"[DMOJ] Địa chỉ trang: {problem_site}\n"
        details += f"[DMOJ] Mã đề bài: {problem_code}\n"
        details += f"[DMOJ] Tên đề bài: {problem_title}\n"
        details += f"[DMOJ] Thông tin chi tiết: {problem_info_entries}\n"
        details += f"[DMOJ] Ngôn ngữ cho phép: {problem_allowed_langs}\n"
        details += f"[DMOJ] Phân loại bài toán: {problem_types}\n"

        self.logger.log(details)

        self.problem = {
            "problem_site_type": "DMOJ",
            "problem_url": self.url,
            "problem_site": problem_site,
            "problem_code": problem_code,
            "problem_title": problem_title,
            "problem_info_entries": problem_info_entries,
            "problem_types": problem_types,
            "problem_allowed_langs": problem_allowed_langs,
            "problem_content_raw": html_problem_content
        }

        return self.problem

    def get_base_problem_lqdoj(self):
        """Return and extract the raw problem content from LQDOJ - a strange af DMOJ-themed site"""

        # Problem code is the part after the '/problem/' in the URL
        problem_code = self.url.split("/problem/")[1]

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        # Problem site is the part before the '/problem/' in the URL
        problem_site = self.url.split("/problem/")[0]
        problem_site = problem_site.split("://")[1]

        if self.html_response == str():
            response = requests.get(self.url)
            if(response.status_code != 200):
                self.logger.log_and_status("[LQDOJ] Không thể cào bài từ trang đã cho!", "err")
                raise Exception("Failed to get problem from LQDOJ")
            self.html_response = response.text

        # Extract the problem content from the response
        # SPECIAL CASE: nbk.homes
        if "nbk.homes" in problem_site:
            self.html_response = self.html_response.split('<div id="content-left" class="split-common-content">')
        else:
            self.html_response = self.html_response.split('<div class="md-typeset')
        
        # First half is the problem details
        html_problem_details = self.html_response[0]

        # Extract the problem title, info entries, types, allowed langs, and content
        problem_title = html_problem_details.split('<h2 ')[1].split('</h2>')[0].split('>')[1].strip()
        html_problem_info_entries = html_problem_details.split('<hr style="padding-top: ')[1].split('problem-info d-flex-problem">')[-1].split('<i class="fa fa-')[1:]
        
        problem_info_entries = {}
        for entry in html_problem_info_entries:
            entry_name = entry.split('pi-name">')[-1].split(':</span>')[0].strip().lower()
            entry_value = entry.split('-value">')[-1]

            if(entry_value.find('</span>') != -1):
                entry_value = entry_value.split('</span>')[0].strip()
            elif(entry_value.find('</div>') != -1):
                entry_value = entry_value.split('</div>')[0].strip()

            # Remove all HTML tags in the entry value
            entry_value = re.sub(r'<[^>]*>', '', entry_value).strip("\n")
            problem_info_entries[entry_name] = entry_value

        html_problem_types = html_problem_details.split('<div id="problem-types">')[1]
        html_problem_types = html_problem_types.split('class="toggled">')[1]
        html_problem_types = html_problem_types.split('</div>')[0]

        problem_types = html_problem_types.split(',')
        problem_types = [problem_type.strip() for problem_type in problem_types]

        # Second half is the problem content
        if(len(self.html_response) == 1):
            html_problem_content = self.html_response[-1]
        else:
            html_problem_content = self.html_response[1]
        html_problem_content = html_problem_content.split('<div id="comment-section">')[0]
        html_problem_content = "<div>\n" + html_problem_content.split('<hr>\n')[0].split('">',1)[-1].strip().strip("\n")

        # Uses <h4> tag instead of <summary>, and </h4> instead of </summary> using regex
        html_problem_content = re.sub(r'<summary>(.+?)</summary>', r'<h4>\1</h4>', html_problem_content)

        # Replace the math/tex script if exists
        html_problem_content = re.sub(r'<script type="math/tex">(.+?)</script>', r'\(\1\)', html_problem_content)

        # Nuke the mathjax script preview
        html_problem_content = re.sub(r'<span class="MathJax_Preview">(.+?)</span>', r'', html_problem_content)

        self.logger.status("[LQDOJ] Đã cào nội dung đề bài thành công!", "info", False)

        details = f"===== NỘI DUNG CHI TIẾT =====\n"
        details += f"[LQDOJ] URL: {self.url}\n"
        details += f"[LQDOJ] Loại trang: LQDOJ\n"
        details += f"[LQDOJ] Địa chỉ trang: {problem_site}\n"
        details += f"[LQDOJ] Mã đề bài: {problem_code}\n"
        details += f"[LQDOJ] Tên đề bài: {problem_title}\n"
        details += f"[LQDOJ] Thông tin chi tiết: {problem_info_entries}\n"
        details += f"[LQDOJ] Phân loại bài toán: {problem_types}\n"

        self.logger.log(details)

        self.problem = {
            "problem_site_type": "LQDOJ",
            "problem_url": self.url,
            "problem_site": problem_site,
            "problem_code": problem_code,
            "problem_title": problem_title,
            "problem_info_entries": problem_info_entries,
            "problem_types": problem_types,
            "problem_content_raw": html_problem_content
        }

        return self.problem

    def get_base_problem_csloj(self):
        """Return and extract the raw problem content from CSLOJ."""

        # Problem code is the part after the '/problem/' in the URL
        problem_code = self.url.split("/problem/")[1]

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        # Problem site is the part before the '/problem/' in the URL
        problem_site = self.url.split("/problem/")[0]
        problem_site = problem_site.split("://")[1]

        if self.html_response == str():
            response = requests.get(self.url)
            if(response.status_code != 200):
                self.logger.log_and_status("[CSLOJ] Không thể cào bài từ trang đã cho!", "err")
                raise Exception("Failed to get problem from CSLOJ")
            self.html_response = response.text

        # Extract the problem content from the response
        self.html_response = self.html_response.split('<div class="ui grid">')

        # First half is the problem details
        html_problem_details = self.html_response[0]

        # Extract the problem title, info entries, types, allowed langs, and content
        problem_title = html_problem_details.split('<h1 ')[1].split('</h1>')[0].split('>')[1].strip()
        problem_title = problem_title.replace("–", "-")
        html_problem_info_entries = html_problem_details.split('<span class="ui label">')[1:]
        
        problem_info_entries = {}
        for entry in html_problem_info_entries:
            entry = entry.split('</span>')[0]
            if (entry == "Nhập/xuất từ luồng chuẩn"):
                problem_info_entries["input"] = "stdin"
                problem_info_entries["output"] = "stdout"
                continue
            
            entry_name = entry.split(': ')[0].strip().lower()
            entry_value = entry.split(': ')[1].strip()

            # Remove all HTML tags in the entry value
            entry_value = re.sub(r'<[^>]*>', '', entry_value).strip("\n")
            problem_info_entries[entry_name] = entry_value

        html_problem_types = self.html_response[1].split('<h3 class="ui top attached block header">Đề bài</h3>')[1].split('<div class="row">')[1]
        html_problem_types = html_problem_types.split(' label">')[1:]

        problem_types = [problem_type.split("</a>")[0].strip().strip('\n') for problem_type in html_problem_types]

        # Special tag: ***** one that indicate the difficulty of the problem
        for prob_type in problem_types:
            rating = prob_type.count("⭐")
            if rating > 0:
                problem_types.remove(prob_type)
                problem_info_entries["độ khó"] = str(rating) + "/5 sao"
        
        # Second half is the problem content
        html_problem_content = self.html_response[1].split('<h3 class="ui top attached block header">Đề bài</h3>')[1]
        html_problem_content = html_problem_content.split('<div class="row">')[0].strip().strip("\n")

        # Nuke the mathjax script preview
        html_problem_content = re.sub(r'<span class="mjpage"><svg xmlns((.|\n)+?)<title id="MathJax(.+?)">(.+?)</title>((.|\n)+?)</svg></span>', r'\(\4\)', html_problem_content, count = 0, flags=re.MULTILINE | re.DOTALL)

        self.logger.status("[CSLOJ] Đã cào nội dung đề bài thành công!", "info", False)

        details = f"===== NỘI DUNG CHI TIẾT =====\n"
        details += f"[CSLOJ] URL: {self.url}\n"
        details += f"[CSLOJ] Loại trang: CSLOJ\n"
        details += f"[CSLOJ] Địa chỉ trang: {problem_site}\n"
        details += f"[CSLOJ] Mã đề bài: {problem_code}\n"
        details += f"[CSLOJ] Tên đề bài: {problem_title}\n"
        details += f"[CSLOJ] Thông tin chi tiết: {problem_info_entries}\n"
        details += f"[CSLOJ] Phân loại bài toán: {problem_types}\n"

        self.logger.log(details)

        self.problem = {
            "problem_site_type": "CSLOJ",
            "problem_url": self.url,
            "problem_site": problem_site,
            "problem_code": problem_code,
            "problem_title": problem_title,
            "problem_info_entries": problem_info_entries,
            "problem_types": problem_types,
            "problem_content_raw": html_problem_content
        }

        return self.problem

    def get_base_problem_codeforces(self):
        """Return and extract the raw problem content from a Codeforces site."""

        # Convert problemset type URL to contest type URL using regex
        # https://codeforces.com/problemset/problem/75/C -> https://codeforces.com/contest/75/problem/C
        if "/problemset/problem/" in self.url:
            self.url = re.sub(r'\/problemset\/problem\/(\d+)(\/[A-Z0-9]+)', r'/contest/\1/problem\2', self.url)

        problem_site_type = "Codeforces"

        # URL type classification
        if ".contest.codeforces.com" in self.url:
            codeforces_url_type = "contest"
            problem_site_type = "CodeforcesCD"
        elif "/gym/" in self.url:
            codeforces_url_type = "gym"
        else:
            codeforces_url_type = "contest"
        
        # Problem code is the part after the '/problem/' in the URL
        if codeforces_url_type == "gym":
            problem_contest_id = self.url.split("/gym/")[1].split("/problem/")[0]
        elif codeforces_url_type == "contest":
            problem_contest_id = self.url.split("/contest/")[1].split("/problem/")[0]

        # Problem order id is the part after the '/problem/' in the URL
        problem_order_id = self.url.split("/problem/")[1]

        # Problem code = Contest ID + Problem Order ID
        problem_code = problem_contest_id + problem_order_id

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        # Problem site is the part from the ".com" back to the first "/"
        problem_site = self.url.split(".com")[0] + ".com"
        problem_site = problem_site.split("://")[1]

        if self.html_response == str():
            response = requests.get(self.url)
            if(response.status_code != 200):
                self.logger.log_and_status("[Codeforces] Không thể cào bài từ trang đã cho!", "err")
                raise Exception("Failed to get problem from Codeforces site")
            self.html_response = response.text

        # Extract contest name
        html_sideboxes = self.html_response.split('<div class="roundbox sidebox borderTopRound " style="">')[1:]
        problem_contest_name = ""

        for sidebox in html_sideboxes:
            try:
                sidebox = sidebox.split('</div>')[0]
                if codeforces_url_type == "gym":
                    if sidebox.find('/gym/') == -1:
                        continue
                    problem_contest_name = sidebox.split('</a></th>')[0].split("/gym/")[1].split("\">")[1].strip()
                    break

                elif codeforces_url_type == "contest":
                    if sidebox.find('/contest/') == -1:
                        continue
                    problem_contest_name = sidebox.split('</a></th>')[0].split("/contest/")[1].split("\">")[1].strip()
                    break
            except:
                continue

        # Extract the problem tags from the response
        problem_types = []
        try:
            html_problem_types = self.html_response.split('<div class="caption titled">&rarr; Problem tags')[1].split('<form id="addTagForm"')[0]

            problem_types_unfi = html_problem_types.split('<span class="tag-box"')[1:]

            for problem_type in problem_types_unfi:
                problem_type = problem_type.split('">')[1].split('</span>')[0].strip().strip("\n")
                problem_types.append(problem_type)
        except:
            self.logger.log("[Codeforces] Không tìm được phân loại bài toán.")
            pass

        # Cut the response to the part that starts the problem
        self.html_response = self.html_response.split('<div class="problem-statement">')[1]

        # Extract the problem content from the response
        self.html_response = self.html_response.split('</div></div><div>', 1)
        
        # Alternative method to extract the problem content
        if len(self.html_response) == 1:
            self.html_response = self.html_response[0].split('<div class="output-file output-standard">')
            self.html_response[0] += self.html_response[1].split('<div>',1)[0]
            self.html_response[1] = self.html_response[1].split('<div>',1)[1]

        # First half is the problem details
        html_problem_details = self.html_response[0]

        # Extract the problem title, info entries, types, allowed langs, and content
        problem_title = html_problem_details.split('<div class="title">')[1].split('</div>')[0].strip()
        html_problem_info_entries = html_problem_details.split('<div class="property-title">')[1:]

        problem_info_entries = {}
        for entry in html_problem_info_entries:
            entry = entry.split('<div class="')[0].split('</div>')
            entry_name = entry[0].strip().lower()
            entry_value = entry[1].strip()

            # Remove all HTML tags in the entry value
            entry_value = re.sub(r'<[^>]*>', '', entry_value)
            problem_info_entries[entry_name] = entry_value

        # Second half is the problem content
        html_problem_content = self.html_response[1].split('<script')[0]
        html_problem_content = "<div>" + html_problem_content.strip().strip("\n")

        # Uses <h4> tag instead of <div class=\"section-title\">, and </h4> instead of </div> using regex
        html_problem_content = re.sub(r'<div class="section-title">(.+?)</div>', r'<h4>\1</h4>', html_problem_content)
        
        # Try to replace as much old tex-span style with the new format as possible
        html_problem_content = re.sub(r'<span class="tex-span">(.+?)</span>', r'$$$\1$$$', html_problem_content)

        # Try to replace as much old tex-inline style with the new format as possible
        # First group is the number of dollar signs, second group is the content
        math_functions = re.findall(r'(\${1,3})((?:(?!\1)[\s\S])*)\1', html_problem_content, re.DOTALL)
        
        for i, math_func_need in enumerate(math_functions):
            math_func_need_str = str(math_func_need[0]) + str(math_func_need[1]) + str(math_func_need[0]) # The entire math function
            math_func_str = math_func_need_str.replace('<i>', '').replace('</i>', '') # The math function without <i> tags
            math_func_str = math_func_str.replace('<sup class="upper-index">', '^{').replace('</sup>', '}') # Replace upper index
            math_func_str = math_func_str.replace('<sub class="upper-index">', '^{').replace('</sub>', '}') # Replace upper index
            math_func_str = math_func_str.replace('<sup class="lower-index">', '_{').replace('</sup>', '}') # Replace lower index
            math_func_str = math_func_str.replace('<sub class="lower-index">', '_{').replace('</sub>', '}') # Replace lower index
            html_problem_content = html_problem_content.replace(math_func_need_str, math_func_str, 1)
        

        self.logger.status("[Codeforces] Đã cào nội dung đề bài thành công!", "info", False)

        details = f"===== NỘI DUNG CHI TIẾT =====\n"
        details += f"[Codeforces] URL: {self.url}\n"
        details += f"[Codeforces] Loại trang: Codeforces\n"
        details += f"[Codeforces] Địa chỉ trang: {problem_site}\n"
        details += f"[Codeforces] Mã đề bài: {problem_code}\n"
        details += f"[Codeforces] Mã cuộc thi: {problem_contest_id}\n"
        details += f"[Codeforces] Tên cuộc thi: {problem_contest_name}\n"
        details += f"[Codeforces] Thứ tự bài: {problem_order_id}\n"
        details += f"[Codeforces] Tên đề bài: {problem_title}\n"
        details += f"[Codeforces] Thông tin chi tiết: {problem_info_entries}\n"
        details += f"[Codeforces] Phân loại bài toán: {problem_types}\n"

        self.logger.log(details)

        self.problem = {
            "problem_site_type": problem_site_type,
            "problem_url": self.url,
            "problem_site": problem_site,
            "problem_code": problem_code,
            "problem_contest_id": problem_contest_id,
            "problem_contest_name": problem_contest_name,
            "problem_order_id": problem_order_id,
            "problem_title": problem_title,
            "problem_info_entries": problem_info_entries,
            "problem_types": problem_types,
            "problem_content_raw": html_problem_content
        }

        return self.problem

    def get_files(self):
        """Return the list of files embedded in the problem content."""

        problem_content = str(self.problem["problem_content_raw"])
        problem_site = self.problem["problem_site"]
        
        # Extract the files from the problem content
        files = []
        if self.problem_site_type == "DMOJ":
            files = re.findall(r'\/martor(.+?)"', problem_content)
        elif self.problem_site_type == "LQDOJ":
            files = re.findall(r'\/media/pagedown-uploads(.+?)"', problem_content)
        elif self.problem_site_type == "Codeforces":
            files = re.findall(r'\/espresso.codeforces.com(.+?)"', problem_content)
        elif self.problem_site_type == "CodeforcesCD":
            files = re.findall(r'\/espresso(.+?)"', problem_content)
        elif self.problem_site_type == "CSLOJ":
            files = re.findall(r'\/images/problems(.+?)"', problem_content)

        # Remove the duplicates
        files = list(set(files))

        # Remove empty strings
        files = [file for file in files if file != ""]

        # Download the files
        for i, file in enumerate(files):
            self.logger.status(f"[{self.problem_site_type}] Đang tải tệp tin {file}... ({i + 1}/{len(files)})", "info", False)
            
            response = None
            # SPECIAL CASE: oj.lequydon.net
            if "oj.lequydon.net" in problem_site:
                response = requests.get(f"https://{problem_site}/media/martor/{file}")
            elif self.problem_site_type == "DMOJ":
                response = requests.get(f"https://{problem_site}/martor/{file}")
            elif self.problem_site_type == "LQDOJ":
                response = requests.get(f"https://{problem_site}/media/pagedown-uploads/{file}")
            elif self.problem_site_type == "CodeforcesCD":
                response = requests.get(f"https://{problem_site}/espresso/{file}")
            elif self.problem_site_type == "Codeforces":
                response = requests.get(f"https://espresso.codeforces.com/{file}")
            elif self.problem_site_type == "CSLOJ":
                response = requests.get(f"http://{problem_site}/images/problems/{file}")
            
            if(response.status_code != 200):
                self.logger.log_and_status(f"[{self.problem_site_type}] Không thể tải tệp tin {file} do bị chặn. Vui lòng tải tệp này thủ công.", "err", False)
                if (response.status_code > 400):
                    continue
                else:
                    raise Exception(f"[{self.problem_site_type}] Failed to get file {file} from the site!")

            # Save the file
            with open(os.path.join(self.output_problem_path_dir, str(file).split("/")[-1]), "wb") as f:
                f.write(response.content)
            
            self.logger.step(step=20/len(files), force_update=False)

        if len(files) > 0:
            self.logger.log_and_status(f"[{self.problem_site_type}] Đã tải về {len(files)} file!", "info")
        else:
            self.logger.step(step=20, force_update=False)

        # Imgur files
        external_files = re.findall(r'\/i.imgur.com(.+?)"', problem_content)
        external_files = list(set(external_files))
        external_files = [file for file in external_files if file != ""]

        for i, file in enumerate(external_files):
            self.logger.status(f"[External-Imgur] Đang tải tệp tin đính ngoài {file}... ({i + 1}/{len(external_files)})", "info", False)

            response = requests.get(f"https://i.imgur.com{file}")
            if(response.status_code != 200):
                self.logger.log_and_status(f"[External-Imgur] Không thể tải tệp tin {file} do bị chặn. Vui lòng tải tệp này thủ công.", "err", False)
                if (response.status_code > 400):
                    continue
                else:
                    raise Exception("[External-Imgur] Failed to get file {file} from the site!")

            # Save the file
            with open(os.path.join(self.output_problem_path_dir, str(file).split("/")[-1]), "wb") as f:
                f.write(response.content)
            
            self.logger.step(step=5/len(files), force_update=False)

        if len(external_files) > 0:
            self.logger.log_and_status(f"[External-Imgur] Đã tải về {len(external_files)} file!", "info")
        else:
            self.logger.step(step=5, force_update=False)

        return files

    def get_zip_test_files(self):
        """ Get the test files from the server (if any). """
        if not self.problem_site_type == "CSLOJ": # Only CSLOJ has the test file download feature
            return

        # Problem code is the part after the '/problem/' in the URL
        problem_code = self.url.split("/problem/")[1]

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        self.logger.status(f"[{self.problem_site_type}] Đang tải file ZIP chứa test 'testcases-{problem_code}.zip'...", "info", False)
        response = requests.get(f"http://csloj.ddns.net/problem/{problem_code}/testdata/download")
        
        if(response.status_code != 200):
            self.logger.log_and_status(f"[{self.problem_site_type}] Không thể tải file ZIP chứa test!", "err")
            return

        # Save the file
        with open(os.path.join(self.output_problem_path_dir, f"testcases-{problem_code}.zip"), "wb") as f:
            f.write(response.content)
        
        self.logger.log_and_status(f"[{self.problem_site_type}] Đã tải file ZIP chứa test 'testcases-{problem_code}.zip'!", "info", False)

    def get_testcases(self):
        """Extract the testcases from the problem content."""

        self.logger.status(f"[{self.problem_site_type}] Đang trích xuất test từ nội dung đề bài...", "info", False)

        problem_content = str(self.problem["problem_content_raw"])

        # Remove the content before the first testcase, if not found, raise a warning
        for(indicator) in TESTCASE_INDICATOR_LIST:
            if problem_content.find(indicator) != -1:
                problem_content = problem_content[problem_content.find(indicator):]
                break
        else:
            self.logger.log(f"[{self.problem_site_type}] Không tìm thấy chỉ báo test trong nội dung đề bài. Vui lòng kiểm tra lại nội dung đề bài.")

        # Replace to make the content easier to parse
        if self.problem_site_type == "DMOJ" or self.problem_site_type == "LQDOJ" or self.problem_site_type == "CSLOJ":
            problem_content = problem_content.replace('<code>', '||begin||').replace('</code></pre>', '||end||')

            # Remove the content after the last testcase
            problem_content = problem_content[:problem_content.rfind('||end||') + len('||end||')]

            # Remove all HTML tags
            problem_content = re.sub(r'<[^>]*>', '\n', problem_content)
        elif self.problem_site_type == "Codeforces" or self.problem_site_type == "CodeforcesCD":
            problem_content = problem_content.replace('</div><pre>', '||begin||').replace('</pre></div>', '||end||')

            # Remove the content after the last testcase
            problem_content = problem_content[:problem_content.rfind('||end||') + len('||end||')]

            # Codeforces uses <div> to differentiate the smaller testcases in a bigger one, 
            # so we need to only replace the end tag with a newline, the begin tag will just be deleted
            problem_content = re.sub(r'</[^>]*>', '\n', problem_content)

            # some old problems uses <br /> instead of <div>
            problem_content = re.sub(r'<br />', '\n', problem_content)

            # remove other tags
            problem_content = re.sub(r'<[^>]*>', '', problem_content)

        # Extract the testcases from "||begin||" to "||end||"
        testcases = re.findall(r'\|\|begin\|\|(.+?)\|\|end\|\|', problem_content, re.DOTALL)

        # Remove the leading and trailing whitespaces
        testcases = [testcase.strip() for testcase in testcases]

        # Remove part before ||begin|| and after ||end||, if not found, ignore
        testcases = [testcase.split('||begin||')[-1].split('||end||')[0] for testcase in testcases]

        if len(testcases) % 2 != 0:
            self.logger.log(f"[{self.problem_site_type}] Phát hiện lẻ số lượng test, hãy kiểm tra lại.")
        
        if len(testcases) == 0:
            self.logger.log(f"[{self.problem_site_type}] Không tìm thấy test trong nội dung đề bài, hãy kiểm tra lại.")
        
        # Split the testcases into input and output
        testcases_separated = []
        try:
            for i in range(0, len(testcases), 2):
                testcases_separated.append([testcases[i], testcases[i + 1]])
        except:
            pass
        
        self.problem["problem_testcases"] = testcases_separated
        
        self.logger.log_and_status(f"[{self.problem_site_type}] Đã trích xuất {len(testcases_separated)} test từ nội dung đề bài!", "info", False)

        return testcases_separated

    def generate_testcase_table(self, testcases: list, input_name: str, output_name: str):
        """Generate a LaTeX table for the testcases."""
        testcase_table = """

\\ttfamily
\\begin{center}
\\begin{tabularx}{1\\textwidth}{| >{\\raggedright\\arraybackslash}X | >{\\raggedright\\arraybackslash}X |}
\\hline
"""
        testcase_table += f"{input_name} & {output_name} \\\\ \n"

        for testcase in testcases:
            testcase_table += f"\\hline\n{str(testcase[0]).replace("\n", "\\par ")} & {str(testcase[1]).replace("\n", "\\par ")} \\\\ \n"

        testcase_table += "\\hline\n\\end{tabularx}\n\\end{center}\n\\rmfamily\n"

        return testcase_table

    def generate_testcase_list(self, testcases: list, input_name: str, output_name: str):
        """Generate a list of testcases for the LaTeX content."""
        testcase_list = "\n\n"

        testcase_list += f"\\textbf{{Input}}: {input_name} \n\n"
        testcase_list += f"\\textbf{{Output}}: {output_name} \n\n"

        for i, testcase in enumerate(testcases):
            testcase_list += f"\\textbf{{Testcase {i + 1}}} \\\\ \n"
            testcase_list += "\\ttfamily\nInput:\n\\begin{lstlisting}"
            testcase_list += f"\n{testcase[0]}\n"
            testcase_list += f"\\end{{lstlisting}}\n"
            testcase_list += "Output:\n\\begin{lstlisting}"
            testcase_list += f"\n{testcase[1]}\n"
            testcase_list += f"\\end{{lstlisting}}\n\\rmfamily\n\n"

        return testcase_list

    def generate_testcase_text(self, testcases: list, input_name: str, output_name: str):
        """Generate a list of testcases for the general content."""
        testcase_text = "\n\n"

        testcase_text += f"Input: {input_name} \n"
        testcase_text += f"Output: {output_name} \n"

        for i, testcase in enumerate(testcases):
            testcase_text += f"\nTestcase {i + 1}: \n"
            testcase_text += f"\n{testcase[0]}\n"
            testcase_text += f"\n====="
            testcase_text += f"\n{testcase[1]}\n"

        return testcase_text
    
    def generate_testcase_md(self, testcases: list, input_name: str, output_name: str):
        """Generate a list of testcases for the markdown content."""
        testcase_text = "\n\n### Ví dụ\n\n"
        
        testcase_text += f"- Input: {input_name}\n"
        testcase_text += f"- Output: {output_name}\n\n"

        for i, testcase in enumerate(testcases):
            testcase_text += f"#### Sample Input {i + 1} \n\n"
            testcase_text += f"```\n{testcase[0]}\n```\n\n"
            testcase_text += f"#### Sample Output {i + 1} \n\n"
            testcase_text += f"```\n{testcase[1]}\n```\n\n"

        return testcase_text

    def generate_testcase_exmp(self, testcases: list, input_name: str, output_name: str):
        """Generate a list of testcases for the LaTeX content."""
        testcase_list = "\n\n"

        testcase_list += "\\begin{example}%\n"

        for i, testcase in enumerate(testcases):
            testcase_list += "\\exmp{\n"
            testcase_list += f"{testcase[0]}\n"
            testcase_list += "}{\n"
            testcase_list += f"{testcase[1]}\n"
            testcase_list += "}%\n"

        testcase_list += "\\end{example}\n"

        return testcase_list

    def generate_problem_info(self):
        """Generate the problem information section for the LaTeX content."""
        problem_info = "\n\\subsubsection*{Thông tin bài toán}\n"

        problem_info += f"\\textbf{{Site}}: \\texttt{"{" + self.problem['problem_site'] + "}"} \\\\\n"
        problem_info += f"\\textbf{{Code}}: \\texttt{"{" + self.problem['problem_code'] + "}"} \\\\\n"
        problem_info += f"\\textbf{{URL}}: \\url{"{!!url!!}"} \\\\\n"

        if(self.problem_site_type == "Codeforces"):
            problem_info += f"\\textbf{{Contest ID}}: \\texttt{"{" + self.problem['problem_contest_id'] + "}"} \\\\\n"
            problem_info += f"\\textbf{{Contest}}: {self.problem['problem_contest_name']} \\\\\n"
        
        try:
            # First name is the problem title
            problem_info += f"\\textbf{{Tên bài}}: {self.problem['problem_title']} \\\\\n"

            # Second name is the problem title + problem code, try to find any code in the statements
            if self.problem_site_type == "CSLOJ":
                # SPECIAL CASE: CSLOJ
                problem_info += f"\\textbf{{Tên bài 2}}: {str(self.problem['problem_title']).split("- ")[-1].capitalize()} "
                problem_info += f"[{str(self.problem['problem_title']).split(" -")[0].split(". ")[-1].upper()}] \\\\\n"
            
            elif self.problem_site_type == "Codeforces":
                # SPECIAL CASE: Codeforces
                problem_info += f"\\textbf{{Tên bài 2}}: {str(self.problem['problem_title']).split(". ")[-1].capitalize()} "
                # If the problem has custom input files, use that as the problem code.
                if str(self.problem['problem_info_entries'].get('input')).find("standard input") != -1: # Standard
                    problem_info += f"[{str(self.problem['problem_code']).upper()}] \\\\\n"
                else: # Custom
                    problem_info += f"[{str(self.problem['problem_info_entries'].get('input')).split('.')[0].upper()}] \\\\\n"
            else:
                problem_info += f"\\textbf{{Tên bài 2}}: {str(self.problem['problem_title']).split(". ")[-1].capitalize()} "
                problem_info += f"[{str(self.problem['problem_code']).upper()}] \\\\\n"
            
        except:
            # Sumthin' went wrong, end the paragraph
            problem_info += "\\\\n"
            pass

        try:
            for entry_name, entry_value in self.problem["problem_info_entries"].items():
                problem_info += f"\\textbf{{{entry_name}}}: {entry_value} \\\\\n"
            
            if len(self.problem['problem_types']) > 0:
                problem_info += f"\\textbf{{Tags}}: {', '.join(self.problem['problem_types'])} \\\\\n"
            if len(self.problem['problem_allowed_langs']) > 0:
                problem_info += f"\\textbf{{Ngôn ngữ cho phép}}: {', '.join(self.problem['problem_allowed_langs'])} \\\\\n"
        except:
            pass

        # Escape the special characters
        problem_info = problem_info.replace("_", "\\_")
        problem_info = problem_info.replace("%", "\\%")
        problem_info = problem_info.replace("&", "\\&")
        problem_info = problem_info.replace("#", "\\#")

        problem_info = problem_info.replace("!!url!!", self.url)

        return problem_info

    def util_replace_testcase(self, problem_content_latex: str, testcase_str: str, safe_replace = True):
        """Replace the old testcases in the problem with the new testcases being generated."""

        problem_testcase_content = problem_content_latex
        # Remove the content before the first testcase, if not found, raise a warning
        for(indicator) in TESTCASE_INDICATOR_LIST:
            ind = problem_testcase_content.find(indicator)
            if ind != -1:
                # Find the last '\n' before the indicator
                ind = problem_testcase_content.rfind('\n', 0, ind)

                # Remove the content before the indicator
                problem_testcase_content = problem_testcase_content[ind:]
                break
        else:
            self.logger.log(f"[{self.problem_site_type}] Không tìm thấy chỉ báo test trong nội dung đề bài. Vui lòng kiểm tra lại nội dung đề bài.")
            return problem_content_latex
        
        # Remove the content after the last testcase
        problem_testcase_content = problem_testcase_content[:problem_testcase_content.rfind('\\end{lstlisting}') + len('\\end{lstlisting}')]

        if safe_replace:
            problem_testcase_content_new = problem_testcase_content
            # Remove every lstlisting block using regex
            problem_testcase_content_new = re.sub(r'\\begin{lstlisting}((.|\n)*?)\\end{lstlisting}', '', string=problem_testcase_content_new, flags=(re.DOTALL | re.MULTILINE))
            return problem_content_latex.replace(problem_testcase_content, "\n\n\\subsubsection*{Example}\n\n" + testcase_str + "\n\n" + problem_testcase_content_new)
        else:
            return problem_content_latex.replace(problem_testcase_content, "\n\n\\subsubsection*{Example}\n\n" + testcase_str)

    def util_process_equation(self, func_str: str):
        """Process the math functions to be converted to LaTeX format."""
        
        # Re-escape some special characters
        func_str = func_str.replace("\\%", "%")
        func_str = func_str.replace("%", "\\%")

        # Fix some special characters cases:
        func_str = func_str.replace("\\*", "\\times ")
        func_str = func_str.replace("*", "\\times ")
        func_str = func_str.replace("×", "\\times ")
        func_str = func_str.replace("...", "\\dots ")
        func_str = func_str.replace("…", "\\dots ")
        func_str = func_str.replace("≤", "\\le ")
        func_str = func_str.replace("≥", "\\ge ")
        func_str = func_str.replace("−", "-")
        func_str = func_str.replace(" ", "")
        func_str = func_str.replace("’", "'")
        func_str = func_str.replace("⇔", "\\Leftrightarrow ")
        func_str = func_str.replace("≠", "\\neq ")
        func_str = func_str.replace("δ", "\\delta ")
        func_str = func_str.replace("Δ", "\\Delta ")
        func_str = func_str.replace("∑", "\\sum ")
        func_str = func_str.replace("∏", "\\prod ")
        func_str = func_str.replace("√", "\\sqrt ")
        func_str = func_str.replace("∈", "\\in ")
        func_str = func_str.replace("∉", "\\notin ")
        func_str = func_str.replace("∞", "\\infty ")
        func_str = func_str.replace("∀", "\\forall ")

        # Replace dollar sign 
        func_str = func_str.replace("!!Dollar!!", "\\$")

        return func_str

    def util_process_post_convert(self, problem_content: str):
        """Replace special characters and other modifications after the conversion."""
        problem_content = problem_content.replace(" ", " ")
        problem_content = problem_content.replace("—", "--")
        problem_content = problem_content.replace("–", "--")

        # Normalize the Unicode characters
        return unicodedata.normalize("NFC", problem_content)

    def convert_md_table_to_latex(self, md_table: str):
        """Convert a Markdown table to LaTeX format."""
        # https://github.com/JINHXu/MDtable2Latex/blob/main/mdtable2latex.py
        inlines = []
        cline = ''
        lines = md_table.strip().split('\n')
        cline = lines[1].strip().replace(':---:', 'c')
        cline = cline.replace(' ', '')
        del lines[1]
        for line in lines:
            line = line.strip()
            line = line[1:]
            line = line[:-1]
            line = line.replace('|', '&')
            line = line+'\\\\'+'\n'
            inlines.append(line)
        
        result_str = ""
        result_str +=('\\begin{center}')
        result_str +=('\\begin{tabular}'+'{' +cline+ '}'+'\n')
        for inline in inlines:
            result_str +=('\\hline'+'\n')
            result_str +=(inline)
        result_str +=('\\hline'+'\n')
        result_str +=('\\end{tabular}')
        result_str +=('\\end{center}')
        return result_str

    def convert_html_to_markdown(self):
        """Convert HTML content to Markdown content."""

        html = self.problem["problem_content_raw"]

        result = markdownify.markdownify(html, heading_style="ATX", bullets="*")

        # Replace dollar sign to prevent the math functions from being replaced
        result = result.replace("\\$", "!!Dollar!!")

        # Change the latex math delimiters
        if (self.problem_site_type == "Codeforces"):
            result = result.replace("$$$", "$")

        # SPECIAL CASE: laptrinhonline.club and laptrinh.ictu.edu.vn
        elif (self.problem_site_type == "LQDOJ" 
            or self.problem_site_type == "CSLOJ"
            or "laptrinhonline.club" in self.problem["problem_site"]
            or "laptrinh.ictu.edu.vn" in self.problem["problem_site"]):
            result = result.replace('\\(', '$')
            result = result.replace('\\)', '$')
            result = result.replace('\\[', '$$')
            result = result.replace('\\]', '$$')
        elif (self.problem_site_type == "DMOJ"):
            result = result.replace("~", "$")

        # Replace some special cases
        result = result.replace("\\left(", "\\ (")
        result = result.replace("\\right)", ")")
        result = result.replace("\\left[", "\\ [")
        result = result.replace("\\right]", "]")
        result = result.replace("\\left{", "\\ {")
        result = result.replace("\\right}", "}")
        result = result.replace("\\left|", "|")
        result = result.replace("\\right|", "|")

        # Remove domain from image links

        if (self.problem_site_type == "Codeforces"):
            # Remove "https://codeforces.com/espresso/" from the image links
            result = result.replace(f"https://{self.problem["problem_site"]}/espresso/", "")
            
        # SPECIAL CASE: oj.lequydon.net
        elif ("oj.lequydon.net" in self.problem["problem_site"]):
            # Remove "/media/martor/" from the image links
            result = result.replace("/media/martor/", "")
        # SPECIAL CASE: lqdoj.edu.vn
        elif ("lqdoj.edu.vn" in self.problem["problem_site"]):
            # Remove "https://cdn.lqdoj.edu.vn/media/pagedown-uploads/" from the image links
            result = result.replace( "https://cdn.lqdoj.edu.vn/media/pagedown-uploads/", "")
        elif (self.problem["problem_site_type"] == "DMOJ"):
            # Remove "/martor/" from the image links
            result = result.replace("/martor/", "")
        elif (self.problem["problem_site_type"] == "LQDOJ"):
            # Remove "/media/pagedown-uploads/" from the image links
            result = result.replace("/media/pagedown-uploads/", "")
        elif (self.problem["problem_site_type"] == "CSLOJ"):
            # Remove "/images/problems/" from the image links
            result = re.sub(r'/images/problems/(.+?)/', r'', result, flags=re.DOTALL)
        
        # Remove the mathoid link
        result = re.sub(r'!\[(.*?)\]\((.*?mathoid.*?)\)', '', result, flags=re.DOTALL)
        
        # Undo the escape of some special characters
        result = result.replace("\\_", "_")

        # Replace image links with a template to process later
        result = re.sub(r'!\[(.*?)\]\((.*?)\)', r'\n!!FileImage!!\2!!EndFileImage!!\n', result)

        # Replace code blocks with a template to process later
        result = re.sub(r'\`\`\`((.|\n)*?)\`\`\`', r'\n!!Codeblock!!\1!!EndCodeblock!!\n', result)

        result = result.strip().strip("\n")

        self.problem["problem_content_md"] = result

        return result

    def convert_to_latex_base(self):
        """Base function to convert the problem content to LaTeX format."""
        markdown_content = self.problem["problem_content_md"]

        md = markdown.Markdown()
        latex_mdx = MDXLatex.LaTeXExtension()
        latex_mdx.extendMarkdown(md)

        # Convert the Markdown content to LaTeX
        result = md.convert(markdown_content)

        # Extract all math functions
        
        # First group is the number of dollar signs, second group is the content
        math_functions = re.findall(r'(\${1,2})((?:(?!\1)[\s\S])*)\1', markdown_content, re.DOTALL)
        
        # First group is the entire math function, second group is the content
        math_functions_need_replace = re.findall(r'(\\[\(|\[]((?:.|\n)*?)\\[\)|\]])', result, re.DOTALL)

        # Replace the math functions in the latex content with the original math_function from markdown (the converter sucks)
        for i, math_func_need in enumerate(math_functions_need_replace):
            math_func_need_str = str(math_func_need[0]) # The entire math function
            math_func_str = str(math_functions[i][0]) + self.util_process_equation(str(math_functions[i][1])) + str(math_functions[i][0]) # The original math function
            result = result.replace(math_func_need_str, math_func_str, 1)

        # Detect and convert the Markdown tables to LaTeX format

        # Properly format the alignment of the table
        result = result.replace("| --- ", "|:---:")

        # Find all the Markdown tables
        # Credit: https://stackoverflow.com/a/54771485
        md_tables = re.findall(r'^(\|[^\n]+\|\r?\n)((?:\|:?[-]+:?)+\|)(\n(?:\|[^\n]+\|\r?\n?)*)?$', result, re.DOTALL | re.MULTILINE)

        # Convert the Markdown tables to LaTeX format
        for md_table in md_tables:
            md_table_string = md_table[0] + md_table[1] + md_table[2]
            result = result.replace(md_table_string, "\n" + self.convert_md_table_to_latex(md_table_string) + "\n")

        # Replace dollar sign 
        result = result.replace("!!Dollar!!", "\\$")

        # Replace the image links with the correct LaTeX format
        result = result.replace("!!FileImage!!", "\\includegraphics{")
        result = result.replace("!!EndFileImage!!", "}\n\n")

        # No number in the section
        result = result.replace("section{", "section*{")

        # Replace the code blocks with the correct LaTeX format (if any)
        result = result.replace("!!Codeblock!!", "\n\\begin{lstlisting}")
        result = result.replace("!!EndCodeblock!!", "\n\\end{lstlisting}")

        self.problem["problem_content_latex_base"] = result
        return result

    def convert_to_latex_general(self):
        """Convert the problem content to LaTeX format."""
        result = self.problem["problem_content_latex_base"]

        # Insert a table with the testcases
        if len(self.problem.get("problem_testcases", [])) > 0:
            testcase_str = self.generate_testcase_table(self.problem.get("problem_testcases", []), 
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))

            # Replace the old testcases format with the new testcases being generated
            result = self.util_replace_testcase(result, testcase_str, (self.problem_site_type != "Codeforces"))

        # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
        problem_info = self.generate_problem_info()
        result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
        result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

        self.result_latex_general = self.util_process_post_convert(result)
        with open(os.path.join(self.output_problem_path_dir, "general.tex"), "w", encoding="utf8") as file:
            file.write(self.result_latex_general)

    def convert_to_latex_polygon(self):
        """Convert the problem content to LaTeX format for Polygon."""
        result = self.problem["problem_content_latex_base"]

        # Make another version for quick copy
        result_quick_copy = result

        # Insert a list with the testcases
        if len(self.problem.get("problem_testcases", [])) > 0:
            testcase_str = self.generate_testcase_list(self.problem.get("problem_testcases", []), 
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))
            result = self.util_replace_testcase(result, testcase_str, (self.problem_site_type != "Codeforces"))

            testcase_str = self.generate_testcase_text(self.problem.get("problem_testcases", []),
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))

            result_quick_copy = self.util_replace_testcase(result_quick_copy, testcase_str, (self.problem_site_type != "Codeforces"))

        # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
        problem_info = self.generate_problem_info()
        result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
        result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

        result_quick_copy = result_quick_copy.replace("<root>", problem_info, 1)
        result_quick_copy = result_quick_copy[::-1].replace("</root>"[::-1], "", 1)[::-1]

        self.result_quick_copy_latex_polygon = self.util_process_post_convert(result_quick_copy)
        
        self.result_latex_polygon = self.util_process_post_convert(result)
        with open(os.path.join(self.output_problem_path_dir, "polygon.tex"), "w", encoding="utf8") as file:
            file.write(self.result_latex_polygon)

    def convert_to_latex_template(self):
        """Convert the problem content to LaTeX format for Templates."""
        result = self.problem["problem_content_latex_base"]

        # Insert a table with the testcases
        if len(self.problem.get("problem_testcases", [])) > 0:
            testcase_str = self.generate_testcase_exmp(self.problem.get("problem_testcases", []), 
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))
            result = self.util_replace_testcase(result, testcase_str, (self.problem_site_type != "Codeforces"))

        problem_info = "\\begin{statement}" + "[" + self.problem["problem_title"] + "]{" + self.problem["problem_code"] + "}{"
        problem_info += self.problem.get("problem_info_entries").get("input", "Input") + "}{" 
        problem_info += self.problem.get("problem_info_entries").get("output", "Output") + "}{xxx}{yyy}{\\points{}}"

        problem_info += self.generate_problem_info()

        problem_info += "\n\\InputFile\n\\OutputFile\n\\begin{scoring}\n\n\\end{scoring}\n"
        result = result.replace("<root>", problem_info, 1)
        result = result[::-1].replace("</root>"[::-1], "\\end{statement}"[::-1], 1)[::-1]

        self.result_latex_template = self.util_process_post_convert(result)
        with open(os.path.join(self.output_problem_path_dir, f"{self.problem["problem_code"]}.tex"), "w", encoding="utf8") as file:
            file.write(self.result_latex_template)

    def convert_to_md_dmoj(self, math_delimiter = "~"):
        """Convert the problem content to Markdown format for DMOJ."""
        result = self.problem["problem_content_md"]

        # First group is the number of dollar signs, second group is the content
        math_functions = re.findall(r'(\${1,2})((?:(?!\1)[\s\S])*)\1', result, re.DOTALL)

        # Replace the math functions in the latex content with the original math_function from markdown (the converter sucks)
        for i, math_func_need in enumerate(math_functions):
            math_func_need_str = str(math_func_need[0]) + str(math_func_need[1]) + str(math_func_need[0]) # The entire math function
            math_func_str = str(math_functions[i][0]) + self.util_process_equation(str(math_functions[i][1])) + str(math_functions[i][0]) # Processed math function
            result = result.replace(math_func_need_str, math_func_str, 1)
        
        # Change back the math delimiters
        result = result.replace("$", math_delimiter)

        # Change back the image links
        result = result.replace("!!FileImage!!", "![](")
        result = result.replace("!!EndFileImage!!", ")")

        # Change back the code blocks
        result = result.replace("!!Codeblock!!", "```")
        result = result.replace("!!EndCodeblock!!", "```")

        # Replace dollar sign
        result = result.replace("!!Dollar!!", "\\$")

        if math_delimiter == "~":
            self.result_md_dmoj = self.util_process_post_convert(result)
            with open(os.path.join(self.output_problem_path_dir, "dmoj.md"), "w", encoding="utf8") as file:
                file.write(self.result_md_dmoj)
        elif math_delimiter == "$":
            self.result_md_general = self.util_process_post_convert(result)
            with open(os.path.join(self.output_problem_path_dir, "general.md"), "w", encoding="utf8") as file:
                file.write(self.result_md_general)

    def detect_problem_site(self):
        """Detect the problem site from the URL."""

        dmoj_list = DMOJ_INDICATOR_LIST.strip().strip("\n").splitlines()
        lqdoj_list = LQDOJ_INDICATOR_LIST.strip().strip("\n").splitlines()

        if "codeforces.com" in self.url:
            self.problem_site_type = "Codeforces"
            return "Codeforces"
        
        elif "csloj.ddns.net" in self.url:
            self.problem_site_type = "CSLOJ"
            return "CSLOJ"
        
        for lqdoj_indicator in lqdoj_list:
            lqdoj_indicator = lqdoj_indicator.strip().strip("\n")
            if lqdoj_indicator in self.url:
                self.problem_site_type = "LQDOJ"
                return "LQDOJ"
        
        for dmoj_indicator in dmoj_list:
            dmoj_indicator = dmoj_indicator.strip().strip("\n")
            if dmoj_indicator in self.url:
                self.problem_site_type = "DMOJ"
                return "DMOJ"

        return None

    def main_converter(self):
        """Main function."""

        self.logger.set_total_steps(100)

        if self.problem_site_type == None:
            self.detect_problem_site()
        

        if self.problem_site_type == None:
            # Default to DMOJ
            self.logger.log("Không thể xác định loại trang, mặc định sẽ sử dụng DMOJ.")
            self.problem_site_type = "DMOJ"
        
        self.logger.step(step=5, force_update=False)
        self.logger.log(f"Loại trang: {self.problem_site_type}")

        self.logger.log_and_status(f"[{self.problem_site_type}] Đang cào nội dung bài toán...\n", "info", False)

        if self.problem_site_type == "Codeforces":
            # Get the raw problem content from the Codeforces site
            self.get_base_problem_codeforces()

        if self.problem_site_type == "CSLOJ":
            # Get the raw problem content from the CSLOJ site
            self.get_base_problem_csloj()
        
        if self.problem_site_type == "LQDOJ":
            # Get the raw problem content from the LQDOJ site
            self.get_base_problem_lqdoj()
        
        if self.problem_site_type == "DMOJ":
            # Get the raw problem content from the DMOJ site
            self.get_base_problem_dmoj()

        self.problem_folder_name = self.problem["problem_site"] + '+' + self.problem["problem_code"]
        self.output_problem_path_dir = os.path.join(self.output_path_dir, self.problem_folder_name)

        self.logger.step(step=20, force_update=False)

        self.logger.log(f"=====\n\n[{self.problem_site_type}] Cào bài thành công! Toàn bộ tệp tin sẽ được lưu tại thư mục: '{self.problem_folder_name}'")

        # check if the output folder exists
        if os.path.exists(self.output_problem_path_dir):
            self.logger.log(f"Phát hiện thư mục cũ: '{self.problem_folder_name}', thư mục sẽ được xóa và tạo lại.")
            import shutil
            shutil.rmtree(self.output_problem_path_dir)
        
        self.os_create_folder(self.output_problem_path_dir)

        self.logger.step(step=5, force_update=False)

        self.logger.log_and_status(f"[{self.problem_site_type}] Đang lấy các tệp tin và ảnh...", "info", False)
        self.get_files()
        self.get_zip_test_files()
        self.logger.step(step=5, force_update=False)

        self.get_testcases()
        self.logger.step(step=5, force_update=False)

        # Convert the base HTML problem content to Markdown
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung HTML sang Markdown...", "info", False)
        self.convert_html_to_markdown() 
        self.logger.step(step=5, force_update=False)

        # Convert the problem content to base LaTeX formats
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung Markdown sang LaTeX...", "info", False)
        self.convert_to_latex_base()
        self.logger.step(step=5, force_update=False)

        # Convert the problem content to LaTeX formats
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung sang LaTeX chung...", "info", False)
        self.convert_to_latex_general()
        self.logger.step(step=5, force_update=False)
        
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung sang LaTeX Polygon...", "info", False)
        self.convert_to_latex_polygon()
        self.logger.step(step=5, force_update=False)
        
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung sang LaTeX theo mẫu...", "info", False)
        self.convert_to_latex_template()
        self.logger.step(step=5, force_update=False)

        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung sang Markdown chung...", "info", False)
        self.convert_to_md_dmoj("$")
        self.logger.step(step=5, force_update=False)
        
        self.logger.status(f"[{self.problem_site_type}] Đang định dạng nội dung sang Markdown DMOJ...", "info", False)
        self.convert_to_md_dmoj("~")
        self.logger.step(step=5, force_update=False)

        self.result_quick_copy_md_dmoj = self.result_md_dmoj
        self.result_quick_copy_example_text = self.generate_testcase_text(self.problem.get("problem_testcases", []),
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))
        self.result_quick_copy_example_md = self.generate_testcase_md(self.problem.get("problem_testcases", []),
                                                self.problem.get("problem_info_entries").get("input", "Input"), 
                                                self.problem.get("problem_info_entries").get("output", "Output"))

        self.logger.log(f"[{self.problem_site_type}] Hoàn tất định dạng nội dung sang LaTex (chung, Polygon, theo mẫu), Markdown (chung, DMOJ)!")

        # Save the problem to a JSON file
        with open(os.path.join(self.output_problem_path_dir, "problem.json"), "w", encoding="utf8") as file:
            json.dump(self.problem, file, indent=4, ensure_ascii=False)
        
        self.logger.step(completed=True)
        self.logger.status(f"[{self.problem_site_type}] Đã hoàn tất định dạng nội dung bài toán!", "ok")

        return self.problem

    def crawl(self):
        """Crawl the problem content from the URL."""

        self.logger.log("===== THỰC THI =====")

        prev_problem_site_type = self.problem_site_type
        try:
            self.main_converter()
        except Exception as e:
            print(f"Error: {e}")
            if e:
                self.problem_site_type = prev_problem_site_type
                self.problem = dict()

                self.logger.log_and_status(f"Không thể cào bài từ trang! Đang chờ phương pháp Thủ công...", "err")

                # Create a temporary text file then open it using notepad
                with open("manual.txt", "w", encoding="utf8") as file:
                    file.write(INSTRUCT_USING_MANUAL_VI + "\n\nĐọc hướng dẫn rồi dán nội dung mới copy vào đây...\n")
                
                try:
                    import os
                    os.system("notepad manual.txt")
                except:
                    self.logger.log("Không thể mở Notepad. Vui lòng thử lại sau.")
                    print("Failed to open notepad. Please open the text file 'manual.txt' manually.")
                
                # Read the content of the file
                with open("manual.txt", "r", encoding="utf8") as file:
                    override = file.read()
                    override = override.replace(INSTRUCT_USING_MANUAL_VI + "\n\nĐọc hướng dẫn rồi dán nội dung mới copy vào đây...\n", "", 1)

                    if override.strip().strip('\n') == "":
                        self.logger.log("Không phát hiện nội dung trong tệp. Đã hủy bỏ.")
                        self.logger.set_total_steps(1)
                        return
                
                self.html_response = override
                
                # delete the file
                os.remove("manual.txt")

                try:
                    self.main_converter()
                except Exception as e:
                    print(f"Error: {e}")
                    traceback.print_exc()
                    self.logger.log_and_status("Không thể cào bài từ trang! Đã hủy bỏ.", "err")
                    self.logger.set_total_steps(1)
                    return

if __name__ == "__main__":
    # Crawler("https://claoj.edu.vn/problem/superprime2").crawl()
    Crawler("").crawl()