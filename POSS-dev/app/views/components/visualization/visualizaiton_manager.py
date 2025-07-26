import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from app.models.common.screen_manager import *

"""Basic visualization module"""


class VisualizationManager:
    @staticmethod
    def create_chart(data, chart_type='bar', title='Chart', xlabel='X', ylabel='Y', ax=None, **kwargs):
        # Args:
        # data: Dictionary or DataFrame with data to visualize
        # chart_type: Type of chart ('bar', 'line', 'pie', 'heatmap', etc)
        # title: Chart title
        # xlabel: X-axis label
        # ylabel: Y-axis label
        # ax: Matplotlib axes to plot on (optional)
        # **kwargs: Additional parameters for specific chart types

        # Returns:
        # Matplotlib axes with the plot

        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 5))
        else:
            ax.clear()
            ax.set_axis_on()

        # 비교 차트 처리
        if chart_type == 'comparison_bar':
            return VisualizationManager.create_comparison_bar_chart(data, title, xlabel, ylabel, ax, **kwargs)

        # 시각화에 필요한 형식으로 데이터 변환
        if isinstance(data, dict):
            # 정렬 기능 추가 - 데이터 정렬 옵션
            sort_data = kwargs.get('sort_data', False)
            sort_descending = kwargs.get('sort_descending', True)

            if sort_data:
                # 딕셔너리를 값(value) 기준으로 정렬하여 리스트로 변환
                sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=sort_descending)
                x_data = [item[0] for item in sorted_items]
                y_data = [item[1] for item in sorted_items]
            else:
                # 기존 방식 유지
                x_data = list(data.keys())
                y_data = list(data.values())
        elif isinstance(data, pd.DataFrame):
            if 'x' in kwargs and 'y' in kwargs:
                x_data = data[kwargs['x']].tolist()
                y_data = data[kwargs['y']].tolist()
            else:
                x_data = data.index.tolist()
                y_data = data.loc[:, 0].tolist() if data.shape[1] > 0 else []
        else:
            raise ValueError("Data must be a dictionary or DataFrame")

        # 유형에 따라 차트 생성
        if chart_type == 'bar':
            bars = ax.bar(x_data, y_data, color=kwargs.get('color', 'steelblue'),
                          alpha=kwargs.get('alpha', 0.8), width=kwargs.get('width', 0.7))

            # 필요시 값 레이블 추가
            if kwargs.get('show_value', True):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{height:.1f}' if isinstance(height, float) else f'{height}',
                            ha='center', va='bottom', fontsize=kwargs.get('value_fontsize', 9))

            # show_thresholds=True + thresholds 임계선 표현 (bar 차트에만 적용)
            if kwargs.get('show_thresholds', False) and 'thresholds' in kwargs:
                thresholds = kwargs['thresholds']

                # 각 바(제조동)에 대해 임계점 표시
                for i, key in enumerate(x_data):
                    if key in thresholds:
                        plant_thresholds = thresholds[key]

                        # 상한 임계점
                        if 'upper_limit' in plant_thresholds:
                            upper = plant_thresholds['upper_limit']
                            # 특정 막대에 대해서만 임계선 그리기
                            ax.hlines(y=upper, xmin=i - 0.4, xmax=i + 0.4, colors='red', linestyles='dashed', alpha=0.7)
                            # 임계점 텍스트 추가
                            ax.text(i, upper, f"{upper}%", ha='center', va='bottom', color='red', fontsize=f(9))

                        # 하한 임계점
                        if 'lower_limit' in plant_thresholds:
                            lower = plant_thresholds['lower_limit']
                            ax.hlines(y=lower, xmin=i - 0.4, xmax=i + 0.4, colors='blue', linestyles='dashed',
                                      alpha=0.7)
                            # 임계점 텍스트 추가
                            ax.text(i, lower, f"{lower}%", ha='center', va='top', color='blue', fontsize=f(9))

            # threshold_values + threshold_colors 방식의 임계선 처리 (한 줄 임계선 표현)
            if 'threshold_values' in kwargs and 'threshold_colors' in kwargs:
                threshold_values = kwargs['threshold_values']
                threshold_colors = kwargs['threshold_colors']
                threshold_labels = kwargs.get('threshold_labels', [''] * len(threshold_values))

                for i, threshold in enumerate(threshold_values):
                    color = threshold_colors[i] if i < len(threshold_colors) else threshold_colors[-1]
                    label = threshold_labels[i] if i < len(threshold_labels) else ''

                    # 수평선 그리기
                    ax.axhline(y=threshold, color=color, linestyle='--', alpha=0.7)

                    # 임계선 오른쪽에 라벨 표시
                    if len(x_data) > 0:
                        ax.text(len(x_data) - 1 + 0.2, threshold, f'{threshold}% {label}',
                                color=color, va='center', fontsize=f(9))

        elif chart_type == 'line':
            ax.plot(x_data, y_data, marker=kwargs.get('marker', 'o'),
                    linestyle=kwargs.get('linestyle', '-'),
                    linewidth=kwargs.get('linewidth', 2),
                    color=kwargs.get('color', 'steelblue'),
                    markersize=kwargs.get('markersize', 5))

            # 필요시 값 레이블 추가
            if kwargs.get('show_values', True):
                for i, value in enumerate(y_data):
                    ax.text(i, value, f'{value:.1f}' if isinstance(value, float) else f'{value}',
                            ha='center', va='bottom', fontsize=kwargs.get('value_fontsize', 9))

        elif chart_type == 'pie':
            wedges, texts, autotexts = ax.pie(
                y_data,
                labels=None if kwargs.get('hide_labels', False) else x_data,
                autopct='%1.1f%%' if kwargs.get('show_pct', True) else None,
                startangle=kwargs.get('startangle', 90),
                colors=kwargs.get('colors', None)
            )
            ax.axis('equal')  # 원형 차트가 원으로 그려지도록 동일한 비율 설정

            # 텍스트 속성 사용자 정의
            if autotexts and kwargs.get('show_pct', True):
                for autotext in autotexts:
                    autotext.set_fontsize(kwargs.get('pct_fontsize', 9))
                    autotext.set_color(kwargs.get('pct_color', 'white'))

        elif chart_type == 'heatmap':
            if isinstance(data, pd.DataFrame):
                im = ax.imshow(data.values, cmap=kwargs.get('cmap', 'viridis'))

                # 모든 눈금 표시 및 레이블 지정
                ax.set_xticks(np.arange(len(data.columns)))
                ax.set_yticks(np.arange(len(data.index)))
                ax.set_xticklabels(data.columns)
                ax.set_yticklabels(data.index)

                # 눈금 레이블 회전 및 정렬 설정
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

                # 색상 막대 추가
                if kwargs.get('show_colorbar', True):
                    plt.colorbar(im, ax=ax)

                # 필요시 텍스트 주석 추가
                if kwargs.get('show_values', True):
                    for i in range(len(data.index)):
                        for j in range(len(data.columns)):
                            value = data.iloc[i, j]
                            text_color = 'white' if value > (data.values.max() + data.values.min()) / 2 else 'black'
                            ax.text(j, i, f'{value:.1f}' if isinstance(value, float) else f'{value}',
                                    ha="center", va="center", color=text_color,
                                    fontsize=kwargs.get('value_fontsize', 9))

            else:
                raise ValueError("Data must be a DataFrame for heatmap visualization")

        elif chart_type == 'scatter':
            ax.scatter(x_data, y_data,
                       c=kwargs.get('color', 'steelblue'),
                       s=kwargs.get('size', 50),
                       alpha=kwargs.get('alpha', 0.7),
                       marker=kwargs.get('marker', 'o'))

            # 필요시 추세선 추가
            if kwargs.get('show_trendline', False) and len(x_data) > 1:
                try:
                    z = np.polyfit(x_data, y_data, 1)
                    p = np.poly1d(z)
                    ax.plot(x_data, p(x_data), '--', color=kwargs.get('trendline_color', 'red'))
                except:
                    pass  # 오류 발생 시 추세선 생략

        else:
            raise ValueError(f"Unspported chart type: {chart_type}")

        # 레이블 및 제목 추가
        ax.set_title(title, fontsize=kwargs.get('title_fontsize', 20))
        ax.set_xlabel(xlabel, fontsize=kwargs.get('label_fontsize', 18))
        ax.set_ylabel(ylabel, fontsize=kwargs.get('label_fontsize', 18))

        # 여기에 tick label 폰트 크기 설정 코드 추가
        tick_fontsize = kwargs.get('tick_fontsize', 16)
        ax.tick_params(axis='both', which='major', labelsize=tick_fontsize)

        # 필요시 그리드 추가
        if kwargs.get('show_grid', True):
            ax.grid(alpha=kwargs.get('grid_alpha', 0.3), linestyle=kwargs.get('grid_style', '--'))

        # 필요한 경우 X축 레이블 회전 (레이블이 길거나 요청된 경우)
        if kwargs.get('rotate_xlabels', False) or (len(x_data) > 0 and any(len(str(x)) > 5 for x in x_data)):
            plt.setp(ax.get_xticklabels(), rotation=kwargs.get('xlabels_rotation', 30),
                     ha=kwargs.get('xlabels_ha', 'right'), rotation_mode='anchor')

        # Y축 범위 사용자 정의 (제공된 경우)
        if 'ylim' in kwargs:
            ax.set_ylim(kwargs['ylim'])

        # 그림 레이아웃 조정
        if ax.figure:
            # X축 라벨이 긴 경우 하단 여백 늘리기
            bottom_margin = 0.30 if any(len(str(x)) > 10 for x in x_data) else 0.20

            # 임계선이 있는 경우 약간 더 넓게
            right_margin = 0.9 if 'threshold_values' in kwargs else 0.9

            ax.figure.subplots_adjust(
                left=0.15,  # 왼쪽 여백
                right=right_margin,  # 오른쪽 여백 (임계선 고려)
                top=0.85,  # 상단 여백
                bottom=bottom_margin  # 하단 여백 (X축 라벨 고려)
            )
        return ax

    """
    원본 데이터와 조정 데이터 비교 차트 생성
    Args:
        data: {'original': dict, 'adjusted': dict} 형태의 데이터
        title: 차트 제목
        xlabel: X축 레이블
        ylabel: Y축 레이블
        ax: Matplotlib axes
        **kwargs: 추가 파라미터

    Returns:
        Matplotlib axes with the comparison bar chart
    """

    @staticmethod
    def create_comparison_bar_chart(data, title, xlabel, ylabel, ax, **kwargs):
        if 'original' not in data or 'adjusted' not in data:
            raise ValueError("Data must contain 'original' and 'adjusted' keys for comparison chart")

        orig_data = data['original']
        adj_data = data['adjusted']

        # 요일 순서 유지
        if xlabel == 'Day of week':
            days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            all_keys = [day for day in days_order if day in orig_data.keys() or day in adj_data.keys()]
        else:
            # 정렬 기능 추가 - 비교 차트에서도 정렬 지원
            sort_data = kwargs.get('sort_data', False)
            sort_descending = kwargs.get('sort_descending', True)
            sort_by = kwargs.get('sort_by', 'adjusted')  # 정렬 기준 ('original', 'adjusted', 'sum', 'diff')

            if sort_data:
                # 원본 및 조정 데이터의 모든 키 수집
                all_keys_set = set(list(orig_data.keys()) + list(adj_data.keys()))

                # 정렬 기준에 따라 값 계산 및 정렬
                if sort_by == 'original':
                    # 원본 데이터 기준 정렬
                    sort_dict = {k: orig_data.get(k, 0) for k in all_keys_set}
                elif sort_by == 'sum':
                    # 합계 기준 정렬
                    sort_dict = {k: orig_data.get(k, 0) + adj_data.get(k, 0) for k in all_keys_set}
                elif sort_by == 'diff':
                    # 차이 기준 정렬
                    sort_dict = {k: abs(adj_data.get(k, 0) - orig_data.get(k, 0)) for k in all_keys_set}
                else:
                    # 기본값 - 조정된 데이터 기준 정렬
                    sort_dict = {k: adj_data.get(k, 0) for k in all_keys_set}

                # 딕셔너리를 값 기준으로 정렬하여 키만 추출
                sorted_items = sorted(sort_dict.items(), key=lambda x: x[1], reverse=sort_descending)
                all_keys = [item[0] for item in sorted_items]
            else:
                # 모든 키(x축)를 가져옴 (기존 로직)
                all_keys = sorted(set(list(orig_data.keys()) + list(adj_data.keys())))

        # x 위치 설정
        x = np.arange(len(all_keys))
        width = 0.35  # 막대 너비

        # 원본 데이터와 조정 데이터 값 준비
        orig_values = [orig_data.get(k, 0) for k in all_keys]
        adj_values = [adj_data.get(k, 0) for k in all_keys]

        # 비교 막대 차트 그리기
        bar1 = ax.bar(x - width / 2, orig_values, width, label='Original', color='steelblue', alpha=0.8)
        bar2 = ax.bar(x + width / 2, adj_values, width, label='Adjusted', color='orangered', alpha=0.8)

        # 값 레이블 추가
        if kwargs.get('show_value', True):
            for bars, values in [(bar1, orig_values), (bar2, adj_values)]:
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{height:.1f}' if isinstance(height, float) else f'{height}',
                            ha='center', va='bottom', fontsize=kwargs.get('value_fontsize', 9))

        # 임계값 라인 추가
        if 'threshold_values' in kwargs and 'threshold_colors' in kwargs:
            threshold_values = kwargs['threshold_values']
            threshold_colors = kwargs['threshold_colors']
            threshold_labels = kwargs.get('threshold_labels', [''] * len(threshold_values))

            for i, threshold in enumerate(threshold_values):
                label = threshold_labels[i] if i < len(threshold_labels) else ''
                ax.axhline(y=threshold, color=threshold_colors[i], linestyle='--', alpha=0.7)
                ax.text(len(all_keys) - 1 + 0.2, threshold, f'{threshold}% {label}',
                        color=threshold_colors[i], va='center', fontsize=f(9))

        # 임계점 표시 기능 추가 (비교 차트에도 적용)
        if kwargs.get('show_thresholds', False) and 'thresholds' in kwargs:
            thresholds = kwargs['thresholds']

            # 각 바(제조동)에 대해 임계점 표시
            for i, key in enumerate(all_keys):
                if key in thresholds:
                    plant_thresholds = thresholds[key]

                    # 상한 임계점
                    if 'upper_limit' in plant_thresholds:
                        upper = plant_thresholds['upper_limit']
                        # 특정 막대들에 대해서만 임계선 그리기
                        ax.hlines(y=upper, xmin=x[i] - width, xmax=x[i] + width, colors='red', linestyles='dashed',
                                  alpha=0.7)
                        # 임계점 텍스트 추가
                        ax.text(x[i], upper, f"{upper}%", ha='center', va='bottom', color='red', fontsize=f(9))

                    # 하한 임계점
                    if 'lower_limit' in plant_thresholds:
                        lower = plant_thresholds['lower_limit']
                        ax.hlines(y=lower, xmin=x[i] - width, xmax=x[i] + width, colors='blue', linestyles='dashed',
                                  alpha=0.7)
                        # 임계점 텍스트 추가
                        ax.text(x[i], lower, f"{lower}%", ha='center', va='top', color='blue', fontsize=f(9))

        # 차트 설정
        ax.set_title(title, fontsize=kwargs.get('title_fontsize', 20))
        ax.set_xlabel(xlabel, fontsize=kwargs.get('label_fontsize', 18))
        ax.set_ylabel(ylabel, fontsize=kwargs.get('label_fontsize', 18))

        # y축 범위 설정
        if 'ylim' in kwargs:
            ax.set_ylim(kwargs['ylim'])
        else:
            # 여유 공간 추가
            ax.set_ylim(0, max(max(orig_values, default=0), max(adj_values, default=0)) * 1.2)

        ax.set_xticks(x)
        ax.set_xticklabels(all_keys, fontsize=kwargs.get('tick_fontsize', 14))
        ax.tick_params(axis='y', labelsize=kwargs.get('tick_fontsize', 14))

        # 범례 추가
        if kwargs.get('show_legend', True):
            ax.legend(fontsize=f(9))

        # 그리드 추가
        if kwargs.get('show_grid', True):
            ax.grid(alpha=kwargs.get('grid_alpha', 0.3), linestyle=kwargs.get('grid_style', '--'))

        return ax