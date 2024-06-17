import json
import re
import traceback
import requests
import markdown
import markdownify
import markdown2latex.mdx_latex as MDXLatex
import warnings
import unicodedata

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
"""

LQDOJ_INDICATOR_LIST = """
lqdoj.edu.vn
tleoj.edu.vn
nbk.homes
"""

INSTRUCT_USING_MANUAL = """
Can not convert the problem. You can try using Manual method instead:

1. Go to that problem page.
2. Right click and choose "Inspect".
3. Switch to the "Network" tab.
4. Find the problem in the "Network" tab (if not found, try refreshing the page using F5).
   * It should be a request with the method "GET", has the type "document" and the name is the problem code.
5. Right click on the request and choose "Copy" > "Copy response". (not "Copy response headers")
6. Paste the copied content in the Notepad window (using Right click > Paste or Ctrl + V).
7. Save the file and close the Notepad window.
8. When you are ready, press Enter to continue.
"""

INSTRUCT_USING_MANUAL_VI = """
Không thể chuyển đổi bài toán. Tuy nhiên có thể thử sử dụng phương pháp Thủ công:

1. Truy cập vào trang web cần chuyển đổi.
2. Chuột phải và chọn "Inspect".
3. Chuyển sang tab "Network".
4. Tìm dòng có mã bài toán đó trong tab "Network" (nếu không thấy, thử làm mới trang bằng F5).
   * Đó sẽ là một request có method "GET", có type "document" và tên là mã bài toán.
