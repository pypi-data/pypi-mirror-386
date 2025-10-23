"""List Follows - Admin interface

Handles GET /admin/follows
"""

from dbbasic_follows import Follows


def handle(request):
    """
    Handle /admin/follows requests.

    Lists all follow relationships in the system.
    """
    # Initialize follows API
    follows = Follows()

    # Get all follow relationships
    all_follows = follows.table.select()

    # Build item data for display
    item_data = []
    for follow in all_follows:
        item_data.append({
            'id': follow.get('id', ''),
            'follower_id': follow.get('follower_id', ''),
            'followee_id': follow.get('followee_id', ''),
            'status': follow.get('status', ''),
            'created_at': follow.get('created_at', ''),
        })

    # Build HTML
    from dbbasic_admin.admin import build_nav
    nav_items = build_nav()
    nav_html = "".join(f'<li><a href="{item["href"]}">{item.get("icon", "")} {item["label"]}</a></li>' for item in nav_items)

    # Build table rows
    rows_html = ""
    for item in item_data:
        rows_html += f"""
        <tr>
            <td><input type="checkbox" value="{item['id']}"></td>
            <td>{item['follower_id']}</td>
            <td>→</td>
            <td>{item['followee_id']}</td>
            <td><span style="color: {'green' if item['status'] == 'active' else 'gray'};">●</span> {item['status']}</td>
            <td>{item['created_at'][:10] if item['created_at'] else ''}</td>
            <td>
                <div class="action-buttons">
                    <form method="POST" action="/admin/follows/delete/{item['id']}" style="display: inline;">
                        <button type="submit" class="btn-icon" title="Delete" onclick="return confirm('Remove this follow relationship?')">🗑️</button>
                    </form>
                </div>
            </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Follows - Admin</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; height: 100vh; background: #f5f5f5; }}
        .sidebar {{ width: 250px; background: #2c3e50; color: white; padding: 20px; overflow-y: auto; }}
        .sidebar h1 {{ font-size: 24px; margin-bottom: 30px; color: #ecf0f1; }}
        .sidebar ul {{ list-style: none; }}
        .sidebar li {{ margin-bottom: 10px; }}
        .sidebar a {{ color: #ecf0f1; text-decoration: none; display: block; padding: 10px; border-radius: 5px; transition: background 0.2s; }}
        .sidebar a:hover, .sidebar a.active {{ background: #34495e; }}
        .content {{ flex: 1; padding: 40px; overflow-y: auto; }}
        .header {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
        .header h2 {{ color: #2c3e50; margin: 0; }}
        .btn-primary {{ background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }}
        .btn-primary:hover {{ background: #2980b9; }}
        .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .table-container {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .action-buttons {{ display: flex; gap: 5px; }}
        .btn-icon {{ background: none; border: none; cursor: pointer; font-size: 16px; padding: 5px; }}
        .btn-icon:hover {{ opacity: 0.7; }}
        .breadcrumb {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="sidebar"><h1>Admin</h1><ul>{nav_html}</ul></div>
    <div class="content">
        <div class="header">
            <div>
                <h2>👥 Social Graph</h2>
                <div class="breadcrumb">Home / Follows</div>
            </div>
        </div>

        <div class="card">
            <h3 style="margin-bottom: 20px;">Follow Relationships ({len(item_data)})</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th><input type="checkbox"></th>
                            <th>Follower</th>
                            <th></th>
                            <th>Following</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html if rows_html else '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #999;">No follow relationships yet</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

    # Return HTML response using dbbasic_web format
    try:
        from dbbasic_web.responses import html as html_response
        return html_response(html_content)
    except ImportError:
        # Fallback if dbbasic_web not available
        return (200, [('content-type', 'text/html; charset=utf-8')], [html_content.encode()])
