"""
Application runner script.
Run with: python run.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                   WiFi Tracker System                        ║
    ║                      Version {settings.APP_VERSION}                          ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Starting server at http://{settings.HOST}:{settings.PORT}
    API Documentation: http://localhost:{settings.PORT}/docs
    
    Press CTRL+C to stop the server.
    """)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
