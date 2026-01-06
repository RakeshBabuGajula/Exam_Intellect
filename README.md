# ExamIntellect: AI-Powered Online Exam Proctoring System

<img width="1536" height="1024" alt="ExamIntellect image" src="https://github.com/user-attachments/assets/adf82e99-7d79-45c2-9747-8102b2603088" />


ExamIntellect is a comprehensive Python-based multi-agent AI system designed for online exam proctoring and personalized remedial help. It leverages advanced AI technologies to ensure exam integrity while providing tailored educational support.

## Features

### 🛡️ Proctor Agent
- Real-time audio/video analysis
- Behavioral pattern detection
- Suspicious activity flagging
- Integration with Gemini LLM for pattern analysis

### 📚 Tutor Agent
- Post-exam performance analysis
- Personalized learning plan generation
- Tailored resource recommendations
- Adaptive remedial content creation

### 📧 Communication Agent
- Incident summarization and reporting
- Automated email/API notifications
- Feedback generation and dispatch
- Comprehensive session reports

### 🔍 Additional Features
- Session management with long-term student flagging
- Streamlit dashboard for real-time observability
- Integration with Google API and OpenAI for fact-checking
- Modular architecture for easy extension
- Full documentation and demo hooks

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/examintellect.git
cd examintellect
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with your API keys:
```
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_password
```

## Usage

### Running the System
```bash
python main.py
```

### Starting the Dashboard
```bash
streamlit run dashboard/app_final.py
```

### Demo Walkthrough
```bash
python demo/demo_script.py
```

## Project Structure

```
examintellect/
├── src/
│   ├── agents/
│   │   ├── proctor_agent.py
│   │   ├── tutor_agent.py
│   │   └── communication_agent.py
│   ├── integrations.py
│   ├── session_manager.py
│   └── __init__.py
├── dashboard/
│   └── app_final.py
├── demo/
│   └── demo_script.py
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

## Architecture

ExamIntellect uses a multi-agent architecture where each agent specializes in a specific aspect of the exam proctoring and educational support process:

- **Proctor Agent**: Handles real-time monitoring and analysis
- **Tutor Agent**: Provides personalized educational interventions
- **Communication Agent**: Manages reporting and notifications
- **Session Manager**: Maintains long-term student profiles and flags
- **Integrations Module**: Handles external API calls and LLM interactions

## API Integrations

- **Gemini LLM**: For advanced pattern analysis and feedback generation
- **Google API**: For fact-checking and additional verification
- **OpenAI**: For content generation and analysis

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Demo

Check out our [demo video walkthrough](https://youtu.be/UWnSzhhqeXg?si=JLAp-HLUjR_AMbMU) to see ExamIntellect in action!

## Contact

For questions or support, please open an issue on GitHub.
# ExamIntellect
