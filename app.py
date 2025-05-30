# -*- coding: utf-8 -*-
"""app.ipynb

Aplicación Dash para calcular el Valor Presente Neto (VPN) con gráficos interactivos.
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import random

# Inicializa la aplicación Dash con el tema de Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def generate_random_cash_flows(num_flows=5):
    """Genera una lista de flujos de caja aleatorios."""
    return [random.randint(500, 5000) for _ in range(num_flows)]

# Valores iniciales predeterminados
initial_discount_rate = 10.0
initial_investment = 5000.0
initial_cash_flows = generate_random_cash_flows()

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Calculadora de Valor Presente Neto (VPN)', className='text-center mt-4'),
            html.Hr(),
        ], width=12),
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Label('Tasa de Descuento (%)'),
                dbc.Col(
                    dbc.Input(
                        id='discount-rate',
                        type='number',
                        min=0,
                        step=0.1,
                        value=initial_discount_rate,
                        placeholder='Ingresa la tasa de descuento'
                    ),
                ),
            ]),
            dbc.Row([
                dbc.Label('Inversión Inicial'),
                dbc.Col(
                    dbc.Input(
                        id='initial-investment',
                        type='number',
                        min=0,
                        step=100,
                        value=initial_investment,
                        placeholder='Ingresa la inversión inicial'
                    ),
                ),
            ]),
            dbc.Row([
                dbc.Label('Flujos de Caja (separados por comas)'),
                dbc.Col(
                    dbc.Input(
                        id='cash-flows',
                        type='text',
                        value=', '.join(map(str, initial_cash_flows)),
                        placeholder='Ingresa los flujos de caja'
                    ),
                ),
            ]),
            dbc.Row([
                dbc.Button('Calcular VPN', id='calculate-btn', color='success', className='mr-2'),
                dbc.Button('Resetear', id='reset-btn', color='secondary'),
            ]),
            dbc.Row([
                html.Div(id='viability-message', className='mt-4'),
            ]),
        ], width=4),
        dbc.Col([
            dcc.Graph(id='cash-flows-bar-chart'),
            dcc.Graph(id='cumulative-cash-flow-line-chart'),
        ], width=8),
    ], className='mt-4'),
], fluid=True)

@app.callback(
    Output('cash-flows', 'value'),
    Input('reset-btn', 'n_clicks'),
)
def reset_cash_flows(n_clicks):
    """Genera nuevos flujos de caja aleatorios al presionar el botón de reset."""
    if n_clicks:
        random_flows = generate_random_cash_flows()
        return ', '.join(map(str, random_flows))
    raise dash.exceptions.PreventUpdate

@app.callback(
    [
        Output('cash-flows-bar-chart', 'figure'),
        Output('cumulative-cash-flow-line-chart', 'figure'),
        Output('viability-message', 'children')
    ],
    Input('calculate-btn', 'n_clicks'),
    [
        State('discount-rate', 'value'),
        State('initial-investment', 'value'),
        State('cash-flows', 'value'),
    ]
)
def calculate_npv(n_clicks, discount_rate, initial_investment, cash_flows):
    """Calcula el VPN y actualiza los gráficos y el mensaje de viabilidad."""
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    # Validación de entradas
    error_message = None
    if discount_rate is None or discount_rate < 0:
        error_message = 'Por favor, ingresa una tasa de descuento válida (no negativa).'
    elif initial_investment is None or initial_investment < 0:
        error_message = 'Por favor, ingresa una inversión inicial válida (no negativa).'
    else:
        try:
            cash_flows_list = [float(c.strip()) for c in cash_flows.split(',')]
            if len(cash_flows_list) == 0:
                error_message = 'Por favor, ingresa al menos un flujo de caja.'
        except ValueError:
            error_message = 'Por favor, ingresa flujos de caja válidos separados por comas.'

    if error_message:
        empty_figure = go.Figure()
        return (
            empty_figure,
            empty_figure,
            dbc.Alert(error_message, color='danger')
        )

    # Cálculo del VPN
    discount_rate_decimal = discount_rate / 100
    npv = -initial_investment
    discounted_cash_flows = []
    for i, cash_flow in enumerate(cash_flows_list):
        discounted = cash_flow / ((1 + discount_rate_decimal) ** (i + 1))
        discounted_cash_flows.append(discounted)
        npv += discounted

    # Preparación de gráficos
    years = list(range(1, len(cash_flows_list) + 1))

    bar_chart = go.Figure(data=[
        go.Bar(x=years, y=cash_flows_list, name='Flujos de Caja Anuales')
    ])
    bar_chart.update_layout(
        title='Flujos de Caja Anuales',
        xaxis_title='Año',
        yaxis_title='Flujo de Caja',
        template='plotly_white'
    )

    cumulative_cash_flows = [-initial_investment] + discounted_cash_flows
    cumulative_values = [sum(cumulative_cash_flows[:i+1]) for i in range(len(cumulative_cash_flows))]

    line_chart = go.Figure(data=[
        go.Scatter(
            x=[0] + years,
            y=cumulative_values,
            mode='lines+markers',
            name='Flujo de Caja Acumulado'
        )
    ])
    line_chart.update_layout(
        title='Flujo de Caja Acumulado con Descuento',
        xaxis_title='Año',
        yaxis_title='Flujo de Caja Acumulado',
        template='plotly_white'
    )

    # Mensaje de viabilidad
    if npv > 0:
        viability = dbc.Alert(f'El proyecto es viable. VPN = {npv:,.2f}', color='success')
    else:
        viability = dbc.Alert(f'El proyecto no es viable. VPN = {npv:,.2f}', color='danger')

    return bar_chart, line_chart, viability

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port = 8050)
