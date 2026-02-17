from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.config.database import engine, Base
from src.models import User, UserPortfolio, Skill, UserSkill, ConnectionEvent, Connection
from src.routes import users
from src.routes.users import router as user_router
from src.routes.user_skills import router as user_skill_router
from src.routes.skills import router as skills_router
from src.routes.user_portfolio import router as user_portfolio_router
from src.routes.connections import router as connections_router
from src.routes.uploads import router as uploads_router
from src.routes.auth import router as auth_router
from src.routes.messaging import router as messaging_router
from src.routes.reviews import router as reviews_router
from src.routes.sessions import router as sessions_router
from src.routes.notifications import router as notifications_router
from src.routes.reports import router as reports_router



app = FastAPI(
    title="Peer-to-Peer Skill Discovery Platform",
    description="A platform for sharing and learning skills from peers",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user_router)
app.include_router(user_skill_router)
app.include_router(skills_router)
app.include_router(user_portfolio_router)
app.include_router(connections_router)
app.include_router(uploads_router)
app.include_router(auth_router)
app.include_router(messaging_router)
app.include_router(reviews_router)
app.include_router(sessions_router)
app.include_router(notifications_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Skill Discovery Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        }
