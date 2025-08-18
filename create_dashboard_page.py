#!/usr/bin/env python3
"""
Create a static HTML dashboard page for GitHub Pages
为GitHub Pages创建静态HTML dashboard页面
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import json

def create_static_dashboard():
    """Create a static HTML dashboard"""
    
    # Load data
    print("Loading data...")
    data = pd.read_excel('250810 FFRM Data Input File - Philippines.xlsx', sheet_name=None)
    
    # Create sample plots (you can customize these based on your actual data)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=[2021, 2022, 2023, 2024, 2025], 
                              y=[100, 120, 140, 160, 180], 
                              name='BAU Scenario'))
    fig1.add_trace(go.Scatter(x=[2021, 2022, 2023, 2024, 2025], 
                              y=[100, 110, 120, 130, 140], 
                              name='AD Scenario'))
    fig1.update_layout(title='FFRM Revenue Projection', 
                       xaxis_title='Year', 
                       yaxis_title='Revenue ($M)')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=['2021', '2022', '2023', '2024', '2025'], 
                          y=[50, 45, 40, 35, 30], 
                          name='Coal Generation'))
    fig2.update_layout(title='Coal Generation Forecast', 
                       xaxis_title='Year', 
                       yaxis_title='Generation (TWh)')
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FFRM Dashboard - Fossil Fuel Retirement Model</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #333;
            margin-top: 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .plot-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #ddd;
        }}
        .info-box {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .scenario-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .scenario-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        }}
        .scenario-card h3 {{
            color: #495057;
            margin-top: 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Fossil Fuel Retirement Model (FFRM)</h1>
            <p>Financial and Forced Retirement Model for Coal Power Plants</p>
        </div>
        
        <div class="card">
            <h2>About FFRM</h2>
            <div class="info-box">
                <p><strong>FFRM</strong> is an open-source Python-based fossil fuel retirement model originally developed by the World Bank as a coal retirement optimization model. It can be used to estimate the stranded cost associated with retiring fossil fuel power plants.</p>
            </div>
            
            <div class="scenario-grid">
                <div class="scenario-card">
                    <h3>BAU Scenario</h3>
                    <p><strong>Business As Usual:</strong> Represents the baseline scenario with current policies and market conditions.</p>
                </div>
                <div class="scenario-card">
                    <h3>AD Scenario</h3>
                    <p><strong>Accelerated Decarbonization:</strong> Represents an accelerated transition scenario with stronger climate policies.</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Revenue Projection</h2>
            <div class="plot-container" id="revenue-plot"></div>
        </div>
        
        <div class="card">
            <h2>Coal Generation Forecast</h2>
            <div class="plot-container" id="generation-plot"></div>
        </div>
        
        <div class="card">
            <h2>Key Features</h2>
            <ul>
                <li><strong>Multi-scenario analysis:</strong> Business As Usual, Accelerated Decarbonization</li>
                <li><strong>Multiple price scenarios:</strong> Market Price, Average PPA Price</li>
                <li><strong>Flexible solver options:</strong> Gurobi, CPLEX, GLPK, CBC</li>
                <li><strong>Comprehensive result processing:</strong> Excel output and visualization</li>
                <li><strong>Command-line interface:</strong> Easy configuration and execution</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>© FFRM Dashboard | Data: 2023-11-01 | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><a href="https://github.com/FossilFuelRetirementModel/ffrm_python" target="_blank">View on GitHub</a></p>
        </div>
    </div>
    
    <script>
        // Revenue plot
        const revenueData = {fig1.to_json()};
        Plotly.newPlot('revenue-plot', revenueData.data, revenueData.layout, revenueData.config);
        
        // Generation plot
        const generationData = {fig2.to_json()};
        Plotly.newPlot('generation-plot', generationData.data, generationData.layout, generationData.config);
    </script>
</body>
</html>
"""
    
    # Write to file
    output_file = 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard created: {output_file}")
    print("To deploy to GitHub Pages:")
    print("1. Add this file to your repository")
    print("2. Go to repository Settings > Pages")
    print("3. Select 'Deploy from a branch'")
    print("4. Choose 'main' branch and '/ (root)' folder")
    print("5. Your dashboard will be available at: https://yourusername.github.io/ffrm_python/")
    
    return output_file

if __name__ == '__main__':
    create_static_dashboard() 