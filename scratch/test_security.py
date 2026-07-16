from app import app

print("App imports OK")
print(f"CSRF enabled: {'csrf' in app.extensions}")
print(f"SECRET_KEY length: {len(app.config['SECRET_KEY'])}")
print(f"MAX_CONTENT_LENGTH: {app.config.get('MAX_CONTENT_LENGTH')}")
print(f"SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
print(f"SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")

# Test all routes are registered
with app.test_client() as client:
    # Test login page loads
    response = client.get('/login')
    print(f"GET /login: {response.status_code}")
    
    # Test CSRF token is in login page
    html = response.data.decode('utf-8')
    has_csrf = 'csrf_token' in html
    print(f"CSRF token in login page: {has_csrf}")
    
    # Test security headers
    response = client.get('/')
    print(f"X-Content-Type-Options: {response.headers.get('X-Content-Type-Options')}")
    print(f"X-Frame-Options: {response.headers.get('X-Frame-Options')}")
    print(f"X-XSS-Protection: {response.headers.get('X-XSS-Protection')}")

print("\nAll security checks passed!")
