import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
from collections import Counter
import base64
import traceback

# Page configuration - MUST be the first Streamlit command
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
    """Load the CSV data"""
    try:
        df = pd.read_csv(uploaded_file)
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None

def extract_feedback_insights(feedback_series, positive=True, max_insights=3):
    """Extract common themes from feedback text"""
    if feedback_series.empty or feedback_series.isna().all():
        return []
    
    try:
        # Combine all feedback, handling NaN values
        all_feedback = ' '.join(feedback_series.fillna('').astype(str).tolist())
        
        if len(all_feedback.strip()) < 10:
            return []
        
        # Define positive and negative keywords/phrases
        positive_patterns = [
            r'excellent|strong|clear|professional|effective',
            r'accurate|helpful|empathetic|warm|supportive',
            r'well[\s-]structured|easy to follow|friendly|polite',
            r'proactive|comprehensive|thorough|responsive|good|great'
        ]
        
        negative_patterns = [
            r'could.*improve|should.*focus|needs? to',
            r'lacking|missing|insufficient|unclear',
            r'enhance|develop|work on|pay.*attention|consider',
            r'better|more|less|avoid|reduce'
        ]
        
        patterns = positive_patterns if positive else negative_patterns
        insights = []
        
        # Pattern matching
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

def create_skill_radar_chart(agent_data, agent_name, skill_columns):
    """Create a radar chart for agent skills"""
    try:
        skills = []
        scores = []
        
        for skill_name, col_name in skill_columns.items():
            if col_name and col_name in agent_data.columns:
                score = agent_data[col_name].mean()
                if pd.notna(score):
                    skills.append(skill_name)
                    scores.append(score)
        
        if not skills:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=skills,
            fill='toself',
            name=agent_name,
            line=dict(color='#1f77b4')
        ))
        
        max_score = max(scores) if scores else 3
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(3, max_score * 1.1)]
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

def generate_markdown_report(data, column_mapping, agent_summaries):
    """Generate markdown report for download"""
    report = f"""# QA Analysis Report

## Overview
- **Total Conversations:** {len(data)}
- **Agents Analyzed:** {len(agent_summaries)}
- **Report Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Performance Summary
"""
    
    # Overall metrics
    if column_mapping['overall_score']:
        avg_qa = data[column_mapping['overall_score']].mean()
        report += f"- **Average QA Score:** {avg_qa:.1f}\n"
    
    if column_mapping['cx_rating']:
        avg_cx = data[column_mapping['cx_rating']].mean()
        report += f"- **Average CX Score:** {avg_cx:.1f}\n"
    
    # Overall insights
    feedback_cols = [col for col in column_mapping['feedback_columns'] if col]
    if feedback_cols:
        all_feedback = pd.concat([data[col] for col in feedback_cols if col in data.columns])
        
        report += "\n### Overall Strengths ✅\n"
        positive_insights = extract_feedback_insights(all_feedback, positive=True)
        for insight in positive_insights:
            report += f"- {insight}\n"
        
        report += "\n### Areas for Improvement ⚠️\n"
        negative_insights = extract_feedback_insights(all_feedback, positive=False)
        for insight in negative_insights:
            report += f"- {insight}\n"
    
    report += "\n---\n\n## Individual Agent Analysis\n\n"
    
    for agent_name, summary in agent_summaries.items():
        report += f"### {agent_name}\n\n"
        report += f"**Performance:**\n"
        if summary['qa_score']:
            report += f"- QA Score: {summary['qa_score']:.1f}\n"
        if summary['cx_score']:
            report += f"- CX Score: {summary['cx_score']:.1f}\n"
        report += f"- Conversations: {summary['conversations']}\n\n"
        
        if summary['skills']:
            report += f"**Skill Breakdown:**\n"
            for skill, score in summary['skills'].items():
                if score:
                    report += f"- {skill}: {score:.1f}\n"
        
        if summary['strengths']:
            report += f"\n**Strengths ✅:**\n"
            for strength in summary['strengths']:
                report += f"- {strength}\n"
        
        if summary['improvements']:
            report += f"\n**Improvement Areas 🎯:**\n"
            for improvement in summary['improvements']:
                report += f"- {improvement}\n"
        
        report += "\n---\n\n"
    
    return report

