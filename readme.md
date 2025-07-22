# 📊 QA Dashboard

A comprehensive Quality Assurance dashboard for analyzing customer service team performance. Built with Streamlit, this dashboard provides insights into agent performance, team metrics, and actionable feedback analysis.

## 🌟 Features

### Team Overview
- **Team Selection**: Automatic team grouping based on email domains
- **Key Metrics**: Average QA Score, CX Score, total conversations, team size
- **Intelligent Insights**: AI-powered extraction of strengths and improvement areas
- **Visual Analytics**: Score distribution charts and trend analysis

### Individual Agent Analysis  
- **Skill Assessment**: Radar charts for Writing, Accuracy, and Empathy skills
- **Performance Metrics**: Detailed breakdown of QA and CX scores
- **Feedback Analysis**: Automated extraction of positive patterns and recommendations
- **Conversation Tracking**: Volume and performance correlation

### Export & Reporting
- **Markdown Export**: Notion-friendly reports with complete team and agent summaries
- **Flexible Data Handling**: Supports various CSV column naming conventions
- **Error Resilience**: Graceful handling of missing data and columns

## 🚀 Quick Start

### Method 1: Streamlit Cloud (Recommended)
1. **Fork this repository** to your GitHub account
2. **Go to** [share.streamlit.io](https://share.streamlit.io)  
3. **Sign in** with your GitHub account
4. **Click "New app"**
5. **Select** your forked repository
6. **Set main file** to `app.py`
7. **Click "Deploy!"**

### Method 2: Local Development
```bash
# Clone the repository
git clone <your-repo-url>
cd qa-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## 📊 Data Format

### Required Columns (flexible naming)
Your CSV should contain these columns. The app supports various naming conventions:

**Agent Information:**
- `Representative Name` (or `Agent Name`, `Name`)  
- `Representative Email` (or `Email`) - used for team grouping

**Scores:**
- `Score` (or `Overall Score`, `QA Score`) - Overall QA performance
- `Customer Experience (CX) rating` (or `CX Score`) - Customer satisfaction

### Optional Columns
**Skill Scores (1-3 scale):**
- `Writing style (Score)` 
- `Accuracy (Score)`
- `Empathy & Helpfulness (Score)`

**Feedback Text:**
- `Writing style (Explanation)`
- `Accuracy (Explanation)` 
- `Empathy & Helpfulness (Explanation)`
- `Feedback Focus Areas` - Overall feedback

### Sample Data Structure
```csv
Representative Name,Representative Email,Score,Writing style (Score),Accuracy (Score),Empathy & Helpfulness (Score),Customer Experience (CX) rating
John Doe,john@company.com,85,3,3,2,4
Jane Smith,jane@company.com,92,3,3,3,5
Mike Johnson,mike@company.com,78,2,3,2,4
```

## 🎯 How It Works

### Team Grouping
Teams are automatically created from email domains:
- `john@acme.com` → "Acme" team
- `jane@beta.com` → "Beta" team

### Feedback Analysis
The app uses intelligent pattern matching to extract:
- **Positive patterns**: "excellent", "professional", "clear communication"
- **Improvement areas**: "could improve", "needs attention", "consider enhancing"

### Performance Metrics
- **QA Scores**: Calculated from individual skills or provided overall score
- **Skill Assessment**: Visual radar charts showing strengths/weaknesses
- **Trend Analysis**: Distribution charts and performance patterns

## 🛠️ Customization

### Modify Team Assignment
Edit the `load_data()` function in `app.py`:
```python
# Custom team mapping
team_mapping = {
    'john@company.com': 'Senior Team',
    'jane@company.com': 'Junior Team'
}
df['Team'] = df['Representative Email'].map(team_mapping)
```

### Add New Insights
Extend the `extract_feedback_insights()` function:
```python
positive_patterns = [
    r'excellent|outstanding|exceptional',
    r'your_custom_pattern_here'
]
```

### Custom Visualizations
Add new charts in the main dashboard section using Plotly Express.

## 📈 Performance Tips

### For Large Datasets (1000+ rows)
- Data is automatically cached for faster reloads
- Feedback analysis is optimized for performance
- Charts use efficient rendering with Plotly

### Cloud Deployment Optimization
- Minimal memory footprint
- Efficient data processing
- Error handling for edge cases

## 🔧 Troubleshooting

### Common Issues

**"Missing required columns" error:**
- Check your CSV column names match the expected format
- The app supports flexible naming - see data format section

**Team not showing correctly:**
- Verify email format in your data
- Check team assignment logic in `load_data()` function

**Charts not displaying:**
- Ensure numeric columns contain valid numbers
- Check for sufficient data points

**Slow performance:**
- Large feedback text can slow insight extraction
- Consider filtering to recent data for better performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

Having issues? Check these resources:

1. **Sample Data**: Use the demo data in the app to test functionality
2. **Column Mapping**: Verify your CSV matches the expected format
3. **GitHub Issues**: Report bugs or request features
4. **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)

## 🎉 Features Roadmap

- [ ] Advanced NLP feedback analysis
- [ ] Time-based trend analysis  
- [ ] Custom scoring rubrics
- [ ] PDF report generation
- [ ] Multi-language support
- [ ] Integration with popular helpdesk tools

---

**Built with ❤️ using Streamlit**

Deploy your own version: [![Deploy](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)