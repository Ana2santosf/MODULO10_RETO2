import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Cargar el parquet generado
clientes_tickets_df = pd.read_parquet('Clientes_Tickets.parquet')


# Convertir la columna de fechas a formato datetime
clientes_tickets_df['Fecha_tiquet'] = pd.to_datetime(clientes_tickets_df['Fecha_tiquet'], errors='coerce')

# Eliminar filas con fechas inválidas
clientes_tickets_df = clientes_tickets_df.dropna(subset=['Fecha_tiquet'])

# Extraer el año de las fechas
clientes_tickets_df['Año'] = clientes_tickets_df['Fecha_tiquet'].dt.year.astype(str)

# Inicializar la aplicación Dash
app = dash.Dash(__name__)

# Crear el layout del dashboard
app.layout = html.Div([
    html.H1("Dashboard Interactivo - Análisis de Clientes"),
   
    # Dropdown para seleccionar el año
    html.Label("Selecciona uno o más años:"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': str(year)} for year in sorted(clientes_tickets_df['Año'].unique())],
        value=[str(clientes_tickets_df['Año'].max())],  # Por defecto, el año más reciente
        multi=True  # Permitir seleccionar múltiples años
    ),
   
    # Gráficos
    dcc.Graph(id='bar-plot'),
    dcc.Graph(id='scatter-plot'),
    dcc.Graph(id='line-plot'),
    dcc.Graph(id='comparison-plot'),
    dcc.Graph(id='ticket-evolution-plot')
])

# Definir las callbacks para actualizar los gráficos
@app.callback(
    [Output('bar-plot', 'figure'),
     Output('scatter-plot', 'figure'),
     Output('line-plot', 'figure'),
     Output('comparison-plot', 'figure'),
     Output('ticket-evolution-plot', 'figure')],
    [Input('year-dropdown', 'value')]
)
def update_graphs(selected_years):
    # Filtrar los datos por los años seleccionados
    filtered_df = clientes_tickets_df[clientes_tickets_df['Año'].isin(selected_years)]

    # Asegurarse de que el DataFrame no esté vacío
    if filtered_df.empty:
        return {}, {}, {}, {}, {}

    # Limitar los datos de 2023 hasta mayo
    if '2023' in selected_years:
        filtered_df = filtered_df[(filtered_df['Año'] != '2023') | (filtered_df['Fecha_tiquet'].dt.month <= 5)]

    # Gráfico de barras: valor total de compras por mes
    compras_por_mes = filtered_df.groupby([filtered_df['Fecha_tiquet'].dt.month, 'Año'])['Importe_tiquet'].sum().reset_index()
    compras_por_mes.columns = ['Mes', 'Año', 'Valor Total (€)']

    bar_fig = px.bar(compras_por_mes, x='Mes', y='Valor Total (€)', color='Año',
                     title=f'Valor total de compras por mes en {", ".join(selected_years)}',
                     labels={'Mes': 'Mes', 'Valor Total (€)': 'Valor total (€)'},
                     barmode='group',
                     category_orders={'Mes': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]})

    # Reemplazar números de mes por nombres
    month_labels = {1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR', 5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'}
    bar_fig.update_xaxes(tickvals=list(month_labels.keys()), ticktext=list(month_labels.values()))

    # Gráfico de dispersión: ticket medio por cliente
    ticket_medio_por_cliente = filtered_df.groupby('Id_cliente')['Importe_tiquet'].mean().reset_index()
    ticket_medio_por_cliente.columns = ['Id_cliente', 'Ticket Medio (€)']
    ticket_medio_por_cliente['Año'] = filtered_df.groupby('Id_cliente')['Año'].first().values

    scatter_fig = px.scatter(ticket_medio_por_cliente, x='Id_cliente', y='Ticket Medio (€)',
                             color='Año',
                             title=f'Ticket medio por cliente en {", ".join(selected_years)}',
                             labels={'Id_cliente': 'ID Cliente', 'Ticket Medio (€)': 'Ticket Medio (€)'})
    scatter_fig.update_traces(marker=dict(size=10, opacity=0.6))

    # Gráfico de línea: frecuencia de compra por cliente
    frecuencia_por_cliente = filtered_df.groupby(['Id_cliente', 'Año'])['Fecha_tiquet'].count().reset_index()
    frecuencia_por_cliente.columns = ['Id_cliente', 'Año', 'Frecuencia de Compra']
    line_fig = px.line(frecuencia_por_cliente, x='Id_cliente', y='Frecuencia de Compra', color='Año',
                       title=f'Frecuencia de compra por cliente en {", ".join(selected_years)}',
                       labels={'Id_cliente': 'ID Cliente', 'Frecuencia de Compra': 'Número de Compras'})

    # Gráfico comparativo de compras por año
    compras_por_año = filtered_df.groupby(['Año', filtered_df['Fecha_tiquet'].dt.month])['Importe_tiquet'].sum().reset_index()
    compras_por_año.columns = ['Año', 'Mes', 'Valor Total (€)']
    comparison_fig = px.line(compras_por_año, x='Mes', y='Valor Total (€)', color='Año',
                             title='Comparativa del valor total de compras por año',
                             labels={'Mes': 'Mes', 'Valor Total (€)': 'Valor total (€)'})

    # Reemplazar números de mes por nombres en el gráfico comparativo
    comparison_fig.update_xaxes(tickvals=list(month_labels.keys()), ticktext=list(month_labels.values()))

    # Gráfico de evolución de tickets
    tickets_evolucion = filtered_df.groupby(filtered_df['Fecha_tiquet'].dt.to_period("M"))['Id_tiquet'].count().reset_index()
    tickets_evolucion.columns = ['Fecha', 'Cantidad de Tickets']
    tickets_evolucion['Fecha'] = tickets_evolucion['Fecha'].dt.to_timestamp()  # Convertir a timestamp para Plotly
    ticket_evolution_fig = px.line(tickets_evolucion, x='Fecha', y='Cantidad de Tickets',
                                    title='Evolución de la cantidad de tickets a lo largo del tiempo',
                                    labels={'Fecha': 'Fecha', 'Cantidad de Tickets': 'Cantidad'})

    return bar_fig, scatter_fig, line_fig, comparison_fig, ticket_evolution_fig

# Ejecutar la aplicación
import os

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))


