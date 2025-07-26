import pandas as pd
from app.models.input.material import process_material_data
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, CalculationError
)

class MaterialAnalyzer :

    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def __init__(self) :
        self.material_data = None
        self.material_df = None
        self.date_columns = []
        self.weekly_columns = []
        self.weekly_shortage_materials = None
        self.full_period_shortage_materials = None
        self.shortage_materials = None

    """
    자재 데이터 분석 후 결과 저장
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def analyze(self) :
        try :
            self.material_data = safe_operation(
                process_material_data,
                'Failed to process material data'
            )

            if not self.material_data or 'material_df' not in self.material_data :
                raise DataError('Missing material data or material_df key')
            
            self.material_df = self.material_data['material_df']

            if self.material_df is None or self.material_df.empty :
                raise DataError('Material DataFrame is empty or None')
            
            self.date_columns = self.material_data.get('date_columns', [])
            self.weekly_columns = self.material_data.get('weekly_columns', [])

            safe_operation(
                self.calculate_shortage_amounts,
                'Error calculating shortage amounts'
            )

            safe_operation(
                self.analyze_shortage_materials,
                'Error analyzing shortage materials'
            )

            return True
        except Exception as e :
            if not isinstance(e, DataError) :
                raise DataError(f'Error in analyze method : {str(e)}')
            raise
    
    """
    자재별 부족량 계산
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def calculate_shortage_amounts(self) :
        try :
            if self.material_df is None :
                raise DataError('Material DataFrame is None')
            
            if 'On-Hand' not in self.material_df.columns :
                raise DataError('On-Hand column not found in material data')
            
            self.material_df['Weekly_Sum'] = self.material_df['On-Hand'].copy()

            for col in self.weekly_columns :
                if col in self.material_df.columns :
                    self.material_df['Weekly_Sum'] += self.material_df[col]

            self.material_df['Full_Period_Sum'] = self.material_df['On-Hand'].copy()

            for col in self.date_columns :
                if col in self.material_df.columns :
                    self.material_df['Full_Period_Sum'] += self.material_df[col]

            self.material_df['Weekly_Shortage'] = self.material_df['Weekly_Sum'].apply(
                lambda x : abs(x) if x < 0 else 0
            )
            self.material_df['Full_Period_Shortage'] = self.material_df['Full_Period_Sum'].apply(
                lambda x : abs(x) if x < 0 else 0
            )

            self.material_df['Shortage_Rate'] = 0.0

            mask = (self.material_df['On-Hand'] > 0) & (self.material_df['Weekly_Shortage'] > 0)

            try :
                self.material_df.loc[mask, 'Shortage_Rate'] = (
                    self.material_df.loc[mask, 'Weekly_Shortage'] / self.material_df.loc[mask, 'On-Hand'] * 100
                )
            except Exception as e :
                self.material_df.loc[mask, 'Shortage_Rate'] = 0.0
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error calculating shortage amounts : {str(e)}')
            raise

    """
    부족한 자재 식별하고 분석
    """
    def analyze_shortage_materials(self) :
        try :
            if self.material_df is None :
                raise DataError('Material DataFrame is None')
            
            if 'Weekly_Sum' not in self.material_df.columns :
                raise DataError('Weekly_Sum column not found, please calculate shortage amounts first')
            
            try :
                self.weekly_shortage_materials = self.material_df[self.material_df['Weekly_Sum'] < 0].copy()
            except Exception as e :
                raise CalculationError(f'Error creating weekly shortage materials : {str(e)}')

            try :
                self.full_period_shortage_materials = self.material_df[self.material_df['Full_Period_Sum'] < 0].copy()
            except Exception as e :
                raise CalculationError(f'Error creating full period shortage materials : {str(e)}')

            try :
                if 'Material' in self.material_df.columns :
                    self.shortage_materials = pd.concat([
                        self.weekly_shortage_materials,
                        self.full_period_shortage_materials[~self.full_period_shortage_materials['Material'].isin(
                            self.weekly_shortage_materials['Material'])]
                    ]).drop_duplicates(subset = ['Material'])
                else :
                    self.shortage_materials = pd.concat([
                        self.weekly_shortage_materials,
                        self.full_period_shortage_materials
                    ]).drop_duplicates()
            except Exception as e :
                raise CalculationError(f'Error combining shortage materials : {str(e)}')

            if not self.weekly_shortage_materials.empty :
                try :
                    self.weekly_shortage_materials = self.weekly_shortage_materials.sort_values(
                        by = 'Full_Period_Shortage', ascending=False)
                except Exception as e :
                    pass
                
            if not self.shortage_materials.empty :
                try :
                    self.shortage_materials = self.shortage_materials.sort_values(
                        by='Weekly_Shortage', ascending=False)
                except Exception as e :
                    pass
        except Exception as e :
            if not isinstance(e, (DataError, CalculationError)) :
                raise CalculationError(f'Error analyzing shortage materials : {str(e)}')
            raise
            
    """
    4/7 ~ 4/13 동안 부족한 자재 리포트 반환
    """
    @error_handler(
        show_dialog=True,
        default_return='자재 부족 리포트를 생성할 수 없습니다'
    )
    def get_weekly_shortage_report(self) :
        try :
            if self.weekly_shortage_materials is None :
                raise DataError('Weekly shortage materials is None')
            
            report = []
            report.append(f'[일주일 내 부족한 자재 리포트 (총 {len(self.weekly_shortage_materials)}개)]')
            report.append('=' * 70)
            report.append(f'{'자재코드':<15} {'Active':<6} {'On-Hand':<10} {'부족량':<10} {'부족률 (%)':<10}')
            report.append('-' * 70)

            for _, row in self.weekly_shortage_materials.iterrows() :
                try :
                    material = row.get('Material', 'Unknown')
                    active = row.get('Active_OX', 'N/A')
                    on_hand = float(row.get('On-Hand', 0))
                    shortage = float(row.get('Weekly_Shortage', 0))
                    shortage_rate = float(row.get('Shortage_Rage', 0))

                    report.append(f"{material:<15} {active:<6} {on_hand:<10.0f} {shortage:<10.0f} {shortage_rate:<10.1f}")
                except Exception as e :
                    continue

            return '\n'.join(report)
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error generating weekly shortage report : {str(e)}')
            raise
    
    """
    가장 심각하게 부족한 자재 목록 반환(10개)
    """
    @error_handler(
        show_dialog=True,
        default_return=pd.DataFrame()
    )
    def get_critical_shortage_materials(self, limit=10) :
        try :
            if self.weekly_shortage_materials is None :
                raise DataError('Weekly shortage materials is None')
            
            if self.weekly_shortage_materials.empty :
                return pd.DataFrame()
            
            try :
                if 'Weekly_Shortage' in self.weekly_shortage_materials.columns :
                    critical_materials = self.weekly_shortage_materials.sort_values(
                        by='Weekly_Shortage', ascending=False).head(limit)
                    return critical_materials
                else :
                    return self.weekly_shortage_materials.head(limit)
            except Exception as e :
                return self.weekly_shortage_materials.head(limit)
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error getting critical shortage materials : {str(e)}')
            raise
    
    """
    커스텀한 기준에 따라 부족한 자재 정렬 후 반환
    """
    def get_shortage_materials_by_criteria(self, criteria='quantity', limit=None) :
        try :
            if self.weekly_shortage_materials is None :
                raise DataError('Weekly shortage materials is None')
            
            if self.weekly_shortage_materials.empty :
                return pd.DataFrame()
            
            sorted_materials = self.weekly_shortage_materials.copy()

            try :
                if criteria == 'quantity' :
                    sorted_materials = sorted_materials.sort_values(by='Weekly_Shortage', ascending=False)
                elif criteria == 'rate' :
                    sorted_materials = sorted_materials.sort_values(by='Shortage_Rate', ascending=False)
                elif criteria == 'code' :
                    sorted_materials = sorted_materials.sort_values(by='Material')
            except Exception as e :
                pass

            if limit :
                sorted_materials = sorted_materials.head(limit)

            return sorted_materials
        except Exception as e :
            if not isinstance(e, DataError) :
                raise CalculationError(f'Error getting shortage materials by criteria : {str(e)}')
            raise
    
    """
    일별 부족 추이 계산
    """
    def get_daily_shortage_trend(self, material_code = None) :
        try :
            if self.material_df is None :
                raise DataError('Material DataFrame is None')
            
            if material_code :
                try :
                    material_df = self.material_df[self.material_df['Material'] == material_code]

                    if material_df.empty :
                        return None
                    
                    material_row = material_df.iloc[0]
                    daily_trend = {'Date' : [], 'Cumulative' : []}

                    cumulative = float(material_row.geT('On-Hand', 0))
                    daily_trend['Date'].append('Current')
                    daily_trend['Cumulative'].append(cumulative)

                    for date_col in self.date_columns :
                        if date_col in material_row :
                            try :
                                cumulative += float(material_row.get(date_col, 0))
                                daily_trend['Date'].append(date_col)
                                daily_trend['Cumulative'].append(cumulative)
                            except (ValueError, TypeError) :
                                continue

                    return pd.DataFrame(daily_trend)
                except Exception as e :
                    raise CalculationError(f'Error calculating daily trend for material {material_code} : {str(e)}')
            else :
                try :
                    critical_materials = safe_operation(
                        self.get_critical_shortage_materials,
                        'Error getting critical shortage materials',
                        5
                    )
                    
                    if critical_materials is None or critical_materials.empty :
                        return None
                    
                    date_shortage_count = {'Date' : ['Current'] + self.date_columns, 'Shortage_Count' : [0] * (len(self.date_columns) + 1)}

                    for _, material_row in critical_materials.iterrows() :
                        try :
                            cumulative = float(material_row.get('On-Hand', 0))

                            if cumulative < 0 :
                                date_shortage_count['Shortage_Count'][0] += 1

                            for i, date_col in enumerate(self.date_columns) :
                                if date_col in material_row :
                                    try :
                                        cumulative += float(material_row.get(date_col, 0))

                                        if cumulative < 0 :
                                            date_shortage_count['Shortage_Count'][i + 1] += 1
                                    except (ValueError, TypeError) :
                                        continue
                        except Exception as e :
                            continue

                    return pd.DataFrame(date_shortage_count)
                except Exception as e :
                    raise CalculationError(f'Error calculating overall daily trend : {str(e)}')
        except Exception as e :
            if not isinstance(e, (DataError, CalculationError)) :
                raise CalculationError(f'Error in get_daily_shortage_trend : {str(e)}')
            raise
            
    """
    부족한 자재 상세 정보 로그 출력
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def print_shortage_details(self, detailed=False) :
        try :
            if self.weekly_shortage_materials is None or self.weekly_shortage_materials.empty :
                print('부족한 자재가 없습니다')
                return
            
            weekly_report = safe_operation(
                self.get_weekly_shortage_report,
                'Error getting weekly shortage report'
            )

            if weekly_report :
                print(weekly_report)
                print('\n')

            if detailed and not self.weekly_shortage_materials.empty :
                print('부족 자재 상세 정보')
                
                try :
                    critical_materials = self.weekly_shortage_materials.head(10)

                    for idx, (_, row) in enumerate(critical_materials.iterrows(), 1) :
                        try :
                            material = row.get('Material', 'Unknown')
                            on_hand = float(row.get('On-Hand', 0))
                            weekly_sum = float(row.get('Weekly_Sum', 0))
                            weekly_shortage = float(row.get('Weekly_Shortage', 0))

                            print(f"\n{idx}. 자재코드: {material} (부족량: {weekly_shortage:.0f})")
                            print(f"   현재고(On-Hand): {on_hand:.0f}")
                            print(f"   주간합계(Weekly_Sum): {weekly_sum:.0f}")

                            print('일별 누적 추이')
                            cumulative = on_hand
                            print(f'{cumulative:.0f}')

                            for date_col in self.weekly_columns :
                                if date_col in row :
                                    try :
                                        daily_value = float(row.get(date_col, 0))
                                        cumulative += daily_value
                                        status = '부족' if cumulative < 0 else '정상'

                                        print(f"   - {date_col}: {daily_value:.0f} (누적: {cumulative:.0f}, {status})")
                                    except (ValueError, TypeError) :
                                        continue
                        except Exception as e :
                            continue
                except Exception as e :
                    print(f"부족 자재 상세 정보 출력 중 오류 발생: {str(e)}")
        except Exception as e :
            raise CalculationError(f'Error printing shortage details : {str(e)}')

    """
    결과를 로그에 띄우는 함수
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def analyze_material_shortage() :
        try :
            analyzer = MaterialAnalyzer()

            analysis_success = safe_operation(
                analyzer.analyze,
                'Error in material analysis'
            )

            if analysis_success :
                safe_operation(
                    analyzer.print_shortage_details,
                    'Error printing shortage details',
                    detailed=True
                )

                if analyzer.weekly_shortage_materials is not None :
                    weekly_count = len(analyzer.weekly_shortage_materials)
                    print(f"\n주간(4/7~4/13) 부족 자재 총 {weekly_count}개")

                if analyzer.full_period_shortage_materials is not None :
                    full_count = len(analyzer.full_period_shortage_materials)
                    print(f"전체 기간(4/7~4/20) 부족 자재 총 {full_count}개")

                return {
                    'weekly_shortage' : analyzer.weekly_shortage_materials,
                    'full_period_shortage' : analyzer.full_period_shortage_materials,
                    'all_materials' : analyzer.material_df
                }
            else :
                print('자재 분석에 실패했습니다')
                return None
        except Exception as e :
            raise CalculationError(f'Error in analyze_material_shortage : {str(e)}')