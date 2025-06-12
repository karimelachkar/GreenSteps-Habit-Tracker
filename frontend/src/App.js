import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const [habits, setHabits] = useState([]);
  const [progressStats, setProgressStats] = useState(null);
  const [presetHabits, setPresetHabits] = useState([]);
  const [aiInsights, setAiInsights] = useState([]);
  const [error, setError] = useState('');

  // Auth states
  const [isLogin, setIsLogin] = useState(true);
  const [authForm, setAuthForm] = useState({
    name: '',
    email: '',
    password: ''
  });

  // Habit form states
  const [habitForm, setHabitForm] = useState({
    habit_type: 'preset',
    habit_name: '',
    description: ''
  });

  useEffect(() => {
    checkAuth();
    fetchPresetHabits();
  }, []);

  useEffect(() => {
    if (user) {
      fetchHabits();
      fetchProgressStats();
      fetchAiInsights();
    }
  }, [user]);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const fetchPresetHabits = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/preset-habits`);
      setPresetHabits(response.data);
    } catch (error) {
      console.error('Error fetching preset habits:', error);
    }
  };

  const fetchHabits = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/api/habits`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHabits(response.data);
    } catch (error) {
      console.error('Error fetching habits:', error);
    }
  };

  const fetchProgressStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/api/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProgressStats(response.data);
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const fetchAiInsights = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE_URL}/api/ai/insights`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiInsights(response.data);
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      // Set empty array on error to prevent UI issues
      setAiInsights([]);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/signup';
      const payload = isLogin 
        ? { email: authForm.email, password: authForm.password }
        : authForm;

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
      
      localStorage.setItem('token', response.data.access_token);
      await checkAuth();
      setAuthForm({ name: '', email: '', password: '' });
    } catch (error) {
      setError(error.response?.data?.detail || 'Authentication failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setHabits([]);
    setProgressStats(null);
    setCurrentView('dashboard');
  };

  const handleAddHabit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/api/habits`, habitForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setHabitForm({ habit_type: 'preset', habit_name: '', description: '' });
      await fetchHabits();
      await fetchProgressStats();
      setCurrentView('dashboard');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to add habit');
    }
  };

  const handleDeleteHabit = async (habitId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_BASE_URL}/api/habits/${habitId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      await fetchHabits();
      await fetchProgressStats();
    } catch (error) {
      setError('Failed to delete habit');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStreakColor = (streak) => {
    if (streak >= 7) return 'text-green-400';
    if (streak >= 3) return 'text-yellow-400';
    return 'text-gray-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-green-400 text-xl">Loading GreenSteps...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-green-400 mb-2">🌱 GreenSteps</h1>
            <p className="text-gray-300">Track your sustainability journey</p>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <div className="flex mb-6">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2 px-4 rounded-l-lg font-medium ${
                  isLogin ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-300'
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2 px-4 rounded-r-lg font-medium ${
                  !isLogin ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-300'
                }`}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={handleAuth} className="space-y-4">
              {!isLogin && (
                <input
                  type="text"
                  placeholder="Full Name"
                  value={authForm.name}
                  onChange={(e) => setAuthForm({...authForm, name: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              )}
              <input
                type="email"
                placeholder="Email"
                value={authForm.email}
                onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={authForm.password}
                onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
              
              {error && <p className="text-red-400 text-sm">{error}</p>}
              
              <button
                type="submit"
                className="w-full bg-green-500 text-white py-3 rounded-lg font-medium hover:bg-green-600 transition duration-200"
              >
                {isLogin ? 'Login' : 'Sign Up'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🌱</span>
              <h1 className="text-xl font-bold text-green-400">GreenSteps</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">Hello, {user.name}</span>
              <button
                onClick={handleLogout}
                className="text-red-400 hover:text-red-300"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-t border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-1">
            {[
              { key: 'dashboard', label: '📊 Dashboard', icon: '📊' },
              { key: 'add-habit', label: '➕ Log Habit', icon: '➕' },
              { key: 'my-habits', label: '📝 My Habits', icon: '📝' }
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => setCurrentView(item.key)}
                className={`px-4 py-3 font-medium rounded-t-lg transition duration-200 ${
                  currentView === item.key
                    ? 'bg-gray-900 text-green-400 border-b-2 border-green-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentView === 'dashboard' && progressStats && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-green-400 mb-2">Your Sustainability Journey</h2>
              <p className="text-gray-400">Keep building those green habits! 🌍</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">{progressStats.current_streak}</div>
                <div className={`text-sm ${getStreakColor(progressStats.current_streak)}`}>Day Streak 🔥</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">{progressStats.this_week}</div>
                <div className="text-sm text-gray-400">This Week</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">{progressStats.this_month}</div>
                <div className="text-sm text-gray-400">This Month</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <div className="text-3xl font-bold text-yellow-400 mb-2">{progressStats.total_habits}</div>
                <div className="text-sm text-gray-400">Total Habits</div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Monthly Progress</h3>
              <div className="flex items-center space-x-4">
                <div className="flex-1 bg-gray-700 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-green-500 to-blue-500 h-4 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(progressStats.completion_percentage, 100)}%` }}
                  ></div>
                </div>
                <span className="text-green-400 font-semibold">
                  {Math.round(progressStats.completion_percentage)}%
                </span>
              </div>
            </div>

            {/* Weekly Activity Chart */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Weekly Activity</h3>
              <div className="flex items-end space-x-2 h-24">
                {progressStats.weekly_progress.map((count, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-green-500 rounded-t transition-all duration-300"
                      style={{ height: `${Math.max((count / Math.max(...progressStats.weekly_progress, 1)) * 100, 5)}%` }}
                    ></div>
                    <div className="text-xs text-gray-400 mt-1">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][index]}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Insights */}
            {aiInsights.length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-green-400">🤖 Your AI Sustainability Coach</h3>
                  <button
                    onClick={fetchAiInsights}
                    className="text-sm text-blue-400 hover:text-blue-300 transition duration-200"
                  >
                    Refresh Tips
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {aiInsights.map((insight, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition duration-200">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-2xl">{insight.emoji}</span>
                        <h4 className="font-medium text-green-400">{insight.title}</h4>
                      </div>
                      <p className="text-sm text-gray-300">{insight.content}</p>
                      <div className="mt-2">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          insight.insight_type === 'tip' ? 'bg-blue-900 text-blue-300' :
                          insight.insight_type === 'motivation' ? 'bg-purple-900 text-purple-300' :
                          'bg-green-900 text-green-300'
                        }`}>
                          {insight.insight_type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Habits */}
            {habits.slice(0, 3).length > 0 && (
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Habits</h3>
                <div className="space-y-3">
                  {habits.slice(0, 3).map((habit) => (
                    <div key={habit.id} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-b-0">
                      <div>
                        <div className="font-medium text-green-400">{habit.habit_name}</div>
                        <div className="text-sm text-gray-400">{formatDate(habit.date)}</div>
                      </div>
                      <span className="text-2xl">✅</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {currentView === 'add-habit' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-green-400 mb-2">Log Today's Green Habit</h2>
              <p className="text-gray-400">What sustainable action did you take today?</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <form onSubmit={handleAddHabit} className="space-y-6">
                {/* Habit Type Selection */}
                <div>
                  <label className="block text-sm font-medium mb-3">Habit Type</label>
                  <div className="flex space-x-4">
                    <button
                      type="button"
                      onClick={() => setHabitForm({...habitForm, habit_type: 'preset', habit_name: ''})}
                      className={`flex-1 py-3 px-4 rounded-lg font-medium ${
                        habitForm.habit_type === 'preset'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Preset Habits
                    </button>
                    <button
                      type="button"
                      onClick={() => setHabitForm({...habitForm, habit_type: 'custom', habit_name: ''})}
                      className={`flex-1 py-3 px-4 rounded-lg font-medium ${
                        habitForm.habit_type === 'custom'
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      Custom Habit
                    </button>
                  </div>
                </div>

                {/* Habit Selection */}
                <div>
                  <label className="block text-sm font-medium mb-3">
                    {habitForm.habit_type === 'preset' ? 'Select Habit' : 'Habit Name'}
                  </label>
                  
                  {habitForm.habit_type === 'preset' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {presetHabits.map((preset) => (
                        <button
                          key={preset.name}
                          type="button"
                          onClick={() => setHabitForm({...habitForm, habit_name: preset.name, description: preset.description})}
                          className={`p-4 rounded-lg text-left transition duration-200 ${
                            habitForm.habit_name === preset.name
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                          }`}
                        >
                          <div className="font-medium">{preset.name}</div>
                          <div className="text-sm opacity-75">{preset.description}</div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <input
                      type="text"
                      placeholder="Enter your custom habit"
                      value={habitForm.habit_name}
                      onChange={(e) => setHabitForm({...habitForm, habit_name: e.target.value})}
                      className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      required
                    />
                  )}
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium mb-3">Description (Optional)</label>
                  <textarea
                    placeholder="Add any additional notes about this habit..."
                    value={habitForm.description}
                    onChange={(e) => setHabitForm({...habitForm, description: e.target.value})}
                    className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 h-24 resize-none"
                  />
                </div>

                {error && <p className="text-red-400 text-sm">{error}</p>}

                <button
                  type="submit"
                  disabled={!habitForm.habit_name}
                  className="w-full bg-green-500 text-white py-3 rounded-lg font-medium hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed transition duration-200"
                >
                  Log Habit ✅
                </button>
              </form>
            </div>
          </div>
        )}

        {currentView === 'my-habits' && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-green-400 mb-2">My Sustainability Habits</h2>
              <p className="text-gray-400">Review and manage your logged habits</p>
            </div>

            {habits.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🌱</div>
                <h3 className="text-xl font-semibold text-gray-400 mb-2">No habits logged yet</h3>
                <p className="text-gray-500 mb-6">Start your sustainability journey by logging your first habit!</p>
                <button
                  onClick={() => setCurrentView('add-habit')}
                  className="bg-green-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-green-600 transition duration-200"
                >
                  Log Your First Habit
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {habits.map((habit) => (
                  <div key={habit.id} className="bg-gray-800 rounded-lg p-6 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-2xl">✅</span>
                        <h3 className="text-lg font-semibold text-green-400">{habit.habit_name}</h3>
                        <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                          {habit.habit_type}
                        </span>
                      </div>
                      <div className="text-gray-400 text-sm mb-1">
                        {formatDate(habit.date)}
                      </div>
                      {habit.description && (
                        <div className="text-gray-300 text-sm">
                          {habit.description}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteHabit(habit.id)}
                      className="text-red-400 hover:text-red-300 ml-4 p-2"
                      title="Delete habit"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;