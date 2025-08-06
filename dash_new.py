import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os
from datetime import datetime
import webbrowser
from flask import send_from_directory

# Function to read data from Excel
def read_data_from_excel(file_path):
    data = pd.read_excel(file_path, sheet_name=None)
    return data
# Function to read and process benchmark data - Removed
def read_benchmark_data(file_path):
    return {}

# Function to process benchmark data and integrate it into corresponding charts - Removed
def process_benchmark_data(benchmark_data):
    """Process benchmark data and integrate it into corresponding charts"""
    return {}

# Function to process data for both price scenarios
def process_data_all_scenarios(data):
    results = {}
    for price_scenario in ['MarketPrice', 'AvgPPAPrice']:
        profits_bau = []
        profits_ad = []
        years = []
        
        for scenario in ['BAU', 'AD']:
            df = data[f'{scenario}_{price_scenario}_AnnualSummary']
            if scenario == 'BAU':
                years = df.iloc[0:, 0].values.tolist()
                profits_bau = df['Discounted Net Revenue $b'].tolist()
            else:
                profits_ad = df['Discounted Net Revenue $b'].tolist()
        
        results[price_scenario] = {
            'profits_bau': profits_bau,
            'profits_ad': profits_ad,
            'years': years
        }
    
    return results

def preprocess_dash_data(data):
    processed_data = {}
    
    for price_scenario in ['MarketPrice', 'AvgPPAPrice']:
        processed_data[price_scenario] = {}
        
        for scenario in ['BAU', 'AD']:
            df = data[f'{scenario}_{price_scenario}_AnnualSummary']
            if 'Year' not in df.columns:
                df['Year'] = df.iloc[0:, 0].values.tolist()
                
            # Create a DataFrame for Total Generation
            total_generation_df = data[f'{scenario}_{price_scenario}_AnnualSummary'][['Year', 'Total Coal Gen TWh']].copy()
            total_generation_df.columns = ['Year', 'Total Generation (TWh)']
            processed_data[price_scenario][f'{scenario}_Total_Generation'] = total_generation_df
            
            # Create a DataFrame for Total Capacity
            total_capacity_df = data[f'{scenario}_{price_scenario}_AnnualSummary'][['Year', 'Total Capacity GW']].copy()
            total_capacity_df.columns = ['Year', 'Total Capacity (GW)']
            processed_data[price_scenario][f'{scenario}_Total_Capacity'] = total_capacity_df
            
            # Create a DataFrame for Retirement Schedule
            retirement_schedule_df = data[f'{scenario}_{price_scenario}_retire_sched'].iloc[1:, :].copy()
            processed_data[price_scenario][f'{scenario}_Retirement_Schedule'] = retirement_schedule_df
    
    return processed_data

