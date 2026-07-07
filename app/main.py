import argparse
from nicegui import app, ui
import db

# Import all pages so their @ui.page routes are registered
import pages.dashboard
import pages.teachers
import pages.playgroups
import pages.children

# Initialize database pool on startup
app.on_startup(db.init_db_pool)

# Close database pool on shutdown
app.on_shutdown(db.close_db_pool)

if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(description="Run NiceGUI app")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args, _ = parser.parse_known_args()

    # Start NiceGUI natively using the arguments passed by Docker CMD
    ui.run(title='Kids Database Manager', reload=True, port=args.port, host=args.host)
