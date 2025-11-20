"""
Data collectors para extraer información de la base de datos
y preparar datos para exportar a Excel.
"""
from typing import Dict, Any, List
from datetime import datetime


class FichaAPIDataCollector:
    """
    Recolecta datos de una asignatura y sus modelos relacionados
    para exportar a la plantilla Ficha API.
    
    MANEJO DE DATOS FALTANTES:
    - Si una tabla relacionada no existe, se retornan cadenas vacías
    - Si faltan registros opcionales (empresas, contrapartes), se llenan columnas vacías
    - El sistema SIEMPRE genera un Excel válido, incluso con información parcial
    """
    
    def __init__(self, subject):
        self.subject = subject
        self.missing_data = []  # Track para debug/logging
    
    def collect_all(self) -> Dict[str, Any]:
        """Recolecta todos los datos necesarios para la ficha API."""
        data = {}
        
        # Datos básicos de Subject
        data.update(self._collect_subject_data())
        
        # Competencias técnicas (5 filas)
        data.update(self._collect_technical_competencies())
        
        # Condiciones de contorno de empresa
        data.update(self._collect_company_boundary_conditions())
        
        # Datos de API Type 2 o Type 3
        data.update(self._collect_api_completion())
        
        # Posibles contrapartes (hasta 4 columnas)
        data.update(self._collect_possible_counterparts())
        
        # Empresas y contactos (hasta 4 columnas)
        data.update(self._collect_companies_and_contacts())
        
        # Alternancia API3 (hasta 4 columnas)
        data.update(self._collect_api3_alternance())
        
        # Datos adicionales finales
        data.update(self._collect_additional_data())
        
        return data
    
    def get_missing_data_report(self) -> List[str]:
        """
        Retorna un reporte de qué datos faltan (opcional para debug).
        Útil para mostrar advertencias al usuario sobre información incompleta.
        """
        return self.missing_data
    
    def _collect_subject_data(self) -> Dict[str, Any]:
        """Recolecta datos básicos de la asignatura."""
        return {
            'Subject_name': self.subject.name,
            'Subject_area': self.subject.area.name if self.subject.area else '',
            'Subject_semester': self.subject.semester.name if self.subject.semester else '',
            'Subject_code': self.subject.code,
            'Subject_hours': self.subject.hours,
            'Subject_campus': self.subject.campus,
            'Subject_total_students': self.subject.total_students or '',
        }
    
    def _collect_technical_competencies(self) -> Dict[str, Any]:
        """Recolecta las 5 competencias técnicas."""
        competencies = list(self.subject.technical_competencies.order_by('number')[:5])
        data = {}
        
        if len(competencies) < 5:
            self.missing_data.append(f'Solo {len(competencies)} de 5 competencias técnicas definidas')
        
        for i in range(1, 6):
            comp = next((c for c in competencies if c.number == i), None)
            description = comp.description if comp else ''
            data[f'SubjectTechnicalCompetency_row_{i}'] = description
        
        return data
    
    def _collect_company_boundary_conditions(self) -> Dict[str, Any]:
        """Recolecta condiciones de contorno de empresa."""
        # Valores por defecto si no hay datos
        default_data = {
            'CompanyBoundaryCondition_large_company': '',
            'CompanyBoundaryCondition_medium_company': '',
            'CompanyBoundaryCondition_small_company': '',
            'CompanyBoundaryCondition_family_enterprise': '',
            'CompanyBoundaryCondition_not_relevant': '',
            'CompanyBoundaryCondition_company_type_description': '',
            'CompanyBoundaryCondition_company_requirements_for_level_2_3': '',
            'CompanyBoundaryCondition_project_minimum_elements': '',
        }
        
        try:
            conditions = self.subject.company_boundary_conditions
            return {
                'CompanyBoundaryCondition_large_company': 'X' if conditions.large_company else '',
                'CompanyBoundaryCondition_medium_company': 'X' if conditions.medium_company else '',
                'CompanyBoundaryCondition_small_company': 'X' if conditions.small_company else '',
                'CompanyBoundaryCondition_family_enterprise': 'X' if conditions.family_enterprise else '',
                'CompanyBoundaryCondition_not_relevant': 'X' if conditions.not_relevant else '',
                'CompanyBoundaryCondition_company_type_description': conditions.company_type_description or '',
                'CompanyBoundaryCondition_company_requirements_for_level_2_3': conditions.company_requirements_for_level_2_3 or '',
                'CompanyBoundaryCondition_project_minimum_elements': conditions.project_minimum_elements or '',
            }
        except Exception:
            # Si no existe el registro, retornar valores vacíos
            self.missing_data.append('Condiciones de contorno de empresa no definidas')
            return default_data
    
    def _collect_api_completion(self) -> Dict[str, Any]:
        """Recolecta datos de ApiType2Completion o ApiType3Completion."""
        data = {}
        
        # Siempre inicializar todos los campos vacíos primero
        data.update({
            'ApiType2Completion_project_goal_students': '',
            'ApiType2Completion_deliverables_at_end': '',
            'ApiType2Completion_company_expected_participation': '',
            'ApiType2Completion_other_activities': '',
            'ApiType3Completion_project_goal_students': '',
            'ApiType3Completion_deliverables_at_end': '',
            'ApiType3Completion_expected_student_role': '',
            'ApiType3Completion_other_activities': '',
            'ApiType3Completion_master_guide_expected_support': '',
        })
        
        if self.subject.api_type == 2:
            try:
                completion = self.subject.api2_completion
                data.update({
                    'ApiType2Completion_project_goal_students': completion.project_goal_students or '',
                    'ApiType2Completion_deliverables_at_end': completion.deliverables_at_end or '',
                    'ApiType2Completion_company_expected_participation': completion.company_expected_participation or '',
                    'ApiType2Completion_other_activities': completion.other_activities or '',
                })
            except Exception:
                pass  # Ya inicializamos los valores vacíos
        
        if self.subject.api_type == 3:
            try:
                completion = self.subject.api3_completion
                data.update({
                    'ApiType3Completion_project_goal_students': completion.project_goal_students or '',
                    'ApiType3Completion_deliverables_at_end': completion.deliverables_at_end or '',
                    'ApiType3Completion_expected_student_role': completion.expected_student_role or '',
                    'ApiType3Completion_other_activities': completion.other_activities or '',
                    'ApiType3Completion_master_guide_expected_support': completion.master_guide_expected_support or '',
                })
            except Exception:
                pass  # Ya inicializamos los valores vacíos
        
        return data
    
    def _collect_possible_counterparts(self) -> Dict[str, Any]:
        """Recolecta hasta 4 posibles contrapartes."""
        counterparts = self.subject.possible_counterparts.select_related('company')[:4]
        data = {}
        
        for idx, counterpart in enumerate(counterparts, start=1):
            # Convertir interaction_types a string separado por comas
            interaction_types = ', '.join([it.label for it in counterpart.interaction_types.all()])
            
            data.update({
                f'PossibleCounterpart_sector_col_{idx}': counterpart.sector,
                f'PossibleCounterpart_worked_before_col_{idx}': 'Sí' if counterpart.worked_before else 'No',
                f'PossibleCounterpart_interest_collaborate_col_{idx}': 'Sí' if counterpart.interest_collaborate else 'No',
                f'PossibleCounterpart_can_develop_activities_col_{idx}': 'Sí' if counterpart.can_develop_activities else 'No',
                f'PossibleCounterpart_willing_design_project_col_{idx}': 'Sí' if counterpart.willing_design_project else 'No',
                f'PossibleCounterpart_interaction_types_col_{idx}': interaction_types,
                f'PossibleCounterpart_has_guide_col_{idx}': 'Sí' if counterpart.has_guide else 'No',
                f'PossibleCounterpart_can_receive_alternance_col_{idx}': 'Sí' if counterpart.can_receive_alternance else 'No',
                f'PossibleCounterpart_alternance_students_quota_col_{idx}': counterpart.alternance_students_quota,
            })
        
        # Rellenar columnas vacías
        for idx in range(len(counterparts) + 1, 5):
            data.update({
                f'PossibleCounterpart_sector_col_{idx}': '',
                f'PossibleCounterpart_worked_before_col_{idx}': '',
                f'PossibleCounterpart_interest_collaborate_col_{idx}': '',
                f'PossibleCounterpart_can_develop_activities_col_{idx}': '',
                f'PossibleCounterpart_willing_design_project_col_{idx}': '',
                f'PossibleCounterpart_interaction_types_col_{idx}': '',
                f'PossibleCounterpart_has_guide_col_{idx}': '',
                f'PossibleCounterpart_can_receive_alternance_col_{idx}': '',
                f'PossibleCounterpart_alternance_students_quota_col_{idx}': '',
            })
        
        return data
    
    def _collect_companies_and_contacts(self) -> Dict[str, Any]:
        """Recolecta empresas y sus contactos de las problemáticas."""
        problem_statements = self.subject.problem_statements.select_related('company')[:4]
        data = {}
        
        for idx, ps in enumerate(problem_statements, start=1):
            company = ps.company
            # Obtener el primer contacto de contraparte (a través de la company)
            contact = company.counterpart_contacts.first() if company else None
            
            data.update({
                f'Company_name_col_{idx}': company.name,
                f'Company_address_col_{idx}': company.address,
                f'Company_management_address_col_{idx}': company.management_address,
                f'CounterpartContact_name_col_{idx}': contact.name if contact else '',
                f'CounterpartContact_email_col_{idx}': contact.email if contact else '',
                f'CounterpartContact_phone_col_{idx}': contact.phone if contact else '',
                f'Company_employees_count_col_{idx}': company.employees_count,
                f'Company_sector_col_{idx}': company.sector,
                f'current_Subject_api_type_col_{idx}': self.subject.api_type,
            })
        
        # Rellenar columnas vacías
        for idx in range(len(problem_statements) + 1, 5):
            data.update({
                f'Company_name_col_{idx}': '',
                f'Company_address_col_{idx}': '',
                f'Company_management_address_col_{idx}': '',
                f'CounterpartContact_name_col_{idx}': '',
                f'CounterpartContact_email_col_{idx}': '',
                f'CounterpartContact_phone_col_{idx}': '',
                f'Company_employees_count_col_{idx}': '',
                f'Company_sector_col_{idx}': '',
                f'current_Subject_api_type_col_{idx}': '',
            })
        
        return data
    
    def _collect_api3_alternance(self) -> Dict[str, Any]:
        """Recolecta datos de alternancia para API3."""
        data = {}
        
        if self.subject.api_type == 3:
            try:
                alternance = self.subject.alternance
                # Para API3 solo hay un registro, pero lo ponemos en col_1
                data.update({
                    'Api3Alternance_student_role_col_1': alternance.student_role,
                    'Api3Alternance_students_quota_col_1': alternance.students_quota,
                    'Api3Alternance_tutor_name_col_1': alternance.tutor_name,
                    'Api3Alternance_tutor_email_col_1': alternance.tutor_email,
                    'Api3Alternance_alternance_hours_col_1': alternance.alternance_hours,
                })
            except Exception:
                pass
        
        # Rellenar todas las columnas vacías si no hay datos
        for idx in range(1, 5):
            for field in ['student_role', 'students_quota', 'tutor_name', 'tutor_email', 'alternance_hours']:
                key = f'Api3Alternance_{field}_col_{idx}'
                if key not in data:
                    data[key] = ''
        
        return data
    
    def _collect_additional_data(self) -> Dict[str, Any]:
        """Recolecta datos adicionales finales."""
        # Obtener evidencias de evaluación de todas las unidades
        units = self.subject.units.order_by('number')
        evaluation_evidences = ' / '.join([
            unit.evaluation_evidence or '' 
            for unit in units 
            if unit.evaluation_evidence
        ])
        
        # Obtener definición del problema (primer problem_statement)
        problem_definition = ''
        first_ps = self.subject.problem_statements.first()
        if first_ps:
            problem_definition = first_ps.problem_definition
        
        # Obtener deliverables según el tipo de API
        deliverables = ''
        if self.subject.api_type == 2:
            try:
                deliverables = self.subject.api2_completion.deliverables_at_end
            except Exception:
                pass
        elif self.subject.api_type == 3:
            try:
                deliverables = self.subject.api3_completion.deliverables_at_end
            except Exception:
                pass
        
        # Mes y año actual
        now = datetime.now()
        current_month_year = now.strftime('%B %Y')  # Ej: "November 2025"
        
        return {
            'Subject-name': self.subject.name,
            'SubjectUnit_evaluation_evidence_of_all_units_separated_by_/': evaluation_evidences,
            'ProblemStatement_problem_definition': problem_definition,
            'current_month_and_year': current_month_year,
            'ApiType2Completion_or_ApiType3Completion_deliverables_at_end_of_the_current_subject': deliverables,
        }


