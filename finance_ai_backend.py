# main.py - FastAPI Backend for Finance AI Assistant
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import hashlib
import jwt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import re
import os

# Initialize FastAPI app
app = FastAPI(
    title="Finance AI Assistant API",
    description="Intelligent Personal Finance Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"

# Database setup
def init_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            monthly_income REAL DEFAULT 0,
            financial_goals TEXT
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            date DATE NOT NULL,
            transaction_type TEXT CHECK(transaction_type IN ('income', 'expense')),
            account_name TEXT DEFAULT 'main',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Financial goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date DATE,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Budget categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category_name TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            current_spent REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    monthly_income: Optional[float] = 0

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TransactionCreate(BaseModel):
    amount: float
    description: str
    category: Optional[str] = None
    date: datetime
    transaction_type: str  # 'income' or 'expense'
    account_name: Optional[str] = 'main'

class FinancialGoal(BaseModel):
    goal_name: str
    target_amount: float
    target_date: Optional[datetime] = None
    category: Optional[str] = None

class BudgetCategory(BaseModel):
    category_name: str
    monthly_limit: float

class ChatMessage(BaseModel):
    message: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# AI/ML functions
def categorize_transaction(description: str) -> str:
    """Smart transaction categorization using keyword matching"""
    description = description.lower()
    
    categories = {
        'food': ['restaurant', 'grocery', 'cafe', 'starbucks', 'mcdonald', 'pizza', 'food', 'dining'],
        'transportation': ['uber', 'lyft', 'gas', 'fuel', 'metro', 'bus', 'parking', 'taxi'],
        'shopping': ['amazon', 'target', 'walmart', 'shopping', 'store', 'mall', 'purchase'],
        'entertainment': ['netflix', 'spotify', 'movie', 'theater', 'concert', 'game', 'entertainment'],
        'utilities': ['electric', 'water', 'internet', 'phone', 'cable', 'utility', 'bill'],
        'healthcare': ['doctor', 'hospital', 'pharmacy', 'medical', 'health', 'dental'],
        'education': ['school', 'university', 'book', 'course', 'education', 'tuition'],
        'income': ['salary', 'wage', 'payroll', 'bonus', 'freelance', 'income']
    }
    
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category
    
    return 'other'

def analyze_spending_patterns(user_id: int) -> Dict[str, Any]:
    """Analyze user spending patterns using ML"""
    conn = sqlite3.connect('finance_ai.db')
    
    # Get user transactions
    df = pd.read_sql_query('''
        SELECT amount, category, date, transaction_type
        FROM transactions 
        WHERE user_id = ? AND transaction_type = 'expense'
        ORDER BY date DESC
        LIMIT 100
    ''', conn, params=(user_id,))
    conn.close()
    
    if df.empty:
        return {"message": "No transaction data available"}
    
    # Basic analysis
    category_spending = df.groupby('category')['amount'].sum().to_dict()
    avg_daily_spending = df['amount'].mean()
    
    # ML clustering for spending behavior
    if len(df) >= 5:
        # Prepare features for clustering
        features = df.groupby('category')['amount'].agg(['sum', 'mean', 'count']).fillna(0)
        
        if len(features) > 1:
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Simple clustering
            n_clusters = min(3, len(features))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(features_scaled)
            
            # Map categories to spending behavior
            spending_behavior = {}
            for i, category in enumerate(features.index):
                if clusters[i] == 0:
                    spending_behavior[category] = "low_spender"
                elif clusters[i] == 1:
                    spending_behavior[category] = "moderate_spender"
                else:
                    spending_behavior[category] = "high_spender"
        else:
            spending_behavior = {list(category_spending.keys())[0]: "moderate_spender"}
    else:
        spending_behavior = {}
    
    return {
        "category_spending": category_spending,
        "avg_daily_spending": round(avg_daily_spending, 2),
        "spending_behavior": spending_behavior,
        "total_expenses": round(df['amount'].sum(), 2),
        "transaction_count": len(df)
    }

def predict_monthly_expenses(user_id: int) -> Dict[str, float]:
    """Predict next month's expenses based on historical data"""
    conn = sqlite3.connect('finance_ai.db')
    
    # Get last 3 months of data
    three_months_ago = datetime.now() - timedelta(days=90)
    df = pd.read_sql_query('''
        SELECT amount, category, date
        FROM transactions 
        WHERE user_id = ? AND transaction_type = 'expense' AND date >= ?
        ORDER BY date
    ''', conn, params=(user_id, three_months_ago.strftime('%Y-%m-%d')))
    conn.close()
    
    if df.empty:
        return {}
    
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    # Calculate monthly averages by category
    monthly_by_category = df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)
    predictions = monthly_by_category.mean().to_dict()
    
    return {k: round(v, 2) for k, v in predictions.items()}

