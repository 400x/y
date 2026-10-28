import datetime
import html
import pathlib
import re
import subprocess


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>mtProto</title>
    <meta name="viewport" content="user-scalable=yes, width=device-width, initial-scale=1.0"/>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='25 25 100 100'%3E%3Ccircle cx='75' cy='75' r='50' fill='%234A90E2'/%3E%3Ccircle cx='75' cy='55' r='7' fill='%23FFFFFF'/%3E%3Ccircle cx='95' cy='75' r='7' fill='%23FFFFFF'/%3E%3Ccircle cx='75' cy='95' r='7' fill='%23FFFFFF'/%3E%3Ccircle cx='55' cy='75' r='7' fill='%23FFFFFF'/%3E%3Cline x1='75' y1='55' x2='95' y2='75' stroke='%23FFFFFF' stroke-width='2'/%3E%3Cline x1='95' y1='75' x2='75' y2='95' stroke='%23FFFFFF' stroke-width='2'/%3E%3Cline x1='75' y1='95' x2='55' y2='75' stroke='%23FFFFFF' stroke-width='2'/%3E%3Cline x1='55' y1='75' x2='75' y2='55' stroke='%23FFFFFF' stroke-width='2'/%3E%3C/svg%3E">
    <style>
        body {{ font-family: Courier; padding: 10px; }}
        a {{ text-decoration: none }}
        li {{ padding: 2px; white-space: nowrap; font-weight: bold; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }}
        li.hidden {{ opacity: 0; transform: translateX(-20px); height: 0; padding: 0; margin: 0; pointer-events: none; }}
        .age {{ color: #777; font-weight: normal; display:inline-block; width: 30px; }}
    </style>
</head>
<body>
<h3># {}</h3>
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


def parse_items(content):
    items = {}
    for line in content.splitlines():
        if not line.strip():
            continue
        parsed = re.match(r"^.*?(proxy|webproxy)\?(server=(.+?)&.+)", line)
        if parsed:
            link = f'tg://{parsed.group(1)}?{parsed.group(2)}'
            items[link] = parsed.group(3).split("%2F")[0]
    return items


def git(*args):
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)


def latest_continuous_presence_dates():
    """Return the start date of each item's current uninterrupted presence."""
    dates = {}
    previous_items = set()
    commits = git("log", "--reverse", "--format=%H", "--", "tg.txt").splitlines()

    for commit in commits:
        try:
            commit_date = datetime.date.fromisoformat(
                git("show", "-s", "--format=%cs", commit).strip()
            )
            content = git("show", f"{commit}:tg.txt")
        except subprocess.CalledProcessError:
            # For example, a commit before tg.txt was created.
            continue

        current_items = set(parse_items(content))

        # Reset the start date whenever an item reappears after being absent.
        for link in current_items - previous_items:
            dates.setdefault(link, commit_date) # use first date
            # dates[link] = commit_date # use last date

        previous_items = current_items

    return dates


def pub_tg(txt_file):
    if not txt_file.exists():
        return

    today = datetime.date.today()
    items = parse_items(txt_file.read_text(encoding="utf-8"))
    first_seen = latest_continuous_presence_dates()

    dated_items = []
    for link, server in items.items():
        # If an item has no history, use today's date as a safe fallback.
        start_date = first_seen.get(link, today)
        days = max(0, (today - start_date).days)
        dated_items.append((days, server.lower(), link, server))

    dated_items.sort(key=lambda item: (-item[0], item[1], item[2]))

    lst = []
    for days, _server_sort, link, server in dated_items:
        lst.append(
            f'<li><span title="{days} days in list" class="age">{days} </span>'
            f'<a href="{html.escape(link, quote=True)}">'
            f'{html.escape(server)}</a></li>'
        )

    now = today.strftime("%d %b")
    htm = HTML_TEMPLATE.format(now, "\n".join(lst))
    txt_file.with_suffix(".html").write_text(htm, encoding="utf-8")


pub_tg(pathlib.Path(__file__).parent / "tg.txt")
