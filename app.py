"""
QA Dashboard - Streamlit Application
A comprehensive dashboard for analyzing QA performance data
Optimized for Streamlit Cloud deployment
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
from collections import Counter
import base64
import traceback

# Page configuration
st.set_page_config(
    page_title="QA Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}
.improvement-box {
    background-color: #fff3cd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ffc107;
}
.success-box {
    background-color: #d4edda;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
}
.agent-card {
    background-color: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    """Load and process the CSV data with error handling"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Required columns mapping (flexible column name matching)
        required_columns = {
            'representative_name': ['Representative Name', 'Agent Name', 'Rep Name', 'Name'],
            'representative_email': ['Representative Email', 'Agent Email', 'Rep Email', 'Email'],
            'overall_score': ['Score', 'Overall Score', 'QA Score', 'Overall QA Score'],
            'writing_score': ['Writing style (Score)', 'Writing Score', 'Writing (Score)'],
            'writing_explanation': ['Writing style (Explanation)', 'Writing Explanation', 'Writing (Explanation)'],
            'accuracy_score': ['Accuracy (Score)', 'Accuracy Score'],
            'accuracy_explanation': ['Accuracy (Explanation)', 'Accuracy Explanation'],
            'empathy_score': ['Empathy & Hepfulness (Score)', 'Empathy Score', 'Empathy (Score)', 'Empathy & Helpfulness (Score)'],
            'empathy_explanation': ['Empathy & Hepfulness (Explanation)', 'Empathy Explanation', 'Empathy (Explanation)', 'Empathy & Helpfulness (Explanation)'],
            'cx_rating': ['Customer Experience (CX) rating', 'CX Rating', 'CX Score', 'Customer Experience Rating'],
            'feedback_overall': ['Feedback Focus Areas', 'Overall Feedback', 'Feedback', 'Focus Areas']
        }
        
        # Map columns flexibly
        column_mapping = {}
        missing_columns = []
        
        for key, possible_names in required_columns.items():
            found = False
            for name in possible_names:
                if name in df.columns:
                    column_mapping[name] = key
                    found = True
                    break
            if not found:
                missing_columns.append(f"{key} (looking for: {', '.join(possible_names)})")
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            st.info("💡 Please check your CSV column names match the expected format.")
            return None
        
        # Rename columns to standard format
        df = df.rename(columns={v: k for k, v in column_mapping.items()})
        
        # Handle missing emails gracefully
        if 'representative_email' in df.columns:
            # Create team name from email domain
            df['Team'] = df['representative_email'].str.extract(r'@([^.]+)', expand=False).fillna('Unknown')
            df['Team'] = df['Team'].str.title()
        else:
            df['Team'] = 'Default Team'
        
        # Calculate overall QA score if needed (handle missing skill scores)
        skill_cols = ['writing_score', 'accuracy_score', 'empathy_score']
        available_skills = [col for col in skill_cols if col in df.columns]
        
        if available_skills:
            df['calculated_qa_score'] = df[available_skills].mean(axis=1, skipna=True)
            # Use provided overall score if available, otherwise use calculated
            if 'overall_score' not in df.columns:
                df['overall_score'] = df['calculated_qa_score']
        
        # Ensure numeric columns
        numeric_cols = ['overall_score', 'writing_score', 'accuracy_score', 'empathy_score', 'cx_rating']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with all NaN values in key columns
        key_cols = ['representative_name', 'overall_score']
        df = df.dropna(subset=[col for col in key_cols if col in df.columns], how='all')
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.error("Please check your CSV file format and try again.")
        return None

def extract_feedback_insights(feedback_series, positive=True, max_insights=3):
    """Extract common themes from feedback text with better performance"""
    if feedback_series.empty or feedback_series.isna().all():
        return []
    
    try:
        # Combine all feedback, handling NaN values
        all_feedback = ' '.join(feedback_series.fillna('').astype(str).tolist())
        
        if len(all_feedback.strip()) < 10:
            return []
        
        # Define positive and negative keywords/phrases (optimized)
        positive_patterns = [
            r'excellent|strong|clear|professional|effective',
            r'accurate|helpful|empathetic|warm|supportive',
            r'well[\s-]structured|easy to follow|friendly|polite',
            r'proactive|comprehensive|thorough|responsive'
        ]
        
        negative_patterns = [
            r'could.*improve|should.*focus|needs? to',
            r'lacking|missing|insufficient|unclear',
            r'enhance|develop|work on|pay.*attention|consider'
        ]
        
        patterns = positive_patterns if positive else negative_patterns
        insights = []
        
        # More efficient pattern matching
        for pattern in patterns:
            matches = re.findall(rf'[^.!?]*{pattern}[^.!?]*[.!?]', all_feedback, re.IGNORECASE)
            for match in matches[:2]:  # Limit matches per pattern
                cleaned = match.strip()
                if 20 <= len(cleaned) <= 200 and cleaned not in insights:
                    insights.append(cleaned)
                    if len(insights) >= max_insights:
                        break
            if len(insights) >= max_insights:
                break
        
        return insights
    
    except Exception as e:
        st.warning(f"Could not extract insights: {str(e)}")
        return []

