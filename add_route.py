#!/usr/bin/env python3
with open('app_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '@app.get("/", response_class=HTMLResponse)\nasync def index(request: Request) -> HTMLResponse:\n    return templates.TemplateResponse("index.html", {"request": request})'

if marker in content and '/ai-diagnostics' not in content:
    new_route = '''\n\n@app.get("/ai-diagnostics", response_class=HTMLResponse)\nasync def ai_diagnostics_page(request: Request) -> HTMLResponse:\n    return templates.TemplateResponse("ai_diagnostics.html", {"request": request})'''
    content = content.replace(marker, marker + new_route)
    with open('app_main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Added /ai-diagnostics route!")
else:
    print("⚠️ Route already exists or marker not found")