def generate_financial_advice(user_id: int) -> str:
    """Generate personalized financial advice"""
    analysis = analyze_spending_patterns(user_id)
    
    if "message" in analysis:
        return "Start tracking your expenses to get personalized financial advice!"
    
    advice = []
    
    # Check high spending categories
    category_spending = analysis.get("category_spending", {})
    if category_spending:
        highest_category = max(category_spending, key=category_spending.get)
        highest_amount = category_spending[highest_category]
        
        if highest_amount > 500:
            advice.append(f"Your highest spending category is {highest_category} at ${highest_amount:.2f}. Consider setting a budget limit for this category.")
    
    # Check spending behavior
    spending_behavior = analysis.get("spending_behavior", {})
    high_spenders = [cat for cat, behavior in spending_behavior.items() if behavior == "high_spender"]
    
    if high_spenders:
        advice.append(f"You're a high spender in: {', '.join(high_spenders)}. Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings.")
    
    # General advice
    avg_daily = analysis.get("avg_daily_spending", 0)
    if avg_daily > 50:
        advice.append("Your daily spending is quite high. Consider tracking every purchase for a week to identify unnecessary expenses.")
    
    if not advice:
        advice.append("Great job on managing your expenses! Consider setting up automatic savings to build your emergency fund.")
    
    return " ".join(advice)

# API Routes
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Finance AI Assistant API", "status": "running"}

@app.post("/auth/register")
async def register(user: UserCreate):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (email, password_hash, monthly_income)
            VALUES (?, ?, ?)
        ''', (user.email, hash_password(user.password), user.monthly_income))
        conn.commit()
        user_id = cursor.lastrowid
        
        token = create_token(user_id)
        return {"token": token, "user_id": user_id, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

@app.post("/auth/login")
async def login(user: UserLogin):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (user.email,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(db_user[0])
    return {"token": token, "user_id": db_user[0], "message": "Login successful"}

@app.post("/transactions")
async def add_transaction(transaction: TransactionCreate, user_id: int = Depends(get_current_user)):
    # Auto-categorize if no category provided
    if not transaction.category:
        transaction.category = categorize_transaction(transaction.description)
    
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (user_id, amount, description, category, date, transaction_type, account_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, transaction.amount, transaction.description, transaction.category, 
          transaction.date, transaction.transaction_type, transaction.account_name))
    
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    
    return {"transaction_id": transaction_id, "message": "Transaction added successfully", "category": transaction.category}

@app.get("/transactions")
async def get_transactions(user_id: int = Depends(get_current_user), limit: int = 50):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, amount, description, category, date, transaction_type, account_name, created_at
        FROM transactions 
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
    ''', (user_id, limit))
    
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            "id": row[0],
            "amount": row[1],
            "description": row[2],
            "category": row[3],
            "date": row[4],
            "transaction_type": row[5],
            "account_name": row[6],
            "created_at": row[7]
        })
    
    conn.close()
    return {"transactions": transactions}

@app.get("/analytics/spending-patterns")
async def get_spending_patterns(user_id: int = Depends(get_current_user)):
    return analyze_spending_patterns(user_id)

@app.get("/analytics/predictions")
async def get_predictions(user_id: int = Depends(get_current_user)):
    predictions = predict_monthly_expenses(user_id)
    return {"predicted_monthly_expenses": predictions}

@app.post("/chat")
async def chat_with_ai(message: ChatMessage, user_id: int = Depends(get_current_user)):
    """Simple AI chatbot for financial queries"""
    user_message = message.message.lower()
    
    if "spending" in user_message or "expense" in user_message:
        analysis = analyze_spending_patterns(user_id)
        if "category_spending" in analysis:
            top_category = max(analysis["category_spending"], key=analysis["category_spending"].get)
            amount = analysis["category_spending"][top_category]
            response = f"Your highest spending category is {top_category} with ${amount:.2f}. "
            response += generate_financial_advice(user_id)
        else:
            response = "I don't have enough transaction data to analyze your spending patterns yet."
    
    elif "budget" in user_message:
        response = "I recommend following the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings. Would you like me to help you set up a budget?"
    
    elif "save" in user_message or "saving" in user_message:
        response = "Start with the goal of saving at least 20% of your income. Consider setting up automatic transfers to a high-yield savings account."
    
    elif "invest" in user_message:
        response = "Before investing, ensure you have an emergency fund of 3-6 months of expenses. For beginners, consider low-cost index funds or ETFs."
    
    else:
        response = "I can help you with spending analysis, budgeting advice, saving tips, and basic investment guidance. What would you like to know about your finances?"
    
    return {"response": response}

@app.post("/goals")
async def create_goal(goal: FinancialGoal, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO financial_goals (user_id, goal_name, target_amount, target_date, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, goal.goal_name, goal.target_amount, goal.target_date, goal.category))
    
    conn.commit()
    goal_id = cursor.lastrowid
    conn.close()
    
    return {"goal_id": goal_id, "message": "Financial goal created successfully"}

@app.get("/goals")
async def get_goals(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, goal_name, target_amount, current_amount, target_date, category, created_at
        FROM financial_goals 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    
    goals = []
    for row in cursor.fetchall():
        goals.append({
            "id": row[0],
            "goal_name": row[1],
            "target_amount": row[2],
            "current_amount": row[3],
            "target_date": row[4],
            "category": row[5],
            "created_at": row[6],
            "progress_percentage": round((row[3] / row[2]) * 100, 2) if row[2] > 0 else 0
        })
    
    conn.close()
    return {"goals": goals}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