def create_skill_radar_chart(agent_data, agent_name):
    """Create a radar chart for agent skills with error handling"""
    try:
        skills = ['Writing Style', 'Accuracy', 'Empathy & Helpfulness']
        
        # Handle missing columns gracefully
        scores = []
        skill_cols = ['writing_score', 'accuracy_score', 'empathy_score']
        
        for col in skill_cols:
            if col in agent_data.columns:
                score = agent_data[col].mean()
                scores.append(score if pd.notna(score) else 0)
            else:
                scores.append(0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=skills,
            fill='toself',
            name=agent_name,
            line=dict(color='#1f77b4')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(3, max(scores) * 1.1)]  # Dynamic scale
                )),
            showlegend=True,
            title=f"{agent_name} - Skill Assessment",
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig
    
    except Exception as e:
        st.warning(f"Could not create radar chart for {agent_name}: {str(e)}")
        return None

def generate_markdown_report(team_data, team_name, agent_summaries):
    """Generate markdown report for download"""
    report = f"""# QA Report - {team_name}

## Team Overview
- **Average QA Score:** {team_data['Overall QA Score'].mean():.1f}/3.0
- **Average CX Score:** {team_data['Customer Experience (CX) rating'].mean():.1f}/5.0
- **Total Conversations:** {len(team_data)}
- **Report Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

### Team Strengths ✅
"""
    
    # Add team insights
    positive_insights = extract_feedback_insights(team_data['Feedback Focus Areas'], positive=True)
    for insight in positive_insights:
        report += f"- {insight}\n"
    
    report += "\n### Areas for Improvement ⚠️\n"
    negative_insights = extract_feedback_insights(team_data['Feedback Focus Areas'], positive=False)
    for insight in negative_insights:
        report += f"- {insight}\n"
    
    report += "\n---\n\n## Individual Agent Analysis\n\n"
    
    for agent_name, summary in agent_summaries.items():
        report += f"### {agent_name}\n\n"
        report += f"**Overall Performance:**\n"
        report += f"- QA Score: {summary['qa_score']:.1f}/3.0\n"
        report += f"- CX Score: {summary['cx_score']:.1f}/5.0\n"
        report += f"- Conversations: {summary['conversations']}\n\n"
        
        report += f"**Skill Breakdown:**\n"
        for skill, score in summary['skills'].items():
            report += f"- {skill}: {score:.1f}/3.0\n"
        
        report += f"\n**Strengths ✅:**\n"
        for strength in summary['strengths']:
            report += f"- {strength}\n"
        
        report += f"\n**Improvement Areas 🎯:**\n"
        for improvement in summary['improvements']:
            report += f"- {improvement}\n"
        
        report += "\n---\n\n"
    
    return report

