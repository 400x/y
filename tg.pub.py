import datetime
import pathlib
import re

# CI GitHub script for publish tg.txt to tg.html

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>mtProto {}</title>
    <meta name="viewport" content="user-scalable=yes, width=device-width, initial-scale=1.0"/>
    <style>
        body {{ font-family: Courier; padding: 10px; }}
        a {{ text-decoration: none }}
        li {{ padding: 2px; white-space: nowrap; font-weight: bold; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }}
        li.hidden {{ opacity: 0; transform: translateX(-20px); height: 0; padding: 0; margin: 0; pointer-events: none; }}
    </style>
</head>
<body>
<ol>
{}
</ol>

<script type="text/javascript">
    const links = document.querySelectorAll("a");
    links.forEach(a => {{
        a.addEventListener('click', function() {{
            this.closest("li").classList.add('hidden');
        }});
    }});
</script>

</body>
</html>
"""


def pub_tg(txt_file):
    if not txt_file.exists():
        return

    content = txt_file.read_text(encoding="utf-8").splitlines()
    lst = []
    for line in sorted(content):
        if line.strip():
            parsed = re.match(r"^.*?(server=(.+?)&.+)", line)
            if parsed:
                lst.append(f'<li><a href="tg://proxy?{parsed.group(1)}">{parsed.group(2)}</a></li>')

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    htm = HTML_TEMPLATE.format(now, "\n".join(lst))
    htm_file = txt_file.with_suffix(".html")
    htm_file.write_text(htm, encoding="utf-8")


pub_tg(pathlib.Path(__file__).parent / "tg.txt")
