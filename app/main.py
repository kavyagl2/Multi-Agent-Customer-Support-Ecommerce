from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import models
from .schemas import schemas
from .agents.query_analyzer import QueryAnalyzer
from .agents.sql_generator import SQLGenerator
from .agents.response_formatter import ResponseFormatter
from .auth.auth_handler import (
    get_current_user,
    verify_password,
    create_access_token,
    get_password_hash
)
from .config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserInDB)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/query")
async def process_query(
    request: schemas.QueryRequest,
    current_user: schemas.TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Initialize agents
        query_analyzer = QueryAnalyzer(settings.GROQ_API_KEY)
        sql_generator = SQLGenerator(settings.GROQ_API_KEY)
        response_formatter = ResponseFormatter(settings.GROQ_API_KEY)
        
        # Analyze query
        user_context = {
            "user_id": current_user.user_id,
            "email": current_user.email,
            **(request.context or {})
        }
        query_intent = query_analyzer.analyze_query(request.query, user_context)
        
        # Generate SQL
        sql_query = sql_generator.generate_sql(query_intent, current_user.user_id)
        
        # Execute query
        result = db.execute(sql_query.query, sql_query.parameters).fetchall()
        results_dict = [dict(row) for row in result]
        
        # Format response
        response = response_formatter.format_response(
            request.query,
            results_dict,
            user_context
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
