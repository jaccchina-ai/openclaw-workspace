#!/usr/bin/env python3
"""
Convert Markdown to PDF using WeasyPrint
"""

import sys
import os
from markdown import markdown
from weasyprint import HTML

def markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF"""
    try:
        # Read markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown(md_content, extensions=['extra', 'tables'])
        
        # Add basic CSS styling
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 40px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>T99选股策略详解</h1>
        <p>生成时间: {sys.argv[3] if len(sys.argv) > 3 else "2026-02-27"}</p>
    </div>
    {html_content}
    <div class="footer">
        <p>—— 文档生成自 AI 助手 ——</p>
    </div>
</body>
</html>"""
        
        # Convert HTML to PDF
        HTML(string=styled_html).write_pdf(pdf_file)
        print(f"Successfully converted {markdown_file} to {pdf_file}")
        return True
        
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python markdown_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)
    
    success = markdown_to_pdf(input_file, output_file)
    sys.exit(0 if success else 1)