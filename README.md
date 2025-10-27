# 🎯 Smart Goals Tracker – AI-Powered Productivity App

**Transform any goal into an actionable plan with daily tracking, AI insights, and progress reports.**

---

## 🚀 Overview

**Smart Goals Tracker** is an AI-driven productivity app built with **Streamlit** that helps users:
- Create SMART goals and break them into **actionable, measurable steps**
- Track daily **streaks and consistency**
- View **progress insights** powered by GPT
- Export professional **PDF progress reports**

It’s lightweight, goal-agnostic, and designed for real users who want structure, motivation, and clarity.

---

## 🧠 Key Features

| Category | Highlights |
|-----------|-------------|
| 🎯 **Goal Creation with AI** | Uses OpenAI GPT to generate 6–8 small, achievable steps with metrics and motivation (“why it matters”) |
| 🛠 **Editable Plan** | Inline editing for each step: title, details, metrics, due dates, and completion |
| 📈 **Streak Tracking** | One-click “Check-in / Undo” buttons with real-time Plotly charts for consistency |
| 📋 **Plan Overview Sidebar** | Always-visible summary of next steps and upcoming 14-day mini-schedule |
| 🧾 **Weekly Insights & Quotes** | AI-generated progress recap and motivational one-liners |
| 📄 **PDF Export** | Generates clean report with goals, steps, streaks, and AI summary |
| 🧪 **Testing & Reliability** | Full test coverage via `pytest`, including DB and AI mock tests |

---

## ⚙️ Tech Stack

**Frontend/UI:** Streamlit  
**Backend & Storage:** SQLite (local persistence)  
**AI Integration:** OpenAI GPT-4o mini (chat.completions)  
**Visualization:** Plotly  
**PDF Generation:** ReportLab  
**Testing:** Pytest (unit + mock)  
**Language:** Python 3.11  

---

## 🧩 Architecture
smart-goals-tracker/
├── app.py # Streamlit main interface
├── db.py # SQLite CRUD and streak logic
├── gpt.py # AI generation, summary, and quote logic
├── utils.py # Helper functions for dates & parsing
├── report.py # PDF builder
├── tests/ # Automated test suite (pytest)
├── requirements.txt
├── .env.example # Env vars (OPENAI_API_KEY)
└── data.sqlite3 # Local database (auto-created)


---

## 🧭 How It Works

1. **Enter a Goal** → Example: “Run a half marathon”  
2. **AI Generates Plan** → 6–8 specific, measurable steps with motivation and duration  
3. **Track Progress** → Check-in daily to build your streak  
4. **View Insights** → Weekly GPT summary analyzes consistency and achievements  
5. **Export Report** → PDF download of plan, progress, and AI reflection  

---

## 🛠️ Installation & Setup

###  1. Clone the repository

```bash
git clone https://github.com/Y-ogesh/smart-goals-tracker.git
cd smart-goals-tracker
```

###  2. Create virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```
###  3. Configure your API key

Create a .env file in the root directory:

```bash
    OPENAI_API_KEY=sk-your-key-here
```

###  4. Run the app

```bash
    streamlit run app.py
```

###  5. Run tests (optional)

```bash
pytest -q
```

💡 Example Use Cases

| Goal Type      | Examples                                                |
| -------------- | ------------------------------------------------------- |
| 🧍‍♂️ Personal | Build a reading habit, improve sleep, run a 10K         |
| 💼 Career      | Launch a portfolio website, learn SQL, get certified    |
| 📚 Academic    | Complete thesis, revise for exams, master a new subject |
| 🧘 Health      | Track workouts, plan meals, improve consistency         |



🧪 Testing & QA

- Isolated temporary SQLite DB for every test run
- Mocked OpenAI API to validate GPT responses offline
- 100% pass rate across CRUD, streak, PDF, and utility tests
- Run tests via:

        pytest -q


🌐 Deployment

Easily deploy on Streamlit Cloud or Render:
```bash
streamlit run app.py
```

Streamlit Cloud steps:
- Push to GitHub
- Go to share.streamlit.io
- Connect your repo
- Add OPENAI_API_KEY as a secret


📚 Learnings

- Implemented modular architecture & test-driven development
- Gained practical experience with OpenAI APIs, data persistence, and Streamlit layouts
- Balanced UX design, AI prompt engineering, and data visualization


🧑‍💻 Author
Yogesh Periyasamy
Master of Computer Science @ Illinois Institute of Technology
📍 Chicago, IL
📫 p.yogesh2000@gmail.com


⭐ Future Enhancements
- Multi-goal dashboard and progress analytics
- Cloud database (Supabase/Neon) for multi-user support
- Goal reminders via email/Slack
- Shareable public progress pages
- Theme customization (light/dark mode)


🏆 Status
✅ Fully functional
✅ Test suite passing