# app/views/components/settings_dialogs/settings_components/__init__.py - 모던한 설정 컴포넌트 패키지 초기화
from .basic_tab import ModernBasicTabComponent
from .pre_option_tab import ModernPreOptionTabComponent
from .detail_tab import ModernDetailTabComponent
from .settings_section import ModernSettingsSectionComponent

# 기존 호환성을 위한 별칭
BasicTabComponent = ModernBasicTabComponent
PreOptionTabComponent = ModernPreOptionTabComponent
DetailTabComponent = ModernDetailTabComponent
SettingsSectionComponent = ModernSettingsSectionComponent

# 외부에서 import 가능하도록 설정
__all__ = [
    'BasicTabComponent',
    'PreOptionTabComponent',
    'DetailTabComponent',
    'SettingsSectionComponent',
    'ModernBasicTabComponent',
    'ModernPreOptionTabComponent',
    'ModernDetailTabComponent',
    'ModernSettingsSectionComponent'
]