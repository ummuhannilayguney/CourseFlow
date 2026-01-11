🎓 Course Registration Simulation System

A full-stack course registration simulation system designed to model real-world university enrollment processes such as prerequisites, time conflicts, priorities, quotas, and waitlists.

This project is suitable for academic research, software engineering coursework, and system behavior analysis.

🚀 Features

🧑‍🎓 Student course enrollment simulation

📚 Course catalog management

⏱ Time conflict detection

🔐 Prerequisite validation

⭐ Priority-based enrollment

📊 Metrics & performance analysis

📝 Waitlist handling

🧪 Simulation engine for enrollment scenarios

🌐 Simple web-based UI (HTML/CSS/JS)

🏗 Project Architecture
course-reg-sim/
│
├── server/
│   ├── src/
│   │   ├── core/        # Core simulation logic
│   │   │   ├── catalog.js
│   │   │   ├── conflict.js
│   │   │   ├── prereq.js
│   │   │   ├── priority.js
│   │   │   ├── simulate.js
│   │   │   ├── waitlist.js
│   │   │   └── metrics.js
│   │   │
│   │   ├── routes/      # Express routes
│   │   ├── data/        # Seed data
│   │   ├── config/      # Auth & configuration
│   │   └── index.js     # Server entry point
│   │
│   └── client/          # Frontend (HTML/JS/CSS)
│
├── package.json
└── package-lock.json

🧰 Tech Stack

Backend

Node.js

Express.js

Frontend

HTML5

CSS3

Vanilla JavaScript

Other

RESTful API design

Modular simulation engine

⚙️ Installation & Setup
Prerequisites

Node.js (v16+ recommended)

npm

Installation
git clone https://github.com/your-username/course-reg-sim.git
cd course-reg-sim/server
npm install

Run the Server
npm start


Server will run on:

http://localhost:3000

🖥 Usage

Access the UI via browser (index.html)

Login as admin or student

Browse course catalog

Run enrollment simulations

Analyze results via metrics

🧪 Simulation Logic

The system simulates real-world constraints such as:

Course capacity limits

Student priority levels

Time slot overlaps

Mandatory prerequisites

Automated waitlist management

Simulation logic is modular and extensible.

📊 Metrics

The system tracks:

Enrollment success rates

Course demand

Waitlist statistics

Conflict frequencies

Useful for academic analysis and optimization studies.

📄 License

This project is licensed under the MIT License.

👤 Author

Developed for academic and simulation-based research purposes.
