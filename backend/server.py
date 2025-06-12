from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="GreenSteps API", description="Sustainability Habit Tracker API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class HabitCreate(BaseModel):
    habit_type: str  # 'preset' or 'custom'
    habit_name: str
    description: Optional[str] = None
    date: Optional[datetime] = None

class Habit(BaseModel):
    id: str
    user_id: str
    habit_type: str
    habit_name: str
    description: Optional[str] = None
    date: datetime
    created_at: datetime

class HabitUpdate(BaseModel):
    habit_name: Optional[str] = None
    description: Optional[str] = None

class ProgressStats(BaseModel):
    total_habits: int
    this_week: int
    this_month: int
    current_streak: int
    completion_percentage: float
    weekly_progress: List[int]  # Last 7 days
    monthly_progress: List[int]  # Last 30 days

class AIInsightRequest(BaseModel):
    context: Optional[str] = None

class AIInsight(BaseModel):
    insight_type: str  # 'tip', 'motivation', 'suggestion', 'impact'
    title: str
    content: str
    emoji: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# Auth Routes
@api_router.post("/auth/signup", response_model=Token)
async def signup(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Habit Routes
@api_router.post("/habits", response_model=Habit)
async def create_habit(habit_data: HabitCreate, current_user: User = Depends(get_current_user)):
    habit_id = str(uuid.uuid4())
    habit_date = habit_data.date if habit_data.date else datetime.utcnow()
    
    habit_doc = {
        "id": habit_id,
        "user_id": current_user.id,
        "habit_type": habit_data.habit_type,
        "habit_name": habit_data.habit_name,
        "description": habit_data.description,
        "date": habit_date,
        "created_at": datetime.utcnow()
    }
    
    await db.habits.insert_one(habit_doc)
    return Habit(**habit_doc)

@api_router.get("/habits", response_model=List[Habit])
async def get_user_habits(current_user: User = Depends(get_current_user)):
    habits = await db.habits.find({"user_id": current_user.id}).sort("date", -1).to_list(1000)
    return [Habit(**habit) for habit in habits]

@api_router.get("/habits/{habit_id}", response_model=Habit)
async def get_habit(habit_id: str, current_user: User = Depends(get_current_user)):
    habit = await db.habits.find_one({"id": habit_id, "user_id": current_user.id})
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return Habit(**habit)

@api_router.put("/habits/{habit_id}", response_model=Habit)
async def update_habit(habit_id: str, habit_update: HabitUpdate, current_user: User = Depends(get_current_user)):
    habit = await db.habits.find_one({"id": habit_id, "user_id": current_user.id})
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    update_data = {k: v for k, v in habit_update.dict().items() if v is not None}
    if update_data:
        await db.habits.update_one({"id": habit_id}, {"$set": update_data})
        habit.update(update_data)
    
    return Habit(**habit)

@api_router.delete("/habits/{habit_id}")
async def delete_habit(habit_id: str, current_user: User = Depends(get_current_user)):
    result = await db.habits.delete_one({"id": habit_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"message": "Habit deleted successfully"}

@api_router.get("/progress", response_model=ProgressStats)
async def get_progress_stats(current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Get all user habits
    all_habits = await db.habits.find({"user_id": current_user.id}).to_list(1000)
    
    # Total habits
    total_habits = len(all_habits)
    
    # This week
    this_week = len([h for h in all_habits if h["date"] >= week_ago])
    
    # This month
    this_month = len([h for h in all_habits if h["date"] >= month_ago])
    
    # Calculate current streak
    current_streak = 0
    if all_habits:
        # Sort habits by date descending
        sorted_habits = sorted(all_habits, key=lambda x: x["date"], reverse=True)
        current_date = now.date()
        
        for i in range(30):  # Check last 30 days max
            check_date = current_date - timedelta(days=i)
            day_habits = [h for h in sorted_habits if h["date"].date() == check_date]
            if day_habits:
                current_streak += 1
            else:
                break
    
    # Weekly progress (last 7 days)
    weekly_progress = []
    for i in range(7):
        day = now.date() - timedelta(days=i)
        day_count = len([h for h in all_habits if h["date"].date() == day])
        weekly_progress.append(day_count)
    weekly_progress.reverse()
    
    # Monthly progress (last 30 days)
    monthly_progress = []
    for i in range(30):
        day = now.date() - timedelta(days=i)
        day_count = len([h for h in all_habits if h["date"].date() == day])
        monthly_progress.append(day_count)
    monthly_progress.reverse()
    
    # Completion percentage (habits this month vs target)
    target_days = 30
    completion_percentage = min(100.0, (this_month / target_days) * 100) if target_days > 0 else 0.0
    
    return ProgressStats(
        total_habits=total_habits,
        this_week=this_week,
        this_month=this_month,
        current_streak=current_streak,
        completion_percentage=completion_percentage,
        weekly_progress=weekly_progress,
        monthly_progress=monthly_progress
    )

# Preset habits endpoint
@api_router.get("/preset-habits")
async def get_preset_habits():
    preset_habits = [
        {"name": "Recycled items", "description": "Recycled paper, plastic, or other materials"},
        {"name": "Used public transport", "description": "Took bus, train, or other public transportation"},
        {"name": "Saved water", "description": "Recycled paper, plastic, or other materials"},
        {"name": "Ate plant-based meal", "description": "Had a vegetarian or vegan meal"},
        {"name": "Walked or biked", "description": "Chose walking or cycling over driving"},
        {"name": "Reduced energy usage", "description": "Turned off lights, unplugged devices, or used less AC"},
        {"name": "Bought local/organic", "description": "Purchased locally sourced or organic products"},
        {"name": "Avoided single-use plastic", "description": "Used reusable bags, bottles, or containers"},
        {"name": "Composted", "description": "Composted food scraps or organic waste"},
        {"name": "Planted something", "description": "Planted trees, flowers, or started a garden"}
    ]
    return preset_habits

# AI Insights Endpoint
@api_router.post("/ai/insights", response_model=List[AIInsight])
async def get_ai_insights(request: AIInsightRequest, current_user: User = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    try:
        # Get user's habits for context
        habits = await db.habits.find({"user_id": current_user.id}).sort("date", -1).to_list(100)
        
        # Get progress stats
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        this_week = len([h for h in habits if h["date"] >= week_ago])
        this_month = len([h for h in habits if h["date"] >= month_ago])
        
        # Calculate current streak
        current_streak = 0
        if habits:
            sorted_habits = sorted(habits, key=lambda x: x["date"], reverse=True)
            current_date = now.date()
            
            for i in range(30):
                check_date = current_date - timedelta(days=i)
                day_habits = [h for h in sorted_habits if h["date"].date() == check_date]
                if day_habits:
                    current_streak += 1
                else:
                    break
        
        # Get recent habit names
        recent_habits = [h["habit_name"] for h in habits[:10]]
        habit_types = list(set([h["habit_name"] for h in habits]))
        
        # Create context for AI
        context = f"""
        User: {current_user.name}
        Total habits logged: {len(habits)}
        Habits this week: {this_week}
        Habits this month: {this_month}
        Current streak: {current_streak} days
        Recent habits: {', '.join(recent_habits[:5])}
        Habit types tried: {', '.join(habit_types[:8])}
        """
        
        # Create AI chat instance
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"greensteps_{current_user.id}_{now.timestamp()}",
            system_message="You are a sustainability coach for GreenSteps app. Generate personalized insights, tips, and motivation for users based on their habit tracking data. Always be encouraging and provide actionable advice."
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(1000)
        
        # Create prompt for AI insights
        prompt = f"""Based on this user's sustainability habit data:

{context}

Generate exactly 3 different types of insights in this JSON format:
[
  {{
    "insight_type": "tip",
    "title": "Sustainability Tip",
    "content": "A specific, actionable tip based on their habits",
    "emoji": "💡"
  }},
  {{
    "insight_type": "motivation",
    "title": "Motivational Message",
    "content": "Encouraging message about their progress",
    "emoji": "🌟"
  }},
  {{
    "insight_type": "suggestion",
    "title": "New Habit Suggestion",
    "content": "Suggest a new habit they haven't tried yet",
    "emoji": "🌱"
  }}
]

Rules:
- Keep content under 150 characters each
- Be specific to their habit patterns
- Use encouraging, positive tone
- Make suggestions actionable
- Return only valid JSON array"""

        # Get AI response
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        # Parse the AI response (clean it up if needed)
        import json
        response_text = ai_response.strip()
        
        # Remove potential markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        try:
            insights_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback insights if AI response isn't valid JSON
            insights_data = [
                {
                    "insight_type": "tip",
                    "title": "Great Progress!",
                    "content": f"You've logged {this_week} habits this week! Keep building that momentum.",
                    "emoji": "💡"
                },
                {
                    "insight_type": "motivation", 
                    "title": "Streak Power",
                    "content": f"Your {current_streak}-day streak shows real commitment to sustainability!",
                    "emoji": "🌟"
                },
                {
                    "insight_type": "suggestion",
                    "title": "Try Something New",
                    "content": "Consider starting a small herb garden - it's sustainable and rewarding!",
                    "emoji": "🌱"
                }
            ]
        
        # Convert to Pydantic models
        insights = [AIInsight(**insight) for insight in insights_data]
        return insights
        
    except Exception as e:
        # Fallback insights in case of any error
        logger.error(f"AI insights error: {str(e)}")
        fallback_insights = [
            AIInsight(
                insight_type="tip",
                title="Keep It Up!",
                content=f"You've made great progress with {len(habits)} sustainable actions!",
                emoji="💡"
            ),
            AIInsight(
                insight_type="motivation",
                title="Every Action Counts", 
                content="Your commitment to sustainability is making a real difference!",
                emoji="🌟"
            ),
            AIInsight(
                insight_type="suggestion",
                title="Try Something New",
                content="Consider adding a new green habit to expand your impact!",
                emoji="🌱"
            )
        ]
        return fallback_insights

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
