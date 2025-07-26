"""
이벤트 발생 시 사용하는 공통 클래스 (observer pattern)
"""
class EventBus :
    listeners = {}

    """
    이벤트에 콜백함수 등록
    """
    @classmethod
    def on(cls, event, callback) :
        if event not in cls.listeners :
            cls.listeners[event] = []
        cls.listeners[event].append(callback)

    """
    이벤트의 콜백함수 제거
    """
    @classmethod
    def off(cls, event, callback=None) :
        if event in cls.listeners :
            if callback :
                cls.listeners[event].remove(callback)
            else :
                cls.listeners[event] = []

    """
    이벤트 발생(실행)시키는 함수
    """
    @classmethod
    def emit(cls, event, *args, **kwargs) :
        if event in cls.listeners :
            for callback in cls.listeners[event] :
                callback(*args, **kwargs)