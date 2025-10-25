# xmlrpcutils

XML-RPC Server Simplification.

## 安装

```
pip install xmlrpcutils
```

## TestServer测试服务器

```
from xmlrpcutils.server import SimpleXmlRpcServer
from xmlrpcutils.service import ServiceBase

class SayHelloService(ServiceBase):

    def hello(self, name):
        return f"Hello {name}, how are you!"

class TestServer(SimpleXmlRpcServer):
    
    def register_services(self):
        super().register_services()
        SayHelloService(namespace="debug").register_to(self.server)

app =  TestServer()
app_ctrl = app.get_controller()

if __name__ == "__main__":
    app_ctrl()

```

## 启动测试服务器

```
python test_server.py
```

## 远程调用xmlrpc测试服务器

```
In [9]: from xmlrpc.client import ServerProxy

In [10]: server = ServerProxy('http://127.0.0.1:8381')

In [11]: server.system.listMethods()
Out[11]:
['debug.counter',
 'debug.echo',
 'debug.false',
 'debug.hello',
 'debug.hostname',
 'debug.null',
 'debug.ping',
 'debug.sleep',
 'debug.sum',
 'debug.timestamp',
 'debug.true',
 'debug.uname',
 'debug.urandom',
 'debug.uuid4',
 'system.listMethods',
 'system.methodHelp',
 'system.methodSignature',
 'system.multicall']

In [12]: server.debug.hello('world')
Out[12]: 'Hello world, how are you!'
```

## 使用apikey认证

*服务器端在配置文件中增加apikeys配置*

```
apikey-auth-header: apikey
apikeys:
  HyuTMsNzcSZYmwlVDdacERde9azdTKT8:
    appid: test01
    other-app-info: xxx
  SEEpVkus5b86aHxS6UMSCFLxkIhYMMZF:
    appid: test02
    other-app-info: xxx
```

*客户端在初始化ServerProxy中指定*

```
In [93]: from xmlrpc.client import ServerProxy
    ...: service = ServerProxy("http://127.0.0.1:8911", headers=[("apikey", "HyuTMsNzcSZYmwlVDdacERde9azdTKT8")])
    ...: result = service.debug.ping()
    ...: print(result)
pong
```

## 服务端启用keepalive

```
keepalive:
    enable: true
    timeout: 5
    max: 60
```

默认情况下，服务端不启用http的keepalive特性。在配置文件中设置keepalive.enable=true后启用。

## 启用服务端版本

```
server-tokens: true
```

默认情况下，服务端响应时已经将Server响应头隐藏。在配置文件中设置server-tokens=true显示。


## 启用methodSignature

```
def myfunc1(arg1:int, arg2:str, arg3:list) -> str:
    pass
```

- 使用参数类型注释来启用methodSignature。


```
def myfunc2(arg1, arg2, arg3):
    """
    @methodSignature: ["str", "int", "str", "list"]
    """
    pass
```

- 在函数文档中使用`@methodSignature:`来启用methodSignature。

```
def myfunc3(args, arg1, arg2, arg3):
    pass
myfunc3._methodSignature = ["str", "int", "str", "list"]
```

- 使用函数属性来启用methodSignature。

## 其它配置项

```
pidfile: app.pid
daemon: True
workspace: /app
loglevel: INFO
logfile: app.log
logfmt: default
server:
  listen: ["0.0.0.0", 8381]
  daemon: false
```

## 注意

- python3.7及以下版本，不支持在ServerProxy中使用headers参数，所以添加apikey检验机制时，需要使用高版本客户端。或定制transport参数。

## 版本

### v0.1.1

- 初始版本。

### v0.1.2

- 修正安装包打包时缺少license_files的问题。

### v0.1.3

- 修正DebugService的__init__方法，补充super().__init__()的调用。

### v0.2.0

- 不强制使用gevent。
- 允许注册无命名空间函数。

### v0.3.1

- 清理gevent遗留。
- 增加apikey认证机制。客户端通过headers指定apikey。

### v0.3.2

- 修正get_ignore_methods函数命名。

### v0.4.0

- 增加server-tokens选项，允许用户隐藏和显示Server请求头。默认为隐藏Server请求头。
- 增加keepalive选项，支持keepalive特性。

### v0.4.2

- 文档更新。

### v0.4.3

- 文档修正。
- 添加methodSignature支持。

### v0.4.4

- 修正methodSignature返回值类型。应该反馈[[...], [...]]类型，或"signatures not supported"。

### v0.4.5

- 文档更新。

### v0.5.0

- 添加xrpc命令。
- 允许在配置在文件中指定services。

### v0.5.1

- Doc update.