5. Chuột phải vào request đó và chọn "Copy" > "Copy response". (không phải "Copy response headers")
6. Dán nội dung đã copy vào cửa sổ Notepad (chuột phải > Dán hoặc Ctrl + V).
7. Lưu file và đóng cửa sổ Notepad.
8. Khi bạn đã sẵn sàng, nhấn Enter để tiếp tục.
"""

def os_create_folder(folder_name: str):
    """Create a folder with the given name if it does not exist."""
    import os

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        return True
    
    return False

def get_base_problem_dmoj(url: str, override = None):
    """Return and extract the raw problem content from a DMOJ-themed site."""

    # Problem code is the part after the '/problem/' in the URL
    problem_code = url.split("/problem/")[1]

    # Remove the query string from the problem code
    problem_code = re.sub(r'\/|\?.*', '', problem_code)

    # Problem site is the part before the '/problem/' in the URL
    problem_site = url.split("/problem/")[0]
    problem_site = problem_site.split("://")[1]

    html_response = override
    if override == None:
        response = requests.get(url)
        if(response.status_code != 200):
            raise Exception("Failed to get problem from DMOJ-themed site")
        html_response = response.text

    # Extract the problem content from the response
    
    # SPECIAL CASE: claoj.edu.vn
    if "claoj.edu.vn" in problem_site:
        html_response = html_response.split('<div id="content-left" class="split-common-content">')
    else:
        html_response = html_response.split('<iframe name="raw_problem" id="raw_problem"></iframe>')
    
    if len(html_response) == 1:
        print("[DMOJ] Failed to split the problem content, will use the entire response.")
        
    # First half is the problem details
    html_problem_details = html_response[0]

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
        print("[DMOJ] Failed to get problem types.")
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
        print("[DMOJ] Failed to get allowed languages.")
        pass

    # Second half is the problem content using the last part of the split
    html_problem_content = html_response[-1].split('src="/static/mathjax_config.js"></script>')[0]
    
    # Alternative method to extract the problem content
    if len(html_response) == 1:
        html_problem_content = '<div id="' + html_problem_content.split('<div id="')[-2].strip().strip("\n")
    else:
        html_problem_content = html_problem_content.split('<hr>\n')[0].strip().strip("\n")
    
    return {
        "problem_site_type": "DMOJ",
        "problem_url": url,
        "problem_site": problem_site,
        "problem_code": problem_code,
        "problem_title": problem_title,
        "problem_info_entries": problem_info_entries,
        "problem_types": problem_types,
        "problem_allowed_langs": problem_allowed_langs,
        "problem_content_raw": html_problem_content
    }

def get_base_problem_lqdoj(url: str, override = None):
    """Return and extract the raw problem content from LQDOJ - a strange af DMOJ-themed site"""

    # Problem code is the part after the '/problem/' in the URL
    problem_code = url.split("/problem/")[1]

    # Remove the query string from the problem code
    problem_code = re.sub(r'\/|\?.*', '', problem_code)

    # Problem site is the part before the '/problem/' in the URL
    problem_site = url.split("/problem/")[0]
    problem_site = problem_site.split("://")[1]

    html_response = override
    if override == None:
        response = requests.get(url)
        if(response.status_code != 200):
            raise Exception("Failed to get problem from LQDOJ")
        html_response = response.text

    # Extract the problem content from the response
    # SPECIAL CASE: nbk.homes
    if "nbk.homes" in problem_site:
        html_response = html_response.split('<div id="content-left" class="split-common-content">')
    else:
        html_response = html_response.split('<div class="md-typeset')
    
    # First half is the problem details
    html_problem_details = html_response[0]

    # Extract the problem title, info entries, types, allowed langs, and content
    problem_title = html_problem_details.split('<h2 ')[1].split('</h2>')[0].split('>')[1].strip()
    html_problem_info_entries = html_problem_details.split('fa-fw"></i><span ')[1:]
    
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

    html_problem_types = html_problem_details.split('<div id="problem-types">')[1]
    html_problem_types = html_problem_types.split('class="toggled">')[1]
    html_problem_types = html_problem_types.split('</div>')[0]

    problem_types = html_problem_types.split(',')
    problem_types = [problem_type.strip() for problem_type in problem_types]

    # Second half is the problem content
    if(len(html_response) == 1):
        html_problem_content = html_response[-1]
    else:
        html_problem_content = html_response[1]
    html_problem_content = html_problem_content.split('<div id="comment-section">')[0]
    html_problem_content = "<div>\n" + html_problem_content.split('<hr>\n')[0].split('">',1)[-1].strip().strip("\n")

    # Uses <h4> tag instead of <summary>, and </h4> instead of </summary> using regex
    html_problem_content = re.sub(r'<summary>(.+?)</summary>', r'<h4>\1</h4>', html_problem_content)

    # Replace the math/tex script if exists
    html_problem_content = re.sub(r'<script type="math/tex">(.+?)</script>', r'\(\1\)', html_problem_content)

    # Nuke the mathjax script preview
    html_problem_content = re.sub(r'<span class="MathJax_Preview">(.+?)</span>', r'', html_problem_content)

    return {
        "problem_site_type": "LQDOJ",
        "problem_url": url,
        "problem_site": problem_site,
        "problem_code": problem_code,
        "problem_title": problem_title,
        "problem_info_entries": problem_info_entries,
        "problem_types": problem_types,
        "problem_content_raw": html_problem_content
    }

def get_base_problem_csloj(url: str, override = None):
    """Return and extract the raw problem content from CSLOJ."""

    # Problem code is the part after the '/problem/' in the URL
    problem_code = url.split("/problem/")[1]

    # Remove the query string from the problem code
    problem_code = re.sub(r'\/|\?.*', '', problem_code)

    # Problem site is the part before the '/problem/' in the URL
    problem_site = url.split("/problem/")[0]
    problem_site = problem_site.split("://")[1]

    html_response = override
    if override == None:
        response = requests.get(url)
        if(response.status_code != 200):
            raise Exception("Failed to get problem from CSLOJ")
        html_response = response.text

    # Extract the problem content from the response
    html_response = html_response.split('<div class="ui grid">')

    # First half is the problem details
    html_problem_details = html_response[0]

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

    html_problem_types = html_response[1].split('<h3 class="ui top attached block header">Đề bài</h3>')[1].split('<div class="row">')[1]
    html_problem_types = html_problem_types.split(' label">')[1:]

    problem_types = [problem_type.split("</a>")[0].strip().strip('\n') for problem_type in html_problem_types]

    # Special tag: ***** one that indicate the difficulty of the problem
    for prob_type in problem_types:
        rating = prob_type.count("⭐")
        if rating > 0:
            problem_types.remove(prob_type)
            problem_info_entries["độ khó"] = str(rating) + "/5 sao"
    
    # Second half is the problem content
    html_problem_content = html_response[1].split('<h3 class="ui top attached block header">Đề bài</h3>')[1]
    html_problem_content = html_problem_content.split('<div class="row">')[0].strip().strip("\n")

    # Nuke the mathjax script preview
    html_problem_content = re.sub(r'<span class="mjpage"><svg xmlns((.|\n)+?)<title id="MathJax(.+?)">(.+?)</title>((.|\n)+?)</svg></span>', r'\(\4\)', html_problem_content, count = 0, flags=re.MULTILINE | re.DOTALL)

    return {
        "problem_site_type": "CSLOJ",
        "problem_url": url,
        "problem_site": problem_site,
        "problem_code": problem_code,
        "problem_title": problem_title,
        "problem_info_entries": problem_info_entries,
        "problem_types": problem_types,
        "problem_content_raw": html_problem_content
    }

def get_base_problem_codeforces(url: str, override = None):
    """Return and extract the raw problem content from a Codeforces site."""

    # Convert problemset type URL to contest type URL using regex
    # https://codeforces.com/problemset/problem/75/C -> https://codeforces.com/contest/75/problem/C
    if "/problemset/problem/" in url:
        url = re.sub(r'\/problemset\/problem\/(\d+)(\/[A-Z0-9]+)', r'/contest/\1/problem\2', url)

    # Problem code is the part after the '/problem/' in the URL
    
    # Contest ID is the part after the '/contest/' in the URL
    problem_contest_id = url.split("/contest/")[1].split("/problem/")[0]

    # Problem order id is the part after the '/problem/' in the URL
    problem_order_id = url.split("/problem/")[1]

    # Problem code = Contest ID + Problem Order ID
    problem_code = problem_contest_id + problem_order_id

    # Remove the query string from the problem code
    problem_code = re.sub(r'\/|\?.*', '', problem_code)

    # Problem site is the part from the ".com" back to the first "/"
    problem_site = url.split(".com")[0] + ".com"
    problem_site = problem_site.split("://")[1]

    html_response = override
    if override == None:
        response = requests.get(url)
        if(response.status_code != 200):
            raise Exception("Failed to get problem from Codeforces site")
        html_response = response.text

    # Extract contest name
    html_sideboxes = html_response.split('<div class="roundbox sidebox borderTopRound " style="">')[1:]
    problem_contest_name = ""

    for sidebox in html_sideboxes:
        try:
            sidebox = sidebox.split('</div>')[0]
            if sidebox.find('<div class="caption titled">') != -1:
                continue
            if sidebox.find('/contest/') == -1:
                continue
            problem_contest_name = sidebox.split('</a></th>')[0].split("/contest/")[1].split("\">")[1].strip()
            break
        except:
            continue
    
    # Extract the problem tags from the response
    problem_types = []
    try:
        html_problem_types = html_response.split('<div class="caption titled">&rarr; Problem tags')[1].split('<form id="addTagForm"')[0]

        problem_types_unfi = html_problem_types.split('<span class="tag-box"')[1:]

        for problem_type in problem_types_unfi:
            problem_type = problem_type.split('">')[1].split('</span>')[0].strip().strip("\n")
            problem_types.append(problem_type)
    except:
        print("[Codeforces] Failed to get problem types.")
        pass

    # Cut the response to the part that starts the problem
    html_response = html_response.split('<div class="ttypography"><div class="problem-statement">')[1]

    # Extract the problem content from the response
    html_response = html_response.split('</div></div><div>', 1)

    # First half is the problem details
    html_problem_details = html_response[0]

    # Extract the problem title, info entries, types, allowed langs, and content
    problem_title = html_problem_details.split('<div class="header"><div class="title">')[1].split('</div>')[0].strip()
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
    html_problem_content = html_response[1].split('<script')[0]
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
        math_func_str = math_func_str.replace('<sup class="lower-index">', '_{').replace('</sup>', '}') # Replace lower index
        html_problem_content = html_problem_content.replace(math_func_need_str, math_func_str, 1)
    
    return {
        "problem_site_type": "Codeforces",
        "problem_url": url,
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

def get_files(problem_content: str, problem_site: str, problem_folder_name: str, problem_site_type: str):
    """Return the list of files embedded in the problem content."""

    # Extract the files from the problem content
    files = []
    if problem_site_type == "DMOJ":
        files = re.findall(r'\/martor(.+?)"', problem_content)
    elif problem_site_type == "LQDOJ":
        files = re.findall(r'\/media/pagedown-uploads(.+?)"', problem_content)
    elif problem_site_type == "Codeforces":
        files = re.findall(r'\/espresso(.+?)"', problem_content)
    elif problem_site_type == "CSLOJ":
        files = re.findall(r'\/images/problems(.+?)"', problem_content)

    # Remove the duplicates
    files = list(set(files))

    # Remove empty strings
    files = [file for file in files if file != ""]

    # Download the files
    for i, file in enumerate(files):
        print(f"[{problem_site_type}] Downloading internal file {file}... ({i + 1}/{len(files)})")

        response = None
        # SPECIAL CASE: oj.lequydon.net
        if "oj.lequydon.net" in problem_site:
            response = requests.get(f"https://{problem_site}/media/martor{file}")
        elif problem_site_type == "DMOJ":
            response = requests.get(f"https://{problem_site}/martor{file}")
        elif problem_site_type == "LQDOJ":
            response = requests.get(f"https://{problem_site}/media/pagedown-uploads{file}")
        elif problem_site_type == "Codeforces":
            response = requests.get(f"https://{problem_site}/espresso{file}")
        elif problem_site_type == "CSLOJ":
            response = requests.get(f"http://{problem_site}/images/problems{file}")
        
        if(response.status_code != 200):
            raise Exception("Failed to get file from the site")

        # Save the file
        with open(f"output/{problem_folder_name}/{str(file).split("/")[-1]}", "wb") as f:
            f.write(response.content)

    # Imgur files
    external_files = re.findall(r'\/i.imgur.com(.+?)"', problem_content)
    external_files = list(set(external_files))
    external_files = [file for file in external_files if file != ""]

    for i, file in enumerate(external_files):
        print(f"[External-Imgur] Downloading external file {file}... ({i + 1}/{len(external_files)})")

        response = requests.get(f"https://i.imgur.com{file}")
        if(response.status_code != 200):
            print("[External-Imgur] Failed to get Imgur file, but you can try to download it manually.")
            continue

        # Save the file
        with open(f"output/{problem_folder_name}{file}", "wb") as f:
            f.write(response.content)

    return files

def get_zip_test_files(problem_content: str, url: str, problem_folder_name: str, problem_site_type: str):
    # Get the test files from the server (if any).
    if problem_site_type == "CSLOJ":
        # Problem code is the part after the '/problem/' in the URL
        problem_code = url.split("/problem/")[1]

        # Remove the query string from the problem code
        problem_code = re.sub(r'\/|\?.*', '', problem_code)

        print(f"[{problem_site_type}] Downloading ZIP test file testcases-{problem_code}.zip...")
        response = requests.get(f"http://csloj.ddns.net/problem/{problem_code}/testdata/download")
        
        if(response.status_code != 200):
            raise Exception("Failed to get ZIP test file from CSLOJ")

        # Save the file
        with open(f"output/{problem_folder_name}/testcases-{problem_code}.zip", "wb") as f:
            f.write(response.content)

    print(f"[{problem_site_type}] Downloaded.")

def get_testcases(problem_content: str, problem_site_type: str):
    """Extract the testcases from the problem content."""

    # Remove the content before the first testcase, if not found, raise a warning
    for(indicator) in TESTCASE_INDICATOR_LIST:
        if problem_content.find(indicator) != -1:
            problem_content = problem_content[problem_content.find(indicator):]
            break
    else:
        warnings.warn("There is no clear indication of the testcases in the problem content. Please check the problem content.")

    # Replace to make the content easier to parse
    if problem_site_type == "DMOJ" or problem_site_type == "LQDOJ" or problem_site_type == "CSLOJ":
        problem_content = problem_content.replace('<code>', '||begin||').replace('</code></pre>', '||end||')

        # Remove the content after the last testcase
        problem_content = problem_content[:problem_content.rfind('||end||') + len('||end||')]

        # Remove all HTML tags
        problem_content = re.sub(r'<[^>]*>', '\n', problem_content)
    elif problem_site_type == "Codeforces":
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
        warnings.warn("There is an odd number of testcases, please check the problem content.")
    
    # Split the testcases into input and output
    testcases_separated = []
    try:
        for i in range(0, len(testcases), 2):
            testcases_separated.append([testcases[i], testcases[i + 1]])
    except:
        pass

    return testcases_separated

def generate_testcase_table(testcases: list, input_name: str, output_name: str):
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

def generate_testcase_list(testcases: list, input_name: str, output_name: str):
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

def generate_testcase_exmp(testcases: list, input_name: str, output_name: str):
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

def generate_problem_info(problem: dict):
    """Generate the problem information section for the LaTeX content."""
    problem_info = "\n\\subsubsection*{Thông tin bài toán}\n"

    problem_info += f"\\textbf{{Site}}: \\texttt{"{" + problem['problem_site'] + "}"} \\\\\n"
    problem_info += f"\\textbf{{Code}}: \\texttt{"{" + problem['problem_code'] + "}"} \\\\\n"
    problem_info += f"\\textbf{{URL}}: \\url{"{!!url!!}"} \\\\\n"

    if(problem["problem_site_type"] == "Codeforces"):
        problem_info += f"\\textbf{{Contest ID}}: \\texttt{"{" + problem['problem_contest_id'] + "}"} \\\\\n"
        problem_info += f"\\textbf{{Contest}}: {problem['problem_contest_name']} \\\\\n"
    
    try:
        problem_info += f"\\textbf{{Tên bài}}: {problem['problem_title']} \\\\\n"
        if(problem["problem_site_type"] == "CSLOJ"):
            problem_info += f"\\textbf{{Tên bài 2}}: {str(problem['problem_title']).split("- ")[-1].capitalize()} [{str(problem['problem_title']).split(" -")[0].split(". ")[-1].upper()}] \\\\\n"
        else:
            problem_info += f"\\textbf{{Tên bài 2}}: {str(problem['problem_title']).split(". ")[-1].capitalize()} [{str(problem['problem_code']).upper()}] \\\\\n"

        for entry_name, entry_value in problem["problem_info_entries"].items():
            problem_info += f"\\textbf{{{entry_name}}}: {entry_value} \\\\\n"
        
        if len(problem['problem_types']) > 0:
            problem_info += f"\\textbf{{Tags}}: {', '.join(problem['problem_types'])} \\\\\n"
        if len(problem['problem_allowed_langs']) > 0:
            problem_info += f"\\textbf{{Ngôn ngữ cho phép}}: {', '.join(problem['problem_allowed_langs'])} \\\\\n"
    except:
        pass

    # Escape the special characters
    problem_info = problem_info.replace("_", "\\_")
    problem_info = problem_info.replace("%", "\\%")
    problem_info = problem_info.replace("&", "\\&")
    problem_info = problem_info.replace("#", "\\#")

    problem_info = problem_info.replace("!!url!!", problem['problem_url'])

    return problem_info

def util_replace_testcase(problem_content_latex: str, testcase_str: str, safe_replace = True):
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
        warnings.warn("There is no clear indication of the testcases in the problem content. Please check the problem content.")
        return problem_content_latex
    
    # Remove the content after the last testcase
    problem_testcase_content = problem_testcase_content[:problem_testcase_content.rfind('\\end{lstlisting}') + len('\\end{lstlisting}')]

    if safe_replace:
        problem_testcase_content_new = problem_testcase_content
        # Remove every lstlisting block using regex
        problem_testcase_content_new = re.sub(r'\\begin{lstlisting}((.|\n)*?)\\end{lstlisting}', '', problem_testcase_content_new, re.DOTALL | re.MULTILINE)
        return problem_content_latex.replace(problem_testcase_content, "\n\n\\subsubsection*{Example}\n\n" + testcase_str + "\n\n" + problem_testcase_content_new)
    else:
        return problem_content_latex.replace(problem_testcase_content, "\n\n\\subsubsection*{Example}\n\n" + testcase_str)

def util_process_equation(func_str: str):
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
    func_str = func_str.replace("⇔", "\\Leftrightarrow")

    # Replace dollar sign 
    func_str = func_str.replace("!!Dollar!!", "\\$")

    return func_str

def convert_md_table_to_latex(md_table: str):
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

def convert_html_to_markdown(problem: dict):
    """Convert HTML content to Markdown content."""

    html = problem["problem_content_raw"]

    result = markdownify.markdownify(html, heading_style="ATX", bullets="*")

    # Replace dollar sign to prevent the math functions from being replaced
    result = result.replace("\\$", "!!Dollar!!")

    # Change the latex math delimiters
    if (problem["problem_site_type"] == "Codeforces"):
        result = result.replace("$$$", "$")

    # SPECIAL CASE: laptrinhonline.club and laptrinh.ictu.edu.vn
    elif (problem["problem_site_type"] == "LQDOJ" 
          or problem["problem_site_type"] == "CSLOJ"
          or "laptrinhonline.club" in problem["problem_site"]
          or "laptrinh.ictu.edu.vn" in problem["problem_site"]):
        result = result.replace('\\(', '$')
        result = result.replace('\\)', '$')
        result = result.replace('\\[', '$$')
        result = result.replace('\\]', '$$')
    elif (problem["problem_site_type"] == "DMOJ"):
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

    if (problem["problem_site_type"] == "Codeforces"):
        # Remove "https://codeforces.com/espresso/" from the image links
        result = result.replace(f"https://{problem["problem_site"]}/espresso/", "")
        
    # SPECIAL CASE: oj.lequydon.net
    elif ("oj.lequydon.net" in problem["problem_site"]):
        # Remove "/media/martor/" from the image links
        result = result.replace("/media/martor/", "")
    elif (problem["problem_site_type"] == "DMOJ"):
        # Remove "/martor/" from the image links
        result = result.replace("/martor/", "")
    elif (problem["problem_site_type"] == "LQDOJ"):
        # Remove "/media/pagedown-uploads/" from the image links
        result = result.replace("/media/pagedown-uploads/", "")
    elif (problem["problem_site_type"] == "CSLOJ"):
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
    
    return result

def convert_to_latex_base(problem: dict):
    """Base function to convert the problem content to LaTeX format."""
    markdown_content = problem["problem_content_md"]

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
        math_func_str = str(math_functions[i][0]) + util_process_equation(str(math_functions[i][1])) + str(math_functions[i][0]) # The original math function
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
        result = result.replace(md_table_string, "\n" + convert_md_table_to_latex(md_table_string) + "\n")

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

    return result

def convert_to_latex_general(problem: dict):
    """Convert the problem content to LaTeX format."""
    result = problem["problem_content_latex_base"]

    # Insert a table with the testcases
    if len(problem.get("problem_testcases", [])) > 0:
        testcase_str = generate_testcase_table(problem.get("problem_testcases", []), 
                                               problem.get("problem_info_entries").get("input", "Input"), 
                                               problem.get("problem_info_entries").get("output", "Output"))

        # Replace the old testcases format with the new testcases being generated
        result = util_replace_testcase(result, testcase_str, (problem["problem_site_type"] != "Codeforces"))

    # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
    problem_info = generate_problem_info(problem)
    result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

    return unicodedata.normalize("NFC", result)

def convert_to_latex_polygon(problem: dict):
    """Convert the problem content to LaTeX format for Polygon."""
    result = problem["problem_content_latex_base"]

    # Insert a list with the testcases
    if len(problem.get("problem_testcases", [])) > 0:
        testcase_str = generate_testcase_list(problem.get("problem_testcases", []), 
                                               problem.get("problem_info_entries").get("input", "Input"), 
                                               problem.get("problem_info_entries").get("output", "Output"))
        result = util_replace_testcase(result, testcase_str, (problem["problem_site_type"] != "Codeforces"))

    # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
    problem_info = generate_problem_info(problem)
    result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

    return unicodedata.normalize("NFC", result)

def convert_to_latex_template(problem: dict):
    """Convert the problem content to LaTeX format for Templates."""
    result = problem["problem_content_latex_base"]

    # Insert a table with the testcases
    if len(problem.get("problem_testcases", [])) > 0:
        testcase_str = generate_testcase_exmp(problem.get("problem_testcases", []), 
                                               problem.get("problem_info_entries").get("input", "Input"), 
                                               problem.get("problem_info_entries").get("output", "Output"))
        result = util_replace_testcase(result, testcase_str, (problem["problem_site_type"] != "Codeforces"))

    problem_info = "\\begin{statement}" + "[" + problem["problem_title"] + "]{" + problem["problem_code"] + "}{"
    problem_info += problem.get("problem_info_entries").get("input", "Input") + "}{" 
    problem_info += problem.get("problem_info_entries").get("output", "Output") + "}{xxx}{yyy}{\\points{}}"

    problem_info += generate_problem_info(problem)

    problem_info += "\n\\InputFile\n\\OutputFile\n\\begin{scoring}\n\n\\end{scoring}\n"
    result = result.replace("<root>", problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{statement}"[::-1], 1)[::-1]

    return unicodedata.normalize("NFC", result)

def convert_to_md_dmoj(problem: dict):
    """Convert the problem content to Markdown format for DMOJ."""
    result = problem["problem_content_md"]

    # First group is the number of dollar signs, second group is the content
    math_functions = re.findall(r'(\${1,2})((?:(?!\1)[\s\S])*)\1', result, re.DOTALL)

    # Replace the math functions in the latex content with the original math_function from markdown (the converter sucks)
    for i, math_func_need in enumerate(math_functions):
        math_func_need_str = str(math_func_need[0]) + str(math_func_need[1]) + str(math_func_need[0]) # The entire math function
        math_func_str = str(math_functions[i][0]) + util_process_equation(str(math_functions[i][1])) + str(math_functions[i][0]) # Processed math function
        result = result.replace(math_func_need_str, math_func_str, 1)
    
    # Change back the math delimiters
    result = result.replace("$", "~")

    # Change back the image links
    result = result.replace("!!FileImage!!", "![](")
    result = result.replace("!!EndFileImage!!", ")")

    # Change back the code blocks
    result = result.replace("!!Codeblock!!", "```")
    result = result.replace("!!EndCodeblock!!", "```")

    # Replace dollar sign
    result = result.replace("!!Dollar!!", "\\$")

    return unicodedata.normalize("NFC", result)

def main_converter(url: str, override = None):
    """Main function."""
    problem = {}
    problem_folder_name = ""

    dmoj_list = DMOJ_INDICATOR_LIST.strip().strip("\n").splitlines()
    lqdoj_list = LQDOJ_INDICATOR_LIST.strip().strip("\n").splitlines()

    detected = 0
    if "codeforces.com" in url:
        # Get the raw problem content from the Codeforces site
        print("[Codeforces] Getting the problem content...")
        detected = 1
        problem = get_base_problem_codeforces(url, override)
    
    if "csloj.ddns.net" in url:
        # Get the raw problem content from the CSLOJ site
        print("[CSLOJ] Getting the problem content...")
        detected = 1
        problem = get_base_problem_csloj(url, override)

    for lqdoj_indicator in lqdoj_list:
        lqdoj_indicator = lqdoj_indicator.strip().strip("\n")
        if lqdoj_indicator in url:
            # Get the raw problem content from LQDOJ 
            print("[LQDOJ] Getting the problem content...")
            detected = 1
            problem = get_base_problem_lqdoj(url, override)
            break
    
    for dmoj_indicator in dmoj_list:
        dmoj_indicator = dmoj_indicator.strip().strip("\n")
        if dmoj_indicator in url:
            # Get the raw problem content from the DMOJ-themed site
            print("[DMOJ] Getting the problem content...")
            detected = 1
            problem = get_base_problem_dmoj(url, override)
            break
    
    if(detected == 0):
        print("The site is not officially supported. Defaulting to DMOJ...")

        # Get the raw problem content from the DMOJ site
        print("[DMOJ] Getting the problem content...")
        problem = get_base_problem_dmoj(url, override)

    problem_folder_name = problem["problem_site"] + '+' + problem["problem_code"]
    print(f"[{problem["problem_site_type"]}] You can find the output files in the 'output/{problem_folder_name}' folder.")

    if(os_create_folder(f"output/{problem_folder_name}")):
        print(f"[{problem["problem_site_type"]}] Getting the embedded files...")
        get_files(problem["problem_content_raw"], problem["problem_site"], problem_folder_name, problem["problem_site_type"])
        print(f"[{problem["problem_site_type"]}] Getting the test case file...")
        get_zip_test_files(problem["problem_content_raw"], url, problem_folder_name, problem["problem_site_type"])

    # Extract the testcases from the problem content
    print("Extracting the testcases...")
    problem_testcases = get_testcases(problem["problem_content_raw"], problem["problem_site_type"])

    # Insert result and problem_testcases into a dictionary
    problem["problem_testcases"] = problem_testcases
    
    # Convert the base HTML problem content to Markdown
    print("Converting the problem content to base Markdown...")
    problem["problem_content_md"] = convert_html_to_markdown(problem)

    # Convert the problem content to base LaTeX formats
    print("Converting the problem content to base LaTeX...")
    problem["problem_content_latex_base"] = convert_to_latex_base(problem)

    # Convert the problem content to LaTeX formats
    print("Converting the problem content to General LaTeX...")
    result = convert_to_latex_general(problem)
    with open(f"output/{problem_folder_name}/general.tex", "w", encoding="utf8") as file:
        file.write(result)
    
    print("Converting the problem content to Polygon LaTeX...")
    result = convert_to_latex_polygon(problem)
    with open(f"output/{problem_folder_name}/polygon.tex", "w", encoding="utf8") as file:
        file.write(result)
    
    print("Converting the problem content to Template LaTeX...")
    result = convert_to_latex_template(problem)
    with open(f"output/{problem_folder_name}/{problem["problem_code"]}.tex", "w", encoding="utf8") as file:
        file.write(result)

    print("Converting the problem content to Markdown for DMOJ...")
    result = convert_to_md_dmoj(problem)
    with open(f"output/{problem_folder_name}/dmoj.md", "w", encoding="utf8") as file:
        file.write(result)

    # Save the problem to a JSON file
    print("Saving the problem to a JSON file...")
    with open(f"output/{problem_folder_name}/problem.json", "w", encoding="utf8") as file:
        json.dump(problem, file, indent=4, ensure_ascii=False)
    
    return problem

if __name__ == "__main__":
    url = input("Enter the problem URL: ")
    try:
        main_converter(url)
    except Exception as e:
        print(f"Error: {e}")
        if e:
            print(INSTRUCT_USING_MANUAL_VI)

            # Create a temporary text file then open it using notepad
            with open("manual.txt", "w", encoding="utf8") as file:
                file.write(INSTRUCT_USING_MANUAL_VI + "\n\nĐọc hướng dẫn rồi dán nội dung response mới copy vào đây...\n")
            
            try:
                import os
                os.system("notepad manual.txt")
            except:
                print("Failed to open notepad. Please open the text file 'manual.txt' manually.")

            input("If you saved the file, please press Enter to continue; else press Ctrl-C to cancel.")
            
            # Read the content of the file
            with open("manual.txt", "r", encoding="utf8") as file:
                override = file.read()
                override = override.replace(INSTRUCT_USING_MANUAL_VI + "\n\nĐọc hướng dẫn rồi dán nội dung response mới copy vào đây...\n", "", 1)
            
            try:
                main_converter(url, override)
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()
                print("Failed to convert the problem.")
    
    print("Done!")
    input("Press Enter to exit.")