# **CheeseLog**

## **介绍**

一款完全动态的日志系统，它有以下特点：

1. 多种的消息等级，可自定义添加新的等级。在打印与日志写入可以使用权重、指定消息或指定模块内的消息进行过滤，实现个性化的消息输出。

2. 支持控制台样式打印，有完善的样式体系可以直接使用，自定义的消息模版可以实现个性化的消息输出，在未有打印环境的情况下停止打印节省资源。

3. 支持日志文件记录，支持动态修改输出文件，可自由开启关闭。

4. 可以输出自定义格式的进度条，这对于一些下载或加载的控制台显示非常有帮助。

目前仍处于开发阶段，各种功能并不保证以后的支持。

## **示例**

### **带有日志文件输出的简易应用**

```python
from CheeseLog import CheeseLogger, Message

logger = CheeseLogger(key = 'myLogger', filePath = 'logs/%Y-%m-%d.log')

logger.debug('This is a debug message.')
logger.info('This is an info message.')
logger.warning('This is a warning message.')
logger.danger('This is a danger message.')
logger.error('This is an error message.')

logger.addMessage(Message('CUSTOM', 30, messageTemplate_styled = '(<blue>%k</blue>) <black>%t</black> > %c'))
logger.print('This is a custom message.', messageKey = 'CUSTOM')
```

### **简单的消息过滤**

```python
from CheeseLog import CheeseLogger, Message

logger = CheeseLogger(key = 'myLogger')
logger.setFilter({
    'weight': 20,
    'messageKeys': [ 'FILTERED' ]
})

lowWeight_message = Message('LOW_WEIGHT', 10)
logger.addMessage(lowWeight_message)
highWeight_message = Message('HIGH_WEIGHT', 50)
logger.addMessage(highWeight_message)
filtered_message = Message('FILTERED', 100)
logger.addMessage(filtered_message)

logger.print('This is a low weight message.', messageKey = 'LOW_WEIGHT') # 不会输出
logger.print('This is a high weight message.', messageKey = 'HIGH_WEIGHT')
logger.print('This is a filtered message.', messageKey = 'FILTERED') # 不会输出
```

### **如何使用进度条实现一个loading效果**

```python
import time, random

from CheeseLog import CheeseLogger, Message, ProgressBar

logger = CheeseLogger(key = 'myLogger', filePath = 'logs/%Y-%m-%d.log')

loadingMessage = Message('LOADING')
logger.addMessage(loadingMessage)
loadedMessage = Message('LOADED', 20, messageTemplate_styled = '(<green>%k</green>) <black>%t</black> > %c')
logger.addMessage(loadedMessage)

progressbar = ProgressBar()
i = 0
while i < 100:
    bar, bar_styled = progressbar(i / 100)
    logger.print(bar, bar_styled, messageKey = 'LOADING', refresh = i != 0)
    time.sleep(random.uniform(0.05, 0.15))
    i += random.uniform(0.5, 1)
logger.print('Loading complete!', messageKey = 'LOADED', refresh = True)
```

## **更多...**

### 1. [**Style**](https://github.com/CheeseUnknown/CheeseLog/blob/master/documents/Style.md)

### 2. [**Message**](https://github.com/CheeseUnknown/CheeseLog/blob/master/documents/Message.md)

### 3. [**Logger**](https://github.com/CheeseUnknown/CheeseLog/blob/master/documents/Logger.md)

### 4. [**Progress Bar**](https://github.com/CheeseUnknown/CheeseLog/blob/master/documents/ProgressBar.md)
