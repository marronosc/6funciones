import requests
import json
import logging
from urllib.parse import quote
from datetime import datetime

def search_keyword_suggestions(keyword, max_retries=3):
    """
    Busca sugerencias de palabras clave usando la YouTube Suggest API
    
    Args:
        keyword (str): Palabra clave base para buscar sugerencias
        max_retries (int): Número máximo de reintentos en caso de fallo
    
    Returns:
        dict: Información sobre las sugerencias encontradas
    """
    if not keyword or not keyword.strip():
        raise Exception("La palabra clave no puede estar vacía")
    
    keyword = keyword.strip()
    logging.info(f"Buscando sugerencias para: {keyword}")
    
    # URL de la YouTube Suggest API (no oficial)
    base_url = "https://suggestqueries.google.com/complete/search"
    
    params = {
        'client': 'youtube',
        'ds': 'yt',
        'q': keyword,
        'callback': 'window.google.ac.h'  # JSONP callback que luego limpiamos
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Intento {attempt + 1} de búsqueda")
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Limpiar la respuesta JSONP
            content = response.text
            
            # Remover el callback JSONP para obtener JSON puro
            if content.startswith('window.google.ac.h(') and content.endswith(')'):
                json_content = content[19:-1]  # Remover 'window.google.ac.h(' y ')'
            else:
                # Intentar encontrar el JSON dentro de la respuesta
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end != 0:
                    json_content = content[start:end]
                else:
                    raise Exception("No se pudo extraer JSON de la respuesta")
            
            # Parsear JSON
            data = json.loads(json_content)
            
            # Extraer sugerencias
            suggestions = []
            if len(data) >= 2 and isinstance(data[1], list):
                for item in data[1]:
                    if isinstance(item, list) and len(item) > 0:
                        suggestion = item[0].strip()
                        if suggestion and suggestion.lower() != keyword.lower():
                            suggestions.append(suggestion)
                    elif isinstance(item, str):
                        suggestion = item.strip()
                        if suggestion and suggestion.lower() != keyword.lower():
                            suggestions.append(suggestion)
            
            # Remover duplicados manteniendo el orden
            unique_suggestions = []
            seen = set()
            for suggestion in suggestions:
                suggestion_lower = suggestion.lower()
                if suggestion_lower not in seen:
                    seen.add(suggestion_lower)
                    unique_suggestions.append(suggestion)
            
            logging.info(f"Encontradas {len(unique_suggestions)} sugerencias únicas")
            
            return {
                'keyword': keyword,
                'suggestions': unique_suggestions,
                'total_suggestions': len(unique_suggestions),
                'search_date': datetime.now(),
                'has_suggestions': len(unique_suggestions) > 0
            }
            
        except requests.RequestException as e:
            logging.warning(f"Error de red en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Error de conexión tras {max_retries} intentos: {str(e)}")
        except json.JSONDecodeError as e:
            logging.warning(f"Error parseando JSON en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Error procesando respuesta del servidor: {str(e)}")
        except Exception as e:
            logging.error(f"Error inesperado en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Error inesperado: {str(e)}")

def format_suggestions_for_export(suggestions, keyword):
    """
    Formatea las sugerencias para exportación
    
    Args:
        suggestions (list): Lista de sugerencias
        keyword (str): Palabra clave original
    
    Returns:
        dict: Datos formateados para diferentes tipos de exportación
    """
    # Formato texto plano
    text_format = f"Sugerencias de YouTube para: {keyword}\n"
    text_format += f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    text_format += f"Total de sugerencias: {len(suggestions)}\n\n"
    
    for i, suggestion in enumerate(suggestions, 1):
        text_format += f"{i}. {suggestion}\n"
    
    # Formato CSV
    csv_format = "Número,Sugerencia\n"
    for i, suggestion in enumerate(suggestions, 1):
        # Escapar comillas en CSV
        escaped_suggestion = suggestion.replace('"', '""')
        csv_format += f'{i},"{escaped_suggestion}"\n'
    
    # Formato JSON
    json_format = {
        'keyword': keyword,
        'generated_date': datetime.now().isoformat(),
        'total_suggestions': len(suggestions),
        'suggestions': [
            {
                'position': i,
                'text': suggestion
            }
            for i, suggestion in enumerate(suggestions, 1)
        ]
    }
    
    return {
        'text': text_format,
        'csv': csv_format,
        'json': json.dumps(json_format, indent=2, ensure_ascii=False)
    }