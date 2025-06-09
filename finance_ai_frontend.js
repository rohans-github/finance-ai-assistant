// App.js - Main React Component for Finance AI Assistant
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './App.css';

const API_BASE = 'http://localhost:8000';

// Configure axios defaults
axios.defaults.baseURL = API_BASE;

const App = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('dashboard');
  const [transactions, setTransactions] = useState([]);
  const [spendingPatterns, setSpendingPatterns] = useState({});
  const [predictions, setPredictions] = useState({});
  const [chatMessages, setChatMessages] = useState([]);
  const [goals, setGoals] = useState([]);

  // Set up axios interceptor for authentication
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      await Promise.all([
        fetchTransactions(),
        fetchSpendingPatterns(),
        fetchPredictions(),
        fetchGoals()
      ]);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      const response = await axios.get('/transactions');
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const fetchSpendingPatterns = async () => {
    try {
      const response = await axios.get('/analytics/spending-patterns');
      setSpendingPatterns(response.data);
    } catch (error) {
      console.error('Error fetching spending patterns:', error);
    }
  };

  const fetchPredictions = async () => {
    try {
      const response = await axios.get('/analytics/predictions');
      setPredictions(response.data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  };

  const fetchGoals = async () => {
    try {
      const response = await axios.get('/goals');
      setGoals(response.data.goals);
    } catch (error) {
      console.error('Error fetching goals:', error);
    }
  };

  const AuthForm = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
      email: '',
      password: '',
      monthly_income: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const payload = isLogin 
          ? { email: formData.email, password: formData.password }
          : formData;
        
        const response = await axios.post(endpoint, payload);
        const { token } = response.data;
        
        localStorage.setItem('token', token);
        setToken(token);
      } catch (error) {
        alert(error.response?.data?.detail || 'Authentication failed');
      }
    };

    return (
      <div className="auth-container">
        <div className="auth-form">
          <h2>{isLogin ? 'Login' : 'Register'}</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              required
            />
            {!isLogin && (
              <input
                type="number"
                placeholder="Monthly Income"
                value={formData.monthly_income}
                onChange={(e) => setFormData({...formData, monthly_income: e.target.value})}
              />
            )}
            <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
          </form>
          <button 
            className="switch-mode"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? 'Need to register?' : 'Already have an account?'}
          </button>
        </div>
      </div>
    );
  };

  const Dashboard = () => {
    const categoryData = spendingPatterns.category_spending ? 
      Object.entries(spendingPatterns.category_spending).map(([category, amount]) => ({
        category,
        amount
      })) : [];

    const predictionData = predictions.predicted_monthly_expenses ?
      Object.entries(predictions.predicted_monthly_expenses).map(([category, amount]) => ({
        category,
        predicted: amount,
        current: spendingPatterns.category_spending?.[category] || 0
      })) : [];

    return (
      <div className="dashboard">
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Expenses</h3>
            <p className="stat-value">${spendingPatterns.total_expenses || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Avg Daily Spending</h3>
            <p className="stat-value">${spendingPatterns.avg_daily_spending || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Transactions</h3>
            <p className="stat-value">{transactions.length}</p>
          </div>
          <div className="stat-card">
            <h3>Goals</h3>
            <p className="stat-value">{goals.length}</p>
          </div>
        </div>

        <div className="charts-grid">
          <div className="chart-container">
            <h3>Spending by Category</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  dataKey="amount"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  label
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={`hsl(${index * 45}, 70%, 60%)`} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h3>Current vs Predicted Spending</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={predictionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="current" fill="#8884d8" name="Current" />
                <Bar dataKey="predicted" fill="#82ca9d" name="Predicted" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="recent-transactions">
          <h3>Recent Transactions</h3>
          <div className="transaction-list">
            {transactions.slice(0, 5).map(transaction => (
              <div key={transaction.id} className="transaction-item">
                <div className="transaction-info">
                  <span className="description">{transaction.description}</span>
                  <span className="category">{transaction.category}</span>
                </div>
                <div className="transaction-amount">
                  <span className={transaction.transaction_type === 'income' ? 'income' : 'expense'}>
                    {transaction.transaction_type === 'income' ? '+' : '-'}${transaction.amount}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const TransactionForm = () => {
    const [formData, setFormData] = useState({
      amount: '',
      description: '',
      category: '',
      transaction_type: 'expense',
      date: new Date().toISOString().split('T')[0]
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post('/transactions', {
          ...formData,
          amount: parseFloat(formData.amount),
          date: new Date(formData.date).toISOString()
        });
        
        setFormData({
          amount: '',
          description: '',
          category: '',
          transaction_type: 'expense',
          date: new Date().toISOString().split('T')[0]
        });
        
        fetchTransactions();
        fetchSpendingPatterns();
        alert('Transaction added successfully!');
      } catch (error) {
        alert('Error adding transaction');
      }
    };

    return (
      <div className="transaction-form">
        <h3>Add Transaction</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="number"
            step="0.01"
            placeholder="Amount"
            value={formData.amount}
            onChange={(e) => setFormData({...formData, amount: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Description"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            required
          />
          <select
            value={formData.transaction_type}
            onChange={(e) => setFormData({...formData, transaction_type: e.target.value})}
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
          <input
            type="date"
            value={formData.date}
            onChange={(e) => setFormData({...formData, date: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Category (optional)"
            value={formData.category}
            onChange={(e) => setFormData({...formData, category: e.target.value})}
          />
          <button type="submit">Add Transaction</button>
        </form>
      </div>
    );
  };

  const AIChat = () => {
    const [message, setMessage] = useState('');

    const sendMessage = async () => {
      if (!message.trim()) return;

      const userMessage = { text: message, sender: 'user' };
      setChatMessages(prev => [...prev, userMessage]);

      try {
        const response = await axios.post('/chat', { message });
        const aiMessage = { text: response.data.response, sender: 'ai' };
        setChatMessages(prev => [...prev, aiMessage]);
      } catch (error) {
        const errorMessage = { text: 'Sorry, I encountered an error. Please try again.', sender: 'ai' };
        setChatMessages(prev => [...prev, errorMessage]);
      }

      setMessage('');
    };

    return (
      <div className="ai-chat">
        <div className="chat-messages">
          {chatMessages.length === 0 && (
            <div className="chat-message ai-message">
              <p>Hi! I'm your AI finance assistant. Ask me about your spending patterns, budgeting advice, or investment tips!</p>
            </div>
          )}
          {chatMessages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}-message`}>
              <p>{msg.text}</p>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask me anything about your finances..."
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    );
  };

  const GoalsManager = () => {
    const [showForm, setShowForm] = useState(false);
    const [goalForm, setGoalForm] = useState({
      goal_name: '',
      target_amount: '',
      target_date: '',
      category: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post('/goals', {
          ...goalForm,
          target_amount: parseFloat(goalForm.target_amount),
          target_date: goalForm.target_date ? new Date(goalForm.target_date).toISOString() : null
        });
        
        setGoalForm({
          goal_name: '',
          target_amount: '',
          target_date: '',
          category: ''
        });
        setShowForm(false);
        fetchGoals();
        alert('Goal created successfully!');
      } catch (error) {
        alert('Error creating goal');
      }
    };

    return (
      <div className="goals-manager">
        <div className="goals-header">
          <h3>Financial Goals</h3>
          <button onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : 'Add Goal'}
          </button>
        </div>

        {showForm && (
          <div className="goal-form">
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="Goal name"
                value={goalForm.goal_name}
                onChange={(e) => setGoalForm({...goalForm, goal_name: e.target.value})}
                required
              />
              <input
                type="number"
                step="0.01"
                placeholder="Target amount"
                value={goalForm.target_amount}
                onChange={(e) => setGoalForm({...goalForm, target_amount: e.target.value})}
                required
              />
              <input
                type="date"
                value={goalForm.target_date}
                onChange={(e) => setGoalForm({...goalForm, target_date: e.target.value})}
              />
              <input
                type="text"
                placeholder="Category"
                value={goalForm.category}
                onChange={(e) => setGoalForm({...goalForm, category: e.target.value})}
              />
              <button type="submit">Create Goal</button>
            </form>
          </div>
        )}

        <div className="goals-list">
          {goals.map(goal => (
            <div key={goal.id} className="goal-card">
              <div className="goal-header">
                <h4>{goal.goal_name}</h4>
                <span className="goal-category">{goal.category}</span>
              </div>
              <div className="goal-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${Math.min(goal.progress_percentage, 100)}%` }}
                  ></div>
                </div>
                <span className="progress-text">
                  ${goal.current_amount} / ${goal.target_amount} ({goal.progress_percentage}%)
                </span>
              </div>
              {goal.target_date && (
                <div className="goal-date">
                  Target: {new Date(goal.target_date).toLocaleDateString()}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setTransactions([]);
    setSpendingPatterns({});
    setPredictions({});
    setChatMessages([]);
    setGoals([]);
  };

  if (!token) {
    return <AuthForm />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>💰 Finance AI Assistant</h1>
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={activeTab === 'transactions' ? 'active' : ''}
            onClick={() => setActiveTab('transactions')}
          >
            Transactions
          </button>
          <button 
            className={activeTab === 'goals' ? 'active' : ''}
            onClick={() => setActiveTab('goals')}
          >
            Goals
          </button>
          <button 
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            AI Chat
          </button>
          <button onClick={logout} className="logout-btn">Logout</button>
        </nav>
      </header>

      <main className="app-content">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'transactions' && (
          <div className="transactions-page">
            <TransactionForm />
            <div className="all-transactions">
              <h3>All Transactions</h3>
              <div className="transaction-list">
                {transactions.map(transaction => (
                  <div key={transaction.id} className="transaction-item">
                    <div className="transaction-info">
                      <span className="description">{transaction.description}</span>
                      <span className="category">{transaction.category}</span>
                      <span className="date">{new Date(transaction.date).toLocaleDateString()}</span>
                    </div>
                    <div className="transaction-amount">
                      <span className={transaction.transaction_type === 'income' ? 'income' : 'expense'}>
                        {transaction.transaction_type === 'income' ? '+' : '-'}${transaction.amount}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {activeTab === 'goals' && <GoalsManager />}
        {activeTab === 'chat' && <AIChat />}
      </main>
    </div>
  );
};

export default App;
