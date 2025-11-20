# Exports App

Sistema modular de exportación de datos a Excel usando plantillas.

## 📋 Funcionalidades

### 1. Exportación de Ficha API

Genera un archivo Excel con toda la información de una asignatura usando la plantilla `ficha_api.xlsx`.

**Endpoint:**
```
GET /api/exports/subjects/{subject_id}/ficha-api/
```

**Permisos requeridos:**
- El docente de la asignatura
- Usuarios con rol `admin`, `VCM` o `coordinador`

**Ejemplo de uso:**
```bash
# Con curl
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/exports/subjects/1/ficha-api/ \
     --output ficha_api.xlsx

# Con JavaScript (fetch)
fetch('/api/exports/subjects/1/ficha-api/', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ficha_api.xlsx';
  a.click();
});
```

## 🏗️ Arquitectura

### Componentes

1. **data_collectors.py**: Recolecta datos de la base de datos
   - `FichaAPIDataCollector`: Extrae datos de Subject y modelos relacionados

2. **services.py**: Lógica de exportación
   - `export_ficha_api()`: Genera el archivo Excel
   - `_set_value_safe()`: Maneja celdas combinadas
   - Helper functions para rutas de plantillas

3. **views.py**: Endpoints de la API
   - `export_ficha_api_view()`: Vista para exportar ficha API

4. **templates/excel/**: Plantillas y mapeos
   - `ficha_api.xlsx`: Plantilla Excel
   - `ficha_api_celdas_de_respuestas_mapeadas.json`: Mapeo de campos a celdas

## 📊 Datos Exportados

La Ficha API incluye:

### Información Básica (Subject)
- Nombre de asignatura
- Área, carrera, semestre
- Código, horas, campus
- Total de estudiantes

### Competencias Técnicas
- Hasta 5 competencias técnicas (SubjectTechnicalCompetency)

### Condiciones de Contorno (CompanyBoundaryCondition)
- Tipo de empresa (grande, mediana, pequeña, familiar)
- Descripción de tipo de empresa
- Requisitos para nivel 2/3
- Elementos mínimos del proyecto

### Completación API Type 2 o 3
- Objetivos del proyecto para estudiantes
- Entregables al finalizar
- Participación esperada de la empresa
- Otras actividades
- (API3) Rol esperado del estudiante
- (API3) Apoyo esperado del maestro guía

### Posibles Contrapartes (hasta 4)
- Sector
- Trabajado antes (Sí/No)
- Interés en colaborar
- Puede desarrollar actividades
- Dispuesto a diseñar proyecto
- Tipos de interacción
- Tiene guía
- Puede recibir alternancia
- Cupos para alternancia

### Empresas y Contactos (hasta 4)
- Nombre de empresa
- Dirección
- Dirección de gerencia
- Contacto de contraparte (nombre, email, teléfono)
- Cantidad de empleados
- Sector
- Tipo de API actual

### Alternancia API3 (hasta 4)
- Rol del estudiante
- Cupos de estudiantes
- Nombre del tutor
- Email del tutor
- Horas de alternancia

### Datos Adicionales
- Evidencias de evaluación de todas las unidades
- Definición del problema
- Mes y año actual
- Entregables finales

## 🔧 Agregar Nuevas Exportaciones

Para agregar una nueva plantilla (ej: "proyecto-api"):

### 1. Crear Data Collector

```python
# En data_collectors.py
class ProyectoAPIDataCollector:
    def __init__(self, subject):
        self.subject = subject
    
    def collect_all(self) -> Dict[str, Any]:
        # Implementar lógica de recolección
        return {...}
```

### 2. Crear Servicio de Exportación

```python
# En services.py
def export_proyecto_api(subject) -> HttpResponse:
    template_path = get_template_path('proyecto-api')
    mapping_path = get_mapping_path('proyecto-api')
    
    wb = load_workbook(filename=template_path)
    ws = wb.active
    
    collector = ProyectoAPIDataCollector(subject)
    data = collector.collect_all()
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        cell_mapping = json.load(f)
    
    for field_key, cell_coord in cell_mapping.items():
        value = data.get(field_key, '')
        _set_value_safe(ws, cell_coord, value)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"Proyecto_API_{subject.code}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
```

### 3. Crear Vista

```python
# En views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_proyecto_api_view(request, subject_id: int):
    subject = get_object_or_404(Subject, id=subject_id)
    # Validar permisos...
    return export_proyecto_api(subject)
```

### 4. Agregar URL

```python
# En urls.py
urlpatterns = [
    # ...existing
    path('exports/subjects/<int:subject_id>/proyecto-api/', 
         export_proyecto_api_view, name='export_proyecto_api'),
]
```

### 5. Agregar Plantilla y Mapeo

- Colocar `proyecto_api.xlsx` en `templates/excel/`
- Crear `proyecto_api_celdas_de_respuestas_mapeadas.json` con el mapeo
- Actualizar diccionarios en `get_template_path()` y `get_mapping_path()`

## 🔍 Mapeo JSON

El archivo JSON de mapeo tiene la estructura:

```json
{
  "campo_modelo_tabla": "CeldaExcel",
  "Subject_name": "C5:D5",
  "SubjectTechnicalCompetency_row_1": "B12:D12",
  "Company_name_col_1": "C56"
}
```

**Claves:**
- Formato: `Modelo_campo[_indicador]`
- `_row_N`: Para filas numeradas (1-5)
- `_col_N`: Para columnas numeradas (1-4)

**Valores:**
- Coordenadas de celda Excel (ej: "C5")
- Rangos para celdas combinadas (ej: "C5:D5")

## 🧪 Testing

```python
# Ejemplo de test
from django.test import TestCase
from subjects.models import Subject
from exports_app.data_collectors import FichaAPIDataCollector

class FichaAPIExportTest(TestCase):
    def test_collect_data(self):
        subject = Subject.objects.create(...)
        collector = FichaAPIDataCollector(subject)
        data = collector.collect_all()
        
        self.assertIn('Subject_name', data)
        self.assertEqual(data['Subject_name'], subject.name)
```

## ⚠️ Consideraciones

1. **Celdas Combinadas**: El sistema maneja automáticamente celdas combinadas
2. **Datos Faltantes**: Los campos vacíos se rellenan con cadena vacía
3. **Performance**: Usa `select_related()` y `prefetch_related()` para optimizar queries
4. **Permisos**: Siempre validar permisos en las vistas
5. **Nombres de Archivo**: Incluir información única en el nombre (código, período, etc.)

## 📝 Notas de Desarrollo

- Las plantillas Excel deben mantenerse en `templates/excel/`
- Los mapeos JSON deben sincronizarse con las plantillas
- Documentar cualquier celda especial o formato personalizado
- Mantener consistencia en nombres de campos entre modelos y mapeos
