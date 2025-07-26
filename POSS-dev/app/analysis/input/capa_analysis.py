import pandas as pd
from app.models.common.project_grouping import ProjectGroupManager
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, CalculationError
)

"""
분석 테이블 생성
"""
class PjtGroupAnalyzer:

    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def __init__(self, processed_data):
        if processed_data is None :
            raise DataError('Invalid processed data : None provided')
        
        self.processed_data = processed_data
        self.demand_items = processed_data.get('demand_items', [])

        if not self.demand_items :
            raise DataError('No demand items found in processed data')
        
        self.project_to_buildings = processed_data.get('project_to_buildings', {})
        self.line_capacities = processed_data.get('line_capacities', {})
        self.building_constraints = processed_data.get('building_constraints', {})
        self.line_available_df = processed_data.get('line_available_df', pd.DataFrame())
        self.capa_qty_df = processed_data.get('capa_qty_df', pd.DataFrame())

        if self.line_available_df.empty :
            raise DataError('Line availability data is empty')
        
        if self.capa_qty_df.empty :
            raise DataError('Capacity quantity data is empty')
        
        self.group_manager = ProjectGroupManager()

    """
    그룹 내의 프로젝트들이 사용할 수 있는 라인의 총 용량 계산
    """
    @error_handler(
        show_dialog=True,
        default_return=0
    )
    def calculate_capa_for_group(self, group_projects, line_available_df=None, capa_qty_df=None):
        if not group_projects :
            return 0
        
        if line_available_df is None:
            line_available_df = self.line_available_df

        if capa_qty_df is None:
            capa_qty_df = self.capa_qty_df
        
        total_capa = 0
        
        try :
            used_lines = self.group_manager.get_group_lines(group_projects, line_available_df)
            
            for line in used_lines:
                line_capa = 0
                
                try :
                    if 'Line' in capa_qty_df.columns:
                        line_row = capa_qty_df[capa_qty_df['Line'] == line]
                        
                        if not line_row.empty:
                            numeric_cols = [col for col in capa_qty_df.columns 
                                        if isinstance(col, int) or 
                                            (isinstance(col, str) and col.isdigit())]
                            
                            for col in numeric_cols:
                                try :
                                    if pd.notna(line_row[col].iloc[0]) and line_row[col].iloc[0] > 0:
                                        line_capa += float(line_row[col].iloc[0])
                                except (IndexError, ValueError) as e :
                                    continue
                except Exception as e :
                    continue
                                
                total_capa += line_capa
        except Exception as e :
            raise CalculationError(f'Error calculating capacity for group : {str(e)}')

        return total_capa

    """
    분석 테이블 생성
    """
    @error_handler(
        show_dialog=True,
        default_return=pd.DataFrame()
    )
    def create_analysis_table(self, line_available_df=None, capa_qty_df=None):
        if line_available_df is None:
            line_available_df = self.line_available_df

        if capa_qty_df is None:
            capa_qty_df = self.capa_qty_df

        if line_available_df.empty :
            raise DataError('Line availability data is empty')
        
        if capa_qty_df.empty :
            raise DataError('Capacity quantity data is empty')
            
        try :
            project_groups = self.group_manager.create_project_groups(line_available_df)
        
            if not project_groups :
                raise DataError('No project group could be created')
            
            results = []
            
            for group_name, group_projects in project_groups.items():
                try :
                    group_capa = safe_operation(
                        self.calculate_capa_for_group,
                        f'Error calculating capacity for group {group_name}',
                        group_projects, line_available_df, capa_qty_df
                    ) or 0

                    group_total_mfg = 0
                    group_total_sop = 0
                    
                    for project in group_projects :
                        project_mfg = 0
                        project_sop = 0
                        
                        for item in self.demand_items :
                            try :
                                item_project = item.get('Project', '')
                                
                                if item_project == project :
                                    mfg_value = item.get('MFG', 0)
                                    project_mfg += float(mfg_value) if pd.notna(mfg_value) else 0

                                    sop_value = item.get('SOP', 0)
                                    sop_value = float(sop_value) if pd.notna(sop_value) else 0
                                    project_sop += max(0, sop_value)
                            except (ValueError, TypeError) as e :
                                continue
                        
                        group_total_mfg += project_mfg
                        group_total_sop += project_sop
                        
                        results.append({
                            'PJT Group': group_name,
                            'PJT': project,
                            'MFG': project_mfg,
                            'SOP': project_sop,
                            'CAPA': '',
                            'MFG/CAPA': '',
                            'SOP/CAPA': ''
                        })
                    
                    mfg_capa_ratio = group_total_mfg / group_capa if group_capa > 0 else 0
                    sop_capa_ratio = group_total_sop / group_capa if group_capa > 0 else 0
                    
                    results.append({
                        'PJT Group': group_name,
                        'PJT': 'Total',
                        'MFG': group_total_mfg,
                        'SOP': group_total_sop,
                        'CAPA': group_capa,
                        'MFG/CAPA': mfg_capa_ratio,
                        'SOP/CAPA': sop_capa_ratio,
                        'isOverMFG': mfg_capa_ratio > 1,
                        'isOverSOP': sop_capa_ratio > 1
                    })
                except Exception as e :
                    continue

            if not results :
                return pd.DataFrame()
        
            results_df = pd.DataFrame(results)
            
            sorted_results = []

            for group in results_df['PJT Group'].unique():
                try :
                    group_data = results_df[results_df['PJT Group'] == group]
                    total_row = group_data[group_data['PJT'] == 'Total']
                    other_rows = group_data[group_data['PJT'] != 'Total'].sort_values('MFG', ascending=False)

                    if not total_row.empty and not other_rows.empty :
                        sorted_results.append(pd.concat([other_rows, total_row], ignore_index=True))
                    elif not other_rows.empty :
                        sorted_results.append(other_rows)
                    elif not total_row.empty :
                        sorted_results.append(total_row)
                except Exception as e :
                    continue

            if not sorted_results :
                return pd.DataFrame()
            
            final_df = pd.concat(sorted_results, ignore_index=True)
            
            final_df['status'] = ''

            for idx in final_df.index :
                try :
                    if final_df.loc[idx, 'PJT'] == 'Total' and 'isOverMFG' in final_df.columns:
                        if final_df.loc[idx, 'isOverMFG']:
                            final_df.loc[idx, 'status'] = 'Error'
                except Exception as e :
                    continue
            
            return final_df
        except Exception as e :
            raise CalculationError(f'Error creating analysis table : {str(e)}')

    """
    요약 정보 생성
    """
    @error_handler(
        show_dialog=True,
        default_return=pd.Series()
    )
    def create_summary(self, analysis_df):
        if analysis_df is None or analysis_df.empty :
            raise DataError('Analysis DataFrame is empty or None')
        
        try :
            total_rows = analysis_df[analysis_df['PJT'] == 'Total']

            if total_rows.empty :
                raise DataError('No \'Total\' rows found in analysis data')
            
            summary = {
                'Total number of groups': len(total_rows),
                'Number of error groups': len(total_rows[total_rows['status'] == 'Error']),
                'Total MFG': total_rows['MFG'].sum(),
                'Total SOP': total_rows['SOP'].sum(),
                'Total CAPA': total_rows['CAPA'].sum(),
                'Total MFG/CAPA ratio': f"{total_rows['MFG'].sum() / total_rows['CAPA'].sum():.1%}"
                    if total_rows['CAPA'].sum() > 0 else '0%',
                'Total SOP/CAPA ratio': f"{total_rows['SOP'].sum() / total_rows['CAPA'].sum():.1%}"
                    if total_rows['CAPA'].sum() > 0 else '0%'
            }
            return pd.Series(summary)
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error creating summary : {str(e)}')
            raise

    """
    결과를 데이터프레임 형식으로 출력
    """
    @error_handler(
        show_dialog=True,
        default_return=pd.DataFrame()
    )
    def format_results_for_display(self, analysis_df) :
        if analysis_df is None or analysis_df.empty :
            raise DataError('Analysis DataFrame is empty or None')
        
        try :
            display_df = analysis_df.copy().astype(object)
            
            for idx in display_df.index :
                try :
                    if display_df.loc[idx, 'PJT'] == 'Total':
                        if pd.notna(display_df.loc[idx, 'MFG/CAPA']):
                            display_df.loc[idx, 'MFG/CAPA'] = f"{display_df.loc[idx, 'MFG/CAPA']:.2f}"
                        if pd.notna(display_df.loc[idx, 'SOP/CAPA']):
                            display_df.loc[idx, 'SOP/CAPA'] = f"{display_df.loc[idx, 'SOP/CAPA']:.2f}"
                    else:
                        display_df.loc[idx, 'MFG/CAPA'] = ''
                        display_df.loc[idx, 'SOP/CAPA'] = ''
                except Exception as e :
                    continue
            
            for idx in display_df.index :
                try :
                    if pd.notna(display_df.loc[idx, 'MFG']):
                        mfg_value = int(display_df.loc[idx, 'MFG'])
                        display_df.loc[idx, 'MFG'] = f"{mfg_value:,}"
                        if display_df.loc[idx, 'PJT'] == 'Total' and 'isOverMFG' in analysis_df.columns:
                            if analysis_df.loc[idx, 'isOverMFG']:
                                display_df.loc[idx, 'MFG'] += " (Exceeded)"
                    
                    if pd.notna(display_df.loc[idx, 'SOP']):
                        sop_value = int(display_df.loc[idx, 'SOP'])
                        display_df.loc[idx, 'SOP'] = f"{sop_value:,}"
                        if display_df.loc[idx, 'PJT'] == 'Total' and 'isOverSOP' in analysis_df.columns:
                            if analysis_df.loc[idx, 'isOverSOP']:
                                display_df.loc[idx, 'SOP'] += " (Exceeded)"
                except Exception as e :
                    continue
            
            for idx in display_df.index :
                try :
                    if display_df.loc[idx, 'PJT'] == 'Total' and pd.notna(display_df.loc[idx, 'CAPA']):
                        capa_value = int(display_df.loc[idx, 'CAPA'])
                        display_df.loc[idx, 'CAPA'] = f"{capa_value:,}"
                    else:
                        display_df.loc[idx, 'CAPA'] = ''
                except Exception as e :
                    continue
            
            result_cols = ['PJT Group', 'PJT', 'MFG', 'SOP', 'CAPA', 'MFG/CAPA', 'SOP/CAPA']
            
            if 'status' in display_df.columns :
                display_df.loc[display_df['status'] == '이상', 'status'] = 'Error'
                result_cols.append('status')
            
            return display_df[result_cols]
        except Exception as e :
            raise CalculationError(f'Error formatting results for display : {str(e)}')

    """
    분석 결과 저장
    """
    @error_handler(
        show_dialog=True,
        default_return={}
    )
    def print_analysis_results(self, analysis_df=None, summary=None, display_df=None) :
        try :
            if analysis_df is None :
                analysis_df = safe_operation(
                    self.create_analysis_table,
                    'Error creating analysis table'
                )

                if analysis_df is None or analysis_df.empty :
                    raise DataError('Failed to create analysis table')
            
            if display_df is None :
                display_df = safe_operation(
                    self.format_results_for_display,
                    'Error formatting results for display',
                    analysis_df
                )

                if display_df is None or display_df.empty :
                    raise DataError('Failed to format results for display')
            
            if summary is None :
                summary = safe_operation(
                    self.create_summary,
                    'Error creating summary',
                    analysis_df
                )

                if summary is None or summary.empty :
                    raise DataError('Failed to create summary')
            
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            
            try :
                anomaly_groups = display_df[(display_df['PJT'] == 'Total') & (display_df['status'] == 'Error')]
                if not anomaly_groups.empty :

                    for idx, row in anomaly_groups.iterrows() :
                        try :
                            group_name = row['PJT Group']
                            original_idx = analysis_df[(analysis_df['PJT Group'] == group_name) & 
                                                    (analysis_df['PJT'] == 'Total')].index
                            
                            if len(original_idx) > 0 :
                                original_idx = original_idx[0]
                                mfg = analysis_df.loc[original_idx, 'MFG']
                                capa = analysis_df.loc[original_idx, 'CAPA']
                            
                                shortage = mfg - capa
                        except Exception as e :
                            continue
            except Exception as e :
                pass
            
            return {
                'analysis_df': analysis_df,
                'display_df': display_df,
                'summary': summary
            }
        except Exception as e :
            raise CalculationError(f'Error printing analysis results : {str(e)}')

    """
    전체 분석 수행 및 결과 반환
    """
    @error_handler(
        show_dialog=True,
        default_return={}
    )
    def analyze(self) :
        try :
            analysis_df = safe_operation(
                self.create_analysis_table,
                'Error creating analysis table'
            )

            if analysis_df is None or analysis_df.empty :
                raise DataError('Failed to create analysis table')
            
            summary = safe_operation(
                self.create_summary,
                'Error creating summary',
                analysis_df
            )

            if summary is None or summary.empty :
                raise DataError('Failed to create summary')
            
            display_df = safe_operation(
                self.format_results_for_display,
                'Error formatting results for display',
                analysis_df
            )

            if display_df is None or display_df.empty :
                raise DataError('Failed to format results for display')
            
            results = safe_operation(
                self.print_analysis_results,
                'Error printing analysis results',
                analysis_df, summary, display_df
            )

            if results is None :
                raise DataError('Failed to print analysis results')
                        
            return results
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error in analyze method : {str(e)}')
            raise