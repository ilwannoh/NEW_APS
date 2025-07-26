import os
from datetime import datetime
from app.views.components.common.enhanced_message_box import EnhancedMessageBox
from app.utils.week_plan_manager import WeeklyPlanManager
from app.utils.field_filter import filter_internal_fields
from app.models.common.settings_store import SettingsStore

"""파일 내보내기 작업 클래스"""


class ExportManager:
    """
    데이터를 엑셀파일로 내보내는 통합 메서드
    Parameters:
            parent: 부모 위젯 (QMessageBox 표시용)
            data_df: 내보낼 데이터프레임
            start_date: 시작 날짜 (QDate 객체)
            end_date: 종료 날짜 (QDate 객체)
            is_planning: 사전할당 페이지에서 내보내기인지 여부

        Returns:
            성공 시 파일 경로, 실패 시 None
    """

    @staticmethod
    def export_data(parent, data_df, start_date=None, end_date=None, is_planning=False):
        try:
            if data_df is None or data_df.empty:
                EnhancedMessageBox.show_validation_error(parent, "Export Error", "No data to export")
                return None

            # 데이터 필터링
            export_df = filter_internal_fields(data_df)

            # 설정에서 저장 경로 가져오기
            save_base_path = SettingsStore.get("op_SavingRoute", "")

            # 만약 설정값이 없다면 기존 바탕화면 경로로 대체
            if not save_base_path:
                save_base_path = os.path.join(os.path.expanduser("~"), "Desktop")
                if not os.path.exists(save_base_path) and os.name == 'nt':
                    save_base_path = os.path.join(os.path.expanduser("~"), "바탕 화면")

            now = datetime.now()
            date_str = now.strftime("%Y%m%d")
            time_str = now.strftime("%H%M%S")

            # 저장 경로를 기반으로 주차 폴더 생성
            plan_manager = WeeklyPlanManager(output_dir=save_base_path)
            week_info, _, _ = plan_manager.get_week_info(start_date, end_date)
            week_folder = os.path.join(save_base_path, week_info)
            os.makedirs(week_folder, exist_ok=True)

            # 사전할당 페이지에서 호출된 경우
            if is_planning:
                file_name = f"LP_{date_str}_{time_str}.xlsx"
                file_path = os.path.join(week_folder, file_name)

                export_df.to_excel(file_path, index=False)

                EnhancedMessageBox.show_validation_success(
                    parent,
                    "Export Success",
                    f"Export successful!\nSaved to:\n{file_path}"
                )
                return file_path
            else:
                try:
                    saved_path = plan_manager.save_plan_with_metadata(
                        export_df, start_date, end_date
                    )

                    EnhancedMessageBox.show_validation_success(
                        parent,
                        "Export Success",
                        f"Export successful!\nSaved to:\n{saved_path}"
                    )
                    return saved_path

                except Exception as e:
                    print(f"Error saving metadata: {e}")

                    # 메타데이터 저장 실패 시 fallback 저장
                    default_filename = f"Result_fallback_{date_str}_{time_str}.xlsx"
                    fallback_path = os.path.join(week_folder, default_filename)

                    export_df.to_excel(fallback_path, index=False)

                    EnhancedMessageBox.show_validation_success(
                        parent,
                        "Export Success",
                        f"Export successful (metadata save failed).\nSaved to:\n{fallback_path}"
                    )
                    return fallback_path

        except Exception as e:
            print(f"Error during export process: {str(e)}")

            EnhancedMessageBox.show_validation_error(
                parent,
                "Export Error",
                f"An error occurred during export:\n{str(e)}"
            )
            return None
