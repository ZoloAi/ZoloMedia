# zCLI/subsystems/zServer/zServer_modules/error_pages.py

"""
Built-in Error Pages for zServer

Provides default HTML error pages for common HTTP status codes.
These are fallbacks when custom error templates don't exist.

Philosophy:
    - "Just Works" - No config needed, errors always look professional
    - Override-able - Create templates/404.html to customize
    - Convention - Like nginx, Apache, Flask

Usage:
    handler.py and wsgi_app.py use these when template not found
"""

# =============================================================================
# BUILT-IN ERROR PAGE TEMPLATES
# =============================================================================

DEFAULT_ERROR_PAGES = {
    400: """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>400 - Bad Request</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .error-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }}
        .error-code {{
            font-size: 72px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        h1 {{ color: #333; font-size: 24px; margin-bottom: 15px; }}
        p {{ color: #666; line-height: 1.6; margin-bottom: 25px; }}
        .home-link {{
            display: inline-block;
            background: #667eea;
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 6px;
            transition: background 0.3s;
        }}
        .home-link:hover {{ background: #5568d3; }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">400</div>
        <h1>Bad Request</h1>
        <p>The request could not be understood by the server. Please check your request and try again.</p>
        <a href="/" class="home-link">← Back to Home</a>
    </div>
</body>
</html>""",

    403: """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 - Access Denied</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.css">
</head>
<body class="zBg-light">
    <div class="zHero zHero-full">
        <div class="zContainer">
            <div class="zCard zText-center" style="max-width: 600px; margin: 0 auto;">
                <div style="font-size: 6rem; font-weight: 700; color: var(--zolo-danger); margin-bottom: 1rem;">403</div>
                <h1 class="zTitle-2 zmb-3">Access Denied</h1>
                <p class="zText-muted">You don't have permission to access this resource. Authentication or specific role privileges are required.</p>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.js"></script>
</body>
</html>""",

    404: """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page Not Found</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.css">
</head>
<body class="zBg-light">
    <div class="zHero zHero-full">
        <div class="zContainer">
            <div class="zCard zText-center" style="max-width: 600px; margin: 0 auto;">
                <div style="font-size: 6rem; font-weight: 700; color: var(--zolo-primary); margin-bottom: 1rem;">404</div>
                <h1 class="zTitle-2 zmb-3">Page Not Found</h1>
                <p class="zText-muted">Sorry, the page you're looking for doesn't exist or has been moved.</p>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.js"></script>
</body>
</html>""",

    405: """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>405 - Method Not Allowed</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .error-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }}
        .error-code {{
            font-size: 72px;
            font-weight: bold;
            color: #fa709a;
            margin-bottom: 10px;
        }}
        h1 {{ color: #333; font-size: 24px; margin-bottom: 15px; }}
        p {{ color: #666; line-height: 1.6; margin-bottom: 25px; }}
        .home-link {{
            display: inline-block;
            background: #fa709a;
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 6px;
            transition: background 0.3s;
        }}
        .home-link:hover {{ background: #e8608a; }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">405</div>
        <h1>Method Not Allowed</h1>
        <p>The requested method is not allowed for this resource.</p>
        <a href="/" class="home-link">← Back to Home</a>
    </div>
</body>
</html>""",

    500: """<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>500 - Server Error</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.css">
</head>
<body class="zBg-light">
    <div class="zHero zHero-full">
        <div class="zContainer">
            <div class="zCard zText-center" style="max-width: 600px; margin: 0 auto;">
                <div style="font-size: 6rem; font-weight: 700; color: var(--zolo-warning); margin-bottom: 1rem;">500</div>
                <h1 class="zTitle-2 zmb-3">Internal Server Error</h1>
                <p class="zText-muted">An unexpected error occurred while processing your request. Please check the server logs for details.</p>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@c687707/dist/ztheme.js"></script>
</body>
</html>""",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_error_page(status_code: int, custom_message: str = None) -> str:
    """
    Get error page HTML for given status code.
    
    Args:
        status_code: HTTP status code (400, 403, 404, 405, 500)
        custom_message: Optional custom error message to include
    
    Returns:
        HTML string for error page
    
    Notes:
        - Returns built-in page if status_code in DEFAULT_ERROR_PAGES
        - Returns generic 500 page for unknown status codes
        - Custom message can be injected into template
    """
    # Get default page or fallback to 500
    html = DEFAULT_ERROR_PAGES.get(status_code, DEFAULT_ERROR_PAGES[500])
    
    # Inject custom message if provided (future enhancement)
    if custom_message:
        # Could replace a placeholder in the template
        pass
    
    return html


def has_error_page(status_code: int) -> bool:
    """
    Check if built-in error page exists for status code.
    
    Args:
        status_code: HTTP status code to check
    
    Returns:
        True if built-in page exists, False otherwise
    """
    return status_code in DEFAULT_ERROR_PAGES