class ProyectoAPIDataCollector:
    """
    Recolecta datos de una asignatura y sus modelos relacionados
    para exportar a la plantilla Proyecto API (Ficha Proyecto API).
    
    MANEJO DE DATOS FALTANTES:
    - Si una tabla relacionada no existe, se retornan cadenas vacías
    - Si faltan registros opcionales, se llenan filas/columnas vacías
    - El sistema SIEMPRE genera un Excel válido, incluso con información parcial
    """
    
    def __init__(self, subject):
        self.subject = subject
        self.missing_data = []
    
    def collect_all(self) -> Dict[str, Any]:
        """Recolecta todos los datos necesarios para el proyecto API."""
        data = {}
        
        # Datos básicos de Subject
        data.update(self._collect_subject_data())
        
        # CompanyEngagementScope
        data.update(self._collect_engagement_scope())
        
        # Participantes (contrapartes y/o docentes) - hasta 4 filas
        data.update(self._collect_participants())
        
        # ProblemStatement
        data.update(self._collect_problem_statement())
        
        # SubjectUnits con contactos - hasta 4 filas
        data.update(self._collect_subject_units())
        
        return data
    
    def get_missing_data_report(self) -> List[str]:
        """Retorna un reporte de qué datos faltan."""
        return self.missing_data
    
    def _collect_subject_data(self) -> Dict[str, Any]:
        """Recolecta datos básicos de la asignatura."""
        return {
            'Subject_name': self.subject.name,
            'Subject_area': self.subject.area.name if self.subject.area else '',
            'Subject_semester': self.subject.semester.name if self.subject.semester else '',
            'Subject_code': self.subject.code,
            'Subject_hours': self.subject.hours,
            'Subject_api_type': self.subject.api_type,
        }
    
    def _collect_engagement_scope(self) -> Dict[str, Any]:
        """Recolecta alcance de compromiso con la empresa."""
        default_data = {
            'CompanyEngagementScope_benefits_from_student': '',
            'CompanyEngagementScope_has_value_or_research_project': '',
            'CompanyEngagementScope_time_availability_and_participation': '',
            'CompanyEngagementScope_workplace_has_conditions_for_group': '',
            'CompanyEngagementScope_meeting_schedule_availability': '',
        }
        
        try:
            # Buscar engagement scope para esta asignatura
            from companies.models import CompanyEngagementScope
            scope = CompanyEngagementScope.objects.filter(
                subject_code=self.subject.code,
                subject_section=self.subject.section,
                subject_period_season=self.subject.period_season,
                subject_period_year=self.subject.period_year
            ).first()
            
            if scope:
                return {
                    'CompanyEngagementScope_benefits_from_student': scope.benefits_from_student or '',
                    'CompanyEngagementScope_has_value_or_research_project': 'Sí' if scope.has_value_or_research_project else 'No',
                    'CompanyEngagementScope_time_availability_and_participation': scope.time_availability_and_participation or '',
                    'CompanyEngagementScope_workplace_has_conditions_for_group': 'Sí' if scope.workplace_has_conditions_for_group else 'No',
                    'CompanyEngagementScope_meeting_schedule_availability': scope.meeting_schedule_availability or '',
                }
            else:
                self.missing_data.append('No hay alcance de compromiso definido')
                return default_data
        except Exception:
            self.missing_data.append('Error al obtener alcance de compromiso')
            return default_data
    
    def _collect_participants(self) -> Dict[str, Any]:
        """
        Recolecta participantes (contrapartes y/o docentes) - hasta 4 filas.
        Obtiene los contactos de las problemáticas asociadas.
        """
        data = {}
        
        # Obtener contactos de contrapartes desde problem_statements
        # Los counterpart_contacts están asociados a la company, no directamente al problem_statement
        problem_statements = self.subject.problem_statements.all()
        contacts = []
        
        for ps in problem_statements:
            if ps.company:
                for contact in ps.company.counterpart_contacts.all():
                    contacts.append({
                        'name': contact.name,
                        'area': contact.counterpart_area,
                        'role': contact.role,
                    })
        
        # Limitar a 4
        contacts = contacts[:4]
        
        if len(contacts) < 4:
            self.missing_data.append(f'Solo {len(contacts)} de 4 participantes definidos')
        
        # Llenar hasta 4 filas
        for idx in range(1, 5):
            if idx <= len(contacts):
                contact = contacts[idx - 1]
                data[f'subject_participant_counterpart_and/or_teacher_name_row_{idx}'] = contact['name']
                data[f'subject_participant_counterpart_and/or_teacher_area_row_{idx}'] = contact['area']
                data[f'subject_participant_counterpart_and/or_teacher_role_row_{idx}'] = contact['role']
            else:
                data[f'subject_participant_counterpart_and/or_teacher_name_row_{idx}'] = ''
                data[f'subject_participant_counterpart_and/or_teacher_area_row_{idx}'] = ''
                data[f'subject_participant_counterpart_and/or_teacher_role_row_{idx}'] = ''
        
        return data
    
    def _collect_problem_statement(self) -> Dict[str, Any]:
        """Recolecta la primera problemática asociada."""
        default_data = {
            'ProblemStatement_problem_to_address': '',
            'ProblemStatement_why_important': '',
            'ProblemStatement_stakeholders': '',
            'ProblemStatement_related_area': '',
            'ProblemStatement_benefits_short_medium_long_term': '',
            'ProblemStatement_problem_definition': '',
        }
        
        ps = self.subject.problem_statements.first()
        
        if not ps:
            self.missing_data.append('No hay problemática definida')
            return default_data
        
        return {
            'ProblemStatement_problem_to_address': ps.problem_to_address or '',
            'ProblemStatement_why_important': ps.why_important or '',
            'ProblemStatement_stakeholders': ps.stakeholders or '',
            'ProblemStatement_related_area': ps.related_area or '',
            'ProblemStatement_benefits_short_medium_long_term': ps.benefits_short_medium_long_term or '',
            'ProblemStatement_problem_definition': ps.problem_definition or '',
        }
    
    def _collect_subject_units(self) -> Dict[str, Any]:
        """Recolecta hasta 4 unidades con sus contactos de contraparte."""
        units = list(self.subject.units.order_by('number')[:4])
        data = {}
        
        if len(units) < 4:
            self.missing_data.append(f'Solo {len(units)} de 4 unidades definidas')
        
        # Obtener el primer contacto de contraparte (para todas las filas)
        first_contact = None
        first_ps = self.subject.problem_statements.first()
        if first_ps and first_ps.company:
            first_contact = first_ps.company.counterpart_contacts.first()
        
        # Llenar hasta 4 filas
        for idx in range(1, 5):
            if idx <= len(units):
                unit = units[idx - 1]
                data[f'SubjectUnit_number_row_{idx}'] = unit.number
                data[f'SubjectUnit_ expected_learning_row_{idx}'] = unit.expected_learning or ''
                data[f'SubjectUnit_unit_hours_row_{idx}'] = unit.unit_hours or ''
                data[f'SubjectUnit_activities_description_row_{idx}'] = unit.activities_description or ''
                data[f'SubjectUnit_evaluation_evidence_row_{idx}'] = unit.evaluation_evidence or ''
                data[f'SubjectUnit_evidence_detail_row_{idx}'] = unit.evidence_detail or ''
                data[f'SubjectUnit_counterpart_link_row_{idx}'] = unit.counterpart_link or ''
                data[f'SubjectUnit_place_mode_type_row_{idx}'] = unit.place_mode_type or ''
                data[f'CounterpartContact_name_row_{idx}'] = first_contact.name if first_contact else ''
            else:
                data[f'SubjectUnit_number_row_{idx}'] = ''
                data[f'SubjectUnit_ expected_learning_row_{idx}'] = ''
                data[f'SubjectUnit_unit_hours_row_{idx}'] = ''
                data[f'SubjectUnit_activities_description_row_{idx}'] = ''
                data[f'SubjectUnit_evaluation_evidence_row_{idx}'] = ''
                data[f'SubjectUnit_evidence_detail_row_{idx}'] = ''
                data[f'SubjectUnit_counterpart_link_row_{idx}'] = ''
                data[f'SubjectUnit_place_mode_type_row_{idx}'] = ''
                data[f'CounterpartContact_name_row_{idx}'] = ''
        
        return data
