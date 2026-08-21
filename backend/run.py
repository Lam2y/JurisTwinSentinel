import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
        access_log=os.getenv("ACCESS_LOG", "true").lower() in {"1", "true", "yes"},
    )