# Main App
def main():
    st.title("📊 QA Dashboard")
    st.markdown("Analyze agent performance with custom column mapping")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your QA CSV file", 
        type=['csv'],
        help="Upload any CSV file with QA data"
    )
    
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            df = load_data(uploaded_file)
        
        if df is None:
            return
        
        st.success(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Show data preview
        with st.expander("📋 Data Preview"):
            st.dataframe(df.head(), use_container_width=True)
        
        # Column mapping section
        st.sidebar.header("🎯 Column Mapping")
        st.sidebar.markdown("Map your CSV columns to the analysis fields:")
        
        available_columns = [''] + list(df.columns)
        
        # Core mappings
        st.sidebar.subheader("Required Fields")
        agent_name_col = st.sidebar.selectbox(
            "Agent/Representative Name", 
            available_columns,
            help="Column containing agent names"
        )
        
        st.sidebar.subheader("Score Fields")
        overall_score_col = st.sidebar.selectbox(
            "Overall QA Score", 
            available_columns,
            help="Main QA performance score"
        )
        
        cx_rating_col = st.sidebar.selectbox(
            "Customer Experience Score", 
            available_columns,
            help="Customer satisfaction rating"
        )
        
        # Skill mappings
        st.sidebar.subheader("Individual Skills")
        skill_1_col = st.sidebar.selectbox("Skill 1 (e.g., Writing)", available_columns)
        skill_1_name = st.sidebar.text_input("Skill 1 Name", "Writing Style")
        
        skill_2_col = st.sidebar.selectbox("Skill 2 (e.g., Accuracy)", available_columns)
        skill_2_name = st.sidebar.text_input("Skill 2 Name", "Accuracy")
        
        skill_3_col = st.sidebar.selectbox("Skill 3 (e.g., Empathy)", available_columns)
        skill_3_name = st.sidebar.text_input("Skill 3 Name", "Empathy")
        
        # Feedback mappings
        st.sidebar.subheader("Feedback Fields")
        st.sidebar.markdown("Select columns containing feedback text:")
        
        feedback_cols = []
        for i in range(1, 6):  # Allow up to 5 feedback columns
            col = st.sidebar.selectbox(f"Feedback Column {i}", available_columns, key=f"feedback_{i}")
            if col:
                feedback_cols.append(col)
        
        # Validate required mappings
        if not agent_name_col:
            st.warning("⚠️ Please select an Agent Name column to continue")
            return
        
        # Create column mapping dictionary
        column_mapping = {
            'agent_name': agent_name_col,
            'overall_score': overall_score_col,
            'cx_rating': cx_rating_col,
            'skills': {
                skill_1_name: skill_1_col if skill_1_col else None,
                skill_2_name: skill_2_col if skill_2_col else None,
                skill_3_name: skill_3_col if skill_3_col else None
            },
            'feedback_columns': feedback_cols
        }
        
        # Filter out empty skill mappings
        column_mapping['skills'] = {k: v for k, v in column_mapping['skills'].items() if v}
        
        # Main analysis
        st.header("📈 Analysis Results")
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_conversations = len(df)
            st.metric("Total Conversations", total_conversations)
        
        with col2:
            unique_agents = df[agent_name_col].nunique()
            st.metric("Unique Agents", unique_agents)
        
        with col3:
            if overall_score_col:
                avg_qa = df[overall_score_col].mean()
                st.metric("Average QA Score", f"{avg_qa:.1f}")
            else:
                st.metric("Average QA Score", "N/A")
        
        with col4:
            if cx_rating_col:
                avg_cx = df[cx_rating_col].mean()
                st.metric("Average CX Score", f"{avg_cx:.1f}")
            else:
                st.metric("Average CX Score", "N/A")
        
        # Overall insights
        if feedback_cols:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Overall Strengths")
                all_feedback = pd.concat([df[col] for col in feedback_cols if col in df.columns])
                positive_insights = extract_feedback_insights(all_feedback, positive=True)
                if positive_insights:
                    for insight in positive_insights:
                        st.success(insight)
                else:
                    st.info("No specific positive patterns identified")
            
            with col2:
                st.markdown("### ⚠️ Areas for Improvement")
                negative_insights = extract_feedback_insights(all_feedback, positive=False)
                if negative_insights:
                    for insight in negative_insights:
                        st.warning(insight)
                else:
                    st.info("No specific improvement areas identified")
        
        # Score distributions
        if overall_score_col or cx_rating_col:
            st.markdown("### 📊 Score Distributions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if overall_score_col and df[overall_score_col].notna().any():
                    fig_qa = px.histogram(
                        df.dropna(subset=[overall_score_col]), 
                        x=overall_score_col,
                        title="QA Score Distribution",
                        nbins=min(10, df[overall_score_col].nunique())
                    )
                    fig_qa.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_qa, use_container_width=True)
                else:
                    st.info("QA score data not available")
            
            with col2:
                if cx_rating_col and df[cx_rating_col].notna().any():
                    fig_cx = px.histogram(
                        df.dropna(subset=[cx_rating_col]), 
                        x=cx_rating_col,
                        title="CX Score Distribution",
                        nbins=min(5, df[cx_rating_col].nunique())
                    )
                    fig_cx.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_cx, use_container_width=True)
                else:
                    st.info("CX score data not available")
        
        # Individual agent analysis
        st.markdown("### 👥 Individual Agent Performance")
        
        agents = df[agent_name_col].dropna().unique()
        agent_summaries = {}
        
        for agent in sorted(agents):
            if pd.isna(agent):
                continue
                
            agent_data = df[df[agent_name_col] == agent]
            
            try:
                # Calculate metrics
                qa_score = None
                if overall_score_col:
                    qa_score = agent_data[overall_score_col].mean()
                
                cx_score = None
                if cx_rating_col:
                    cx_score = agent_data[cx_rating_col].mean()
                
                conversations = len(agent_data)
                
                # Skill breakdown
                skills = {}
                for skill_name, col_name in column_mapping['skills'].items():
                    if col_name and col_name in agent_data.columns:
                        skills[skill_name] = agent_data[col_name].mean()
                
                # Feedback analysis
                if feedback_cols:
                    agent_feedback = pd.concat([agent_data[col] for col in feedback_cols if col in agent_data.columns])
                    strengths = extract_feedback_insights(agent_feedback, positive=True)
                    improvements = extract_feedback_insights(agent_feedback, positive=False)
                else:
                    strengths = []
                    improvements = []
                
                # Store summary
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
                        if column_mapping['skills']:
                            radar_fig = create_skill_radar_chart(agent_data, agent, column_mapping['skills'])
                            if radar_fig:
                                st.plotly_chart(radar_fig, use_container_width=True)
                            else:
                                st.info("Not enough skill data for chart")
                        else:
                            st.info("No skills mapped for visualization")
                    
                    with col2:
                        st.markdown("#### 📈 Performance Metrics")
                        if qa_score:
                            st.metric("QA Score", f"{qa_score:.1f}")
                        if cx_score:
                            st.metric("CX Score", f"{cx_score:.1f}")
                        st.metric("Conversations", conversations)
                        
                        if skills:
                            st.markdown("#### 🎯 Skill Breakdown")
                            for skill, score in skills.items():
                                if pd.notna(score):
                                    st.write(f"**{skill}:** {score:.1f}")
                    
                    # Feedback sections
                    if strengths or improvements:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### ✅ What They Did Well")
                            if strengths:
                                for strength in strengths:
                                    st.success(strength)
                            else:
                                st.info("Continue current practices")
                        
                        with col2:
                            st.markdown("#### 🎯 Recommendations")
                            if improvements:
                                for improvement in improvements:
                                    st.warning(improvement)
                            else:
                                st.info("Performance meets expectations")
            
            except Exception as e:
                st.error(f"Error analyzing {agent}: {str(e)}")
                continue
        
        # Export section
        st.markdown("### 📥 Export Report")
        
        if st.button("🔽 Generate Markdown Report", type="primary"):
            try:
                markdown_content = generate_markdown_report(df, column_mapping, agent_summaries)
                
                # Create download link
                b64 = base64.b64encode(markdown_content.encode()).decode()
                filename = f"QA_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md"
                href = f'<a href="data:text/markdown;base64,{b64}" download="{filename}">📥 Download Report</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Report generated! Click the link above to download.")
                
                # Show preview
                with st.expander("📄 Preview Report"):
                    st.markdown(markdown_content)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    else:
        st.info("👆 Please upload a CSV file to get started")
        
        # Instructions
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 How to Use
            
            1. **Upload your CSV** with QA data
            2. **Map columns** using the sidebar:
               - Agent names (required)
               - QA scores (optional)
               - CX scores (optional)
               - Individual skills (optional)
               - Feedback text (optional)
            3. **View analysis** with insights and charts
            4. **Download report** in Markdown format
            """)
        
        with col2:
            st.markdown("""
            ### ✨ Features
            
            - **Flexible column mapping** - works with any CSV format
            - **Automatic insights** from feedback text
            - **Individual agent analysis** with skill radar charts
            - **Score distributions** and performance metrics
            - **Markdown export** ready for Notion
            - **No team grouping required** - focus on individual performance
            """)

if __name__ == "__main__":
    main()