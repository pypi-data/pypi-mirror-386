class Message:
    __slots__ = ('key', 'weight', 'messageTemplate', 'timerTemplate', 'messageTemplate_styled')

    def __init__(self, key: str, weight: int = 10, messageTemplate: str | None = None, timerTemplate: str | None = None, messageTemplate_styled: str | None = None):
        '''
        - Args
            - weight: 权重，更高的权重意味着更高的日志级别
            - messageTemplate: 日志消息模板，未设置时默认为`CheeseLogger`实例的`messageTemplate`
            - timerTemplate: 日期模板，未设置时默认为`CheeseLogger`实例的`timerTemplate`
            - messageTemplate_styled: 带样式的日志消息模板，未设置时默认为`CheeseLogger`实例的`messageTemplate_styled`
        '''

        self.key: str = key
        self.weight: int = weight
        ''' 权重，更高的权重意味着更高的日志级别 '''
        self.messageTemplate: str | None = messageTemplate
        ''' 日志消息模板，未设置时默认为`CheeseLogger`实例的`messageTemplate` '''
        self.timerTemplate: str | None = timerTemplate
        ''' 日期模板，未设置时默认为`CheeseLogger`实例的`timerTemplate` '''
        self.messageTemplate_styled: str | None = messageTemplate_styled
        ''' 带样式的日志消息模板，未设置时默认为`CheeseLogger`实例的`messageTemplate_styled` '''
