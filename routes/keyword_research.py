from flask import Blueprint, request, render_template, redirect, url_for, make_response
from services.keyword_research import search_keyword_suggestions, format_suggestions_for_export
import logging

keyword_research_bp = Blueprint('keyword_research', __name__, url_prefix='/keyword-research')

@keyword_research_bp.route('/', methods=['GET', 'POST'])
def keyword_research():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        
        if not keyword:
            return render_template('keyword_research/index.html', 
                                 error="Por favor, introduce una palabra clave para buscar sugerencias.")
        
        # Validación básica de la palabra clave
        if len(keyword) < 2:
            return render_template('keyword_research/index.html', 
                                 error="La palabra clave debe tener al menos 2 caracteres.")
        
        if len(keyword) > 100:
            return render_template('keyword_research/index.html', 
                                 error="La palabra clave no puede exceder los 100 caracteres.")
        
        return redirect(url_for('keyword_research.generate_results', keyword=keyword))
    
    return render_template('keyword_research/index.html')

@keyword_research_bp.route('/results/<keyword>')
def generate_results(keyword):
    try:
        # Buscar sugerencias
        result = search_keyword_suggestions(keyword)
        
        # Preparar datos para exportación
        export_data = None
        if result['has_suggestions']:
            export_data = format_suggestions_for_export(result['suggestions'], keyword)
        
        return render_template('keyword_research/results.html',
                             result=result,
                             export_data=export_data)
                             
    except Exception as e:
        error_message = f"Error al buscar sugerencias: {str(e)}"
        logging.error(error_message)
        return render_template('keyword_research/error.html', 
                             error=error_message, 
                             keyword=keyword)

@keyword_research_bp.route('/export/<keyword>/<format_type>')
def export_suggestions(keyword, format_type):
    """
    Endpoint para exportar sugerencias en diferentes formatos
    """
    try:
        # Volver a buscar las sugerencias (esto es necesario porque no guardamos estado)
        result = search_keyword_suggestions(keyword)
        
        if not result['has_suggestions']:
            return render_template('keyword_research/error.html', 
                                 error="No hay sugerencias para exportar", 
                                 keyword=keyword)
        
        # Formatear datos para exportación
        export_data = format_suggestions_for_export(result['suggestions'], keyword)
        
        if format_type == 'txt':
            response = make_response(export_data['text'])
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="sugerencias_{keyword.replace(" ", "_")}.txt"'
            return response
            
        elif format_type == 'csv':
            response = make_response(export_data['csv'])
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="sugerencias_{keyword.replace(" ", "_")}.csv"'
            return response
            
        elif format_type == 'json':
            response = make_response(export_data['json'])
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="sugerencias_{keyword.replace(" ", "_")}.json"'
            return response
            
        else:
            return render_template('keyword_research/error.html', 
                                 error="Formato de exportación no válido", 
                                 keyword=keyword)
                                 
    except Exception as e:
        error_message = f"Error al exportar sugerencias: {str(e)}"
        logging.error(error_message)
        return render_template('keyword_research/error.html', 
                             error=error_message, 
                             keyword=keyword)