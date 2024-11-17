from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
from werkzeug.utils import secure_filename
import matplotlib
import seaborn as sns
matplotlib.use('Agg')  # Usar el backend "Agg" para evitar problemas de GUI

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Función para verificar si el archivo es un CSV
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Función para manejar la carga de archivos CSV
def handle_file_upload(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename

# Función para generar gráficos
def generate_graph(filename, col1, col2, graph_type):
    # Cargar el archivo CSV
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_csv(filepath)
    
    # Desactivar la GUI interactiva de Matplotlib
    plt.ioff()

    # Verificar que las columnas sean válidas
    if graph_type == 'line' and not pd.api.types.is_numeric_dtype(df[col2]):
        return "Error: La columna Y debe ser numérica para el gráfico de líneas."
    if graph_type == 'pie' and not pd.api.types.is_numeric_dtype(df[col2]):
        return "Error: La columna Y debe ser numérica para el gráfico circular."
    
    # Crear figura y ejes con tamaño ajustado
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Generar gráfico y aplicar mejoras
    if graph_type == 'bar':
        # El gráfico de barras generalmente requiere que ambas columnas sean numéricas
        df.plot(kind='bar', x=col1, y=col2, ax=ax, color='lightcoral', width=0.8)
        ax.set_title('Gráfico de Barras', fontsize=16)
        ax.set_xlabel(col1, fontsize=14)
        ax.set_ylabel(col2, fontsize=14)
        plt.xticks(rotation=45)
    elif graph_type == 'pie':
        # Asegurarse de que la columna X sea categórica
        group_sizes = df.groupby(col1).size()
        total_size = group_sizes.sum()
        
        # Agrupar categorías pequeñas en "Otros"
        threshold = 0.05
        small_categories = group_sizes[group_sizes / total_size < threshold]
        if not small_categories.empty:
            grouped_df = df.copy()
            grouped_df[col1] = df[col1].apply(lambda x: 'Otros' if x in small_categories.index else x)
            plot_data = grouped_df.groupby(col1).size()
        else:
            plot_data = group_sizes

        plot_data.plot(kind='pie', autopct='%1.1f%%', ax=ax, colors=plt.cm.Paired.colors)
        ax.set_title('Gráfico Circular Mejorado', fontsize=16)
        ax.set_ylabel('')  # Eliminar la etiqueta del eje Y para gráficos circulares
    elif graph_type == 'line':
        # Verificar si col1 es numérico para usarlo en el gráfico de líneas
        if not pd.api.types.is_numeric_dtype(df[col1]):
            return "Error: La columna X debe ser numérica para el gráfico de líneas."
        df.plot(kind='line', x=col1, y=col2, ax=ax, marker='o', color='teal')
        ax.set_title('Gráfico de Líneas', fontsize=16)
        ax.set_xlabel(col1, fontsize=14)
        ax.set_ylabel(col2, fontsize=14)
        plt.grid(visible=True, linestyle='--', alpha=0.5)

    # Asegurarse de que el directorio 'static/graficos' exista
    os.makedirs('static/graficos', exist_ok=True)
    
    # Nombre del archivo del gráfico
    graph_filename = f"graph_{filename.split('.')[0]}_{col1}_{col2}_{graph_type}.png"
    
    # Ruta completa donde se guarda la imagen
    graph_filepath = os.path.join('static', 'graficos', graph_filename)
    
    # Eliminar el archivo anterior si ya existe
    if os.path.exists(graph_filepath):
        os.remove(graph_filepath)
    
    # Guardar el gráfico
    plt.savefig(graph_filepath, bbox_inches='tight')
    plt.close(fig)
    
    # Retornar la ruta relativa para usarla en el HTML
    return f'graficos/{graph_filename}'


@app.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    files = [f for f in files if allowed_file(f)]
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', status='error'))
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = handle_file_upload(file)
        return redirect(url_for('index', status='success'))
    return redirect(url_for('index', status='error'))

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # Obtener los archivos CSV de la carpeta uploads
    files = os.listdir(UPLOAD_FOLDER)
    files = [f for f in files if allowed_file(f)]
    
    if request.method == 'POST':
        # Obtener el archivo seleccionado desde el formulario
        filename = request.form['file']
        return redirect(url_for('analyze_file', filename=filename))  # Redirigir al análisis del archivo

    return render_template('analyze.html', files=files)  # Mostrar el formulario de selección

@app.route('/analyze_file/<filename>', methods=['GET', 'POST'])
def analyze_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_csv(filepath)

    # Capturando la información del DataFrame (df.info()) en una variable
    buffer = io.StringIO()
    df.info(buf=buffer)
    df_info = buffer.getvalue()

    # Obtener las columnas numéricas y categóricas
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

    contingency_table_list = None
    graph_url = None
    graph_url_contingency = None  # Nueva variable para los gráficos de contingencia
    error_message = None

    # Calcular los valores nulos por columna
    null_values = df.isnull().sum().to_dict()  # Esto devuelve un diccionario con el conteo de nulos por columna

    descriptive_stats = df.describe().transpose().round(2).to_dict()

    # Dimensiones del DataFrame
    dimensions = {
        'rows': df.shape[0],
        'columns': df.shape[1]
    }
        
    # Generar medidas de tendencia central para las columnas numéricas
    measures = {}
    if numeric_columns:
        for column in numeric_columns:
            measures[column] = {
                'mean': df[column].mean(),
                'median': df[column].median(),
                'mode': df[column].mode().iloc[0] if not df[column].mode().empty else 'No hay moda'  # Si no hay moda
            }

    if request.method == 'POST':
        # Si se trata de generar un gráfico
        if 'graph_type' in request.form:
            col1 = request.form['col1']
            col2 = request.form['col2']
            graph_type = request.form['graph_type']

            # Asegúrate de que ambas columnas seleccionadas son numéricas
            if col1 not in numeric_columns or col2 not in numeric_columns:
                error_message = "Ambas columnas seleccionadas deben contener valores numéricos."
                return render_template(
                    'analyze_file.html', measures=measures, filename=filename, columns=numeric_columns,
                    error_message=error_message, descriptive_stats=descriptive_stats,
                    df=df, dimensions=dimensions, categorical_columns=categorical_columns, null_values=null_values, df_info=df_info, active_tab='graphs'
                )

            graph_url = generate_graph(filename, col1, col2, graph_type)
            return render_template(
                'analyze_file.html', measures=measures, filename=filename, columns=numeric_columns,
                descriptive_stats=descriptive_stats, graph_url=graph_url,
                df=df, dimensions=dimensions, categorical_columns=categorical_columns, null_values=null_values, df_info=df_info, active_tab='graphs'
            )
        
        # Si se trata de generar la tabla de contingencia
        if 'col1' in request.form and 'col2' in request.form:
            col1 = request.form['col1']
            col2 = request.form['col2']

            if col1 not in categorical_columns or col2 not in categorical_columns:
                error_message = "Ambas columnas seleccionadas deben ser categóricas."
                return render_template(
                    'analyze_file.html', measures=measures, filename=filename, columns=numeric_columns,
                    descriptive_stats=descriptive_stats, df=df, dimensions=dimensions,
                    categorical_columns=categorical_columns, error_message=error_message, null_values=null_values, df_info=df_info, active_tab='contingency'
                )
            
            # Normalizamos las categorías (quitar espacios y convertir a minúsculas)
            df[col1] = df[col1].astype(str).str.strip().str.lower()
            df[col2] = df[col2].astype(str).str.strip().str.lower()

            # Reemplazar valores de 'nan' con 'No disponible' para mejorar la legibilidad
            df[col1] = df[col1].replace('nan', 'No disponible')
            df[col2] = df[col2].replace('nan', 'No disponible')

            # Crear la tabla de contingencia
            contingency_table = pd.crosstab(df[col1], df[col2], dropna=False)

            # Asegurar que todas las categorías de ambas columnas estén incluidas
            all_values_col1 = df[col1].unique().tolist()  # Valores únicos de la columna 1
            all_values_col2 = df[col2].unique().tolist()  # Valores únicos de la columna 2

            # Asegurar que las columnas estén en el orden correcto
            contingency_table = contingency_table.reindex(index=all_values_col1, columns=all_values_col2, fill_value=0)

            # Convertir la tabla a tipo entero
            contingency_table = contingency_table.astype(int)

            # Asegurarse de que las filas y columnas sean tratadas como categorías y no como números
            contingency_table.index = contingency_table.index.astype(str)
            contingency_table.columns = contingency_table.columns.astype(str)

            # Convertir la tabla a una lista para pasar a la plantilla
            contingency_table_list = contingency_table.reset_index().values.tolist() if not contingency_table.empty else None

            # Pasar los nombres de las columnas (categorías) a la plantilla
            column_names = list(contingency_table.columns)

            #print(f"col1: {col1}, col2: {col2}")
            #print(f"Categorical Columns: {categorical_columns}")
            #print(f"Contingency Table: {contingency_table}")         

            # Si se presionó el botón de generar gráfico, generar el gráfico
            if 'generate_graph' in request.form:
                graph_url_contingency = generate_contingency_graph(df, col1, col2)

            return render_template(
                'analyze_file.html', measures=measures, filename=filename, columns=numeric_columns,
                descriptive_stats=descriptive_stats, df=df, dimensions=dimensions,
                categorical_columns=categorical_columns, contingency_table_list=contingency_table_list, null_values=null_values, df_info=df_info, active_tab='contingency',
                col1_name=col1, col2_name=col2, column_names=column_names, graph_url=graph_url, graph_url_contingency=graph_url_contingency
            )      



    # Cuando la solicitud es GET, renderizamos el formulario inicial
    return render_template(
        'analyze_file.html', measures=measures, filename=filename, columns=numeric_columns,
        descriptive_stats=descriptive_stats, df=df, dimensions=dimensions,
        categorical_columns=categorical_columns, null_values=null_values, df_info=df_info, active_tab='basic-info'
    )




@app.route('/contingency_table/<filename>', methods=['GET', 'POST'])
def contingency_table(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_csv(filepath)

    # Obtener las columnas categóricas
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

    contingency_table = None
    error_message = None

    if request.method == 'POST':
        col1 = request.form['col1']
        col2 = request.form['col2']

        if col1 not in categorical_columns or col2 not in categorical_columns:
            error_message = "Ambas columnas seleccionadas deben ser categóricas."
        else:
            # Crear la tabla de contingencia
            contingency_table = pd.crosstab(df[col1], df[col2]).reset_index().values.tolist()

    return render_template(
        'analyze_file.html', filename=filename, categorical_columns=categorical_columns,
        contingency_table=contingency_table, error_message=error_message
    )


def generate_contingency_graph(df, col1, col2):
    # Crear la tabla de contingencia
    contingency_table = pd.crosstab(df[col1], df[col2])

    # Crear la figura del gráfico
    plt.figure(figsize=(10, 7))

    # Usar un mapa de calor para mostrar la tabla de contingencia
    sns.heatmap(contingency_table, annot=True, fmt="d", cmap="Blues", cbar=False)

    # Guardar el gráfico en un archivo
    graph_filename = f"contingency_graph_{col1}_{col2}.png"
    graph_filepath = os.path.join('static', graph_filename)
    plt.savefig(graph_filepath)
    plt.close()  # Cerrar la figura para liberar memoria

    return graph_filename

@app.route('/measures_of_tendency/<filename>', methods=['GET', 'POST'])
def measures_of_tendency(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_csv(filepath)

    # Imprime las primeras filas y tipos de las columnas para depuración
    print(df.head())  # Asegúrate de que los datos se han cargado correctamente
    print(df.dtypes)  # Verifica los tipos de las columnas

    # Convierte todas las columnas a numéricas (si es posible) para asegurar que se procesen correctamente
    df = df.apply(pd.to_numeric, errors='coerce')

    # Obtener las columnas numéricas
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    print(numeric_columns)  # Verifica las columnas numéricas

    # Inicializar 'measures' como un diccionario vacío por si no hay columnas numéricas
    measures = {}

    if numeric_columns:
        # Calcular las medidas de tendencia solo si hay columnas numéricas
        for column in numeric_columns:
            measures[column] = {
                'mean': df[column].mean(),
                'median': df[column].median(),
                'mode': df[column].mode().iloc[0] if not df[column].mode().empty else 'No hay moda'  # Maneja caso sin moda
            }

    return render_template(
        'analyze_file.html', filename=filename, numeric_columns=numeric_columns, measures=measures, active_tab='measures_of_tendency'
    )


# Ruta para mostrar y eliminar archivos subidos
@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.csv')]

    if request.method == "POST":
        file_to_delete = request.form.get("file_to_delete")
        if file_to_delete:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_to_delete)
            try:
                os.remove(file_path)
                print(f"Archivo {file_to_delete} eliminado con éxito.")
            except Exception as e:
                print(f"Error al eliminar el archivo {file_to_delete}: {e}")

        return redirect(url_for('uploads'))

    return render_template("uploads.html", files=files)




if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usar el puerto de Railway
    app.run(host='0.0.0.0', port=port)