# Main App
def main():
    st.title("📊 QA Dashboard")
    st.markdown("Analyze team and individual agent performance from QA scorecards")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your QA CSV file", 
        type=['csv'],
        help="Upload the CSV file containing QA scorecard data"
    )
    
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading and processing data..."):
            df = load_data(uploaded_file)
        
        if df is None:
            return
        
        # Sidebar - Team Selection
        st.sidebar.header("🎯 Team Selection")
        available_teams = ['All Teams'] + sorted(df['Team'].unique().tolist())
        selected_team = st.sidebar.selectbox("Choose Team:", available_teams)
        
        # Filter data based on selection
        if selected_team == 'All Teams':
            team_data = df
            display_name = "All Teams"
        else:
            team_data = df[df['Team'] == selected_team]
            display_name = selected_team
        
        if team_data.empty:
            st.warning(f"No data found for team: {selected_team}")
            return
        
        # Main dashboard
        st.header(f"📈 {display_name} Overview")
        
        # Key metrics with error handling
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'overall_score' in team_data.columns:
                avg_qa = team_data['overall_score'].mean()
                st.metric("Average QA Score", f"{avg_qa:.1f}", 
                         help="Overall QA performance score")
            else:
                st.metric("Average QA Score", "N/A", help="QA score not available")
        
        with col2:
            if 'cx_rating' in team_data.columns:
                avg_cx = team_data['cx_rating'].mean()
                st.metric("Average CX Score", f"{avg_cx:.1f}/5.0",
                         help="Customer Experience rating")
            else:
                st.metric("Average CX Score", "N/A", help="CX score not available")
        
        with col3:
            total_conversations = len(team_data)
            st.metric("Total Conversations", total_conversations)
        
        with col4:
            if 'representative_name' in team_data.columns:
                unique_agents = team_data['representative_name'].nunique()
                st.metric("Team Members", unique_agents)
            else:
                st.metric("Team Members", "N/A")
        
        # Team insights (only if feedback is available)
        if 'feedback_overall' in team_data.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Team Strengths")
                with st.spinner("Analyzing positive feedback..."):
                    positive_insights = extract_feedback_insights(team_data['feedback_overall'], positive=True)
                if positive_insights:
                    for insight in positive_insights:
                        st.success(insight)
                else:
                    st.info("No specific positive patterns identified in feedback")
            
            with col2:
                st.markdown("### ⚠️ Areas for Improvement")
                with st.spinner("Analyzing improvement areas..."):
                    negative_insights = extract_feedback_insights(team_data['feedback_overall'], positive=False)
                if negative_insights:
                    for insight in negative_insights:
                        st.warning(insight)
                else:
                    st.info("No specific improvement areas identified in feedback")
        
        # Score distribution charts (only if data available)
        if any(col in team_data.columns for col in ['overall_score', 'cx_rating']):
            st.markdown("### 📊 Score Distributions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'overall_score' in team_data.columns and team_data['overall_score'].notna().any():
                    fig_qa = px.histogram(
                        team_data.dropna(subset=['overall_score']), 
                        x='overall_score', 
                        nbins=10,
                        title="QA Score Distribution",
                        labels={'overall_score': 'QA Score', 'count': 'Frequency'}
                    )
                    fig_qa.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_qa, use_container_width=True)
                else:
                    st.info("QA score data not available for distribution chart")
            
            with col2:
                if 'cx_rating' in team_data.columns and team_data['cx_rating'].notna().any():
                    fig_cx = px.histogram(
                        team_data.dropna(subset=['cx_rating']), 
                        x='cx_rating', 
                        nbins=5,
                        title="CX Score Distribution",
                        labels={'cx_rating': 'CX Score', 'count': 'Frequency'}
                    )
                    fig_cx.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_cx, use_container_width=True)
                else:
                    st.info("CX score data not available for distribution chart")
        
        # Individual agent analysis
        if 'representative_name' in team_data.columns:
            st.markdown("### 👥 Individual Agent Performance")
            
            agents = team_data['representative_name'].dropna().unique()
            agent_summaries = {}
            
            for agent in sorted(agents):
                if pd.isna(agent):
                    continue
                    
                agent_data = team_data[team_data['representative_name'] == agent]
                
                try:
                    # Calculate agent metrics safely
                    qa_score = agent_data['overall_score'].mean() if 'overall_score' in agent_data.columns else None
                    cx_score = agent_data['cx_rating'].mean() if 'cx_rating' in agent_data.columns else None
                    conversations = len(agent_data)
                    
                    # Skill breakdown
                    skills = {}
                    skill_mapping = {
                        'Writing Style': 'writing_score',
                        'Accuracy': 'accuracy_score', 
                        'Empathy & Helpfulness': 'empathy_score'
                    }
                    
                    for skill_name, col_name in skill_mapping.items():
                        if col_name in agent_data.columns:
                            skills[skill_name] = agent_data[col_name].mean()
                        else:
                            skills[skill_name] = None
                    
                    # Get feedback insights for this agent
                    feedback_cols = ['writing_explanation', 'accuracy_explanation', 'empathy_explanation', 'feedback_overall']
                    available_feedback = []
                    
                    for col in feedback_cols:
                        if col in agent_data.columns:
                            available_feedback.extend(agent_data[col].dropna().tolist())
                    
                    if available_feedback:
                        agent_feedback = pd.Series(available_feedback)
                        strengths = extract_feedback_insights(agent_feedback, positive=True)
                        improvements = extract_feedback_insights(agent_feedback, positive=False)
                    else:
                        strengths = []
                        improvements = []
                    
                    # Store summary for potential export
                    agent_summaries[agent] = {
                        'qa_score': qa_score,
                        'cx_score': cx_score,
                        'conversations': conversations,
                        'skills': skills,
                        'strengths': strengths,
                        'improvements': improvements
                    }
                    
                    # Display agent card
                    qa_display = f"{qa_score:.1f}" if qa_score else "N/A"
                    cx_display = f"{cx_score:.1f}" if cx_score else "N/A"
                    
                    with st.expander(f"📋 {agent} - QA: {qa_display} | CX: {cx_display} | Conversations: {conversations}"):
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            # Skill radar chart
                            radar_fig = create_skill_radar_chart(agent_data, agent)
                            if radar_fig:
                                st.plotly_chart(radar_fig, use_container_width=True)
                            else:
                                st.info("Skill chart not available")
                        
                        with col2:
                            st.markdown("#### 📈 Performance Metrics")
                            if qa_score:
                                st.metric("QA Score", f"{qa_score:.1f}")
                            if cx_score:
                                st.metric("CX Score", f"{cx_score:.1f}/5.0")
                            st.metric("Conversations", conversations)
                            
                            st.markdown("#### 🎯 Skill Breakdown")
                            for skill, score in skills.items():
                                if score:
                                    st.write(f"**{skill}:** {score:.1f}")
                                else:
                                    st.write(f"**{skill}:** N/A")
                        
                        # Feedback sections
                        if strengths or improvements:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### ✅ What They Did Well")
                                if strengths:
                                    for strength in strengths:
                                        st.success(strength)
                                else:
                                    st.info("Continue current good practices")
                            
                            with col2:
                                st.markdown("#### 🎯 Recommendations")
                                if improvements:
                                    for improvement in improvements:
                                        st.warning(improvement)
                                else:
                                    st.info("Performance meets expectations")
                
                except Exception as e:
                    st.error(f"Error processing data for {agent}: {str(e)}")
                    continue
        
        # Download section
        st.markdown("### 📥 Export Reports")
        
        if st.button("🔽 Generate Markdown Report", type="primary"):
            try:
                markdown_content = generate_markdown_report(team_data, display_name, agent_summaries)
                
                # Create download link
                b64 = base64.b64encode(markdown_content.encode()).decode()
                filename = f"QA_Report_{display_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md"
                href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}">📥 Download Report</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success(f"Report generated! Click the link above to download.")
                
                # Show preview
                with st.expander("📄 Preview Report"):
                    st.markdown(markdown_content)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    else:
        st.info("👆 Please upload a CSV file to get started")
        
        # Show sample data format and demo
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("📋 Expected CSV Format"):
                st.markdown("""
                Your CSV should contain these columns (flexible naming):
                
                **Required:**
                - **Representative Name** (or Agent Name, Name)
                - **Representative Email** (or Email) - for team grouping
                - **Score** (or Overall Score, QA Score)
                
                **Skills (Optional):**
                - **Writing style (Score)** - Writing skill score
                - **Accuracy (Score)** - Accuracy skill score  
                - **Empathy & Helpfulness (Score)** - Empathy score
                
                **Feedback (Optional):**
                - **Writing style (Explanation)** - Writing feedback
                - **Accuracy (Explanation)** - Accuracy feedback
                - **Empathy & Helpfulness (Explanation)** - Empathy feedback
                - **Feedback Focus Areas** - Overall feedback
                
                **Customer Experience (Optional):**
                - **Customer Experience (CX) rating** - CX score
                """)
        
        with col2:
            with st.expander("🎯 Demo Data"):
                # Create sample data for demonstration
                sample_data = {
                    'Representative Name': ['John Doe', 'Jane Smith', 'Mike Johnson'],
                    'Representative Email': ['john@company.com', 'jane@company.com', 'mike@company.com'],
                    'Score': [85, 92, 78],
                    'Writing style (Score)': [3, 3, 2],
                    'Accuracy (Score)': [3, 3, 3], 
                    'Empathy & Hepfulness (Score)': [2, 3, 2],
                    'Customer Experience (CX) rating': [4, 5, 4]
                }
                sample_df = pd.DataFrame(sample_data)
                st.dataframe(sample_df, use_container_width=True)

if __name__ == "__main__":
    main()
