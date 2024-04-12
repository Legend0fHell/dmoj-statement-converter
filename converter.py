import json
import re
import requests
import markdown
import markdownify
import markdown2latex.mdx_latex as MDXLatex

SPECIAL_CHAR_BULLET = "―"
LATEX_HEADER = """
\\documentclass[12pt,a4paper]{article}
\\usepackage[utf8]{vietnam}
\\usepackage{graphicx}
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

TESTCASE_INDICATOR_LIST = ["Sample", "Example", "Ví dụ", "Test", "Testcase", "Case"]

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

def get_dmoj_raw_problem(url: str, override = None):
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
    html_response = html_response.split('<iframe name="raw_problem" id="raw_problem"></iframe>')

    # First half is the problem details
    html_problem_details = html_response[0]

    # Extract the problem title, info entries, types, allowed langs, and content
    problem_title = html_problem_details.split('<h2 style="display: inline-block">')[1].split('</h2>')[0].strip()
    html_problem_info_entries = html_problem_details.split('<div class="problem-info-entry">')[1:]

    problem_info_entries = {}
    for entry in html_problem_info_entries:
        entry = entry.split('</div>')[0]
        entry_name = entry.split('pi-name">')[1].split(':</span>')[0].strip()
        entry_value = entry.split('-value">')[1]

        if(entry_value.find('</span>') != -1):
            entry_value = entry_value.split('</span>')[0].strip()
        elif(entry_value.find('</div>') != -1):
            entry_value = entry_value.split('</div>')[0].strip()

        # Remove all HTML tags in the entry value
        entry_value = re.sub(r'<[^>]*>', '', entry_value)
        problem_info_entries[entry_name] = entry_value

    html_problem_types = html_problem_details.split('<div id="problem-types">')[1]
    html_problem_types = html_problem_types.split('class="toggled">')[1]
    html_problem_types = html_problem_types.split('</div>')[0]

    problem_types = html_problem_types.split(',')
    problem_types = [problem_type.strip() for problem_type in problem_types]

    html_problem_allowed_langs = html_problem_details.split('<div id="allowed-langs">')[1]
    html_problem_allowed_langs = html_problem_allowed_langs.split('class="toggled">')[1]
    html_problem_allowed_langs = html_problem_allowed_langs.split('</div>')[0]

    problem_allowed_langs = html_problem_allowed_langs.split(',')
    problem_allowed_langs = [lang for lang in problem_allowed_langs if lang.find('<s title="') == -1]
    problem_allowed_langs = [lang.strip() for lang in problem_allowed_langs]

    # Second half is the problem content
    html_problem_content = html_response[1].split('<script type="text/javascript" src="/static/mathjax_config.js"></script>')[0]
    html_problem_content = html_problem_content.split('<hr>\n')[0].strip().strip("\n")

    return {
        "problem_code": problem_code,
        "problem_site": problem_site,
        "problem_url": url,
        "problem_title": problem_title,
        "problem_info_entries": problem_info_entries,
        "problem_types": problem_types,
        "problem_allowed_langs": problem_allowed_langs,
        "problem_content_raw": html_problem_content
    }

def get_martor_files(problem_content: str, problem_site: str, problem_folder_name: str):
    """Return the list of Martor files from the problem content."""

    # Extract the Martor files from the problem content
    martor_files = re.findall(r'\/martor(.+?)"', problem_content)

    # Remove the duplicates
    martor_files = list(set(martor_files))

    # Download the Martor files
    for martor_file in martor_files:
        response = requests.get(f"https://{problem_site}/martor{martor_file}")

        if(response.status_code != 200):
            raise Exception("Failed to get Martor file from DMOJ-themed site")

        # Save the Martor file
        with open(f"output/{problem_folder_name}{martor_file}", "wb") as file:
            file.write(response.content)

    return martor_files


def extract_testcase(problem_content: str):
    """Extract the testcases from the problem content."""

    # Remove the content before the first testcase, if not found, raise a warning
    for(indicator) in TESTCASE_INDICATOR_LIST:
        if problem_content.find(indicator) != -1:
            problem_content = problem_content[problem_content.find(indicator):]
            break
    else:
        raise Warning("There is no clear indication of the testcases in the problem content. Please check the problem content.")

    # Replace to make the content easier to parse
    problem_content = problem_content.replace('<pre><code>', '||begin||').replace('</code></pre>', '||end||')

    # Remove the content after the last testcase
    problem_content = problem_content[:problem_content.rfind('||end||') + len('||end||')]

    # Remove all HTML tags
    problem_content = re.sub(r'<[^>]*>', '\n', problem_content)

    # Extract the testcases from "||begin||" to "||end||"
    testcases = re.findall(r'\|\|begin\|\|(.+?)\|\|end\|\|', problem_content, re.DOTALL)

    # Remove the leading and trailing whitespaces
    testcases = [testcase.strip() for testcase in testcases]

    if len(testcases) % 2 != 0:
        raise Warning("There is an odd number of testcases, please check the problem content.")
    
    # Split the testcases into input and output
    testcases_separated = []
    for i in range(0, len(testcases), 2):
        testcases_separated.append([testcases[i], testcases[i + 1]])

    return testcases_separated

def convert_html_to_markdown(html: str, bullet="*", replace_latex = True):
    """Convert HTML content to Markdown content."""

    result = markdownify.markdownify(html, heading_style="ATX", bullets=bullet)

    # Replace dollar sign to prevent the math functions from being replaced
    result = re.sub(r'\\\$', r'!!Dollar!!', result)

    # Change the latex math delimiters
    if replace_latex:
        # result = result.replace("~~", "~")
        result = result.replace("~", "$")
    
    # Undo the MDXLatex's escape of some special characters (Line :50)
    result = result.replace("\\_", "_")
    # result = result.replace("\\%", "%")
    # result = result.replace("\\&", "&")
    # result = result.replace("\\#", "#")

    # Replace some special cases
    result = result.replace("\\left(", "\\ (")
    result = result.replace("\\right)", ")")
    result = result.replace("\\left[", "\\ [")
    result = result.replace("\\right]", "]")
    result = result.replace("\\left{", "\\ {")
    result = result.replace("\\right}", "}")
    result = result.replace("\\left|", "|")
    result = result.replace("\\right|", "|")

    # Escape the \ character 

    # Remove "/martor/" from the image links
    result = result.replace("/martor/", "")

    # Replace image links with a template to process later
    result = re.sub(r'!\[(.*?)\]\((.*?)\)', r'\n!!FileImage!!\2!!EndFileImage!!\n', result)

    # Replace code blocks with a template to process later
    result = re.sub(r'\`\`\`((.|\n)*?)\`\`\`', r'\n!!Codeblock!!\1!!EndCodeblock!!\n', result)

    result = result.strip().strip("\n")
    
    return result

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
    problem_info += f"\\textbf{{URL}}: \\url{"{" + problem['problem_url'] + "}"} \\\\\n"
    problem_info += f"\\textbf{{Tên bài}}: {problem['problem_title']} \\\\\n"

    for entry_name, entry_value in problem["problem_info_entries"].items():
        problem_info += f"\\textbf{{{entry_name}}}: {entry_value} \\\\\n"

    problem_info += f"\\textbf{{Tags}}: {', '.join(problem['problem_types'])} \\\\\n"
    problem_info += f"\\textbf{{Ngôn ngữ cho phép}}: {', '.join(problem['problem_allowed_langs'])} \\\\\n"

    # Escape the special characters
    problem_info = problem_info.replace("_", "\\_")
    problem_info = problem_info.replace("%", "\\%")
    problem_info = problem_info.replace("&", "\\&")
    problem_info = problem_info.replace("#", "\\#")

    return problem_info

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

def convert_to_latex_base(problem: dict):
    """Base function to convert the problem content to LaTeX format."""
    markdown_content = convert_html_to_markdown(problem["problem_content_raw"])

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
        math_func_str = str(math_functions[i][0]) + str(math_functions[i][1]) + str(math_functions[i][0]) # The original math function
        result = result.replace(math_func_need_str, math_func_str, 1)

    # Replace dollar sign 
    result = result.replace("!!Dollar!!", "\\$")

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

    # Replace the image links with the correct LaTeX format
    result = result.replace("!!FileImage!!", "\\includegraphics{")
    result = result.replace("!!EndFileImage!!", "}")

    # No number in the section
    result = result.replace("section{", "section*{")

    # Replace the code blocks with the correct LaTeX format (if any)
    result = result.replace("!!Codeblock!!", "\n\\begin{lstlisting}")
    result = result.replace("!!EndCodeblock!!", "\n\\end{lstlisting}")

    return result

def replace_old_testcase(problem_content_latex: str, testcase_str: str):
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
        raise Warning("There is no clear indication of the testcases in the problem content. Please check the problem content.")
    
    # Remove the content after the last testcase
    problem_testcase_content = problem_testcase_content[:problem_testcase_content.rfind('\\end{lstlisting}') + len('\\end{lstlisting}')]

    return problem_content_latex.replace(problem_testcase_content, "\n\n" + testcase_str)


def convert_to_latex(problem: dict):
    """Convert the problem content to LaTeX format."""
    result = convert_to_latex_base(problem)

    # Insert a table with the testcases
    testcase_str = generate_testcase_table(problem["problem_testcases"], problem["problem_info_entries"]["Input"], problem["problem_info_entries"]["Output"])
    result = replace_old_testcase(result, testcase_str)

    # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
    problem_info = generate_problem_info(problem)
    result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

    return result

def convert_to_polygon_latex(problem: dict):
    """Convert the problem content to LaTeX format for Polygon."""
    result = convert_to_latex_base(problem)

    # Insert a list with the testcases
    testcase_str = generate_testcase_list(problem["problem_testcases"], problem["problem_info_entries"]["Input"], problem["problem_info_entries"]["Output"])
    result = replace_old_testcase(result, testcase_str)

    # Replace only the first occurrence of "<root>" and last occurrence of "</root>" with the LaTeX header and footer
    problem_info = generate_problem_info(problem)
    result = result.replace("<root>", LATEX_HEADER + problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{document}"[::-1], 1)[::-1]

    return result

def convert_to_template_latex(problem: dict):
    """Convert the problem content to LaTeX format for Templates."""
    result = convert_to_latex_base(problem)

    # Insert a table with the testcases
    testcase_str = generate_testcase_exmp(problem["problem_testcases"], problem["problem_info_entries"]["Input"], problem["problem_info_entries"]["Output"])
    result = replace_old_testcase(result, testcase_str)

    problem_info = "\\begin{statement}" + "[" + problem["problem_title"] + "]{" + problem["problem_code"] + "}{" + problem["problem_info_entries"]["Input"] + "}{" + problem["problem_info_entries"]["Output"] + "}{xxx}{yyy}{\\points{}}"

    problem_info += generate_problem_info(problem)

    problem_info += "\n\\InputFile\n\\OutputFile\n\\begin{Scoring}\n\n\\end{Scoring}\n"
    result = result.replace("<root>", problem_info, 1)
    result = result[::-1].replace("</root>"[::-1], "\\end{statement}"[::-1], 1)[::-1]

    return result

def create_folder(folder_name: str):
    """Create a folder with the given name if it does not exist."""

    import os

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        return True
    
    return False

def main_converter(url: str, override = None):
    """Main function."""
    problem = get_dmoj_raw_problem(url, override)

    problem_folder_name = problem["problem_site"] + '+' + problem["problem_code"]

    if(create_folder(f"output/{problem_folder_name}")):
        get_martor_files(problem["problem_content_raw"], problem["problem_site"], problem_folder_name)

    problem_testcases = extract_testcase(problem["problem_content_raw"])

    # Insert result and problem_testcases into a dictionary
    problem["problem_testcases"] = problem_testcases
    
    # Save the problem to a JSON file
    with open(f"output/{problem_folder_name}/problem.json", "w", encoding="utf8") as file:
        json.dump(problem, file, indent=4, ensure_ascii=False)
    
    result = convert_to_latex(problem)
    with open(f"output/{problem_folder_name}/general.tex", "w", encoding="utf8") as file:
        file.write(result)
    
    result = convert_to_polygon_latex(problem)
    with open(f"output/{problem_folder_name}/polygon.tex", "w", encoding="utf8") as file:
        file.write(result)
    
    result = convert_to_template_latex(problem)
    with open(f"output/{problem_folder_name}/{problem["problem_code"]}.tex", "w", encoding="utf8") as file:
        file.write(result)

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
                print("Failed to convert the problem.")
    
    print("Done!")
    print("The output files are saved in the 'output' folder.")
    input("Press Enter to exit.")