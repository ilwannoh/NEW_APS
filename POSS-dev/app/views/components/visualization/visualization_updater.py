from app.views.components.visualization.visualizaiton_manager import VisualizationManager
from app.views.components.visualization.display_helper import DisplayHelper
from app.analysis.output.material_shortage_analysis import MaterialShortageAnalyzer
from app.analysis.output.capa_ratio import CapaRatioAnalyzer

"""output 시각화 업데이트 클래스"""


class VisualizationUpdater:
    """Capa 차트의 데이터 유효성 확인 함수"""

    @staticmethod
    def _is_capa_data_valid(data):
        if isinstance(data, dict) and 'original' in data and 'adjusted' in data:
            return data['original'] and len(data['original']) > 0
        return data and len(data) > 0

    """Utilization 차트의 데이터 유효성 확인 함수"""

    @staticmethod
    def _is_utilization_data_valid(data):
        if isinstance(data, dict) and 'original' in data and 'adjusted' in data:
            return data['original'] and any(value > 0 for value in data['original'].values())
        return data and any(value > 0 for value in data.values())

    """요일 데이터 정렬 함수"""

    @staticmethod
    def _transform_utilization_data(data):
        days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        if isinstance(data, dict) and 'original' in data and 'adjusted' in data:
            # 비교 데이터가 있는 경우
            sorted_original = {}
            sorted_adjusted = {}

            for day in days_order:
                sorted_original[day] = data['original'].get(day, 0)
                sorted_adjusted[day] = data['adjusted'].get(day, 0)

            return {'original': sorted_original, 'adjusted': sorted_adjusted}
        else:
            # 단일 데이터인 경우
            sorted_data = {}
            for day in days_order:
                sorted_data[day] = data.get(day, 0)
            return sorted_data

    """Capa 비율 차트 업데이트"""

    @staticmethod
    def update_capa_chart(canvas, capa_ratio_data):
        # 비교 데이터형식 감지
        is_comparison = isinstance(capa_ratio_data,
                                   dict) and 'original' in capa_ratio_data and 'adjusted' in capa_ratio_data

        chart_config = {
            'has_data_check': VisualizationUpdater._is_capa_data_valid,
            'chart_type': 'comparison_bar' if is_comparison else 'bar',
            'title': 'Plan Capacity Ratio Comparison' if is_comparison else 'Plant Capacity Ratio',
            'xlabel': 'Plant',
            'ylabel': 'Ratio (%)',
            'transform_data': None,
            'extra_params': {
                'show_value': True,
                'value_fontsize': 11,
                'show_legend': is_comparison,
                'ylim': None,
                'show_thresholds': True,
                # 내림차순 정렬 파라미터 명시적 추가
                'sort_data': True,
                'sort_descending': True,
                # 비교 차트인 경우 정렬 기준 설정 (조정된 데이터 기준)
                'sort_by': 'adjusted' if is_comparison else None,
                'thresholds': {
                    'I': {'lower_limit': 69.5, 'upper_limit': 100},
                    'D': {'lower_limit': 8.3, 'upper_limit': 100},
                    'K': {'lower_limit': 8.3, 'upper_limit': 100},
                    'M': {'lower_limit': 12.5, 'upper_limit': 100}
                }
            }
        }

        DisplayHelper.show_chart_or_message(canvas, capa_ratio_data, chart_config)

    """요일별 가동률 차트 업데이트"""

    @staticmethod
    def update_utilization_chart(canvas, utilization_data):
        # 비교 데이터 형식 감지
        is_comparison = isinstance(utilization_data,
                                   dict) and 'original' in utilization_data and 'adjusted' in utilization_data

        chart_config = {
            'has_data_check': VisualizationUpdater._is_utilization_data_valid,
            'chart_type': 'comparison_bar' if is_comparison else 'bar',
            'title': 'Daily Utilization Rate Comparison' if is_comparison else 'Daily Utilization Rate',
            'xlabel': 'Day of week',
            'ylabel': 'Utilization Rate(%)',
            'transform_data': VisualizationUpdater._transform_utilization_data,
            'extra_params': {
                'ylim': (0, 110),
                'threshold_values': [80, 100, 110],
                'threshold_colors': ['#4CAF50', '#FFC107', '#F44336'],
                'threshold_labels': ['Good', 'Warn', 'High'],
                'show_value': True,
                'value_fontsize': 7,
                'show_legend': is_comparison,
                # 요일 데이터는 고정된 순서를 유지해야 하므로 정렬 비활성화
                'sort_data': False,
                'width' : 0.8
            }
        }

        DisplayHelper.show_chart_or_message(canvas, utilization_data, chart_config)

    """출하포트 Capa 차트 업데이트"""

    @staticmethod
    def update_port_capa_chart(canvas, port_capa_data):
        pass

    """Material 차트의 데이터 유효성 확인 함수"""

    @staticmethod
    def _is_material_shortage_data_valid(data):
        return data and len(data) > 0