def create_profit_plot(scenario_data, benchmark_data=None, title_prefix=""):
    fig = make_subplots(rows=2, cols=2, 
                       subplot_titles=(f"{title_prefix} Market Price Scenario", 
                                      f"{title_prefix} Avg PPA Price Scenario",
                                      f"{title_prefix} Market Price Scenario - Cumulative",
                                      f"{title_prefix} Avg PPA Price Scenario - Cumulative"),
                       shared_yaxes=True,vertical_spacing=0.2)  # Increase vertical spacing
    
    # Update subplot title font size
    fig.update_annotations(font_size=16)
    
    # Market Price subplot
    fig.add_trace(
        go.Scatter(
            x=scenario_data['MarketPrice']['years'],
            y=scenario_data['MarketPrice']['profits_bau'],
            mode='lines+markers',
            name='BAU - Market Price',
            line=dict(color='#1f77b4', width=2.5),  # deep blue
            marker=dict(size=7, color='#1f77b4')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=scenario_data['MarketPrice']['years'],
            y=scenario_data['MarketPrice']['profits_ad'],
            mode='lines+markers',
            name='AD - Market Price',
            line=dict(color='#d62728', width=2.5),  # red
            marker=dict(size=7, color='#d62728')
        ),
        row=1, col=1
    )
    
    # Avg PPA Price subplot
    fig.add_trace(
        go.Scatter(
            x=scenario_data['AvgPPAPrice']['years'],
            y=scenario_data['AvgPPAPrice']['profits_bau'],
            mode='lines+markers',
            name='BAU - Avg PPA Price',
            line=dict(color='#2ca02c', width=2.5),  # green
            marker=dict(size=7, color='#2ca02c')
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=scenario_data['AvgPPAPrice']['years'],
            y=scenario_data['AvgPPAPrice']['profits_ad'],
            mode='lines+markers',
            name='AD - Avg PPA Price',
            line=dict(color='#ff7f0e', width=2.5),  # orange
            marker=dict(size=7, color='#ff7f0e')
        ),
        row=1, col=2
    )
    
    # Calculate cumulative profits
    cumulative_profits = {}
    for price_scenario in ['MarketPrice', 'AvgPPAPrice']:
        cumulative_profits[price_scenario] = {
            'profits_bau_cumulative': [],
            'profits_ad_cumulative': []
        }
        
        # Calculate BAU cumulative profits
        cumulative_sum = 0
        for profit in scenario_data[price_scenario]['profits_bau']:
            cumulative_sum += profit
            cumulative_profits[price_scenario]['profits_bau_cumulative'].append(cumulative_sum)
        
        # Calculate AD cumulative profits
        cumulative_sum = 0
        for profit in scenario_data[price_scenario]['profits_ad']:
            cumulative_sum += profit
            cumulative_profits[price_scenario]['profits_ad_cumulative'].append(cumulative_sum)
    
    # Market Price annual profits
    fig.add_trace(
        go.Scatter(
            x=scenario_data['MarketPrice']['years'],
            y=scenario_data['MarketPrice']['profits_bau'],
            mode='lines+markers',
            name='BAU - Market Price',
            line=dict(color='#4E79A7', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    # ... existing code ...
    
    # Add cumulative profit charts
    # Market Price cumulative profits
    fig.add_trace(
        go.Scatter(
            x=scenario_data['MarketPrice']['years'],
            y=cumulative_profits['MarketPrice']['profits_bau_cumulative'],
            mode='lines+markers',
            name='BAU - Market Price (Cumulative)',
            line=dict(color='#1f77b4', width=2.5, dash='dot'),
            marker=dict(size=7, color='#1f77b4')
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=scenario_data['MarketPrice']['years'],
            y=cumulative_profits['MarketPrice']['profits_ad_cumulative'],
            mode='lines+markers',
            name='AD - Market Price (Cumulative)',
            line=dict(color='#d62728', width=2.5, dash='dot'),
            marker=dict(size=7, color='#d62728')
        ),
        row=2, col=1
    )
    
    # Avg PPA Price cumulative profits
    fig.add_trace(
        go.Scatter(
            x=scenario_data['AvgPPAPrice']['years'],
            y=cumulative_profits['AvgPPAPrice']['profits_bau_cumulative'],
            mode='lines+markers',
            name='BAU - Avg PPA Price (Cumulative)',
            line=dict(color='#2ca02c', width=2.5, dash='dot'),
            marker=dict(size=7, color='#2ca02c')
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=scenario_data['AvgPPAPrice']['years'],
            y=cumulative_profits['AvgPPAPrice']['profits_ad_cumulative'],
            mode='lines+markers',
            name='AD - Avg PPA Price (Cumulative)',
            line=dict(color='#ff7f0e', width=2.5, dash='dot'),
            marker=dict(size=7, color='#ff7f0e')
        ),
        row=2, col=2
    )
    
    # Add benchmark data (if available) - Removed
    # Update layout
    fig.update_layout(
        # title=f'{title_prefix} Profits Comparison Across Price Scenarios',
        height=800,  # Further increase chart height
        legend_title='Scenario',
        hovermode='x unified',
        template='plotly_white',
        title_font=dict(size=24, family='Georgia, serif', color='#1a1a1a'),  #   style title
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,  # Further adjust legend position, away from title
            xanchor="right",
            x=1,
            font=dict(size=14, family='Georgia, serif'),  #   style font
            bgcolor='rgba(255,255,255,0.9)',  # More opaque background
            bordercolor='rgba(0,0,0,0.3)',    # Darker border
            borderwidth=1.5
        ),
        margin=dict(l=80, r=50, t=120, b=80),  # Increase top margin
        font=dict(size=14, family='Georgia, serif'),  #   style font
        plot_bgcolor='rgba(248,248,248,0.8)',  #   style background color
        paper_bgcolor='white'
    )
    
        # Collect annual profit data for setting first row y-axis range
    annual_profits = []
    annual_profits.extend(scenario_data['MarketPrice']['profits_bau'])
    annual_profits.extend(scenario_data['MarketPrice']['profits_ad'])
    annual_profits.extend(scenario_data['AvgPPAPrice']['profits_bau'])
    annual_profits.extend(scenario_data['AvgPPAPrice']['profits_ad'])
    
    # Collect cumulative profit data for setting second row y-axis range
    cumulative_profits_all = []
    cumulative_profits_all.extend(cumulative_profits['MarketPrice']['profits_bau_cumulative'])
    cumulative_profits_all.extend(cumulative_profits['MarketPrice']['profits_ad_cumulative'])
    cumulative_profits_all.extend(cumulative_profits['AvgPPAPrice']['profits_bau_cumulative'])
    cumulative_profits_all.extend(cumulative_profits['AvgPPAPrice']['profits_ad_cumulative'])
    
    # Calculate appropriate y-axis ranges
    annual_max = max(annual_profits) * 1.1
    cumulative_max = max(cumulative_profits_all) * 1.1
    fig.update_xaxes(
        title_text='Year', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  #
        title_font=dict(size=16, family='Georgia, serif'),  # 
        tickfont=dict(size=14, family='Georgia, serif'),     # 
        zeroline=False,  # 
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    # Set y-axis range for first row (annual profits)
    fig.update_yaxes(
        title_text='Annual Profit (Billion $)', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  #   style grid lines
        range=[0, annual_max],
        row=1,
        title_font=dict(size=16, family='Georgia, serif'),  #   style font
        tickfont=dict(size=14, family='Georgia, serif'),     #   style font
        zeroline=False,  # Remove zero line
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    
    # Set y-axis range for second row (cumulative profits)
    fig.update_yaxes(
        title_text='Cumulative Profit (Billion $)', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  #   style grid lines
        range=[0, cumulative_max],
        row=2,
        title_font=dict(size=16, family='Georgia, serif'),  #   style font
        tickfont=dict(size=14, family='Georgia, serif'),     #   style font
        zeroline=False,  # Remove zero line
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )    
    return fig

# Function to create the total generation plot for both price scenarios
def create_total_generation_plot(processed_data,benchmark_data=None):
    fig = make_subplots(rows=1, cols=2, 
                       subplot_titles=("Market Price Scenario", "Avg PPA Price Scenario"),
                       shared_yaxes=True)
    
    # Update subplot title font size
    fig.update_annotations(font_size=18)
    # Market Price subplot
    fig.add_trace(
        go.Scatter(
            x=processed_data['MarketPrice']['BAU_Total_Generation']['Year'],
            y=processed_data['MarketPrice']['BAU_Total_Generation']['Total Generation (TWh)'],
            mode='lines+markers',
            name='BAU - Market Price',
            line=dict(color='#1f77b4', width=2.5),  #  deep blue
            marker=dict(size=7, color='#1f77b4')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=processed_data['MarketPrice']['AD_Total_Generation']['Year'],
            y=processed_data['MarketPrice']['AD_Total_Generation']['Total Generation (TWh)'],
            mode='lines+markers',
            name='AD - Market Price',
            line=dict(color='#d62728', width=2.5),  # Economist red
            marker=dict(size=7, color='#d62728')
        ),
        row=1, col=1
    )
    
    # Avg PPA Price subplot
    fig.add_trace(
        go.Scatter(
            x=processed_data['AvgPPAPrice']['BAU_Total_Generation']['Year'],
            y=processed_data['AvgPPAPrice']['BAU_Total_Generation']['Total Generation (TWh)'],
            mode='lines+markers',
            name='BAU - Avg PPA Price',
            line=dict(color='#2ca02c', width=2.5),  # Economist green
            marker=dict(size=7, color='#2ca02c')
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=processed_data['AvgPPAPrice']['AD_Total_Generation']['Year'],
            y=processed_data['AvgPPAPrice']['AD_Total_Generation']['Total Generation (TWh)'],
            mode='lines+markers',
            name='AD - Avg PPA Price',
            line=dict(color='#ff7f0e', width=2.5),  # Economist orange
            marker=dict(size=7, color='#ff7f0e')
        ),
        row=1, col=2
    )
    # Add benchmark data (if available) - Removed
    
    fig.update_layout(
        # title='Total Generation Comparison Across Price Scenarios',
        height=700,  # 增加图表高度
        legend_title='Scenario',
        hovermode='x unified',
        template='plotly_white',
        title_font=dict(size=24, family='Georgia, serif', color='#1a1a1a'),  # 经济学人风格标题
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,  # 调整图例位置，远离标题
            xanchor="right",
            x=1,
            font=dict(size=14, family='Georgia, serif'),  # 经济学人风格字体
            bgcolor='rgba(255,255,255,0.9)',  # 更不透明的背景
            bordercolor='rgba(0,0,0,0.3)',    # 更深的边框
            borderwidth=1.5
        ),
        margin=dict(l=80, r=50, t=120, b=80),  # 增加顶部边距
        font=dict(size=14, family='Georgia, serif'),  # 经济学人风格字体
        plot_bgcolor='rgba(248,248,248,0.8)',  # 经济学人风格背景色
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(
        title_text='Year', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  # 经济学人风格网格线
        title_font=dict(size=16, family='Georgia, serif'),  # 经济学人风格字体
        tickfont=dict(size=14, family='Georgia, serif'),     # 经济学人风格字体
        zeroline=False,  # 移除零线
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    fig.update_yaxes(
        title_text='Total Generation (TWh)', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  # 经济学人风格网格线
        title_font=dict(size=16, family='Georgia, serif'),  # 经济学人风格字体
        tickfont=dict(size=14, family='Georgia, serif'),     # 经济学人风格字体
        zeroline=False,  # 移除零线
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    
    return fig

# Function to create the total capacity plot for both price scenarios
def create_total_capacity_plot(processed_data,benchmark_data=None):
    fig = make_subplots(rows=1, cols=2, 
                       subplot_titles=("Market Price Scenario", "Avg PPA Price Scenario"),
                       shared_yaxes=True)
    
    # Update subplot title font size
    fig.update_annotations(font_size=18)
 
    # Market Price subplot
    fig.add_trace(
        go.Scatter(
            x=processed_data['MarketPrice']['BAU_Total_Capacity']['Year'],
            y=processed_data['MarketPrice']['BAU_Total_Capacity']['Total Capacity (GW)'],
            mode='lines+markers',
            name='BAU - Market Price',
            line=dict(color='#1f77b4', width=2.5),  # 经济学人深蓝色
            marker=dict(size=7, color='#1f77b4')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=processed_data['MarketPrice']['AD_Total_Capacity']['Year'],
            y=processed_data['MarketPrice']['AD_Total_Capacity']['Total Capacity (GW)'],
            mode='lines+markers',
            name='AD - Market Price',
            line=dict(color='#d62728', width=2.5),  # 经济学人红色
            marker=dict(size=7, color='#d62728')
        ),
        row=1, col=1
    )
    
    # Avg PPA Price subplot
    fig.add_trace(
        go.Scatter(
            x=processed_data['AvgPPAPrice']['BAU_Total_Capacity']['Year'],
            y=processed_data['AvgPPAPrice']['BAU_Total_Capacity']['Total Capacity (GW)'],
            mode='lines+markers',
            name='BAU - Avg PPA Price',
            line=dict(color='#2ca02c', width=2.5),  # 经济学人绿色
            marker=dict(size=7, color='#2ca02c')
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(
            x=processed_data['AvgPPAPrice']['AD_Total_Capacity']['Year'],
            y=processed_data['AvgPPAPrice']['AD_Total_Capacity']['Total Capacity (GW)'],
            mode='lines+markers',
            name='AD - Avg PPA Price',
            line=dict(color='#ff7f0e', width=2.5),  # 经济学人橙色
            marker=dict(size=7, color='#ff7f0e')
        ),
        row=1, col=2
    )
    
       # Add benchmark data (if available) - Removed
    
    
    fig.update_layout(
        # title='Total Capacity Comparison Across Price Scenarios',
        height=700,  # 增加图表高度
        legend_title='Scenario',
        hovermode='x unified',
        template='plotly_white',
        title_font=dict(size=24, family='Georgia, serif', color='#1a1a1a'),  # 经济学人风格标题
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,  # 调整图例位置，远离标题
            xanchor="right",
            x=1,
            font=dict(size=14, family='Georgia, serif'),  # 经济学人风格字体
            bgcolor='rgba(255,255,255,0.9)',  # 更不透明的背景
            bordercolor='rgba(0,0,0,0.3)',    # 更深的边框
            borderwidth=1.5
        ),
        margin=dict(l=80, r=50, t=120, b=80),  # 增加顶部边距
        font=dict(size=14, family='Georgia, serif'),  # 经济学人风格字体
        plot_bgcolor='rgba(248,248,248,0.8)',  # 经济学人风格背景色
        paper_bgcolor='white'
    )
    
    fig.update_xaxes(
        title_text='Year', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  # 经济学人风格网格线
        title_font=dict(size=16, family='Georgia, serif'),  # 经济学人风格字体
        tickfont=dict(size=14, family='Georgia, serif'),     # 经济学人风格字体
        zeroline=False,  # 移除零线
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    fig.update_yaxes(
        title_text='Total Capacity (GW)', 
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(200,200,200,0.5)',  # 经济学人风格网格线
        title_font=dict(size=16, family='Georgia, serif'),  # 经济学人风格字体
        tickfont=dict(size=14, family='Georgia, serif'),     # 经济学人风格字体
        zeroline=False,  # 移除零线
        showline=True,
        linecolor='rgba(0,0,0,0.3)',
        linewidth=1
    )
    
    return fig

# Function to create retirement schedule tables
def create_retirement_tables(processed_data):
    tables = {}
    
    for price_scenario in ['MarketPrice', 'AvgPPAPrice']:
        for scenario in ['BAU', 'AD']:
            key = f"{scenario}_{price_scenario}"
            df = processed_data[price_scenario][f'{scenario}_Retirement_Schedule']
            
            # Convert all column names to strings to avoid DataTable errors
            df.columns = [str(col) for col in df.columns]
            
            # 创建条件样式列表，根据单元格值设置颜色
            style_data_conditional = [
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'},
                {'if': {'column_type': 'numeric'}, 'textAlign': 'right'}
            ]
            
            # 为不同的退役年份添加不同的颜色
            # 数值越大（越晚退役）颜色越深
            for i, year in enumerate(range(2021, 2051)):
                if str(year) in df.columns:
                    intensity = min(100, int(30 + i * 2.5))  # 颜色强度随年份增加
                    style_data_conditional.append({
                        'if': {
                            'column_id': str(year),
                            'filter_query': f'{{{year}}} = 1'
                        },
                        'backgroundColor': f'rgba(66, 133, 244, 0.{intensity})',
                        'color': 'white' if intensity > 50 else 'black',
                        'fontWeight': 'bold'
                    })
            
            tables[key] = html.Div([
                # 添加搜索和筛选功能
                html.Div([
                    html.Div([
                        html.Label("Search:"),
                        dcc.Input(
                            id=f'search-input-{key}',
                            type='text',
                            placeholder='type in plant names...',
                            style={'width': '100%', 'marginBottom': '10px'}
                        ),
                    ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Label("Filter by year of retirement:"),
                        dcc.RangeSlider(
                            id=f'year-slider-{key}',
                            min=2021,
                            max=2050,
                            step=1,
                            marks={i: str(i) for i in range(2021, 2051, 5)},
                            value=[2021, 2050]
                        ),
                    ], style={'width': '60%', 'display': 'inline-block'})
                ], style={'marginBottom': '20px'}),
                
                # 增强的数据表
                dash_table.DataTable(
                    id=f'retirement-table-{key}',
                    columns=[{"name": str(i), "id": str(i)} for i in df.columns],
                    data=df.to_dict('records'),
                    filter_action="native",  # 启用内置筛选
                    sort_action="native",    # 启用内置排序
                    sort_mode="multi",       # 允许多列排序
                    style_table={
                        'overflowX': 'auto', 
                        'maxHeight': '400px',
                        'border': '1px solid #ddd',
                        'borderRadius': '5px'
                    },
                    style_cell={
                        'textAlign': 'center',
                        'padding': '10px',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '12px',
                        'minWidth': '80px', 'width': '80px', 'maxWidth': '80px',
                    },
                    style_header={
                        'backgroundColor': '#2a5298',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'border': '1px solid #ddd',
                        'fontSize': '14px',
                        'textAlign': 'center'
                    },
                    style_data_conditional=style_data_conditional,
                    fixed_rows={'headers': True},
                    page_size=15,
                    tooltip_data=[
                        {
                            column: {'value': f'Retiring in {column}' if value == 1 else ''}
                            for column, value in row.items() if column not in ['Plant', 'Unnamed: 0'] and value == 1
                        } for row in df.to_dict('records')
                    ],
                    tooltip_duration=None,
                    css=[{
                        'selector': '.dash-table-tooltip',
                        'rule': 'background-color: #2a5298; color: white; font-size: 12px;'
                    }]
                ),
                
                # 添加图形化展示 - 退役时间线
                html.Div([
                    html.H4("Retirement Schedule", style={'textAlign': 'center', 'marginTop': '20px'}),
                    dcc.Graph(
                        id=f'retirement-timeline-{key}',
                        figure=create_retirement_timeline(df, scenario, price_scenario)
                    )
                ], style={'marginTop': '20px'})
            ])
    
    return tables

# Create retirement timeline chart
def create_retirement_timeline(df, scenario, price_scenario):
    # Prepare data
    plants = []
    years = []
    colors = []
    
    # Color mapping
    color_map = {
        'BAU_MarketPrice': '#4E79A7',
        'AD_MarketPrice': '#E15759',
        'BAU_AvgPPAPrice': '#76B7B2',
        'AD_AvgPPAPrice': '#F28E2B'
    }
    
    # Get all year columns
    year_columns = [col for col in df.columns if str(col).isdigit()]
    
    # Find retirement year for each plant
    for idx, row in df.iterrows():
        plant_name = row.iloc[0] if 'Plant' not in df.columns else row['Plant']
        
        # Skip rows without names
        if pd.isna(plant_name) or plant_name == '':
            continue
            
        # Find retirement year
        retirement_year = None
        for year in year_columns:
            if row[year] == 1:
                retirement_year = int(year)
                break
        
        if retirement_year:
            plants.append(str(plant_name))
            years.append(retirement_year)
            colors.append(color_map[f'{scenario}_{price_scenario}'])
    
    # Create chart
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=years,
        y=plants,
        mode='markers',
        marker=dict(
            size=12,
            color=colors,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        name='Year of Retirement',
    ))
    
    # Update layout
    fig.update_layout(
        title=f'{scenario} - {price_scenario} Retirement Schedule',
        xaxis_title='Year of Retirement',
        yaxis_title='Plant Name',
        template='plotly_white',
        height=max(400, len(plants) * 25),  # Adjust height based on number of plants
        margin=dict(l=150, r=30, t=50, b=50),
        xaxis=dict(
            tickmode='linear',
            tick0=2021,
            dtick=5,
            gridcolor='LightGray'
        )
    )
    
    return fig


# Initialize the Dash app with a custom theme
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Create static folder for saving exported HTML files
EXPORT_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
if not os.path.exists(EXPORT_DIRECTORY):
    os.makedirs(EXPORT_DIRECTORY)

# Add export functionality callback
@app.callback(
    Output('export-status', 'children'),
    Input('export-button', 'n_clicks'),
    prevent_initial_call=True
)
def export_dashboard(n_clicks):
    if n_clicks:
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ffrm_dashboard_{timestamp}.html"
            filepath = os.path.join(EXPORT_DIRECTORY, filename)
            
            # Get current page HTML and save
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write HTML header
                f.write('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>FFRM Dashboard Export</title>
                    <style>
                        body {
                            font-family: 'Arial', sans-serif;
                            background-color: #f8f9fa;
                            margin: 0;
                            padding: 0;
                        }
                        .dashboard-container {
                            max-width: 1400px;
                            margin: 0 auto;
                            padding: 20px;
                        }
                        .header {
                            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                            color: white;
                            padding: 20px;
                            border-radius: 10px 10px 0 0;
                            margin-bottom: 20px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }
                        .header h1 {
                            margin: 0;
                            font-size: 32px;
                            text-align: center;
                        }
                        .header p {
                            margin: 10px 0 0;
                            text-align: center;
                            opacity: 0.8;
                        }
                        .card {
                            background-color: white;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                            padding: 20px;
                            margin-bottom: 20px;
                        }
                        .export-info {
                            text-align: center;
                            padding: 10px;
                            background-color: #f0f0f0;
                            border-radius: 5px;
                            margin: 10px 0;
                        }
                    </style>
                    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                </head>
                <body>
                    <div class="dashboard-container">
                        <div class="header">
                            <h1>Fossil Fuel Retirement Model (FFRM)</h1>
                            <p>Financial and Forced Retirement Model for Coal Power Plants</p>
                        </div>
                        <div class="export-info">
                            This file is static HTML version of FFRM dashboard, generated on ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '''
                        </div>
                ''')
                
                # Add charts
                f.write('<div class="card"><h3>Revenues</h3><div id="profit-plot"></div></div>')
                f.write('<div class="card"><h3>Total Generation</h3><div id="generation-plot"></div></div>')
                f.write('<div class="card"><h3>Total Capacity</h3><div id="capacity-plot"></div></div>')
                
                # Add script to render charts - using placeholder data for now
                f.write('<script>')
                f.write('''
                    // Placeholder data - charts will be generated when data is available
                    console.log("Export functionality requires data to be available");
                ''')
                f.write('</script>')
                
                # Add footer
                f.write('''
                        <div class="footer">
                            <p>© FFRM | Data: 2023-11-01</p>
                        </div>
                    </div>
                </body>
                </html>
                ''')
            
            # Automatically open generated HTML file
            webbrowser.open('file://' + filepath)
            
            return html.Div([
                html.P(f"Dashboard exported as HTML", style={'color': 'green'}),
                html.A("Download", href=f"/exports/{filename}", download=filename, target="_blank")
            ])
        except Exception as e:
            return html.Div([
                html.P(f"Error exporting dashboard: {str(e)}", style={'color': 'red'})
            ])
    
    return ""

# 添加保存图片功能的回调
@app.callback(
    Output('save-images-status', 'children'),
    Input('save-images-button', 'n_clicks'),
    prevent_initial_call=True
)
def save_images(n_clicks):
    if n_clicks:
        try:
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Function to save plot as image
            def save_plot_as_image(fig, filename):
                # Create images directory
                images_dir = os.path.join(EXPORT_DIRECTORY, 'images')
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                
                filepath = os.path.join(images_dir, filename)
                
                # Save as PNG format
                fig.write_image(filepath, format='png', width=1200, height=600, scale=2)
                return filepath
            
            # Save all charts
            saved_files = []
            
            # Note: This function will need access to the actual plot objects
            # which are created later in the code. For now, we'll return a message
            # indicating that this feature needs to be implemented differently.
            
            return html.Div([
                html.P("Image saving feature requires plot objects to be available.", style={'color': 'blue'}),
                html.P("This feature will be implemented in a future update.", style={'color': 'blue'})
            ])
            
        except Exception as e:
            return html.Div([
                html.P(f"Error saving images: {str(e)}", style={'color': 'red'})
            ])
    
    return ""


# 添加路由以访问导出的文件
@app.server.route('/exports/<path:path>')
def serve_static(path):
    return send_from_directory(EXPORT_DIRECTORY, path)

# 添加路由以访问图片文件
@app.server.route('/exports/images/<path:path>')
def serve_images(path):
    images_dir = os.path.join(EXPORT_DIRECTORY, 'images')
    return send_from_directory(images_dir, path)
# Custom CSS for better styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>FFRM Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            .dashboard-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .header h1 {
                margin: 0;
                font-size: 32px;
                text-align: center;
            }
            .header p {
                margin: 10px 0 0;
                text-align: center;
                opacity: 0.8;
            }
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                padding: 20px;
                margin-bottom: 20px;
            }
            .tab-content {
                padding: 20px;
                background-color: white;
                border-radius: 0 0 8px 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .footer {
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 12px;
                margin-top: 40px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Read and process data
file_path = 'Results.xlsx'
data = read_data_from_excel(file_path)
scenario_data = process_data_all_scenarios(data)
processed_data = preprocess_dash_data(data)

# 读取和处理 benchmark 数据 - 已移除
benchmark_data = None

# Create the plots
profit_plot = create_profit_plot(scenario_data, benchmark_data)
total_generation_plot = create_total_generation_plot(processed_data, benchmark_data)
total_capacity_plot = create_total_capacity_plot(processed_data, benchmark_data)

# Create retirement tables
retirement_tables = create_retirement_tables(processed_data)

# Define the layout of the dashboard
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Fossil Fuel Retirement Model (FFRM)"),
        html.P("Financial and Forced Retirement Model for Coal Power Plants")
    ], className="header"),
    html.Div([
        html.Button('Export as HTML', id='export-button', 
                   style={
                       'backgroundColor': '#2a5298',
                       'color': 'white',
                       'border': 'none',
                       'padding': '10px 20px',
                       'borderRadius': '5px',
                       'cursor': 'pointer',
                       'float': 'right',
                       'marginBottom': '10px',
                       'marginRight': '10px'
                   }),
        html.Button('Save Images', id='save-images-button', 
                   style={
                       'backgroundColor': '#28a745',
                       'color': 'white',
                       'border': 'none',
                       'padding': '10px 20px',
                       'borderRadius': '5px',
                       'cursor': 'pointer',
                       'float': 'right',
                       'marginBottom': '10px'
                   }),
        html.Div(id='export-status'),
        html.Div(id='save-images-status')
    ], className="card"),
    # Main content
    html.Div([
        # Summary Cards
        html.Div([
            html.Div([
                html.H3("Introduction", style={'margin-top': '0'}),
                html.P("... ... Market Price and Avg PPA Price"),
                html.P("BAU (Business As Usual)，AD (Accelerated Depreciation) to fit goals of different levels")
            ], className="card")
        ]),
        
        # Profit Plot
        html.Div([
            html.H3("Revenues", style={'margin-top': '0'}),
            dcc.Graph(id='profit-plot', figure=profit_plot)
        ], className="card"),
        
        # Generation and Capacity Plots
        html.Div([
            html.Div([
                html.H3("Total Generation", style={'margin-top': '0'}),
                dcc.Graph(id='total-generation-plot', figure=total_generation_plot)
            ], className="card"),
            
            html.Div([
                html.H3("Total Capacity", style={'margin-top': '0'}),
                dcc.Graph(id='total-capacity-plot', figure=total_capacity_plot)
            ], className="card"),
        ]),
        
        # Retirement Schedules
        html.Div([
            html.H3("Retirement Schedule", style={'margin-top': '0'}),
            
            # Tabs for different scenarios
            dcc.Tabs([
                dcc.Tab(label='Market Price - BAU', children=[
                    html.Div([
                        retirement_tables['BAU_MarketPrice']
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Market Price - AD', children=[
                    html.Div([
                        retirement_tables['AD_MarketPrice']
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Average PPA - BAU', children=[
                    html.Div([
                        retirement_tables['BAU_AvgPPAPrice']
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Average PPA - AD', children=[
                    html.Div([
                        retirement_tables['AD_AvgPPAPrice']
                    ], style={'padding': '20px'})
                ]),
            ], className="custom-tabs")
        ], className="card"),
        
        # Footer
        html.Div([
            html.P("© (FFRM) | data: 2023-11-01")
        ], className="footer")
        
    ], className="dashboard-container")
])

# Run the app
if __name__ == '__main__':
    app.run(debug=True)