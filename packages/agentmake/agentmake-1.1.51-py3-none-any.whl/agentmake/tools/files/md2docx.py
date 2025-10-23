from agentmake.utils.manage_package import installPipPackage
import shutil
REQUIREMENTS = ["pypandoc"]
try:
    import pypandoc
except:
    for i in REQUIREMENTS:
        installPipPackage(i)
    import pypandoc

TOOL_SCHEMA = {
    "name": "md2docx",
    "description": "Convert Markdown format into Docx.",
    "parameters": {
        "type": "object",
        "properties": {
            "markdown_file_path": {
                "type": "string",
                "description": "Either a file path. Return an empty string '' if not given.",
            },
            "output_file_path": {
                "type": "string",
                "description": "Output file path. Return an empty string '' if not given.",
            },
        },
        "required": ["markdown_file_path"],
    },
}

def md2docx(markdown_file: str="", output_file: str="", **kwargs):
    if not markdown_file:
        return None
    if output_file and not output_file.endswith(".docx"):
        output_file = output_file + ".docx"
    import pypandoc, os, shutil
    from agentmake import getOpenCommand
    if not shutil.which("pandoc"):
        print("Required tool 'pandoc' is not found on your system! Read https://pandoc.org/installing.html for installation.")
        return ""
    docx_file = output_file if output_file else markdown_file.replace(".md", ".docx")
    pypandoc.convert_file(markdown_file, 'docx', outputfile=docx_file)
    print(f"Converted {markdown_file} to {docx_file}")
    #os.system(f"{getOpenCommand()} {docx_file}")
    return ""

TOOL_FUNCTION = md2docx

